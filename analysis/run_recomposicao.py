# Numeros, tabelas e figuras para a recomposicao da Secao 6 (RQ1-RQ4) com a base atual, mais duas sensibilidades
# citadas nas Secoes 8 e 10 do manuscrito.
#  - Secao 6: Tabela 4 (composicao por cor em cada etapa); Tabela 5 (linhas das regioes e parte das linhas de setor e
#    modalidade); Fig. 4 ((a) serie da RQ1 lida da Fig. 4 da versao da conferencia x reconstrucao com a contagem tratada
#    como indicador 0/1 x parcela preta nas bases declarada e total; (b) absolutos de ingressantes e concluintes pretos);
#    Fig. 5 (concentracao por curso, 2010-2024 acumulado); numeros do texto de RQ1-RQ4.
#  - Secao 8: ano de paridade sob ajuste logit-linear (sensibilidade ao ajuste linear).
#  - Secao 10: Fig. 11 (parcela negra entre declarados por modalidade e por categoria administrativa).
# Uso: python analysis/run_recomposicao.py   (sem argumentos)
# Entradas:
#  - pkl de build_dataset.py, na variavel de ambiente CENSO_PKL (padrao analysis/data/computacao_2009_2024.pkl);
#  - analysis/data/rq1_valores_lidos_fig4.csv: valores lidos do grafico publicado (Fig. 4 da versao da conferencia);
#  - analysis/output/rob_cursos_acumulado.csv (de run_robustez.py), analysis/output/sec10_modality_share_negra.csv
#    (de run_figuras_extras.py) e analysis/output/sec10_share_negra_categoria_adm.csv (de run_section_10.py), que
#    precisam ser gerados antes deste script.
# Saidas:
#  - analysis/output/rec_rq1_reconstrucao.csv, rec_composicao.csv, rec_regioes.csv e rec_numeros_texto.txt;
#  - analysis/figures/sec6_rq1_absolutos.pdf/.png, sec6_concentracao_cursos.pdf/.png e sec10_modalidade_categoria.pdf/.png.

import os
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size': 7, 'axes.labelsize': 7, 'axes.titlesize': 7, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5, 'legend.fontsize': 6})

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("CENSO_PKL", ROOT / "analysis" / "data" / "computacao_2009_2024.pkl"))
OUT = ROOT / "analysis" / "output"
FIG = ROOT / "analysis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
REG = {1: "North", 2: "Northeast", 3: "Southeast", 4: "South", 5: "Central-West"}

df = pd.read_pickle(DATA)
df = df.rename(columns={"ano_arquivo": "ano"})
log = []


def nota(txt):
    log.append(str(txt))
    print(txt)


def shares(g, base="qt_ing"):
    decl = g[base] - g[f"{base}_cornd"]
    return pd.DataFrame({"preta_total": 100 * g[f"{base}_preta"] / g[base], "preta_decl": 100 * g[f"{base}_preta"] / decl,
                         "negro_decl": 100 * (g[f"{base}_preta"] + g[f"{base}_parda"]) / decl})


cols = [f"{b}{s}" for b in ("qt_ing", "qt_conc", "qt_mat") for s in ("", "_preta", "_parda", "_branca", "_cornd")]
nac = df.groupby("ano")[cols].sum()

# RQ1: reconstrucao com a contagem tratada como indicador 0/1
linhas = []
for ano, g in df.groupby("ano"):
    t = g.qt_ing.sum()
    um, zero = g.loc[g.qt_ing_preta == 1, "qt_ing"].sum(), g.loc[g.qt_ing_preta == 0, "qt_ing"].sum()
    linhas.append({"ano": ano, "reconstruido": 100 * um / t, "black": um, "others": zero, "total": t,
                   "fora_dos_grupos": 100 * (1 - (um + zero) / t), "qt_ing_preta": g.qt_ing_preta.sum()})
rq1 = pd.DataFrame(linhas).set_index("ano")
lido = pd.read_csv(ROOT / "analysis" / "data" / "rq1_valores_lidos_fig4.csv", index_col=0)
rq1["lido_fig4"] = lido["pct"]
rq1["preta_total"] = 100 * nac.qt_ing_preta / nac.qt_ing
rq1["preta_decl"] = shares(nac)["preta_decl"]
rq1.round(3).to_csv(OUT / "rec_rq1_reconstrucao.csv")
d = (rq1.reconstruido - rq1.lido_fig4).loc[2009:2023]
nota(f"RQ1, reconstrucao x valores lidos: diferenca media absoluta 2009-2023 {d.abs().mean():.3f} p.p.; maximo {d.abs().max():.3f}; correlacao {rq1.reconstruido.loc[2009:2023].corr(rq1.lido_fig4.loc[2009:2023]):.4f}")
nota(f"fora dos grupos 2010-2023: {rq1.fora_dos_grupos.loc[2010:2023].min():.1f}-{rq1.fora_dos_grupos.loc[2010:2023].max():.1f}")

