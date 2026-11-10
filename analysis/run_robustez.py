# Robustez e numeros pontuais do artigo estendido: contagens das licoes de ETL (Secao 5.2), numeros do texto
# das Secoes 4.4, 6 (RQ1-RQ4), 7, 10, 11 e 12, robustez das tendencias e IC de Fieller do ano de paridade
# (Tabelas 7 e 8), tabela regional com benchmarks do Censo 2022 (Tabela 9), sensibilidade a k e a cobertura de
# cor (Tabela 10), gradiente de cotas bruto e liquido (Tabela 12), comparacao acesso x conclusao e limites da
# nao declaracao (Secoes 7 e 11). rob_cursos_acumulado.csv alimenta a Figura 5, desenhada por
# run_recomposicao.py, que deve rodar depois deste script.
# Le os zips brutos do INEP, com alinhamento por nome de coluna, sem depender do pkl de build_dataset.py
# (nao usa CENSO_PKL). Os benchmarks do IBGE (Censo 2022) estao fixos no codigo.
# Uso: python analysis/run_robustez.py [pasta com micro_YYYY.zip]
# Entradas: micro_2009.zip ... micro_2024.zip (nomes locais) na pasta indicada, por padrao dados/microdados na
#   raiz do repositorio; conferir com analysis/data/checksums_sha256.txt.
# Saidas, em analysis/output/: rob_cursos_acumulado.csv, rob_parity_windows.csv, rob_regional.csv,
#   rob_quota_net.csv, rob_k_sensitivity.csv, rob_access_vs_completion.csv, rob_undeclared.csv,
#   rob_public_private_le10.csv e rob_numeros_texto.txt (o mesmo texto impresso na tela).

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
ZIP_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dados" / "microdados"
OUT = ROOT / "analysis" / "output"
OUT.mkdir(parents=True, exist_ok=True)
YEARS = list(range(2009, 2025))
WIN = list(range(2010, 2025))

REG = {1: "North", 2: "Northeast", 3: "Southeast", 4: "South", 5: "Central-West"}

# Censo 2022, Identificacao etnico-racial (IBGE), populacao residente: total, branca, preta, parda.
IBGE = {
    "Brazil": (203080756, 88252121, 20656458, 92083286),
    "North": (17354884, 3598298, 1530418, 11654390),
    "Northeast": (54658515, 14571557, 7127018, 32559846),
    "Southeast": (84840113, 42318768, 9003372, 32833389),
    "South": (29937706, 21729713, 1505526, 6499382),
    "Central-West": (16289538, 6033785, 1490124, 8536279),
}

COLS = ["nu_ano_censo", "co_cine_area_geral", "co_regiao", "co_municipio", "co_curso", "co_ies", "no_curso",
        "tp_dimensao", "tp_modalidade_ensino", "tp_categoria_administrativa", "tp_grau_academico",
        "co_cine_rotulo", "co_cine_rotulo2"]
for base in ("qt_ing", "qt_mat", "qt_conc"):
    COLS += [base] + [f"{base}_{s}" for s in ("branca", "preta", "parda", "amarela", "indigena", "cornd")]
COLS += ["qt_ing_reserva_vaga", "qt_ing_rvetnico", "qt_ing_rvppi", "qt_ing_rvquilo", "qt_ing_prounii",
         "qt_ing_prounip", "qt_ing_fies", "qt_ing_apoio_social"]
TEXTO = ("no_curso", "co_cine_rotulo", "co_cine_rotulo2")


def carrega():
    """Le os zips, com alinhamento por nome, e devolve so a area geral CINE 6 e os cabecalhos brutos."""
    frames, heads = [], {}
    for ano in YEARS:
        with zipfile.ZipFile(ZIP_DIR / f"micro_{ano}.zip") as zf:
            nome = [n for n in zf.namelist() if n.upper().endswith(f"MICRODADOS_CADASTRO_CURSOS_{ano}.CSV")][0]
            with zf.open(nome) as f:
                hdr = pd.read_csv(f, sep=";", encoding="latin-1", nrows=0).columns.tolist()
            heads[ano] = [c.strip().lower() for c in hdr]
            with zf.open(nome) as f:
                d = pd.read_csv(f, sep=";", encoding="latin-1", low_memory=False, dtype=str,
                                usecols=lambda c: c.strip().lower() in COLS)
        d.columns = [c.strip().lower() for c in d.columns]
        area = d["co_cine_area_geral"].astype(str).str.strip().str.replace('"', "", regex=False)
        d = d[area.isin(["6", "06", "6.0"])].copy()
        for c in COLS:
            if c not in d.columns:
                d[c] = pd.NA
        d["ano"] = ano
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    for c in COLS:
        if c not in TEXTO:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # Ausente continua NA nas variaveis de politica; as contagens raciais sao preenchidas apos a selecao.
    return df, heads


