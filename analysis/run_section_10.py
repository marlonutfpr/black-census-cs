# Secao 6.5 do artigo estendido (RQ8): mecanismos de acao afirmativa (analise ecologica) +
# desagregacao institucional. O nome do arquivo, o prefixo sec10_ das saidas e os rotulos 10.1-10.3 das etapas
# abaixo seguem uma numeracao anterior das secoes (as etapas nao sao subsecoes do artigo).
#  10.1 uptake das politicas entre ingressantes (serie nacional: reserva de vagas, cota etnico-racial, PROUNI,
#       FIES, escola publica); a cota etnico-racial soma RVETNICO (ate 2023) e RVPPI + RVQUILO (2024).
#  10.2 intensidade de reserva de vagas x share negra (preta+parda, declarados) no nivel oferta-ano: ofertas
#       sem ingressantes via cota + tercis de intensidade entre as demais; Kruskal-Wallis por ano.
#  10.3 share negra (declarados) por categoria administrativa (codigos 1-9 do INEP) e por organizacao academica.
# No artigo: Fig. 10 (fig:uptake), paineis (a) sec10_policy_uptake e (b) sec10_quota_terciles; colunas brutas
# ("Gross") da Tabela 12 (tab:quota) e numeros do texto da Secao 6.5. As colunas liquidas ("Net") da Tabela 12
# vem de run_robustez.py. O painel (b) da Fig. 11 (fig:modality) e desenhado por run_recomposicao.py a partir
# de sec10_share_negra_categoria_adm.csv; por isso este script deve rodar antes de run_recomposicao.py.
# Uso: python analysis/run_section_10.py   (sem argumentos)
# Entrada: pkl de build_dataset.py, no caminho da variavel de ambiente CENSO_PKL
# (padrao analysis/data/computacao_2009_2024.pkl).
# Saidas em analysis/output/: sec10_policy_uptake.csv, sec10_tercis_quota.csv,
# sec10_share_negra_categoria_adm.csv, sec10_share_negra_organizacao.csv (auxiliar).
# Em analysis/figures/ (PDF e PNG): sec10_policy_uptake, sec10_quota_terciles e sec10_share_negra_categoria_adm
# (esta ultima nao entra no artigo). Os p-valores de Kruskal-Wallis saem apenas no stdout.

import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("CENSO_PKL", ROOT / "analysis" / "data" / "computacao_2009_2024.pkl"))
OUT = ROOT / "analysis" / "output"
FIG = ROOT / "analysis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

df = pd.read_pickle(DATA)
WIN = slice(2010, 2024)

CAT_ADM = {1: "Public-Federal", 2: "Public-State", 3: "Public-Municipal",
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
    rvetnico=("qt_ing_rvetnico", "sum"), rvppi=("qt_ing_rvppi", "sum"), rvquilo=("qt_ing_rvquilo", "sum"),
    prounii=("qt_ing_prounii", "sum"),
    prounip=("qt_ing_prounip", "sum"), fies=("qt_ing_fies", "sum"),
    esc_pub=("qt_ing_procescpublica", "sum"))
pol["pct_reserva"] = 100 * pol["reserva"] / pol["ing"]
# Geracoes da variavel: RVETNICO ate 2023; RVPPI + RVQUILO em 2024.
pol["racial"] = pol["rvetnico"] + pol["rvppi"] + pol["rvquilo"]
pol["pct_rvetnico"] = 100 * pol["racial"] / pol["ing"]
pol["pct_prouni"] = 100 * (pol["prounii"] + pol["prounip"]) / pol["ing"]
pol["pct_fies"] = 100 * pol["fies"] / pol["ing"]
pol["pct_esc_publica"] = 100 * pol["esc_pub"] / pol["ing"]
pol.round(2).to_csv(OUT / "sec10_policy_uptake.csv")
print("== 10.1 Uptake das politicas entre ingressantes (%) ==")
print(pol[["pct_reserva", "pct_rvetnico", "pct_prouni", "pct_fies", "pct_esc_publica"]].loc[WIN].round(1).to_string())