# RQ2: series relativas e absolutas
for base, nome in (("qt_ing", "ingressantes"), ("qt_conc", "concluintes"), ("qt_mat", "matriculados")):
    s = shares(nac, base).round(2)
    nota(f"{nome}: " + "; ".join(f"{a}: {s.loc[a, 'preta_total']}/{s.loc[a, 'preta_decl']}/{s.loc[a, 'negro_decl']}" for a in (2010, 2013, 2014, 2018, 2020, 2024)))
nota(f"pretos: ingressantes 2010 {nac.qt_ing_preta[2010]}, 2020 {nac.qt_ing_preta[2020]}, 2024 {nac.qt_ing_preta[2024]}; concluintes 2010 {nac.qt_conc_preta[2010]}, 2020 {nac.qt_conc_preta[2020]}, 2024 {nac.qt_conc_preta[2024]}; matriculados 2010 {nac.qt_mat_preta[2010]}, 2024 {nac.qt_mat_preta[2024]}")
nota(f"crescimento ingressantes pretos 2019-2022: {nac.qt_ing_preta[2022] / nac.qt_ing_preta[2019]:.2f}x; total {nac.qt_ing[2022] / nac.qt_ing[2019]:.2f}x")

# RQ1: composicao por cor em cada etapa, sobre o total (a distribuicao por curso esta em run_robustez.py)
linhas_comp = []
for base, nome in (("qt_ing", "Entrants"), ("qt_mat", "Enrolled"), ("qt_conc", "Graduates")):
    g = df.groupby("ano")[[base] + [f"{base}_{s}" for s in ("branca", "preta", "parda", "amarela", "indigena", "cornd")]].sum()
    for ano in (2010, 2014, 2019, 2024):
        linhas_comp.append({"etapa": nome, "ano": ano, **{s: round(100 * g.loc[ano, f"{base}_{s}"] / g.loc[ano, base], 1) for s in ("branca", "preta", "parda", "amarela", "indigena", "cornd")}})
comp = pd.DataFrame(linhas_comp)
comp.to_csv(OUT / "rec_composicao.csv", index=False)
nota("composicao (% do total):\n" + comp.to_string(index=False))

# RQ3: regioes
r = df[df.ano.between(2010, 2024)].groupby(["ano", "co_regiao"])[cols].sum()
s = shares(r).unstack("co_regiao")
rows = []
for cod, nome in REG.items():
    a = s["preta_total"][cod]
    b = s["preta_decl"][cod]
    n = s["negro_decl"][cod]
    rows.append({"regiao": nome, "preta_total_2010": a[2010], "preta_total_2016": a[2016], "preta_total_2024": a[2024], "preta_total_max": a.max(), "ano_max": a.idxmax(),
                 "preta_decl_2010": b[2010], "preta_decl_2024": b[2024], "negro_decl_2010": n[2010], "negro_decl_2024": n[2024]})
rr = pd.DataFrame(rows).round(2)
rr.to_csv(OUT / "rec_regioes.csv", index=False)
nota("regioes:\n" + rr.to_string(index=False))

