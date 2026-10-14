# Figuras extras do plano de extensao (LNCS/Springer, em ingles):
#  1. sec8_regional_trends.pdf    - tendencias regionais da participacao preta (Secao 8)
#  2. sec6_share_by_course.pdf    - participacao por curso, 2024 (Secao 6)
#  3. sec10_modality_evolution.pdf- evolucao por modalidade (Discussao)
# Tambem gera analysis/output/figuras_extras_check.txt com a verificacao cruzada
# dos numeros citados no texto do artigo. NAO ajusta dados em caso de divergencia.

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "analysis" / "data" / "computacao_2009_2024.pkl"
MAP = ROOT / "analysis" / "data" / "mapa_curso_nome.csv"  # co_curso -> no_curso (moda em 2024)
OUT = ROOT / "analysis" / "output"
FIG = ROOT / "analysis" / "figures"
PAPER_FIG = ROOT / "paper" / "figures"
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

fig, axes = plt.subplots(5, 1, figsize=(7.0, 7.6), sharex=True)
for ax, reg in zip(axes, [1, 2, 3, 4, 5]):
    s, r = region_stats[reg]
    ax.axhline(BENCH_PRETA, ls=":", lw=1.0, color=C_BENCH, zorder=1)
    ax.plot(s.index, s.values, "o-", ms=3.5, lw=1.4, color=C_MAIN, zorder=3)
    xs = np.array([2010, 2024])
    ax.plot(xs, r.slope * xs + r.intercept, "--", lw=1.2, color=C_GRAY, zorder=2)
    ax.set_ylim(0, 14)
    ax.set_yticks([0, 5, 10])
    ax.grid(alpha=0.3)
    nome = REGIOES_EN[reg]
    ax.set_title(nome, fontsize=9, loc="left", pad=2)
    if r.pvalue < 0.05:
        ax.annotate(f"slope {r.slope:+.2f} pp/yr (p<0.05)", (2010.3, 0.6),
                    fontsize=7.5, color=C_GRAY, va="bottom")
    if reg == 1:
        ax.annotate(f"population benchmark {BENCH_PRETA}% (IBGE 2022)",
                    (2024, BENCH_PRETA), fontsize=7, color=C_BENCH,
                    ha="right", va="bottom")
axes[-1].set_xlabel("Census year")
axes[-1].set_xlim(2010, 2024)
fig.supylabel("Black (preta) share of declared entrants (%)", fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.99))
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
#  - ano 2024 apenas: todos os cursos do top-10 tem volume alto (>= 700 ingressantes
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
g["pct_dos_negros"] = 100 * g["preta"] / g["preta"].sum()
g = g.sort_values("preta", ascending=False)

top = g.head(10).copy()
top["curso_en"] = [TRAD.get(c, c.title()) for c in top.index]
top[["total", "preta", "parda", "declarados", "share_preta",
     "share_negra", "pct_dos_negros"]].round(2).to_csv(OUT / "sec6_share_by_course.csv")

ads_pct = g.loc["Análise E Desenvolvimento De Sistemas", "pct_dos_negros"]
log("")
log("[1] Share dos ingressantes pretos (2024) em Analysis and Systems Development")
log(f"    (texto: ~42%)  ->  computado: {ads_pct:.1f}% (variantes de nome unificadas)")
for y in (2022, 2023, 2024):
    dy = df[df["ano_arquivo"] == y].copy()
    dy["curso"] = dy["co_curso"].map(curso_map).replace(VARIANTES)
    gy = dy.groupby("curso")["qt_ing_preta"].sum()
    log(f"    {y}: {100 * gy.get('Análise E Desenvolvimento De Sistemas', 0) / gy.sum():.1f}%")
if abs(ads_pct - 42) > 1.0:
    log(f"    *** DIVERGENCIA vs. texto (~42%): {ads_pct - 42:+.1f} p.p. - NAO ajustado ***")

