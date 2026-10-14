# Secao 10 do plano de extensao: mecanismos de acao afirmativa (analise ecologica) +
# desagregacao institucional (7 categorias administrativas).
# Saidas: series temporais de uptake das politicas; comparacao por quartis de intensidade
# de reserva de vagas; representatividade por categoria administrativa.

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "analysis" / "data" / "computacao_2009_2024.pkl"
OUT = ROOT / "analysis" / "output"
FIG = ROOT / "analysis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

df = pd.read_pickle(DATA)
WIN = slice(2010, 2024)

CAT_ADM = {1: "Public -- Federal", 2: "Public -- State", 3: "Public -- Municipal",
           4: "Private for-profit", 5: "Private non-profit",
           6: "Private (strictly particular)", 7: "Special",
           8: "Private community", 9: "Private confessional"}
ORG_ACAD = {1: "Universidade", 2: "Centro Universitario", 3: "Faculdade",
            4: "IF/CEFET", 5: "Outros"}

# ============================================================
# 10.1 Uptake agregado das politicas entre ingressantes (serie nacional)
# ============================================================
pol = df.groupby("ano_arquivo").agg(
    ing=("qt_ing", "sum"), reserva=("qt_ing_reserva_vaga", "sum"),
    rvetnico=("qt_ing_rvetnico", "sum"), prounii=("qt_ing_prounii", "sum"),
    prounip=("qt_ing_prounip", "sum"), fies=("qt_ing_fies", "sum"),
    esc_pub=("qt_ing_procescpublica", "sum"))
pol["pct_reserva"] = 100 * pol["reserva"] / pol["ing"]
pol["pct_rvetnico"] = 100 * pol["rvetnico"] / pol["ing"]
pol["pct_prouni"] = 100 * (pol["prounii"] + pol["prounip"]) / pol["ing"]
pol["pct_fies"] = 100 * pol["fies"] / pol["ing"]
pol["pct_esc_publica"] = 100 * pol["esc_pub"] / pol["ing"]
pol.round(2).to_csv(OUT / "sec10_policy_uptake.csv")
print("== 10.1 Uptake das politicas entre ingressantes (%) ==")
print(pol[["pct_reserva", "pct_rvetnico", "pct_prouni", "pct_fies", "pct_esc_publica"]].loc[WIN].round(1).to_string())

# ============================================================
# 10.2 Quartis de intensidade de reserva de vagas x representatividade
#     (analise ecologica no nivel oferta-ano; apenas ofertas com ingressantes)
# ============================================================
d = df[(df["ano_arquivo"] >= 2010) & (df["qt_ing"] > 0)].copy()
d["declarados"] = d["qt_ing"] - d["qt_ing_cornd"]
d = d[d["declarados"] > 0]
d["share_negra"] = (d["qt_ing_preta"] + d["qt_ing_parda"]) / d["declarados"]
d["int_quota"] = d["qt_ing_reserva_vaga"] / d["qt_ing"]

def faz_grupos(g):
    """Grupo 0 = sem ingressantes via cota; entre as ofertas com cota, tercis de intensidade."""
    grupos = pd.Series(np.where(g["int_quota"] <= 0, "0_sem_cota", None), index=g.index, dtype=object)
    pos = g["int_quota"] > 0
    if pos.sum() >= 30:
        terc = pd.qcut(g.loc[pos, "int_quota"], 3, labels=["T1", "T2", "T3"], duplicates="drop")
        grupos.loc[pos] = terc.astype(str)
    return grupos


linhas = []
kw = {}
for ano, g in d.groupby("ano_arquivo"):
    g = g.copy()
    g["grupo"] = faz_grupos(g)
    for q, gg in g.groupby("grupo", observed=True):
        linhas.append({"ano": ano, "grupo": str(q), "n_ofertas": len(gg),
                       "int_quota_med": round(gg["int_quota"].mean(), 4),
                       "share_negra_med": round(100 * gg["share_negra"].mean(), 2),
                       "share_negra_ic95": round(1.96 * 100 * gg["share_negra"].std() / np.sqrt(len(gg)), 2)})
    grupos_kw = [gg["share_negra"].values for _, gg in g.groupby("grupo") if len(gg) > 5]
    if len(grupos_kw) >= 2:
        kw[ano] = stats.kruskal(*grupos_kw).pvalue
quartis = pd.DataFrame(linhas)
quartis.to_csv(OUT / "sec10_quartis_quota.csv", index=False)