def ols(x, y):
    r = stats.linregress(x, y)
    return r


def fieller(x, y, alvo, alpha=0.05):
    """IC do ano em que a reta alcanca o benchmark. Devolve (NaN, NaN) quando nao ha intervalo finito."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    r = stats.linregress(x, y)
    res = y - (r.intercept + r.slope * x)
    s = np.sqrt((res ** 2).sum() / (n - 2))
    sxx = ((x - x.mean()) ** 2).sum()
    t = stats.t.ppf(1 - alpha / 2, n - 2)
    g = t ** 2 * s ** 2 / (r.slope ** 2 * sxx)
    if g >= 1 or r.slope <= 0:
        return np.nan, np.nan
    x0 = x.mean() + (alvo - y.mean()) / r.slope
    d = x0 - x.mean()
    meio = t * s / r.slope * np.sqrt((1 - g) / n + d ** 2 / sxx)
    return x.mean() + (d - meio) / (1 - g), x.mean() + (d + meio) / (1 - g)


def durbin_watson(x, y):
    r = stats.linregress(x, y)
    e = np.asarray(y) - (r.intercept + r.slope * np.asarray(x))
    return float((np.diff(e) ** 2).sum() / (e ** 2).sum())


def share(g, base, grupo):
    num = g[f"{base}_preta"] if grupo == "preta" else (
        g[f"{base}_preta"] + g[f"{base}_parda"] if grupo == "negra" else g[f"{base}_branca"])
    return 100 * num / (g[base] - g[f"{base}_cornd"])


def linha_trend(s, alvo, rotulo):
    s = s.dropna()
    x, y = s.index.values.astype(float), s.values.astype(float)
    r = stats.linregress(x, y)
    lo, hi = fieller(x, y, alvo)
    ts = stats.theilslopes(y, x)
    tau = stats.kendalltau(x, y)
    par = (alvo - r.intercept) / r.slope if r.slope > 0 else np.nan
    return {**rotulo, "n": len(x), "beta": r.slope, "r2": r.rvalue ** 2, "p": r.pvalue, "dw": durbin_watson(x, y),
            "theil_sen": ts[0], "ts_lo": ts[2], "ts_hi": ts[3], "kendall_p": tau.pvalue,
            "parity_year": par, "parity_lo": lo, "parity_hi": hi, "share_2024": s.get(2024, np.nan), "benchmark": alvo}


df, heads = carrega()
med = [c for c in df.columns if c.startswith("qt_")]
RACA = [c for c in med if not any(k in c for k in ("reserva", "rv", "prouni", "fies", "apoio"))]
df[RACA] = df[RACA].fillna(0)
log = []


def nota(txt):
    log.append(txt)
    print(txt, flush=True)


# ------------------------------------------------------------------
# Licoes de ETL sobre os arquivos atuais (Secao 5.2)
# ------------------------------------------------------------------
nota("== Esquema dos arquivos ==")
n_cols = {a: len(h) for a, h in heads.items()}
nota(f"colunas por ano: {n_cols}")
uni = set().union(*[set(h) for h in heads.values()])
nota(f"uniao de colunas: {len(uni)}")
for a, b in zip(YEARS, YEARS[1:]):
    add, rem = set(heads[b]) - set(heads[a]), set(heads[a]) - set(heads[b])
    com = [c for c in heads[a] if c in heads[b]]
    mudou = com != [c for c in heads[b] if c in heads[a]]
    if add or rem or mudou:
        nota(f"{a}->{b}: +{len(add)} -{len(rem)} ordem_mudou={mudou} add={sorted(add)[:30]} rem={sorted(rem)[:30]}")
linhas = df.groupby("ano").size()
nota(f"linhas por ano: {linhas.to_dict()} total={int(linhas.sum())}")
nota(f"co_municipio nulo: {int(df.co_municipio.isna().sum())}; zero: {df[df.co_municipio == 0].groupby('ano').size().to_dict()}")
chave = ["nu_ano_censo", "co_curso", "co_municipio", "tp_dimensao"]
nota(f"duplicatas da chave natural: {int(df.duplicated(chave).sum())}")
mun = df[df.co_municipio.notna() & (df.tp_modalidade_ensino == 2)].groupby(["ano", "co_curso"]).co_municipio.nunique()
nota(f"maximo de municipios por curso EaD no ano: {int(mun.max())}; por ano: {mun.groupby('ano').max().to_dict()}")

df["cine_rot"] = df.co_cine_rotulo.fillna(df.co_cine_rotulo2)
cur = df.dropna(subset=["co_curso"])
n_cursos = cur.co_curso.nunique()
nomes = cur.groupby("co_curso").no_curso.nunique()
nomes_ci = cur.assign(n=cur.no_curso.str.strip().str.upper()).groupby("co_curso").n.nunique()
multi = cur.groupby("co_curso").ano.nunique()
idx = multi[multi >= 2].index
nota(f"cursos: {n_cursos}; em 2+ edicoes: {len(idx)}")
nota(f"nome muda (2+ edicoes): {100 * (nomes.loc[idx] > 1).mean():.1f}%; ignorando caixa: {100 * (nomes_ci.loc[idx] > 1).mean():.1f}%")
rot = cur.groupby("co_curso").cine_rot.nunique()
nota(f"rotulo CINE muda (2+ edicoes): {100 * (rot.loc[idx] > 1).mean():.1f}%")
ies = cur.groupby("co_curso").co_ies.nunique()
nota(f"cursos que mudam de IES: {int((ies > 1).sum())}")
por_curso = cur.drop_duplicates(["ano", "co_curso"]).set_index(["co_curso", "ano"]).cine_rot.unstack("ano")
for a, b in zip(YEARS, YEARS[1:]):
    both = por_curso[[a, b]].dropna()
    if len(both):
        nota(f"recodificacao CINE {a}->{b}: {100 * (both[a] != both[b]).mean():.1f}% de {len(both)}")
# Cursos que estavam na area 6 em 2023 e nao estao mais em 2024
c23 = set(cur[cur.ano == 2023].co_curso)
c24 = set(cur[cur.ano == 2024].co_curso)
sai = c23 - c24
nota(f"cursos em 2023 ausentes da area 6 em 2024: {len(sai)}; ingressantes em 2023: {int(df[(df.ano == 2023) & df.co_curso.isin(sai)].qt_ing.sum())}")
# Dos que saem, os que continuam no arquivo de 2024 em outra area geral: recodificados, nao encerrados (Secoes 5.2 e 12)
with zipfile.ZipFile(ZIP_DIR / "micro_2024.zip") as zf:
    nome24 = [n for n in zf.namelist() if n.upper().endswith("MICRODADOS_CADASTRO_CURSOS_2024.CSV")][0]
    with zf.open(nome24) as f:
        todos24 = pd.read_csv(f, sep=";", encoding="latin-1", dtype=str,
                              usecols=lambda c: c.strip().lower() in ("co_curso", "co_cine_area_geral"))
todos24.columns = [c.strip().lower() for c in todos24.columns]
recod = sai & set(pd.to_numeric(todos24.co_curso, errors="coerce").dropna())
ing_recod = int(df[(df.ano == 2023) & df.co_curso.isin(recod)].qt_ing.sum())
nota(f"dos quais em outra area geral em 2024 (recodificados): {len(recod)}; ingressantes em 2023: {ing_recod} "
     f"({100 * ing_recod / df[df.ano == 2023].qt_ing.sum():.1f}% dos ingressantes de 2023)")
# Mesmas mudancas de nome sobre todos os cursos, o denominador usado na Secao 5.2
nota(f"nome muda (todos os {n_cursos} cursos): {100 * (nomes > 1).mean():.1f}%; ignorando caixa: {100 * (nomes_ci > 1).mean():.1f}%")

# ------------------------------------------------------------------
# Numeros pontuais do texto (Secoes 6, 10, 11 e 12; distribuicao por curso tambem na Figura 5)
# ------------------------------------------------------------------
nac = df.groupby("ano")[med].sum(min_count=1)
nota("\n== Numeros do texto ==")
for c in ("qt_ing", "qt_ing_preta", "qt_conc_preta", "qt_mat_preta", "qt_ing_cornd"):
    nota(f"{c}: 2010={int(nac.loc[2010, c])} 2013={int(nac.loc[2013, c])} 2023={int(nac.loc[2023, c])} 2024={int(nac.loc[2024, c])}")
for base in ("qt_ing", "qt_mat", "qt_conc"):
    bd = share(nac, base, "branca").loc[WIN]
    bt = (100 * nac[f"{base}_branca"] / nac[base]).loc[WIN]
    und = (100 * nac[f"{base}_cornd"] / nac[base])
    nota(f"{base}: branca/declarados {bd.min():.1f}-{bd.max():.1f} (2024 {bd.loc[2024]:.1f}); branca/total max {bt.max():.1f}; nao declarado 2010 {und.loc[2010]:.2f} 2014 {und.loc[2014]:.2f} 2024 {und.loc[2024]:.2f}")
p_t = (100 * nac.qt_ing_preta / nac.qt_ing)
nota(f"preta/total ingressantes: {p_t.loc[WIN].round(2).to_dict()}")
nota(f"preta/declarados ingressantes: {share(nac, 'qt_ing', 'preta').loc[WIN].round(2).to_dict()}")
nota(f"negra/declarados ingressantes: {share(nac, 'qt_ing', 'negra').loc[WIN].round(2).to_dict()}")
nota(f"total declarado ingressantes 2010 {int(nac.loc[2010, 'qt_ing'] - nac.loc[2010, 'qt_ing_cornd'])} 2024 {int(nac.loc[2024, 'qt_ing'] - nac.loc[2024, 'qt_ing_cornd'])}")

d24 = df[df.ano == 2024]
ti = d24.qt_ing.sum()
luc = d24[d24.tp_categoria_administrativa == 4]
ead = d24[d24.tp_modalidade_ensino == 2]
lucead = luc[luc.tp_modalidade_ensino == 2]
nota(f"2024 lucrativas {100 * luc.qt_ing.sum() / ti:.2f}; EaD {100 * ead.qt_ing.sum() / ti:.2f}; lucrativa EaD {100 * lucead.qt_ing.sum() / ti:.2f}; matriculas {100 * lucead.qt_mat.sum() / d24.qt_mat.sum():.2f}")
d10 = df[df.ano == 2010]
nota(f"EaD 2010 {100 * d10[d10.tp_modalidade_ensino == 2].qt_ing.sum() / d10.qt_ing.sum():.2f}")
luc_g = df[(df.tp_categoria_administrativa == 4) & (df.tp_modalidade_ensino == 2)].groupby("ano").qt_ing.sum()
tot_g = df.groupby("ano").qt_ing.sum()
nota(f"parcela lucrativa EaD no crescimento 2010-2024: {100 * (luc_g[2024] - luc_g[2010]) / (tot_g[2024] - tot_g[2010]):.1f}")

ads = df[df.no_curso.str.upper().str.contains("DESENVOLVIMENTO DE SISTEMAS", na=False)]
for nome, base in (("todos", "qt_ing"), ("preta", "qt_ing_preta"), ("parda", "qt_ing_parda"), ("branca", "qt_ing_branca")):
    n24, a24 = d24[base].sum(), ads[ads.ano == 2024][base].sum()
    pool, apool = df[df.ano.isin(WIN)][base].sum(), ads[ads.ano.isin(WIN)][base].sum()
    nota(f"ADS {nome}: 2024 {100 * a24 / n24:.2f}; acumulado 2010-24 {100 * apool / pool:.2f}")
tec = d24[d24.tp_grau_academico == 3]
for nome, base in (("todos", "qt_ing"), ("preta", "qt_ing_preta"), ("parda", "qt_ing_parda"), ("branca", "qt_ing_branca")):
    nota(f"tecnologos {nome} 2024: {100 * tec[base].sum() / d24[base].sum():.2f}")

# Distribuicao por curso no acumulado 2010-2024, pelo nome registrado em cada edicao (sem acento e em maiusculas)
janela = df[df.ano.isin(WIN)].copy()
janela["nome"] = janela.no_curso.fillna("").str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii").str.upper()
GRUPOS_CURSO = {"ADS": "DESENVOLVIMENTO DE SISTEMAS", "Sistemas de Informacao": "SISTEMAS? DE INFORMACAO",
                "Ciencia da Computacao": "CIENCIAS? DA COMPUTACAO", "Gestao de TI": "GESTAO DA TECNOLOGIA DA INFORMACAO",
                "Redes": "REDES DE COMPUTADORES", "Eng. Software": "ENGENHARIA DE SOFTWARE", "Eng. Computacao": "ENGENHARIA DA? COMPUTACAO",
                "Jogos": "JOGOS DIGITAIS", "Seguranca": "SEGURANCA DA INFORMACAO", "Internet": "SISTEMAS PARA INTERNET"}
linhas_c = []
for rot, pad in GRUPOS_CURSO.items():
    g = janela[janela.nome.str.contains(pad, regex=True)]
    linhas_c.append({"curso": rot, **{b: 100 * g[b].sum() / janela[b].sum() for b in ("qt_ing_preta", "qt_conc_preta", "qt_ing_branca", "qt_conc_branca", "qt_ing", "qt_conc")}})
cur_p = pd.DataFrame(linhas_c).set_index("curso").round(2)
cur_p.to_csv(OUT / "rob_cursos_acumulado.csv")
nota("cursos, % do acumulado 2010-2024 pelo nome registrado:\n" + cur_p.to_string())
nota(f"tres maiores (ADS, SI, CC): ingressantes pretos {cur_p.qt_ing_preta.iloc[:3].sum():.1f}; concluintes pretos {cur_p.qt_conc_preta.iloc[:3].sum():.1f}")

dp = df.assign(pub=df.tp_categoria_administrativa.isin([1, 2, 3])).groupby(["ano", "pub"])[med].sum(min_count=1)
for grupo in ("preta", "negra"):
    s = share(dp, "qt_ing", grupo).unstack("pub").rename(columns={True: "pub", False: "priv"})
    nota(f"{grupo}/declarados publico x privado: { {a: (round(s.loc[a, 'pub'], 2), round(s.loc[a, 'priv'], 2)) for a in (2010, 2014, 2020, 2021, 2022, 2023, 2024)} }")

cats = df.groupby(["ano", "tp_categoria_administrativa"])[med].sum(min_count=1)
sc = share(cats, "qt_ing", "negra").unstack(1)
nota(f"federal x lucrativa (negra/decl): { {a: (round(sc.loc[a, 1], 2), round(sc.loc[a, 4], 2)) for a in (2010, 2011, 2014, 2024)} }")
fed = sc.loc[2011:2024]
nota(f"federal lider desde 2011 entre cat 1,2,4,5: {bool((fed[1] >= fed[[2, 4, 5]].max(axis=1)).all())}; faixa federal 2014-24 {fed.loc[2014:, 1].min():.1f}-{fed.loc[2014:, 1].max():.1f}; lucrativa 2014-24 {fed.loc[2014:, 4].min():.1f}-{fed.loc[2014:, 4].max():.1f}")

gr = df.groupby("tp_grau_academico", dropna=False).agg(linhas=("qt_ing", "size"), ing=("qt_ing", "sum"))
nota(f"tp_grau_academico: {gr.to_dict('index')}")
gr_a = df[df.tp_grau_academico.isna()].groupby("ano").size()
nota(f"sem grau por ano: {gr_a.to_dict()}")

# ------------------------------------------------------------------
# Sensibilidade da tendencia e do ano de paridade (Tabelas 7 e 8; Theil-Sen na Secao 4.4)
# ------------------------------------------------------------------
BEN = {g: (100 * IBGE["Brazil"][2] / IBGE["Brazil"][0], 100 * (IBGE["Brazil"][2] + IBGE["Brazil"][3]) / IBGE["Brazil"][0]) for g in ["x"]}
nota(f"\nbenchmarks nacionais calculados: preta {BEN['x'][0]:.2f} negra {BEN['x'][1]:.2f} branca {100 * IBGE['Brazil'][1] / IBGE['Brazil'][0]:.2f}")
linhas_t = []
JANELAS = [(2010, 2024), (2010, 2014), (2014, 2024), (2015, 2024), (2017, 2024), (2018, 2024)]
for base, nome in (("qt_ing", "Entrants"), ("qt_mat", "Enrolled"), ("qt_conc", "Graduates")):
    for grupo, alvo in (("preta", 10.2), ("negra", 55.5)):
        s = share(nac, base, grupo)
        for a, b in JANELAS:
            linhas_t.append(linha_trend(s.loc[a:b], alvo, {"serie": nome, "definicao": grupo, "janela": f"{a}-{b}"}))
pd.DataFrame(linhas_t).round(4).to_csv(OUT / "rob_parity_windows.csv", index=False)

# ------------------------------------------------------------------
# Tabela regional nas duas definicoes, com benchmark da propria regiao (Tabela 9; lider por ano na Secao 6, RQ3)
# ------------------------------------------------------------------
reg = df.groupby(["ano", "co_regiao"])[med].sum(min_count=1)
linhas_r = []
for cod, nome in REG.items():
    t, b, p, pa = IBGE[nome]
    g = reg.xs(cod, level="co_regiao")
    for grupo, alvo_nac, alvo_reg in (("preta", 10.2, 100 * p / t), ("negra", 55.5, 100 * (p + pa) / t)):
        s = share(g, "qt_ing", grupo)
        for a, bb in ((2010, 2024), (2014, 2024)):
            ln = linha_trend(s.loc[a:bb], alvo_reg, {"regiao": nome, "definicao": grupo, "janela": f"{a}-{bb}"})
            ln["benchmark_nacional"] = alvo_nac
            ln["gap_regional"] = alvo_reg - s.loc[2024]
            ln["gap_nacional"] = alvo_nac - s.loc[2024]
            linhas_r.append(ln)
    nota(f"{nome}: lider? preta 2024 {share(g, 'qt_ing', 'preta').loc[2024]:.2f}, negra 2024 {share(g, 'qt_ing', 'negra').loc[2024]:.2f}; benchmark regional preta {100 * p / t:.1f} negra {100 * (p + pa) / t:.1f}")
pd.DataFrame(linhas_r).round(4).to_csv(OUT / "rob_regional.csv", index=False)
for grupo in ("preta", "negra"):
    m = pd.DataFrame({REG[c]: share(reg.xs(c, level="co_regiao"), "qt_ing", grupo) for c in REG}).loc[WIN]
    nota(f"lider por ano ({grupo}): {m.idxmax(axis=1).to_dict()}")
    nota(f"ultimo por ano ({grupo}): {m.idxmin(axis=1).value_counts().to_dict()}")

# ------------------------------------------------------------------
# Gradiente de cotas bruto e liquido (Tabela 12 e Secao 10)
# ------------------------------------------------------------------
d = df[df.ano.isin(WIN) & (df.qt_ing > 0)].copy()
d["decl"] = d.qt_ing - d.qt_ing_cornd
d = d[d.decl > 0]
d["neg"] = d.qt_ing_preta + d.qt_ing_parda
d["bruto"] = d.neg / d.decl
d["iq"] = d.qt_ing_reserva_vaga.fillna(0) / d.qt_ing
# Geracao das variaveis: RVETNICO ate 2023; RVPPI + RVQUILO em 2024.
d["racial"] = np.where(d.ano < 2024, d.qt_ing_rvetnico.fillna(0), d.qt_ing_rvppi.fillna(0) + d.qt_ing_rvquilo.fillna(0))
den = d.decl - d.racial
d["liq"] = (d.neg - d.racial).clip(lower=0) / den.where(den > 0)
linhas_q = []
for ano, g in d.groupby("ano"):
    g = g.copy()
    g["grupo"] = "0"
    pos = g.iq > 0
    if pos.sum() < 30:
        continue
    g.loc[pos, "grupo"] = pd.qcut(g.loc[pos, "iq"], 3, labels=["T1", "T2", "T3"], duplicates="drop").astype(str)
    for q, gg in g.groupby("grupo"):
        linhas_q.append({"ano": ano, "grupo": q, "n": len(gg), "bruto": 100 * gg.bruto.mean(), "liquido": 100 * gg.liq.mean(),
                         "ponderado": 100 * gg.neg.sum() / gg.decl.sum(), "pct_publica": 100 * gg.tp_categoria_administrativa.isin([1, 2, 3]).mean()})
    com = g[pos]
    rho = stats.spearmanr(com.iq, com.bruto)
    rho_l = stats.spearmanr(com.iq, com.liq, nan_policy="omit")
    grupos_kw = [gg.bruto.values for _, gg in g.groupby("grupo") if len(gg) > 5]
    kw_tod = stats.kruskal(*grupos_kw).pvalue
    terc = [gg.bruto.values for q, gg in g.groupby("grupo") if q != "0"]
    kw_ter = stats.kruskal(*terc).pvalue if len(terc) >= 2 else np.nan
    linhas_q.append({"ano": ano, "grupo": "testes", "n": int(pos.sum()), "bruto": rho.statistic, "liquido": rho_l.statistic,
                     "ponderado": kw_tod, "pct_publica": kw_ter})
q = pd.DataFrame(linhas_q)
q.round(4).to_csv(OUT / "rob_quota_net.csv", index=False)
qp = q[q.grupo != "testes"].pivot_table(index="ano", columns="grupo", values=["bruto", "liquido"]).round(2)
nota("\n== Gradiente de cotas ==\n" + qp.to_string())
b = qp["bruto"].loc[2014:]
ord_b = ((b["0"] < b["T1"]) & (b["T1"] < b["T2"]) & (b["T2"] < b["T3"]))
nota(f"ordem completa bruta em {int(ord_b.sum())} de {len(ord_b)}: {ord_b[ord_b].index.tolist()}")
l = qp["liquido"].loc[2014:]
nota(f"T3 liquido acima de sem cota em: {l[l['T3'] > l['0']].index.tolist()} de {len(l)}")
nota("testes (spearman bruto, spearman liquido, KW todos, KW tercis):\n" + q[q.grupo == "testes"].set_index("ano")[["bruto", "liquido", "ponderado", "pct_publica"]].round(3).to_string())
c24 = d[(d.ano == 2024)]
nota(f"ofertas 2024: {len(c24)}; com cota {int((c24.iq > 0).sum())}")

# ------------------------------------------------------------------
# Coortes, sensibilidade a k e vies de cobertura (Tabela 10 e Secao 9)
# ------------------------------------------------------------------
linhas_k = []
for rotulo, sub in (("Brazil", df), ("Public", df[df.tp_categoria_administrativa.isin([1, 2, 3])]),
                    ("Private", df[df.tp_categoria_administrativa.isin([4, 5, 6, 7])]),
                    ("For-profit", df[df.tp_categoria_administrativa == 4]),
                    ("For-profit distance", df[(df.tp_categoria_administrativa == 4) & (df.tp_modalidade_ensino == 2)])):
    for grau, nome_g, ks in ((3, "Technologist", (2, 3, 4)), (1, "Bachelor", (4, 5))):
        g = sub[sub.tp_grau_academico == grau].groupby("ano")[med].sum(min_count=1)
        for k in ks:
            for t in range(2017, 2025):
                i, c = g.loc[t - k], g.loc[t]
                cob_i, cob_c = 1 - i.qt_ing_cornd / i.qt_ing, 1 - c.qt_conc_cornd / c.qt_conc
                lin = {"recorte": rotulo, "grau": nome_g, "k": k, "ano": t, "cob_ing": 100 * cob_i, "cob_conc": 100 * cob_c,
                       "taxa_todos": 100 * c.qt_conc / i.qt_ing}
                for gr, ni, nc in (("branca", i.qt_ing_branca, c.qt_conc_branca), ("preta", i.qt_ing_preta, c.qt_conc_preta),
                                   ("negra", i.qt_ing_preta + i.qt_ing_parda, c.qt_conc_preta + c.qt_conc_parda)):
                    lin[f"taxa_{gr}"] = 100 * nc / ni
                    lin[f"aj_{gr}"] = 100 * (nc / cob_c) / (ni / cob_i)
                lin["razao_negra"] = lin["taxa_negra"] / lin["taxa_branca"]
                lin["razao_preta"] = lin["taxa_preta"] / lin["taxa_branca"]
                linhas_k.append(lin)
kk = pd.DataFrame(linhas_k)
kk.round(3).to_csv(OUT / "rob_k_sensitivity.csv", index=False)
v = kk[(kk.recorte == "Brazil") & (kk.ano == 2024)][["grau", "k", "taxa_todos", "taxa_branca", "taxa_negra", "aj_branca", "aj_negra", "razao_negra", "razao_preta"]].round(2)
nota("\n== Coortes, Brasil 2024 ==\n" + v.to_string(index=False))
# k adotado = prazo oficial - 1: 2 para tecnologo e 4 para bacharelado (ver run_validacao_trajetoria.py)
faixa = kk[(kk.recorte == "Brazil") & (((kk.grau == "Technologist") & (kk.k == 2)) | ((kk.grau == "Bachelor") & (kk.k == 4)))]
nota(f"razao negra/branca 2017-2024 (k nominal): {faixa.razao_negra.min():.3f}-{faixa.razao_negra.max():.3f}; por ano {faixa.groupby(['grau', 'ano']).razao_negra.first().round(3).to_dict()}")
faixa_p = faixa.razao_preta
nota(f"razao preta/branca 2017-2024 (k nominal): {faixa_p.min():.3f}-{faixa_p.max():.3f}")
for rec in ("Public", "Private", "For-profit", "For-profit distance"):
    z = kk[(kk.recorte == rec) & (((kk.grau == "Technologist") & (kk.k == 2)) | ((kk.grau == "Bachelor") & (kk.k == 4)))]
    nota(f"{rec} razao negra: {z.groupby(['grau', 'ano']).razao_negra.first().round(3).to_dict()}")
    nota(f"{rec} razao preta: {z.groupby(['grau', 'ano']).razao_preta.first().round(3).to_dict()}")

# ------------------------------------------------------------------
# Acesso x conclusao com o mesmo comparador, negros relativos a brancos (Secoes 7 e 11)
# ------------------------------------------------------------------
tot, bra, pre, par = IBGE["Brazil"]
linhas_a = []
for ano in WIN:
    neg = share(nac.loc[[ano]], "qt_ing", "negra").iloc[0]
    bran = share(nac.loc[[ano]], "qt_ing", "branca").iloc[0]
    rel_pop = neg / (100 * (pre + par) / tot)
    linhas_a.append({"ano": ano, "negra_decl": neg, "branca_decl": bran, "negra_sobre_populacao": rel_pop,
                     "negra_rel_branca": (neg / (100 * (pre + par) / tot)) / (bran / (100 * bra / tot))})
aa = pd.DataFrame(linhas_a)
aa.round(3).to_csv(OUT / "rob_access_vs_completion.csv", index=False)
nota("\n== Acesso com comparador comum ==\n" + aa[aa.ano.isin([2014, 2017, 2020, 2024])].round(3).to_string(index=False))

# ------------------------------------------------------------------
# Robustez a nao declaracao (Secao 7)
# ------------------------------------------------------------------
linhas_u = []
b2 = df[(df.qt_ing > 0)].copy()
b2["und"] = b2.qt_ing_cornd / b2.qt_ing
for ano in (2010, 2014, 2019, 2024):
    g = b2[(b2.ano == ano) & (b2.und <= 0.10)]
    a = df[df.ano == ano]
    ti_a, un = a.qt_ing.sum(), a.qt_ing_cornd.sum()
    pr, ne = a.qt_ing_preta.sum(), a.qt_ing_preta.sum() + a.qt_ing_parda.sum()
    dec_g = g.qt_ing.sum() - g.qt_ing_cornd.sum()
    linhas_u.append({"ano": ano, "pct_ing_na_amostra": 100 * g.qt_ing.sum() / ti_a, "preta_le10": 100 * g.qt_ing_preta.sum() / dec_g,
                     "negra_le10": 100 * (g.qt_ing_preta.sum() + g.qt_ing_parda.sum()) / dec_g, "preta_lim_inf": 100 * pr / ti_a,
                     "preta_lim_sup": 100 * (pr + un) / ti_a, "negra_lim_inf": 100 * ne / ti_a, "negra_lim_sup": 100 * (ne + un) / ti_a})
uu = pd.DataFrame(linhas_u)
uu.round(2).to_csv(OUT / "rob_undeclared.csv", index=False)
nota("\n== Robustez a nao declaracao ==\n" + uu.round(2).to_string(index=False))

# Publico x privado nas ofertas de alta cobertura de cor (Secao 6, RQ4); modalidade e lucrativa (Secao 10)
b2["pub"] = b2.tp_categoria_administrativa.isin([1, 2, 3])
linhas_c = []
for ano in range(2019, 2025):
    for pub, g in b2[(b2.ano == ano) & (b2.und <= 0.10)].groupby("pub"):
        dec = g.qt_ing.sum() - g.qt_ing_cornd.sum()
        linhas_c.append({"ano": ano, "setor": "publico" if pub else "privado", "negra_le10": 100 * (g.qt_ing_preta.sum() + g.qt_ing_parda.sum()) / dec,
                         "preta_le10": 100 * g.qt_ing_preta.sum() / dec})
for ano in (2018, 2019, 2021, 2024):
    for mod, g in b2[(b2.ano == ano) & (b2.und <= 0.10)].groupby("tp_modalidade_ensino"):
        dec = g.qt_ing.sum() - g.qt_ing_cornd.sum()
        nota(f"modalidade {int(mod)} {ano}, nao declaracao <=10%: negro {100 * (g.qt_ing_preta.sum() + g.qt_ing_parda.sum()) / dec:.2f}")
g = b2[(b2.ano == 2024) & (b2.und <= 0.10) & (b2.tp_categoria_administrativa == 4)]
nota(f"lucrativa 2024, nao declaracao <=10%: negro {100 * (g.qt_ing_preta.sum() + g.qt_ing_parda.sum()) / (g.qt_ing.sum() - g.qt_ing_cornd.sum()):.2f}")
cc = pd.DataFrame(linhas_c).round(2)
cc.to_csv(OUT / "rob_public_private_le10.csv", index=False)
nota("\n== Publico x privado, nao declaracao <=10% ==\n" + cc.to_string(index=False))

# Segmento lucrativo EaD (Secoes 10 e 11); serie de nao declaracao e decomposicao log (Secao 7); crescimento (Secao 10)
for ano in (2022, 2023, 2024):
    a = df[df.ano == ano]
    s = a[(a.tp_categoria_administrativa == 4) & (a.tp_modalidade_ensino == 2)]
    nota(f"lucrativa EaD {ano}: {100 * s.qt_ing.sum() / a.qt_ing.sum():.1f}% ing, {100 * s.qt_mat.sum() / a.qt_mat.sum():.1f}% mat; prouni {100 * (s.qt_ing_prounii.sum() + s.qt_ing_prounip.sum()) / s.qt_ing.sum():.2f}% do segmento")
und_s = (100 * nac.qt_ing_cornd / nac.qt_ing).loc[WIN].round(1)
nota(f"nao declarado ingressantes: {und_s.to_dict()}")
pt, pd_ = 100 * nac.qt_ing_preta.loc[2024] / nac.qt_ing.loc[2024], 100 * nac.qt_ing_preta.loc[2010] / nac.qt_ing.loc[2010]
dec24, dec10 = share(nac, "qt_ing", "preta").loc[2024], share(nac, "qt_ing", "preta").loc[2010]
nota(f"decomposicao log da alta preta/total 2010-2024: cobertura {100 * (1 - np.log(dec24 / dec10) / np.log(pt / pd_)):.1f}%")
tq = nac.qt_ing
nota(f"crescimento ingressantes 2015-2024: {tq.loc[2024] / tq.loc[2015]:.2f}x ({int(tq.loc[2015])} a {int(tq.loc[2024])})")

# ------------------------------------------------------------------
# Apoio social como proxy declarada (Secao 11)
# ------------------------------------------------------------------
ap = d24.groupby("tp_categoria_administrativa")[["qt_ing_apoio_social", "qt_ing"]].sum()
nota(f"\napoio social/ingressantes 2024 por categoria: {(100 * ap.qt_ing_apoio_social / ap.qt_ing).round(2).to_dict()}")

(OUT / "rob_numeros_texto.txt").write_text("\n".join(log), encoding="utf-8")
print("ok")
