# Consolida os microdados do Censo da Educacao Superior do INEP (2009-2024), modulo de cursos
# (MICRODADOS_CADASTRO_CURSOS_<ano>.CSV dentro de cada zip), filtrando cursos de computacao (CINE area geral = 6),
# seguindo as convencoes de db/ETL.md (alinhamento por nome de coluna, superset de colunas). Coluna ausente na
# edicao fica NA nas medidas de politica e nos codigos; nas contagens por etapa e cor, NA vira zero.
# A base resultante (331.023 ofertas de curso, 2009-2024; Secao 5.1 do artigo estendido) e lida por
# run_sections_7_8.py, run_section_9.py, run_section_10.py, run_figuras_extras.py, run_recomposicao.py e
# run_validacao_trajetoria.py (Secoes 6 a 11). run_robustez.py le os zips diretamente.
# Uso: python analysis/build_dataset.py [pasta dos zips] [arquivo pkl de saida]
# Entradas: micro_2009.zip ... micro_2024.zip (nomes locais) na pasta dos zips, por padrao dados/microdados
#   na raiz do repositorio; conferir com analysis/data/checksums_sha256.txt. Nao usa variaveis de ambiente.
# Saida: analysis/data/computacao_2009_2024.pkl por padrao (apenas colunas necessarias as analises, mais
#   ano_arquivo). Os demais scripts leem o pkl pela variavel CENSO_PKL, com o mesmo padrao; se gravar em outro
#   caminho, defina CENSO_PKL com ele. Imprime as linhas de computacao por ano e o total consolidado.

import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ZIP_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dados" / "microdados"
OUT_PKL = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "analysis" / "data" / "computacao_2009_2024.pkl"
OUT_PKL.parent.mkdir(parents=True, exist_ok=True)

YEARS = list(range(2009, 2025))

RACE_SUFFIXES = ["", "_branca", "_preta", "_parda", "_amarela", "_indigena", "_cornd"]
BASES = ["qt_ing", "qt_conc", "qt_mat"]
AA_SUFFIXES = ["_reserva_vaga", "_rvetnico", "_rvppi", "_rvquilo", "_rvredepublica", "_rvsocial_rf", "_rvpdef",
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


AA_COLS = {f"qt_ing{s}" for s in AA_SUFFIXES}

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
        # Variavel ausente na edicao fica NA nas medidas de politica, para nao confundir ausencia com zero.
        num = pd.to_numeric(full[c], errors="coerce")
        full[c] = num.astype("Int64") if c in AA_COLS else num.fillna(0).astype("int64")
    elif c in ("co_regiao", "tp_modalidade_ensino", "tp_categoria_administrativa",
               "tp_organizacao_academica", "tp_rede", "tp_grau_academico",
               "tp_dimensao", "co_curso", "co_ies"):
        full[c] = pd.to_numeric(full[c], errors="coerce").astype("Int64")

full.to_pickle(OUT_PKL)
print(f"\nTotal consolidado: {len(full):,} linhas")
print(full.groupby("ano_arquivo").size().to_string())
