# Secao 9 do plano de extensao: conclusao por coorte sintetica defasada.
# taxa_coorte(t) = concluintes(t) / ingressantes(t - k), k=3 (tecnologo) e k=4 (bacharelado/licenciatura).
# Grupos: preta, negra (preta+parda), branca. Denominador declarado (desconta cornd) nas razoes de disparidade.
# Estratificacao: rede (publica x privada) e modalidade (presencial x EaD).

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "analysis" / "data" / "computacao_2009_2024.pkl"
OUT = ROOT / "analysis" / "output"
FIG = ROOT / "analysis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

df = pd.read_pickle(DATA)

# tp_grau_academico (dicionario INEP): 1=Bacharelado, 2=Licenciatura, 3=Tecnologico,
# 4=Bacharelado e Licenciatura. k=3 para tecnologico; k=4 para os demais.
GRAU_K = {1: 4, 2: 4, 3: 3, 4: 4}
df["k_coorte"] = df["tp_grau_academico"].map(GRAU_K)
print("Cursos sem grau academico mapeado:", int(df["k_coorte"].isna().sum()))
df = df.dropna(subset=["k_coorte"])

GRUPOS = {"preta": ["preta"], "negra": ["preta", "parda"], "branca": ["branca"]}


def somas(d, base):
    g = d.groupby("ano_arquivo")[[f"qt_{base}", f"qt_{base}_preta", f"qt_{base}_parda",
                                  f"qt_{base}_branca", f"qt_{base}_cornd"]].sum()
    g.columns = ["total", "preta", "parda", "branca", "cornd"]
    g["negra"] = g["preta"] + g["parda"]
    return g


def taxa_coorte(d, rotulo):
    """Retorna DF indexado por ano de conclusao t, com taxa por grupo e razoes de disparidade."""
    linhas = []
    for k in (3, 4):
        dd = d[d["k_coorte"] == k]
        ing = somas(dd, "ing")
        conc = somas(dd, "conc")
        anos_t = sorted(set(conc.index) & {a + k for a in ing.index})
        for t in anos_t:
            i = ing.loc[t - k]
            c = conc.loc[t]
            row = {"grau_k": k, "ano_conclusao": t, "ano_ingresso": t - k,
                   "recorte": rotulo}
            for gname in ("preta", "negra", "branca"):
                row[f"taxa_{gname}"] = 100 * c[gname] / i[gname] if i[gname] > 0 else np.nan
            row["disp_preta_vs_branca"] = row["taxa_preta"] / row["taxa_branca"] if row.get("taxa_branca") else np.nan
            row["disp_negra_vs_branca"] = row["taxa_negra"] / row["taxa_branca"] if row.get("taxa_branca") else np.nan
            linhas.append(row)
    return pd.DataFrame(linhas)


# --- Brasil (todos os cursos) ---
res = [taxa_coorte(df, "Brasil")]

# --- rede: publica (cat adm 1-3) x privada (4-7) ---
res.append(taxa_coorte(df[df["tp_categoria_administrativa"].isin([1, 2, 3])], "Publica"))
res.append(taxa_coorte(df[df["tp_categoria_administrativa"].isin([4, 5, 6, 7])], "Privada"))

# --- modalidade ---
res.append(taxa_coorte(df[df["tp_modalidade_ensino"] == 1], "Presencial"))
res.append(taxa_coorte(df[df["tp_modalidade_ensino"] == 2], "EaD"))

cohort = pd.concat(res, ignore_index=True).round(3)
cohort.to_csv(OUT / "sec9_cohort_completion.csv", index=False)

print("\n== Brasil: taxa de conclusao por coorte (%) ==")
br = cohort[cohort["recorte"] == "Brasil"]
print(br.pivot_table(index="ano_conclusao", columns="grau_k",
                     values=["taxa_preta", "taxa_negra", "taxa_branca"]).round(1).to_string())

print("\n== Brasil: razao de disparidade (grupo / branca) ==")
print(br.pivot_table(index="ano_conclusao", columns="grau_k",
                     values=["disp_preta_vs_branca", "disp_negra_vs_branca"]).round(3).to_string())

print("\n== Recortes (k=3 tecnologo e k=4 bacharelado), ultimos 3 anos de coorte ==")
ult = cohort[cohort["ano_conclusao"] >= cohort["ano_conclusao"].max() - 2]
print(ult.pivot_table(index=["recorte", "ano_conclusao"], columns="grau_k",
                      values=["taxa_preta", "taxa_negra", "taxa_branca"]).round(1).to_string())

# --- figuras ---
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CORES_G = {"preta": "#222222", "negra": "#B07AA1", "branca": "#4C78A8"}

# Fig 1: evolucao das taxas por grupo, painel por k (Brasil)
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), sharey=True)
for ax, k, tit in zip(axes, (3, 4), ("Technologist (k=3)", "Bachelor/Licenciatura (k=4)")):
    sub = br[br["grau_k"] == k]
    for gname, rot in (("preta", "Black (preta)"), ("negra", "Black+Brown (IBGE)"), ("branca", "White")):
        ax.plot(sub["ano_conclusao"], sub[f"taxa_{gname}"], marker="o", ms=3.5,
                color=CORES_G[gname], label=rot)
    ax.set_title(tit, fontsize=9)
    ax.set_xlabel("Graduation year"); ax.grid(alpha=0.3)
axes[0].set_ylabel("Cohort completion rate (%)")
axes[1].legend(fontsize=8, loc="lower right")
fig.tight_layout()
fig.savefig(FIG / "sec9_cohort_completion_brazil.pdf")
fig.savefig(FIG / "sec9_cohort_completion_brazil.png", dpi=200)
plt.close(fig)

# Fig 2: razao de disparidade negra/branca por recorte (k=3 e k=4 empilhados)
fig, axes = plt.subplots(2, 1, figsize=(6.8, 6.0), sharex=True, sharey=True)
for ax, k, tit in zip(axes, (3, 4), ("Technologist (k=3)", "Bachelor/Licenciatura (k=4)")):
    for rec, cor in (("Publica", "#2E7D32"), ("Privada", "#C62828"),
                     ("Presencial", "#1565C0"), ("EaD", "#EF6C00")):
        sub = cohort[(cohort["recorte"] == rec) & (cohort["grau_k"] == k)]
        rot = {"Publica": "Public", "Privada": "Private",
               "Presencial": "On-site", "EaD": "Distance (EaD)"}[rec]
        ax.plot(sub["ano_conclusao"], sub["disp_negra_vs_branca"], marker="o", ms=3,
                lw=1.3, label=rot)
    ax.axhline(1.0, ls=":", color="gray", lw=1)
    ax.set_title(tit, fontsize=9)
    ax.set_ylabel("Disparity ratio\n(Black+Brown / White)", fontsize=8)
    ax.grid(alpha=0.3)
axes[1].set_xlabel("Graduation year")
axes[0].legend(fontsize=8, ncol=4, loc="upper center")
fig.tight_layout()
fig.savefig(FIG / "sec9_disparity_ratio_by_strata.pdf")
fig.savefig(FIG / "sec9_disparity_ratio_by_strata.png", dpi=200)
plt.close(fig)

print(f"\nArquivos em: {OUT} e {FIG}")