# RQ4: modalidade e setor, base total e declarada
m = shares(df.groupby(["ano", "tp_modalidade_ensino"])[cols].sum()).unstack("tp_modalidade_ensino")
nota("modalidade 1=presencial 2=EaD, preta_total: " + "; ".join(f"{a}: {m['preta_total'][1][a]:.2f}/{m['preta_total'][2][a]:.2f}" for a in (2010, 2014, 2018, 2022, 2024)))
nota("modalidade preta_decl: " + "; ".join(f"{a}: {m['preta_decl'][1][a]:.2f}/{m['preta_decl'][2][a]:.2f}" for a in (2010, 2014, 2018, 2022, 2024)))
anos_ead = [a for a in range(2010, 2025) if m["preta_total"][2][a] > m["preta_total"][1][a]]
nota(f"EaD acima do presencial em preta_total: {anos_ead}")
anos_ead_d = [a for a in range(2010, 2025) if m["preta_decl"][2][a] > m["preta_decl"][1][a]]
nota(f"EaD acima do presencial em preta_decl: {anos_ead_d}")
pub = df.assign(pub=df.tp_categoria_administrativa.isin([1, 2, 3]))
p = shares(pub.groupby(["ano", "pub"])[cols].sum()).unstack("pub")
nota("publico/privado preta_total: " + "; ".join(f"{a}: {p['preta_total'][True][a]:.2f}/{p['preta_total'][False][a]:.2f}" for a in (2010, 2014, 2018, 2024)))
anos_pub = [a for a in range(2010, 2025) if p["preta_total"][True][a] > p["preta_total"][False][a]]
nota(f"publico acima em preta_total: {anos_pub}")
und = 100 * pub.groupby(["ano", "pub"]).qt_ing_cornd.sum() / pub.groupby(["ano", "pub"]).qt_ing.sum()
nota(f"nao declarado publico/privado 2010 e 2024: {und[2010][True]:.1f}/{und[2010][False]:.1f}; {und[2024][True]:.1f}/{und[2024][False]:.1f}")

a10 = pub[(pub.ano == 2010) & pub["pub"]]
nota(f"reserva de vagas no setor publico em 2010: {int(a10.qt_ing_reserva_vaga.sum())} de {a10.qt_ing.sum()} ({100 * a10.qt_ing_reserva_vaga.sum() / a10.qt_ing.sum():.1f}%)")
d10 = shares(pub.groupby(["ano", "pub"])[cols].sum())["negro_decl"].unstack("pub")
nota("negro/declarados publico x privado: " + "; ".join(f"{a}: {d10[True][a]:.2f}/{d10[False][a]:.2f}" for a in (2010, 2011, 2012, 2013)))
# Sensibilidade a classificar a categoria 7 (Especial) como publica
alt = df.assign(pub=df.tp_categoria_administrativa.isin([1, 2, 3, 7]))
s7 = shares(alt[alt.ano == 2024].groupby("pub")[cols].sum()).round(2)
nota(f"categoria 7 como publica, 2024 (pub/priv): preta_decl {s7.preta_decl[True]}/{s7.preta_decl[False]}, negro_decl {s7.negro_decl[True]}/{s7.negro_decl[False]}, preta_total {s7.preta_total[True]}/{s7.preta_total[False]}")
c7 = df[(df.ano == 2024) & (df.tp_categoria_administrativa == 7)].qt_ing.sum()
nota(f"categoria 7 em 2024: {c7} ingressantes ({100 * c7 / df[df.ano == 2024].qt_ing.sum():.2f}%)")

# Sensibilidade do ano de paridade a um ajuste logit-linear (base declarada, 2010-2024, por etapa)
from scipy import stats

for base in ("qt_ing", "qt_mat", "qt_conc"):
    dec = nac[base] - nac[f"{base}_cornd"]
    for nome, serie, alvo in (("preta", nac[f"{base}_preta"] / dec, 0.102), ("negro", (nac[f"{base}_preta"] + nac[f"{base}_parda"]) / dec, 0.555)):
        w_ = serie.loc[2010:2024].astype(float)
        x_ = w_.index.values.astype(float)
        lin_ = stats.linregress(x_, w_.values)
        r_ = stats.linregress(x_, np.log(w_.values / (1 - w_.values)))
        nota(f"paridade {base} {nome}: linear {(alvo - lin_.intercept) / lin_.slope:.1f}; logit {(np.log(alvo / (1 - alvo)) - r_.intercept) / r_.slope:.1f}")

