# Consolida os microdados INEP (2009-2024) filtrando cursos de computacao (CINE area geral = 6),
# seguindo o pipeline descrito em repo/db/ETL.md (alinhamento por nome de coluna, superset de colunas).
# Saida: analysis/data/computacao_2009_2024.parquet (apenas colunas necessarias as analises).

import io
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ZIP_DIR = ROOT / "dados" / "microdados"
OUT_DIR = ROOT / "analysis" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = list(range(2009, 2025))

RACE_SUFFIXES = ["", "_branca", "_preta", "_parda", "_amarela", "_indigena", "_cornd"]
BASES = ["qt_ing", "qt_conc", "qt_mat"]
AA_SUFFIXES = ["_reserva_vaga", "_rvetnico", "_rvredepublica", "_rvsocial_rf", "_rvpdef",
               "_rvoutros", "_prounii", "_prounip", "_fies", "_rpfies", "_nrpfies",
               "_apoio_social", "_procescpublica", "_procescprivada", "_procnaoinformada"]
WANT_COLS = (
    ["nu_ano_censo", "co_cine_area_geral", "co_regiao", "tp_modalidade_ensino",
     "tp_categoria_administrativa", "tp_organizacao_academica", "tp_grau_academico",
     "tp_dimensao", "co_curso", "co_ies", "tp_rede"]
    + [f"{b}{s}" for b in BASES for s in RACE_SUFFIXES]
    + [f"qt_ing{s}" for s in AA_SUFFIXES]
)


def find_cursos_member(zf: zipfile.ZipFile, year: int) -> str:
    target = f"MICRODADOS_CADASTRO_CURSOS_{year}.CSV"
    for name in zf.namelist():
        if name.upper().endswith(target):
            return name
    raise FileNotFoundError(f"{target} nao encontrado em {zf.filename}")


frames = []
for year in YEARS:
    zpath = ZIP_DIR / f"micro_{year}.zip"
    with zipfile.ZipFile(zpath) as zf:
        member = find_cursos_member(zf, year)
        with zf.open(member) as f:
            df = pd.read_csv(
                f, sep=";", encoding="latin-1", low_memory=False,
                dtype=str,
            )
    df.columns = [c.strip().lower() for c in df.columns]
    # filtra computacao: aceita 6 ou "06"
    area = df["co_cine_area_geral"].astype(str).str.strip().str.replace('"', '', regex=False)
    df = df[area.isin(["6", "06", "6.0"])].copy()
    keep = [c for c in WANT_COLS if c in df.columns]
    missing = [c for c in WANT_COLS if c not in df.columns]
    df = df[keep]
    for c in missing:
        df[c] = pd.NA
    df["ano_arquivo"] = year
    frames.append(df)
    print(f"{year}: {len(df):>6} linhas de computacao | colunas ausentes: {len(missing)}")

full = pd.concat(frames, ignore_index=True)

# converte medidas para numerico
for c in WANT_COLS:
    if c.startswith("qt_"):
        full[c] = pd.to_numeric(full[c], errors="coerce").fillna(0).astype("int64")
    elif c in ("co_regiao", "tp_modalidade_ensino", "tp_categoria_administrativa",
               "tp_organizacao_academica", "tp_rede", "tp_grau_academico",
               "tp_dimensao", "co_curso", "co_ies"):
        full[c] = pd.to_numeric(full[c], errors="coerce").astype("Int64")

full.to_pickle(OUT_DIR / "computacao_2009_2024.pkl")
print(f"\nTotal consolidado: {len(full):,} linhas")
print(full.groupby("ano_arquivo").size().to_string())
