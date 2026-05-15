"""
Carga do modelo relacional no Supabase (PostgreSQL).

Reaproveita a leitura/limpeza e os builders de dimensão de `etl.py`,
traduz o `schema.sql` (dialeto SQLite) para PostgreSQL, recria o schema no
Supabase e carrega tudo via `COPY` (rápido para a tabela fato de ~319k linhas).

Connection string (escolha uma fonte, nesta ordem de prioridade):
  1. argumento  --db-url "postgresql://..."
  2. variável de ambiente  SUPABASE_DB_URL
  3. .streamlit/secrets.toml   ->   [supabase]\n db_url = "postgresql://..."

Uso:
    python db/load_supabase.py
    python db/load_supabase.py --db-url "postgresql://postgres.<ref>:<senha>@aws-0-<regiao>.pooler.supabase.com:5432/postgres"
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
import tomllib
from pathlib import Path

import pandas as pd
import psycopg2

# Reusa a lógica já validada do ETL para SQLite.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import etl  # noqa: E402

HERE = Path(__file__).resolve().parent
SCHEMA_SQLITE = HERE / "schema.sql"
SCHEMA_PG_OUT = HERE / "schema_postgres.sql"
SECRETS_TOML = HERE.parent / ".streamlit" / "secrets.toml"


# ---------------------------------------------------------------------------
# Connection string
# ---------------------------------------------------------------------------

def resolve_db_url(cli_value: str | None) -> str:
    if cli_value:
        url = cli_value
    elif os.environ.get("SUPABASE_DB_URL"):
        url = os.environ["SUPABASE_DB_URL"]
    elif SECRETS_TOML.exists():
        with open(SECRETS_TOML, "rb") as fh:
            data = tomllib.load(fh)
        url = data.get("supabase", {}).get("db_url", "")
    else:
        url = ""

    if not url:
        raise SystemExit(
            "Connection string não encontrada. Defina em "
            f"{SECRETS_TOML} ([supabase] db_url = \"...\"), na env "
            "SUPABASE_DB_URL, ou passe --db-url."
        )
    return url


def parse_pg_url(url: str) -> dict:
    """Parse manual tolerante a caracteres especiais (ex.: '/') na senha,
    que quebrariam o parser de URI do libpq se não fossem percent-encoded.
    A senha é tratada literalmente (como o usuário colou)."""
    _, _, rest = url.partition("://")
    rest, _, query = rest.partition("?")
    creds, _, hostpart = rest.rpartition("@")
    user, _, password = creds.partition(":")
    hostport, _, dbname = hostpart.partition("/")
    host, _, port = hostport.rpartition(":")
    params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
    return {
        "host": host,
        "port": int(port) if port else 5432,
        "user": user,
        "password": password,
        "dbname": dbname or "postgres",
        "sslmode": params.get("sslmode", "require"),
    }


# ---------------------------------------------------------------------------
# Tradução SQLite -> PostgreSQL
# ---------------------------------------------------------------------------

def to_postgres_schema(sqlite_sql: str) -> str:
    pg = sqlite_sql

    # PK surrogate autoincremento
    pg = re.sub(
        r"id\s+INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT",
        "id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY",
        pg,
    )
    # Postgres não aceita CREATE VIEW IF NOT EXISTS
    pg = pg.replace(
        "CREATE VIEW IF NOT EXISTS v_censo_consolidado AS",
        "CREATE VIEW v_censo_consolidado AS",
    )
    return pg


def table_names(sqlite_sql: str) -> list[str]:
    return re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", sqlite_sql)


# Materialized view: roll-up nas dimensões/medidas que o dashboard usa.
# O dashboard faz `SELECT * FROM mv_censo_rollup` (~9k linhas, sem joins),
# em vez de agregar a view de 319k linhas a cada sessão.
MV_NAME = "mv_censo_rollup"
MV_DIMS = [
    "nu_ano_censo",
    "no_regiao",
    "no_curso",
    "tp_categoria_administrativa",
    "tp_modalidade_ensino",
]
MV_MEASURES = [
    f"qt_{t}{suf}"
    for t in ("ing", "conc", "mat")
    for suf in ("", "_preta", "_parda", "_amarela", "_indigena", "_branca", "_cornd")
]


def mv_sql() -> str:
    dims = ", ".join(MV_DIMS)
    meas = ", ".join(f"COALESCE(SUM({m}), 0)::bigint AS {m}" for m in MV_MEASURES)
    return (
        f"DROP MATERIALIZED VIEW IF EXISTS {MV_NAME};\n"
        f"CREATE MATERIALIZED VIEW {MV_NAME} AS\n"
        f"SELECT {dims}, {meas}\n"
        f"FROM v_censo_consolidado GROUP BY {dims};\n"
        f"CREATE INDEX ix_{MV_NAME}_dims ON {MV_NAME} "
        f"(nu_ano_censo, no_regiao, tp_categoria_administrativa, tp_modalidade_ensino);"
    )


def drop_all_sql(tables: list[str]) -> str:
    stmts = ["DROP VIEW IF EXISTS v_censo_consolidado CASCADE;"]
    stmts += [f"DROP TABLE IF EXISTS {t} CASCADE;" for t in reversed(tables)]
    return "\n".join(stmts)


# ---------------------------------------------------------------------------
# Carga via COPY
# ---------------------------------------------------------------------------

def copy_df(cur, table: str, df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    cols = list(df.columns)
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep="")
    buf.seek(0)
    collist = ", ".join(cols)
    cur.copy_expert(
        f"COPY {table} ({collist}) FROM STDIN WITH (FORMAT csv, NULL '')",
        buf,
    )
    return len(df)


def run(db_url: str) -> None:
    sqlite_sql = SCHEMA_SQLITE.read_text(encoding="utf-8")
    pg_sql = to_postgres_schema(sqlite_sql)
    SCHEMA_PG_OUT.write_text(pg_sql, encoding="utf-8")
    print(f"[supabase] schema PostgreSQL escrito em {SCHEMA_PG_OUT.name}")

    tables = table_names(sqlite_sql)

    df = etl.clean(etl.load_csv(etl.DEFAULT_CSV))

    conn = psycopg2.connect(**parse_pg_url(db_url))
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            print("[supabase] recriando schema ...")
            cur.execute(drop_all_sql(tables))
            cur.execute(pg_sql)
        conn.commit()

        with conn.cursor() as cur:
            # 1. Lookups
            for table, (col, desc_map) in etl.REF_TABLES.items():
                n = copy_df(cur, table, etl.build_ref_table(df, col, desc_map))
                print(f"[supabase] {table:36s} {n:>7} linhas")

            # 2. Geografia
            for table, builder in (
                ("regiao", etl.build_regiao),
                ("uf", etl.build_uf),
                ("municipio", etl.build_municipio),
            ):
                n = copy_df(cur, table, builder(df))
                print(f"[supabase] {table:36s} {n:>7} linhas")

            # 3. CINE
            for name, data in etl.build_cine_hierarchy(df).items():
                n = copy_df(cur, name, data)
                print(f"[supabase] {name:36s} {n:>7} linhas")

            # 4. IES e curso
            n = copy_df(cur, "ies", etl.build_ies(df))
            print(f"[supabase] {'ies':36s} {n:>7} linhas")
            n = copy_df(cur, "curso", etl.build_curso(df))
            print(f"[supabase] {'curso':36s} {n:>7} linhas")

            # 5. Fato
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'fato_curso_ano' ORDER BY ordinal_position"
            )
            fato_cols = [r[0] for r in cur.fetchall()]
            cols_in_df = [c for c in fato_cols if c in df.columns]
            natural_key = ["nu_ano_censo", "co_curso", "co_municipio", "tp_dimensao"]
            fato = (
                df.loc[df["co_curso"].notna() & df["nu_ano_censo"].notna(), cols_in_df]
                .drop_duplicates(subset=natural_key)
            )
            n = copy_df(cur, "fato_curso_ano", fato)
            print(f"[supabase] {'fato_curso_ano':36s} {n:>7} linhas")

        conn.commit()

        # Materialized view de roll-up (criada após a carga; precisa dos dados)
        with conn.cursor() as cur:
            print(f"[supabase] criando materialized view {MV_NAME} ...")
            cur.execute(mv_sql())
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT MIN(nu_ano_censo), MAX(nu_ano_censo), COUNT(*) FROM fato_curso_ano")
            amin, amax, total = cur.fetchone()
            print(f"[supabase] OK — anos {amin}..{amax}, total fato: {total:,}")
            cur.execute("SELECT COUNT(*) FROM v_censo_consolidado")
            print(f"[supabase] view v_censo_consolidado: {cur.fetchone()[0]:,} linhas")
            cur.execute(f"SELECT COUNT(*) FROM {MV_NAME}")
            print(f"[supabase] {MV_NAME}: {cur.fetchone()[0]:,} linhas (roll-up)")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-url", default=None, help="Connection string PostgreSQL do Supabase")
    args = parser.parse_args()
    run(resolve_db_url(args.db_url))


if __name__ == "__main__":
    main()