# ============================================================
# 10.2 Tercis de intensidade de reserva de vagas x representatividade
#     (analise ecologica no nivel oferta-ano; apenas ofertas com ingressantes)
# ============================================================
d = df[(df["ano_arquivo"] >= 2010) & (df["qt_ing"] > 0)].copy()
d["declarados"] = d["qt_ing"] - d["qt_ing_cornd"]
d = d[d["declarados"] > 0]
d["share_negra"] = (d["qt_ing_preta"] + d["qt_ing_parda"]) / d["declarados"]
d["int_quota"] = d["qt_ing_reserva_vaga"].fillna(0).astype("float64") / d["qt_ing"]

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
quartis = pd.DataFrame(linhas)  # nome historico da variavel; os grupos sao tercis
quartis.to_csv(OUT / "sec10_tercis_quota.csv", index=False)

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
fig, ax = plt.subplots(figsize=(2.4, 2.1))
for col, rot, cor in (("pct_reserva", "Quota entrants (any)", "#2E7D32"),
                      ("pct_rvetnico", "Ethnic-racial quota", "#1B5E20"),
                      ("pct_prouni", "PROUNI (full+partial)", "#1565C0"),
                      ("pct_fies", "FIES", "#C62828")):
    s = pol[col].loc[WIN].copy()
    ax.plot(s.index, s.values, marker="o", ms=2, lw=1.1, label=rot, color=cor)
ax.set_title("(a) Policy uptake", fontsize=7, loc="left", pad=2)
ax.set_xticks(range(2010, 2025, 4))
ax.set_xlabel("Census year", fontsize=6.5); ax.set_ylabel("Share of entrants (%)", fontsize=6.5)
ax.tick_params(labelsize=6)
ax.legend(fontsize=5.5, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, frameon=False, handlelength=1.2, columnspacing=0.8); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec10_policy_uptake.pdf")
fig.savefig(FIG / "sec10_policy_uptake.png", dpi=200)
plt.close(fig)

# Fig 2: share negra media por grupo de intensidade de cota
fig, ax = plt.subplots(figsize=(2.4, 2.1))
CORES_G = {"0_sem_cota": "#9E9E9E", "T1": "#64B5F6", "T2": "#FB8C00", "T3": "#C62828"}
ROT_G = {"0_sem_cota": "No quota entrants", "T1": "Low quota intensity",
         "T2": "Mid quota intensity", "T3": "High quota intensity"}
for q in ("0_sem_cota", "T1", "T2", "T3"):
    sub = quartis[quartis["grupo"] == q]
    if len(sub):
        ax.plot(sub["ano"], sub["share_negra_med"], marker="o", ms=2, lw=1.1,
                color=CORES_G[q], label=ROT_G[q])
ax.set_title("(b) Quota intensity", fontsize=7, loc="left", pad=2)
ax.set_xticks(range(2010, 2025, 4))
ax.set_xlabel("Census year", fontsize=6.5); ax.set_ylabel("Mean negro share (%)", fontsize=6.5)
ax.tick_params(labelsize=6)
ax.legend(fontsize=5.5, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, frameon=False, handlelength=1.2, columnspacing=0.8); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec10_quota_terciles.pdf")
fig.savefig(FIG / "sec10_quota_terciles.png", dpi=200)
plt.close(fig)

# Fig 3: share negra por categoria administrativa
plt.rcParams.update({'font.size': 7, 'axes.labelsize': 7, 'axes.titlesize': 7, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5, 'legend.fontsize': 6})
fig, ax = plt.subplots(figsize=(4.4, 1.8))
for c in cat.columns:
    s = cat[c].loc[WIN].dropna()
    if len(s) >= 8:  # ignora categorias sem serie minima (ex.: comunitaria/confessional)
        ax.plot(s.index, s.values, marker="o", ms=3, lw=1.3, label=c)
ax.set_xlabel("Census year"); ax.set_ylabel("negro share among entrants (%)")
ax.legend(fontsize=5.5, ncol=2, loc="lower right"); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec10_share_negra_categoria_adm.pdf")
fig.savefig(FIG / "sec10_share_negra_categoria_adm.png", dpi=200)
plt.close(fig)

print(f"\nArquivos em: {OUT} e {FIG}")