log("")
log("[2] 2024: privadas com fins lucrativos (texto: 70% de 489 mil) e EaD")
tot24 = d24["qt_ing"].sum()
priv = 100 * d24.loc[d24["tp_categoria_administrativa"] == 4, "qt_ing"].sum() / tot24
ead = 100 * d24.loc[d24["tp_modalidade_ensino"] == 2, "qt_ing"].sum() / tot24
log(f"    total ingressantes 2024 = {tot24:,} (texto: 489 mil)")
log(f"    privadas c/ fins lucrativos = {priv:.1f}% (texto: 70%)")
log(f"    EaD (distance) = {ead:.1f}% dos ingressantes 2024")

# figura: barras horizontais agrupadas (Black / Black+Brown), destaque no 1o curso
plot = top.iloc[::-1]  # maior no topo
y = np.arange(len(plot))
h = 0.38
fig, ax = plt.subplots(figsize=(7.0, 4.8))
colors = [C_ACCENT if c == "Analysis and Systems Development" else C_MAIN
          for c in plot["curso_en"]]
ax.barh(y + h / 2, plot["share_preta"], height=h, color=colors, label="Black (preta)")
ax.barh(y - h / 2, plot["share_negra"], height=h, color=colors, alpha=0.45,
        label="Black+Brown (preta+parda)")
ax.set_yticks(y, plot["curso_en"], fontsize=8.5)
ax.set_xlabel("Share of declared entrants, 2024 (%)")
ax.axvline(BENCH_PRETA, ls=":", lw=1.0, color=C_BENCH)
ax.annotate(f"{BENCH_PRETA}% population benchmark", (BENCH_PRETA, len(plot) - 0.15),
            fontsize=7, color=C_BENCH, ha="left", va="bottom",
            xytext=(3, 0), textcoords="offset points")
for yi, (_, row) in zip(y, plot.iterrows()):
    ax.annotate(f"{row['pct_dos_negros']:.1f}% of all Black entrants",
                (max(row["share_preta"], row["share_negra"]) + 0.6, yi),
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
MOD_EN = {1: "On-site", 2: "Distance (EaD)"}
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

fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.8, 5.6), sharex=True)
xt = list(range(2010, 2025, 2))
a1.stackplot(absol.index, absol[1] / 1000, absol[2] / 1000,
             labels=[MOD_EN[1], MOD_EN[2]],
             colors=[C_MAIN, "#9ECAE1"])
a1.set_title("(a) Entrants by modality", fontsize=9, loc="left")
a1.set_ylabel("Entrants (thousands)")
a1.set_xlim(2010, 2024); a1.set_xticks(xt)
a1.legend(fontsize=8, loc="upper left")
a1.grid(alpha=0.3)
for m, cor in ((1, C_MAIN), (2, C_ACCENT)):
    s = share[m].dropna()
    a2.plot(s.index, s.values, "o-", ms=3, lw=1.4, color=cor, label=MOD_EN[m])
a2.set_title("(b) Black+Brown share of declared entrants", fontsize=9, loc="left")
a2.set_xlabel("Census year"); a2.set_ylabel("Share (%)")
a2.set_xlim(2010, 2024); a2.set_xticks(xt)
a2.legend(fontsize=8)
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
        f"share Black+Brown EaD = {share.loc[y, 2]:.1f}% | On-site = {share.loc[y, 1]:.1f}%")

# ============================================================
# copia PDFs para o paper e grava arquivo de verificacao
# ============================================================
import shutil
for nome in ("sec8_regional_trends.pdf", "sec6_share_by_course.pdf",
             "sec10_modality_evolution.pdf"):
    shutil.copy2(FIG / nome, PAPER_FIG / nome)

(OUT / "figuras_extras_check.txt").write_text("\n".join(check_lines), encoding="utf-8")
print(f"\nArquivos em: {FIG}, {PAPER_FIG} e {OUT / 'figuras_extras_check.txt'}")