# Figura
fig, (a1, a2) = plt.subplots(1, 2, figsize=(4.8, 2.1))
rec = rq1.loc[2009:2024]
a1.plot(rec.index, rec.lido_fig4, "o", ms=4.5, mfc="none", color="#C62828", label="Fig. 4 of the conference paper (read)")
a1.plot(rec.index, rec.reconstruido, "-", lw=1.2, color="#C62828", label="Count treated as 0/1 flag")
a1.plot(rec.index, rec.preta_decl, "s-", ms=2.5, lw=1.1, color="#1565C0", label="preta / declared entrants")
a1.plot(rec.index, rec.preta_total, "^-", ms=2.5, lw=1.1, color="#555555", label="preta / all entrants")
a1.set_ylim(0, 18)
a1.set_xlabel("Census year")
a1.set_ylabel("Share (%)")
a1.set_title("(a) RQ1 series", loc="left", pad=2)
a1.set_xticks(range(2010, 2025, 4))
a1.legend(fontsize=5.5, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False, handlelength=1.4, columnspacing=0.8)
abs_ = nac.loc[2010:2024]
a2.plot(abs_.index, abs_.qt_ing_preta / 1000, "o-", ms=2.5, lw=1.2, color="#222222", label="preta entrants")
a2.plot(abs_.index, abs_.qt_conc_preta / 1000, "s-", ms=2.5, lw=1.2, color="#B07AA1", label="preta graduates")
a2.set_xlabel("Census year")
a2.set_ylabel("Students (thousands)")
a2.set_title("(b) Absolute counts", loc="left", pad=2)
a2.set_xticks(range(2010, 2025, 4))
a2.legend(fontsize=6)
for a in (a1, a2):
    a.tick_params(labelsize=6.5)
    a.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec6_rq1_absolutos.pdf")
fig.savefig(FIG / "sec6_rq1_absolutos.png", dpi=200)
plt.close(fig)

# Concentracao por curso: acumulado 2010-2024, por etapa, preta x branca
cur = pd.read_csv(OUT / "rob_cursos_acumulado.csv", index_col=0)
NOMES = {"ADS": "Analysis and Systems Dev.", "Sistemas de Informacao": "Information Systems", "Ciencia da Computacao": "Computer Science",
         "Gestao de TI": "IT Management", "Redes": "Computer Networks", "Eng. Software": "Software Engineering", "Internet": "Internet Systems",
         "Seguranca": "Information Security", "Jogos": "Digital Games"}
cur = cur.loc[list(NOMES)].iloc[::-1]
fig, ax = plt.subplots(figsize=(4.8, 2.0))
y = np.arange(len(cur))
h = 0.2
for i, (col, rot, cor, alfa) in enumerate((("qt_conc_branca", "White graduates", "#4C78A8", 0.5), ("qt_ing_branca", "White entrants", "#4C78A8", 1.0),
                                           ("qt_conc_preta", "preta graduates", "#222222", 0.5), ("qt_ing_preta", "preta entrants", "#222222", 1.0))):
    ax.barh(y + (i - 1.5) * h, cur[col], height=h, color=cor, alpha=alfa, label=rot)
ax.set_yticks(y, [NOMES[c] for c in cur.index], fontsize=6.5)
ax.set_xlabel("Share of the group's students, 2010–2024 pooled (%)")
hs, ls = ax.get_legend_handles_labels()
ax.legend(hs[::-1], ls[::-1], fontsize=6.5, loc="lower right")
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec6_concentracao_cursos.pdf")
fig.savefig(FIG / "sec6_concentracao_cursos.png", dpi=200)
plt.close(fig)

# Modalidade e categoria administrativa em uma so figura
mod = pd.read_csv(OUT / "sec10_modality_share_negra.csv", index_col=0)
cat = pd.read_csv(OUT / "sec10_share_negra_categoria_adm.csv", index_col=0).loc[2010:2024]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(4.8, 1.85))
a1.plot(mod.index, mod["1"], "o-", ms=2.2, lw=1.1, color="#4C78A8", label="On-site")
a1.plot(mod.index, mod["2"], "o-", ms=2.2, lw=1.1, color="#E45756", label="Distance")
a1.set_title("(a) By modality", loc="left", pad=2)
a1.legend(fontsize=6)
for c_ in cat.columns:
    s_ = cat[c_].dropna()
    if len(s_) >= 8:
        a2.plot(s_.index, s_.values, "o-", ms=1.8, lw=1.0, label=c_)
a2.set_title("(b) By administrative category", loc="left", pad=2)
a2.legend(fontsize=5, ncol=2, loc="upper left", handlelength=1, columnspacing=0.6)
a2.set_ylim(top=a2.get_ylim()[1] * 1.28)
for a in (a1, a2):
    a.set_xticks(range(2010, 2025, 4))
    a.set_xlabel("Census year")
    a.set_ylabel("negro share (%)")
    a.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec10_modalidade_categoria.pdf")
fig.savefig(FIG / "sec10_modalidade_categoria.png", dpi=200)
plt.close(fig)

(OUT / "rec_numeros_texto.txt").write_text("\n".join(log), encoding="utf-8")
