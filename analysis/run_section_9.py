# Secao 9 do manuscrito estendido (RQ7): razoes de conclusao defasadas por grupo racial.
# taxa_coorte(t) = concluintes(t) / ingressantes(t - k), com k = prazo oficial - 1 (convencao do INEP em
# NU_ANO_INTEGRALIZACAO): k=2 para tecnologo (prazo 3 em 74,6% dos ingressantes) e k=4 para bacharelado (prazo 5 em 86,8%).
# A razao nao acompanha estudantes: nao e coorte real nem taxa de conclusao. O teste contra turmas acompanhadas
# (Secao 9.1, Tabela 11) fica em run_validacao_trajetoria.py.
# Grupos: preta, negra (preta+parda), branca. Contagens brutas por grupo; a cobertura de cor e tratada em run_robustez.py.
# Estratificacao: rede (publica x privada) e modalidade (presencial x EaD).
#
# Sustenta no manuscrito:
#  - Figura 9: razao negro/branco observada (Brasil, publica, privada) contra a serie mecanica nacional, 2017-2024;
#  - as faixas da razao de disparidade em 2017-2024 e a comparacao publica x privada do texto da Secao 9.
# A Tabela 10 (sensibilidade a k e ajuste de cobertura) vem de rob_k_sensitivity.csv (run_robustez.py).
#
# Uso: python analysis/run_section_9.py   (sem argumentos)
# Entradas: pkl de build_dataset.py, lido de CENSO_PKL (padrao analysis/data/computacao_2009_2024.pkl), e
#   analysis/output/val_teste_nulo.csv (serie mecanica, gerada por run_validacao_trajetoria.py). Sem esse arquivo,
#   a Figura 9 nao e gerada e o restante nao muda.
# Saida em analysis/output/: sec9_cohort_completion.csv.
# Saidas em analysis/figures/ (.pdf e .png): sec9_cohort_completion_brazil e sec9_disparity_ratio_by_strata
#   (auxiliares, fora do manuscrito) e sec9_disparity_mechanical (Figura 9).

import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("CENSO_PKL", ROOT / "analysis" / "data" / "computacao_2009_2024.pkl"))
OUT = ROOT / "analysis" / "output"
FIG = ROOT / "analysis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

df = pd.read_pickle(DATA)

# tp_grau_academico (dicionario INEP): 1=Bacharelado, 3=Tecnologico. O filtro CINE 6 nao traz licenciaturas
# em 2010-2024 (so 2 ingressantes em 2009), que ficam fora, como as linhas sem grau.
GRAU_K = {1: 4, 3: 2}
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
    for k in (2, 4):
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

print("\n== Recortes (k=2 tecnologo e k=4 bacharelado), ultimos 3 anos de coorte ==")
ult = cohort[cohort["ano_conclusao"] >= cohort["ano_conclusao"].max() - 2]
print(ult.pivot_table(index=["recorte", "ano_conclusao"], columns="grau_k",
                      values=["taxa_preta", "taxa_negra", "taxa_branca"]).round(1).to_string())

# --- figuras ---
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CORES_G = {"preta": "#222222", "negra": "#B07AA1", "branca": "#4C78A8"}

# Fig 1: evolucao das taxas por grupo, painel por k (Brasil, empilhados)
fig, axes = plt.subplots(2, 1, figsize=(2.4, 2.9), sharex=True, sharey=True)
for ax, k, tit in zip(axes, (2, 4), ("(a) Lagged ratio: technologist, k=2", "Lagged ratio: bachelor, k=4")):
    sub = br[(br["grau_k"] == k) & (br["ano_conclusao"] >= 2017)]
    for gname, rot in (("preta", "preta"), ("negra", "negro (preta+parda)"), ("branca", "White")):
        ax.plot(sub["ano_conclusao"], sub[f"taxa_{gname}"], marker="o", ms=2, lw=1.1,
                color=CORES_G[gname], label=rot)
    ax.set_title(tit, fontsize=7, loc="left", pad=2)
    ax.set_ylabel("Ratio (%)", fontsize=6.5)
    ax.tick_params(labelsize=6)
    ax.grid(alpha=0.3)
