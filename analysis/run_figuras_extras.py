# Figuras extras do artigo estendido (rotulos em ingles):
#  1. sec8_regional_trends     - share preta entre ingressantes declarados por regiao, com tendencia OLS,
#                                2010-2024: Fig. 8 (fig:regional), Secao 8 (RQ6).
#  2. sec6_share_by_course     - share por curso, 2024 (top-10 em ingressantes pretos). Nao entra no artigo;
#                                a Secao 6 usa sec6_concentracao_cursos, de run_recomposicao.py.
#  3. sec10_modality_evolution - ingressantes e share negra por modalidade, 2010-2024. Nao entra no artigo;
#                                sec10_modality_share_negra.csv alimenta o painel (a) da Fig. 11 (fig:modality),
#                                desenhado por run_recomposicao.py, que deve rodar depois deste script.
# Tambem gera analysis/output/figuras_extras_check.txt com a verificacao cruzada
# dos numeros citados no texto do artigo (Secoes 6, 8 e 10: share e inclinacao por regiao, peso de Analise e
# Desenvolvimento de Sistemas entre os pretos, privadas com fins lucrativos e EaD). NAO ajusta dados em caso
# de divergencia.
# Uso: python analysis/run_figuras_extras.py   (sem argumentos)
# Entradas: pkl de build_dataset.py, no caminho da variavel de ambiente CENSO_PKL
# (padrao analysis/data/computacao_2009_2024.pkl); analysis/data/mapa_curso_nome.csv (versionado).
# Saidas em analysis/output/: sec6_share_by_course.csv, sec10_modality_absolutos.csv,
# sec10_modality_share_negra.csv e figuras_extras_check.txt. Em analysis/figures/ (PDF e PNG):
# sec8_regional_trends, sec6_share_by_course e sec10_modality_evolution. Se a pasta paper/figures/ existir
# (ela nao faz parte deste repositorio), os tres PDFs tambem sao copiados para ela.

import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("CENSO_PKL", ROOT / "analysis" / "data" / "computacao_2009_2024.pkl"))
MAP = ROOT / "analysis" / "data" / "mapa_curso_nome.csv"  # co_curso -> no_curso (moda em 2024)
OUT = ROOT / "analysis" / "output"
FIG = ROOT / "analysis" / "figures"
PAPER_FIG = ROOT / "paper" / "figures"  # copia opcional, feita so se a pasta existir
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

df = pd.read_pickle(DATA)
WIN = slice(2010, 2024)

REGIOES_EN = {1: "North", 2: "Northeast", 3: "Southeast", 4: "South", 5: "Central-West"}
BENCH_PRETA = 10.2  # % pretos na populacao, Censo IBGE 2022

# paleta sobria: azul/cinza + um acento laranja
C_MAIN = "#4C78A8"   # azul aco
C_GRAY = "#8C8C8C"   # cinza
C_ACCENT = "#E45756"  # acento (laranja-avermelhado)
C_BENCH = "#444444"

check_lines = []


def log(msg=""):
    print(msg)
    check_lines.append(str(msg))


# ============================================================
# FIGURA 1 - tendencias regionais (share preta / declarados, ingressantes)
# ============================================================
def serie_regiao(reg):
    g = df[df["co_regiao"] == reg].groupby("ano_arquivo").agg(
        total=("qt_ing", "sum"), preta=("qt_ing_preta", "sum"),
        cornd=("qt_ing_cornd", "sum"))
    decl = g["total"] - g["cornd"]
    return (100 * g["preta"] / decl).loc[WIN].dropna()


log("=" * 70)
log("VERIFICACAO CRUZADA - figuras extras")
log("=" * 70)
log("")
log("[3] Regiao Sudeste 2024 (texto: 10,2%) e slope Nordeste (texto: beta=-0,34, p<0,001)")
log("[4] Slopes por regiao (share preta/declarados entre ingressantes, 2010-2024)")

region_stats = {}
for reg in [1, 2, 3, 4, 5]:
    s = serie_regiao(reg)
    r = stats.linregress(s.index.values.astype(float), s.values)
    region_stats[reg] = (s, r)
    sig = "significant" if r.pvalue < 0.05 else "n.s."
    log(f"  {REGIOES_EN[reg]:12s}: share_2024 = {s.loc[2024]:5.2f}% | "
        f"slope = {r.slope:+.3f} pp/yr ({sig}, p={r.pvalue:.2e}, R2={r.rvalue**2:.2f})")

