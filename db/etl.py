"""
ETL: CSV consolidado -> SQLite

Lê `dados/dados_censo_computacao_consolidado.csv`, aplica o schema definido em
`db/schema.sql` e popula as dimensões + a tabela fato.

Uso:
    python db/etl.py
    python db/etl.py --csv caminho/para/dados.csv --db caminho/para/saida.db
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
DEFAULT_CSV = PROJECT_ROOT.parent.parent.parent / "dados" / "dados_censo_computacao_consolidado.csv"
DEFAULT_DB = HERE / "censo.db"
SCHEMA_PATH = HERE / "schema.sql"


# ---------------------------------------------------------------------------
# Dicionários de descrição para as tabelas ref_tp_* (códigos do INEP).
# Códigos não mapeados aqui recebem descrição genérica "Código N".
# ---------------------------------------------------------------------------

# Descrições oficiais do dicionário de dados do Censo da Educação Superior
# 2024 (aba "cadastro_cursos", coluna "Categoria").
DESC_TP_DIMENSAO = {
    1: "Cursos presenciais ofertados no Brasil",
    2: "Cursos a distância ofertados no Brasil",
    3: "Cursos a distância com dimensão de dados somente a nível Brasil",
    4: "Cursos a distância ofertados por instituições brasileiras no exterior",
}

DESC_TP_ORGANIZACAO_ACADEMICA = {
    1: "Universidade",
    2: "Centro Universitário",
    3: "Faculdade",
    4: "Instituto Federal de Educação, Ciência e Tecnologia",
    5: "Centro Federal de Educação Tecnológica",
}

DESC_TP_CATEGORIA_ADMINISTRATIVA = {
    1: "Pública Federal",
    2: "Pública Estadual",
    3: "Pública Municipal",
    4: "Privada com fins lucrativos",
    5: "Privada sem fins lucrativos",
    6: "Privada - Particular em sentido estrito",
    7: "Especial",
    8: "Privada comunitária",
    9: "Privada confessional",
}

DESC_TP_REDE = {
    1: "Pública",
    2: "Privada",
}

DESC_TP_GRAU_ACADEMICO = {
    1: "Bacharelado",
    2: "Licenciatura",
    3: "Tecnológico",
    4: "Bacharelado e Licenciatura",
}

DESC_TP_MODALIDADE_ENSINO = {
    1: "Presencial",
    2: "Curso a distância",
}

DESC_TP_NIVEL_ACADEMICO = {
    1: "Graduação",
    2: "Sequencial de formação específica",
}


REF_TABLES = {
    "ref_tp_dimensao": ("tp_dimensao", DESC_TP_DIMENSAO),
    "ref_tp_organizacao_academica": ("tp_organizacao_academica", DESC_TP_ORGANIZACAO_ACADEMICA),
    "ref_tp_categoria_administrativa": ("tp_categoria_administrativa", DESC_TP_CATEGORIA_ADMINISTRATIVA),
    "ref_tp_rede": ("tp_rede", DESC_TP_REDE),
    "ref_tp_grau_academico": ("tp_grau_academico", DESC_TP_GRAU_ACADEMICO),
    "ref_tp_modalidade_ensino": ("tp_modalidade_ensino", DESC_TP_MODALIDADE_ENSINO),
    "ref_tp_nivel_academico": ("tp_nivel_academico", DESC_TP_NIVEL_ACADEMICO),
}


# ---------------------------------------------------------------------------
# Carga e limpeza
# ---------------------------------------------------------------------------

def load_csv(csv_path: Path) -> pd.DataFrame:
    print(f"[etl] lendo {csv_path} ...")
    df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)
    print(f"[etl]   {len(df):,} linhas, {len(df.columns)} colunas")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza tipos e remove ruído (aspas extras em strings, floats em códigos)."""

    df.columns = [c.strip().lower() for c in df.columns]

    # co_cine_rotulo vem como '"""0615S02"""' — tira aspas extras
    for col in ("co_cine_rotulo", "co_cine_rotulo2"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('"', "", regex=False).str.strip()
            df.loc[df[col].isin(("", "nan", "None")), col] = pd.NA

    int_cols = [c for c in df.columns if c.startswith(("qt_", "co_", "tp_", "in_", "nu_"))]
    # co_cine_rotulo é texto — proteger
    int_cols = [c for c in int_cols if c not in ("co_cine_rotulo", "co_cine_rotulo2")]

    for col in int_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # no_curso e demais nomes ficam como string
    str_cols = [c for c in df.columns if c.startswith(("no_", "sg_"))]
    for col in str_cols:
        df[col] = df[col].astype(str).where(df[col].notna(), None)
        df.loc[df[col].isin(("nan", "None")), col] = None

    return df


# ---------------------------------------------------------------------------
# Construção das dimensões a partir do DataFrame
# ---------------------------------------------------------------------------

SENTINEL = "Não informado"


def build_regiao(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df[["co_regiao", "no_regiao"]]
        .dropna(subset=["co_regiao"])
        .drop_duplicates(subset=["co_regiao"])
        .sort_values("co_regiao")
    )
    out["no_regiao"] = out["no_regiao"].fillna(SENTINEL)
    return out


def build_uf(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df[["co_uf", "sg_uf", "no_uf", "co_regiao"]]
        .dropna(subset=["co_uf"])
        .drop_duplicates(subset=["co_uf"])
        .sort_values("co_uf")
    )
    out["sg_uf"] = out["sg_uf"].fillna("??")
    out["no_uf"] = out["no_uf"].fillna(SENTINEL)
    # UF sem região: agrupa sob co_regiao=0 (criamos um sentinela na regiao se necessário)
    out["co_regiao"] = out["co_regiao"].fillna(0).astype("Int64")
    return out


def build_municipio(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df[["co_municipio", "no_municipio", "in_capital", "co_uf"]]
        .dropna(subset=["co_municipio"])
        .drop_duplicates(subset=["co_municipio"])
        .sort_values("co_municipio")
    )
    out["no_municipio"] = out["no_municipio"].fillna(SENTINEL)
    out["co_uf"] = out["co_uf"].fillna(0).astype("Int64")
    return out


def build_cine_hierarchy(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    area_geral = (
        df[["co_cine_area_geral", "no_cine_area_geral"]]
        .dropna(subset=["co_cine_area_geral"])
        .drop_duplicates(subset=["co_cine_area_geral"])
        .sort_values("co_cine_area_geral")
    )
    area_geral["no_cine_area_geral"] = area_geral["no_cine_area_geral"].fillna(SENTINEL)

    area_especifica = (
        df[["co_cine_area_especifica", "no_cine_area_especifica", "co_cine_area_geral"]]
        .dropna(subset=["co_cine_area_especifica"])
        .drop_duplicates(subset=["co_cine_area_especifica"])
        .sort_values("co_cine_area_especifica")
    )
    area_especifica["no_cine_area_especifica"] = area_especifica["no_cine_area_especifica"].fillna(SENTINEL)
    area_especifica["co_cine_area_geral"] = area_especifica["co_cine_area_geral"].fillna(0).astype("Int64")

    area_detalhada = (
        df[["co_cine_area_detalhada", "no_cine_area_detalhada", "co_cine_area_especifica"]]
        .dropna(subset=["co_cine_area_detalhada"])
        .drop_duplicates(subset=["co_cine_area_detalhada"])
        .sort_values("co_cine_area_detalhada")
    )
    area_detalhada["no_cine_area_detalhada"] = area_detalhada["no_cine_area_detalhada"].fillna(SENTINEL)
    area_detalhada["co_cine_area_especifica"] = area_detalhada["co_cine_area_especifica"].fillna(0).astype("Int64")

    rotulo = (
        df[["co_cine_rotulo", "no_cine_rotulo", "co_cine_area_detalhada"]]
        .dropna(subset=["co_cine_rotulo"])
        .drop_duplicates(subset=["co_cine_rotulo"])
        .sort_values("co_cine_rotulo")
    )
    rotulo["no_cine_rotulo"] = rotulo["no_cine_rotulo"].fillna(SENTINEL)
    rotulo["co_cine_area_detalhada"] = rotulo["co_cine_area_detalhada"].fillna(0).astype("Int64")

    return {
        "cine_area_geral": area_geral,
        "cine_area_especifica": area_especifica,
        "cine_area_detalhada": area_detalhada,
        "cine_rotulo": rotulo,
    }


def build_ies(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["co_ies"]].dropna().drop_duplicates().sort_values("co_ies")
    return out


def build_curso(df: pd.DataFrame) -> pd.DataFrame:
    # `curso` guarda só a identidade + um nome representativo (grafia mais
    # frequente, pois ~67% dos cursos têm variação de grafia entre anos).
    # IES, CINE e município variam ano a ano e ficam no fato.
    base = df[["co_curso", "no_curso"]].dropna(subset=["co_curso"])
    out = (
        base.sort_values("co_curso")
        .groupby("co_curso", as_index=False)
        .agg(no_curso=("no_curso", lambda s: s.dropna().mode().iloc[0] if not s.dropna().empty else None))
    )
    return out


def build_ref_table(df: pd.DataFrame, col: str, desc_map: dict[int, str]) -> pd.DataFrame:
    codigos = (
        pd.to_numeric(df[col], errors="coerce")
        .dropna()
        .astype(int)
        .unique()
    )
    rows = [{"codigo": int(c), "descricao": desc_map.get(int(c), f"Código {int(c)}")} for c in sorted(codigos)]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Persistência
# ---------------------------------------------------------------------------

def create_schema(conn: sqlite3.Connection) -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)


def insert_df(conn: sqlite3.Connection, table: str, df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    # method=None (executemany) evita o limite "too many SQL variables" do
    # SQLite na tabela fato (225 colunas).
    df.to_sql(table, conn, if_exists="append", index=False, chunksize=5000)
    return len(df)


def run(csv_path: Path, db_path: Path) -> None:
    if db_path.exists():
        print(f"[etl] removendo BD anterior: {db_path}")
        db_path.unlink()

    df = clean(load_csv(csv_path))

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = OFF;")
        create_schema(conn)

        # 1. Tabelas de lookup
        for table, (col, desc_map) in REF_TABLES.items():
            ref_df = build_ref_table(df, col, desc_map)
            n = insert_df(conn, table, ref_df)
            print(f"[etl] {table:40s} {n:>6} linhas")

        # 2. Geografia
        for table, builder in (
            ("regiao", build_regiao),
            ("uf", build_uf),
            ("municipio", build_municipio),
        ):
            data = builder(df)
            n = insert_df(conn, table, data)
            print(f"[etl] {table:40s} {n:>6} linhas")

        # 3. CINE
        for name, data in build_cine_hierarchy(df).items():
            n = insert_df(conn, name, data)
            print(f"[etl] {name:40s} {n:>6} linhas")

        # 4. IES e Curso
        ies_df = build_ies(df)
        n = insert_df(conn, "ies", ies_df)
        print(f"[etl] {'ies':40s} {n:>6} linhas")

        curso_df = build_curso(df)
        n = insert_df(conn, "curso", curso_df)
        print(f"[etl] {'curso':40s} {n:>6} linhas")

        # 5. Fato — só as colunas que existem na tabela (id é AUTOINCREMENT,
        # não está no df, então é ignorado automaticamente).
        cursor = conn.execute("PRAGMA table_info(fato_curso_ano);")
        fato_cols = [row[1] for row in cursor.fetchall()]
        cols_in_df = [c for c in fato_cols if c in df.columns]

        # Grão = (ano, curso, município, dimensão). drop_duplicates é só uma
        # rede de segurança — o CSV já é único nessa chave (0 duplicatas).
        natural_key = ["nu_ano_censo", "co_curso", "co_municipio", "tp_dimensao"]
        fato = (
            df.loc[df["co_curso"].notna() & df["nu_ano_censo"].notna(), cols_in_df]
            .drop_duplicates(subset=natural_key)
        )
        n = insert_df(conn, "fato_curso_ano", fato)
        print(f"[etl] {'fato_curso_ano':40s} {n:>6} linhas")

        conn.commit()

        # Sanity check: intervalo de anos + total
        ano_min, ano_max = conn.execute(
            "SELECT MIN(nu_ano_censo), MAX(nu_ano_censo) FROM fato_curso_ano"
        ).fetchone()
        total = conn.execute("SELECT COUNT(*) FROM fato_curso_ano").fetchone()[0]
        print(f"[etl] OK — anos {ano_min}..{ano_max}, total fato: {total:,}")

        # Contagem por ano (confirma os 15 censos 2009..2023)
        print("[etl] linhas por ano:")
        for ano, qtd in conn.execute(
            "SELECT nu_ano_censo, COUNT(*) FROM fato_curso_ano "
            "GROUP BY nu_ano_censo ORDER BY nu_ano_censo"
        ):
            print(f"[etl]   {ano}: {qtd:,}")

        # Integridade referencial: reporta órfãos sem abortar
        orphans = conn.execute("PRAGMA foreign_key_check;").fetchall()
        if orphans:
            print(f"[etl] AVISO: {len(orphans)} violações de FK (dados sujos preservados)")
        else:
            print("[etl] integridade referencial: OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    if not args.csv.exists():
        raise SystemExit(f"CSV não encontrado: {args.csv}")

    run(args.csv, args.db)


if __name__ == "__main__":
    main()