axes[1].set_xlabel("Graduation year", fontsize=6.5)
axes[1].legend(fontsize=5.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.3), frameon=False, handlelength=1, columnspacing=0.8)
fig.tight_layout()
fig.savefig(FIG / "sec9_cohort_completion_brazil.pdf")
fig.savefig(FIG / "sec9_cohort_completion_brazil.png", dpi=200)
plt.close(fig)

# Fig 2: razao de disparidade negra/branca por recorte (k=2 e k=4 empilhados)
fig, axes = plt.subplots(2, 1, figsize=(2.4, 2.9), sharex=True, sharey=True)
for ax, k, tit in zip(axes, (2, 4), ("(b) Disparity: technologist, k=2", "Disparity: bachelor, k=4")):
    for rec, cor in (("Publica", "#2E7D32"), ("Privada", "#C62828"),
                     ("Presencial", "#1565C0"), ("EaD", "#EF6C00")):
        sub = cohort[(cohort["recorte"] == rec) & (cohort["grau_k"] == k) & (cohort["ano_conclusao"] >= 2017)]
        rot = {"Publica": "Public", "Privada": "Private",
               "Presencial": "On-site", "EaD": "Distance"}[rec]
        ax.plot(sub["ano_conclusao"], sub["disp_negra_vs_branca"], marker="o", ms=2,
                lw=1.1, label=rot)
    ax.axhline(1.0, ls=":", color="gray", lw=1)
    ax.set_title(tit, fontsize=7, loc="left", pad=2)
    ax.set_ylim(0.5, 1.15)
    ax.set_ylabel("negro / White", fontsize=6.5)
    ax.tick_params(labelsize=6)
    ax.grid(alpha=0.3)
axes[1].set_xlabel("Graduation year", fontsize=6.5)
axes[1].legend(fontsize=5.5, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.3), frameon=False, handlelength=1, columnspacing=0.6)
fig.tight_layout()
fig.savefig(FIG / "sec9_disparity_ratio_by_strata.pdf")
fig.savefig(FIG / "sec9_disparity_ratio_by_strata.png", dpi=200)
plt.close(fig)

# Fig 3 (Figura 9 do manuscrito): razao negra/branca observada, por setor, contra a serie mecanica de
# run_validacao_trajetoria.py; so e gerada se val_teste_nulo.csv existir
NULO = OUT / "val_teste_nulo.csv"
if NULO.exists():
    nulo = pd.read_csv(NULO)
    fig, axes = plt.subplots(1, 2, figsize=(4.8, 1.8), sharey=True)
    for ax, k, nome_val, tit in zip(axes, (2, 4), ("Technologist", "Bachelor"), ("Technologist, k=2", "Bachelor, k=4")):
        n = nulo[(nulo["recorte"] == "Brazil") & (nulo["grau"] == nome_val) & (nulo["k"] == k)]
        ax.plot(n["ano"], n["nulo_negro_bruto"], ls="--", lw=1.1, color="#777777", label="Mechanical, national")
        for rec, cor, rot, lw in (("Brasil", "#222222", "Brazil, observed", 1.6), ("Publica", "#1565C0", "Public, observed", 1.1), ("Privada", "#EF6C00", "Private, observed", 1.1)):
            sub = cohort[(cohort["recorte"] == rec) & (cohort["grau_k"] == k) & (cohort["ano_conclusao"] >= 2017)]
            ax.plot(sub["ano_conclusao"], sub["disp_negra_vs_branca"], marker="o", ms=2.2, lw=lw, color=cor, label=rot)
        ax.axhline(1.0, ls=":", color="gray", lw=0.8)
        ax.set_title(tit, fontsize=7, loc="left", pad=2)
        ax.set_ylim(0.6, 1.1)
        ax.tick_params(labelsize=6)
        ax.grid(alpha=0.3)
        ax.set_xlabel("Graduation year", fontsize=6.5)
    axes[0].set_ylabel("negro / White", fontsize=6.5)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=5.8, ncol=4, loc="lower center", frameon=False, handlelength=1.8, columnspacing=1.0)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(FIG / "sec9_disparity_mechanical.pdf")
    fig.savefig(FIG / "sec9_disparity_mechanical.png", dpi=200)
    plt.close(fig)

print(f"\nArquivos em: {OUT} e {FIG}")