print("\n== 10.2 Share negra media por grupo de intensidade de cota (%) ==")
piv = quartis.pivot_table(index="ano", columns="grupo", values="share_negra_med")
print(piv.round(1).to_string())

print("\nKruskal-Wallis (p-valor) por ano:")
print({a: f"{p:.1e}" for a, p in kw.items()})

# ============================================================
# 10.3 Desagregacao institucional: share negra (declarados) por categoria adm.
# ============================================================
def share_por_dim(dim, mapa):
    g = df.groupby(["ano_arquivo", dim]).agg(
        total=("qt_ing", "sum"), preta=("qt_ing_preta", "sum"),
        parda=("qt_ing_parda", "sum"), cornd=("qt_ing_cornd", "sum"))
    decl = g["total"] - g["cornd"]
    s = 100 * (g["preta"] + g["parda"]) / decl.where(decl > 0)
    s = s.unstack(dim).rename(columns=mapa)
    return s.round(2)

cat = share_por_dim("tp_categoria_administrativa", CAT_ADM)
cat.to_csv(OUT / "sec10_share_negra_categoria_adm.csv")
print("\n== 10.3 Share negra entre ingressantes (declarados) por categoria administrativa ==")
print(cat.loc[WIN].to_string())

org = share_por_dim("tp_organizacao_academica", ORG_ACAD)
org.to_csv(OUT / "sec10_share_negra_organizacao.csv")

# ============================================================
# Figuras
# ============================================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Fig 1: uptake das politicas
fig, ax = plt.subplots(figsize=(7.0, 3.8))
for col, rot, cor in (("pct_reserva", "Quota seats (any)", "#2E7D32"),
                      ("pct_rvetnico", "Ethnic-racial quota", "#1B5E20"),
                      ("pct_prouni", "PROUNI (full+partial)", "#1565C0"),
                      ("pct_fies", "FIES", "#C62828"),
                      ("pct_esc_publica", "Public-school origin", "#6A1B9A")):
    s = pol[col].loc[WIN].copy()
    if col == "pct_rvetnico":
        s.loc[2024] = np.nan  # 2024: variavel substituida pelas subcategorias RV* (schema novo)
    ax.plot(s.index, s.values, marker="o", ms=3.5, lw=1.4, label=rot, color=cor)
ax.set_xlabel("Census year"); ax.set_ylabel("Share of entrants (%)")
ax.legend(fontsize=8); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec10_policy_uptake.pdf")
fig.savefig(FIG / "sec10_policy_uptake.png", dpi=200)
plt.close(fig)

# Fig 2: share negra media por grupo de intensidade de cota
fig, ax = plt.subplots(figsize=(7.0, 3.8))
CORES_G = {"0_sem_cota": "#9E9E9E", "T1": "#64B5F6", "T2": "#FB8C00", "T3": "#C62828"}
ROT_G = {"0_sem_cota": "No quota entrants", "T1": "Low quota intensity",
         "T2": "Mid quota intensity", "T3": "High quota intensity"}
for q in ("0_sem_cota", "T1", "T2", "T3"):
    sub = quartis[quartis["grupo"] == q]
    if len(sub):
        ax.plot(sub["ano"], sub["share_negra_med"], marker="o", ms=3.5, lw=1.4,
                color=CORES_G[q], label=ROT_G[q])
ax.set_xlabel("Census year"); ax.set_ylabel("Mean Black+Brown share among entrants (%)")
ax.legend(fontsize=8); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec10_quota_quartiles.pdf")
fig.savefig(FIG / "sec10_quota_quartiles.png", dpi=200)
plt.close(fig)

# Fig 3: share negra por categoria administrativa
fig, ax = plt.subplots(figsize=(7.0, 4.0))
for c in cat.columns:
    s = cat[c].loc[WIN].dropna()
    if len(s) >= 8:  # ignora categorias sem serie minima (ex.: comunitaria/confessional)
        ax.plot(s.index, s.values, marker="o", ms=3, lw=1.3, label=c)
ax.set_xlabel("Census year"); ax.set_ylabel("Black+Brown share among entrants (%)")
ax.legend(fontsize=7, ncol=2); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec10_share_negra_categoria_adm.pdf")
fig.savefig(FIG / "sec10_share_negra_categoria_adm.png", dpi=200)
plt.close(fig)

print(f"\nArquivos em: {OUT} e {FIG}")