fig, axes = plt.subplots(2, 3, figsize=(4.8, 2.0), sharex=True, sharey=True)
for ax, reg in zip(axes.flat, [1, 2, 3, 4, 5]):
    s, r = region_stats[reg]
    ax.axhline(BENCH_PRETA, ls=":", lw=1.0, color=C_BENCH, zorder=1, label=f"National benchmark ({BENCH_PRETA}%)")
    ax.plot(s.index, s.values, "o-", ms=1.8, lw=1.0, color=C_MAIN, zorder=2, label="Observed")
    xs = np.array([2010, 2024])
    ax.plot(xs, r.slope * xs + r.intercept, "--", lw=1.0, color="#222222", zorder=3, label="OLS trend")
    ax.set_ylim(0, 17)
    ax.set_yticks([0, 5, 10, 15])
    ax.set_xticks(range(2010, 2025, 4))
    ax.grid(alpha=0.3)
    nome = REGIOES_EN[reg]
    # A inclinacao fica no titulo do painel, onde nao cobre os dados
    sufixo = f": {r.slope:+.2f} p.p./yr*".replace("-", "−") if r.pvalue < 0.05 else ""
    ax.set_title(nome + sufixo, fontsize=6.5, loc="left", pad=2)
    ax.tick_params(labelsize=6)
axes[1, 2].axis("off")
handles, labels = axes[0, 0].get_legend_handles_labels()
axes[1, 2].legend(handles, labels, title="* Slope with p<0.05", title_fontsize=6, fontsize=6, loc="center", frameon=False)
axes[0, 2].tick_params(labelbottom=True)
axes[1, 0].set_xlim(2010, 2024)
fig.supxlabel("Census year", fontsize=7)
fig.supylabel("preta share of declared entrants (%)", fontsize=7, x=0.015)
fig.subplots_adjust(left=0.085, right=0.995, top=0.93, bottom=0.17, wspace=0.07, hspace=0.42)
fig.savefig(FIG / "sec8_regional_trends.pdf", bbox_inches="tight")
fig.savefig(FIG / "sec8_regional_trends.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ============================================================
# FIGURA 2 - participacao por curso, 2024
# ============================================================
# Decisoes de dados:
#  - nomes de curso nao existem no pickle; mapa co_curso -> no_curso extraido dos
#    microdados de 2024 (moda do nome por codigo): analysis/data/mapa_curso_nome.csv
#  - variantes evidentes de nome (plural/truncamento) sao unificadas antes da traducao
#  - shares sobre ingressantes DECLARADOS (qt_ing - qt_ing_cornd)
#  - ano 2024 apenas: todos os cursos do top-10 tem volume alto (> 500 ingressantes
#    pretos), logo nao foi necessaria agregacao 2022-2024
curso_map = pd.read_csv(MAP, index_col=0)["no_curso"]
VARIANTES = {
    "Análise Eimento De Sistemas": "Análise E Desenvolvimento De Sistemas",
    "Ciências Da Computação": "Ciência Da Computação",
    "Sistema De Informação": "Sistemas De Informação",
    "Banco De Dados (Básico)": "Banco De Dados",
}
TRAD = {
    "Análise E Desenvolvimento De Sistemas": "Analysis and Systems Development",
    "Gestão Da Tecnologia Da Informação": "IT Management",
    "Ciência Da Computação": "Computer Science",
    "Engenharia De Software": "Software Engineering",
    "Sistemas De Informação": "Information Systems",
    "Tecnologia Da Informação": "Information Technology",
    "Redes De Computadores": "Computer Networks",
    "Ciência De Dados": "Data Science",
    "Sistemas Para Internet": "Internet Systems",
    "Segurança Da Informação": "Information Security",
    "Banco De Dados": "Databases",
    "Jogos Digitais": "Digital Games",
    "Defesa Cibernética": "Cyber Defense",
}

d24 = df[df["ano_arquivo"] == 2024].copy()
d24["curso"] = d24["co_curso"].map(curso_map).replace(VARIANTES)
g = d24.groupby("curso").agg(
    total=("qt_ing", "sum"), preta=("qt_ing_preta", "sum"),
    parda=("qt_ing_parda", "sum"), cornd=("qt_ing_cornd", "sum"))
g["declarados"] = g["total"] - g["cornd"]
g["share_preta"] = 100 * g["preta"] / g["declarados"]
g["share_negra"] = 100 * (g["preta"] + g["parda"]) / g["declarados"]
g["pct_dos_pretos"] = 100 * g["preta"] / g["preta"].sum()
g = g.sort_values("preta", ascending=False)

top = g.head(10).copy()
top["curso_en"] = [TRAD.get(c, c.title()) for c in top.index]
top[["total", "preta", "parda", "declarados", "share_preta",
     "share_negra", "pct_dos_pretos"]].round(2).to_csv(OUT / "sec6_share_by_course.csv")

# "~42%": valor citado na versao da conferencia (42,1%). O artigo estendido o compara com o acumulado
# 2010-2024 (41,3%, em run_robustez.py) e cita o valor de 2024 calculado aqui (44,9%); a linha "diferenca"
# abaixo apenas registra a distancia entre o valor de 2024 e essa referencia.
ads_pct = g.loc["Análise E Desenvolvimento De Sistemas", "pct_dos_pretos"]
log("")
log("[1] Share dos ingressantes pretos (2024) em Analysis and Systems Development")
log(f"    (versao da conferencia: ~42%)  ->  2024: {ads_pct:.1f}% (variantes de nome unificadas)")
for y in (2022, 2023, 2024):
    dy = df[df["ano_arquivo"] == y].copy()
    dy["curso"] = dy["co_curso"].map(curso_map).replace(VARIANTES)
    gy = dy.groupby("curso")["qt_ing_preta"].sum()
    log(f"    {y}: {100 * gy.get('Análise E Desenvolvimento De Sistemas', 0) / gy.sum():.1f}%")
if abs(ads_pct - 42) > 1.0:
    log(f"    diferenca de 2024 para a referencia da versao da conferencia (~42%): {ads_pct - 42:+.1f} p.p.")

log("")
log("[2] 2024: privadas com fins lucrativos (texto: 70% de 489 mil) e EaD")
tot24 = d24["qt_ing"].sum()
priv = 100 * d24.loc[d24["tp_categoria_administrativa"] == 4, "qt_ing"].sum() / tot24
ead = 100 * d24.loc[d24["tp_modalidade_ensino"] == 2, "qt_ing"].sum() / tot24
log(f"    total ingressantes 2024 = {tot24:,} (texto: 489 mil)")
log(f"    privadas c/ fins lucrativos = {priv:.1f}% (texto: 70%)")
log(f"    EaD (distance) = {ead:.1f}% dos ingressantes 2024")

# figura: barras horizontais agrupadas (preta / negro)
plot = top.iloc[::-1]  # maior no topo
y = np.arange(len(plot))
h = 0.38
fig, ax = plt.subplots(figsize=(7.0, 3.7))
colors = C_MAIN
ax.barh(y + h / 2, plot["share_preta"], height=h, color=colors, label="preta")
ax.barh(y - h / 2, plot["share_negra"], height=h, color=colors, alpha=0.45,
        label="negro (preta+parda)")
ax.set_yticks(y, plot["curso_en"], fontsize=8.5)
ax.set_xlabel("Share of declared entrants, 2024 (%)")
ax.axvline(BENCH_PRETA, ls=":", lw=1.0, color=C_BENCH)
ax.annotate(f"{BENCH_PRETA}% preta benchmark", (BENCH_PRETA, len(plot) - 0.15),
            fontsize=7, color=C_BENCH, ha="left", va="bottom",
            xytext=(3, 0), textcoords="offset points")
ax.axvline(55.5, ls=":", lw=1.0, color=C_BENCH)
ax.annotate("55.5% negro benchmark", (55.5, len(plot) - 0.15), fontsize=7, color=C_BENCH,
            ha="right", va="bottom", xytext=(-3, 0), textcoords="offset points")
for yi, (_, row) in zip(y, plot.iterrows()):
    ax.annotate(f"{row['pct_dos_pretos']:.1f}% of all preta entrants",
                (row["share_preta"] + 0.6, yi + h / 2),
                fontsize=7, color=C_GRAY, va="center")
ax.set_xlim(0, 62)
ax.set_ylim(-0.6, len(plot) + 0.4)
ax.legend(fontsize=8, loc="lower center", bbox_to_anchor=(0.5, -0.26), ncol=2,
          frameon=False)
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec6_share_by_course.pdf", bbox_inches="tight")
fig.savefig(FIG / "sec6_share_by_course.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ============================================================
# FIGURA 3 - evolucao por modalidade (EaD x presencial), 2010-2024
# ============================================================
MOD_EN = {1: "On-site", 2: "Distance"}
mod = df[df["tp_modalidade_ensino"].isin([1, 2])].groupby(
    ["ano_arquivo", "tp_modalidade_ensino"]).agg(
    total=("qt_ing", "sum"), preta=("qt_ing_preta", "sum"),
    parda=("qt_ing_parda", "sum"), cornd=("qt_ing_cornd", "sum"))
mod["declarados"] = mod["total"] - mod["cornd"]
mod["share_negra"] = 100 * (mod["preta"] + mod["parda"]) / mod["declarados"]
absol = mod["total"].unstack("tp_modalidade_ensino").loc[WIN]
share = mod["share_negra"].unstack("tp_modalidade_ensino").loc[WIN]
absol.to_csv(OUT / "sec10_modality_absolutos.csv")
share.round(2).to_csv(OUT / "sec10_modality_share_negra.csv")

plt.rcParams.update({'font.size': 7, 'axes.labelsize': 7, 'axes.titlesize': 7, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5, 'legend.fontsize': 6})
fig, (a1, a2) = plt.subplots(1, 2, figsize=(4.8, 1.75))
xt = list(range(2010, 2025, 4))
a1.stackplot(absol.index, absol[1] / 1000, absol[2] / 1000,
             labels=[MOD_EN[1], MOD_EN[2]],
             colors=[C_MAIN, "#9ECAE1"])
a1.set_title("(a) Entrants by modality", loc="left", pad=2)
a1.set_ylabel("Entrants (thousands)")
a1.set_xlim(2010, 2024); a1.set_xticks(xt)
a1.legend(fontsize=6, loc="upper left")
a1.grid(alpha=0.3)
for m, cor in ((1, C_MAIN), (2, C_ACCENT)):
    s = share[m].dropna()
    a2.plot(s.index, s.values, "o-", ms=3, lw=1.4, color=cor, label=MOD_EN[m])
a2.set_title("(b) negro share of declared entrants", loc="left", pad=2)
a1.set_xlabel("Census year"); a2.set_xlabel("Census year"); a2.set_ylabel("Share (%)")
a2.set_xlim(2010, 2024); a2.set_xticks(xt)
a2.legend(fontsize=6)
a2.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec10_modality_evolution.pdf", bbox_inches="tight")
fig.savefig(FIG / "sec10_modality_evolution.png", dpi=200, bbox_inches="tight")
plt.close(fig)

log("")
log("[extra] Modalidade (ingressantes computacao):")
for y in (2010, 2015, 2020, 2024):
    log(f"    {y}: EaD = {100 * absol.loc[y, 2] / absol.loc[y].sum():.1f}% "
        f"({int(absol.loc[y, 2]):,} de {int(absol.loc[y].sum()):,}) | "
        f"share negro EaD = {share.loc[y, 2]:.1f}% | On-site = {share.loc[y, 1]:.1f}%")

# ============================================================
# copia PDFs para paper/figures (se a pasta existir) e grava arquivo de verificacao
# ============================================================
import shutil
if PAPER_FIG.is_dir():
    for nome in ("sec8_regional_trends.pdf", "sec6_share_by_course.pdf",
                 "sec10_modality_evolution.pdf"):
        shutil.copy2(FIG / nome, PAPER_FIG / nome)

(OUT / "figuras_extras_check.txt").write_text("\n".join(check_lines), encoding="utf-8")
destinos = f"{FIG}, {PAPER_FIG}" if PAPER_FIG.is_dir() else f"{FIG}"
print(f"\nArquivos em: {destinos} e {OUT / 'figuras_extras_check.txt'}")
