# Secoes 7 (RQ5) e 8 (RQ6) do manuscrito estendido:
#  - Secao 7: espectro racial completo + efeito da nao-declaracao de cor
#  - Secao 8: regressao de tendencia (MQO) + horizonte de paridade
# Janela de analise principal: 2010-2024 (compativel com a versao da conferencia, DATA 2026);
# 2009 aparece nas tabelas da Secao 7 para referencia.
#
# Sustenta no manuscrito:
#  - Figura 6: (a) composicao racial dos matriculados e (b) cor nao declarada por etapa;
#  - Tabela 6 (tres indicadores entre ingressantes) e os numeros de nao-declaracao do texto da Secao 7;
#  - Tabela 7: beta, R2, p, participacao em 2024 e gap em 2040 (linhas "Brasil" de sec8_trend_parity.csv).
#    O ano de paridade com IC de Fieller e o DW da Tabela 7, e as janelas da Tabela 8, vem de rob_parity_windows.csv
#    (run_robustez.py); a coluna parity_year daqui arredonda para cima e pode ficar um ano acima do texto;
#  - Figura 7 (horizonte de paridade dos ingressantes).
# As linhas regionais de sec8_trend_parity.csv usam o benchmark nacional; a Tabela 9 (benchmark de cada regiao)
# vem de rob_regional.csv (run_robustez.py) e a Figura 8 de run_figuras_extras.py.
#
# Uso: python analysis/run_sections_7_8.py   (sem argumentos)
# Entrada: pkl de build_dataset.py, lido de CENSO_PKL (padrao analysis/data/computacao_2009_2024.pkl).
# Saidas em analysis/output/: sec7_indicadores_ingressantes.csv, sec7_composicao_racial_matriculados.csv,
#   sec7_taxa_nao_declarada.csv e sec8_trend_parity.csv.
# Saidas em analysis/figures/ (.pdf e .png): sec7_racial_composition_2010_2024, sec7_undeclared_rate,
#   sec7_three_indicators_entrants (auxiliar, fora do manuscrito) e sec8_parity_horizon_entrants.
# No terminal, imprime tambem a comparacao com os numeros citados na versao da conferencia (RQ1 e RQ2).

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

REGIOES = {1: "Norte", 2: "Nordeste", 3: "Sudeste", 4: "Sul", 5: "Centro-Oeste", 0: "Nao informado"}
RACAS = ["branca", "preta", "parda", "amarela", "indigena", "cornd"]
SERIES = {"ing": "Entrants", "mat": "Enrolled", "conc": "Graduates"}
META_PRETA = 10.2     # % pretos, Censo IBGE 2022: 20.656.458 / 203.080.756 = 10,17% (totais em run_robustez.py)
META_NEGRA = 55.5     # % pretos+pardos, Censo IBGE 2022: (20.656.458 + 92.083.286) / 203.080.756 = 55,51%
HORIZONTE = 2040

df = pd.read_pickle(DATA)

def agrega(d, base):
    cols = {f"qt_{base}_{r}": r for r in RACAS}
    g = d.groupby("ano_arquivo")[[f"qt_{base}", *cols.keys()]].sum()
    g = g.rename(columns={f"qt_{base}": "total", **cols})
    return g

# ============================================================
# COMPARACAO com os numeros citados na versao da conferencia (RQ1 e RQ2), apenas no terminal.
# A reconstrucao da serie publicada da RQ1 (Secao 6) fica em run_recomposicao.py.
# ============================================================
mat = agrega(df, "mat")
ing = agrega(df, "ing")
conc = agrega(df, "conc")

print("== COMPARACAO com a versao da conferencia ==")
print("RQ1 (share preta / total dos matriculados): versao da conferencia cita 10,8% (2010), ~15,2% (2013), ~11% (2024)")
for y in (2010, 2013, 2024):
    print(f"  {y}: {100*mat.loc[y,'preta']/mat.loc[y,'total']:.1f}%  (total={int(mat.loc[y,'total']):,})")
print("RQ2 (share preta entre ingressantes): versao da conferencia cita ~1,8% (2010) -> >7% (2024)")
for y in (2010, 2024):
    print(f"  {y}: {100*ing.loc[y,'preta']/ing.loc[y,'total']:.2f}%")
print("RQ2 absolutos ingressantes pretos: versao da conferencia cita <3.000 (2010) -> >30.000 (2023)")
print(f"  2010: {int(ing.loc[2010,'preta']):,} | 2023: {int(ing.loc[2023,'preta']):,}")
print(f"RQ2 absolutos concluintes pretos: versao da conferencia cita <500 (2010) -> ~6.000 (2023)")
print(f"  2010: {int(conc.loc[2010,'preta']):,} | 2023: {int(conc.loc[2023,'preta']):,}")

# ============================================================
# SECAO 7 - espectro racial completo + nao-declaracao
# ============================================================
def indicadores(g):
    out = pd.DataFrame(index=g.index)
    out["declared_total"] = g["total"] - g["cornd"]
    out["share_preta_bruto"] = 100 * g["preta"] / g["total"]
    out["share_preta_declarado"] = 100 * g["preta"] / out["declared_total"]
    out["share_negra_declarado"] = 100 * (g["preta"] + g["parda"]) / out["declared_total"]
    out["taxa_nao_declarada"] = 100 * g["cornd"] / g["total"]
    for r in RACAS:
        out[f"pct_{r}"] = 100 * g[r] / g["total"]
    return out

inds = {b: indicadores(agrega(df, b)) for b in SERIES}

# tabela comparativa dos 3 indicadores (ingressantes)
tab = inds["ing"][["share_preta_bruto", "share_preta_declarado",
                   "share_negra_declarado", "taxa_nao_declarada"]].round(2)
tab.to_csv(OUT / "sec7_indicadores_ingressantes.csv")
print("\n== SECAO 7: indicadores (ingressantes) ==")
print(tab.to_string())

# composicao racial (matriculados) para area empilhada
comp = inds["mat"][[f"pct_{r}" for r in RACAS]].round(3)
comp.to_csv(OUT / "sec7_composicao_racial_matriculados.csv")

inds["mat"][["taxa_nao_declarada"]].round(2).to_csv(OUT / "sec7_taxa_nao_declarada.csv")
print("\nTaxa de nao-declaracao (matriculados), min/max:")
tnd = inds["mat"]["taxa_nao_declarada"]
print(f"  min {tnd.min():.2f}% ({tnd.idxmin()}) | max {tnd.max():.2f}% ({tnd.idxmax()})")

# ---- figuras Secao 7 ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CORES = {"branca": "#4C78A8", "preta": "#222222", "parda": "#B07AA1",
         "amarela": "#F2CF5B", "indigena": "#E45756", "cornd": "#BAB0AC"}
ROTULOS = {"branca": "White (branca)", "preta": "preta", "parda": "parda",
           "amarela": "Asian (amarela)", "indigena": "Indigenous", "cornd": "Undeclared"}
WIN = slice(2010, 2024)

fig, ax = plt.subplots(figsize=(2.4, 2.1))
w = comp.loc[WIN]
ax.stackplot(w.index, [w[f"pct_{r}"] for r in RACAS],
             labels=[ROTULOS[r] for r in RACAS], colors=[CORES[r] for r in RACAS])
ax.set_xlim(2010, 2024); ax.set_ylim(0, 100)
ax.set_title("(a) Composition", fontsize=7, loc="left", pad=2)
ax.set_xticks(range(2010, 2025, 4))
ax.set_xlabel("Census year", fontsize=6.5); ax.set_ylabel("Share of enrolled (%)", fontsize=6.5)
ax.tick_params(labelsize=6)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), fontsize=5.5, ncol=3, frameon=False, handlelength=1, columnspacing=0.8)
fig.tight_layout()
fig.savefig(FIG / "sec7_racial_composition_2010_2024.pdf")
fig.savefig(FIG / "sec7_racial_composition_2010_2024.png", dpi=200)
plt.close(fig)

fig, ax = plt.subplots(figsize=(2.4, 2.1))
for b, nome in SERIES.items():
    s = inds[b]["taxa_nao_declarada"].loc[WIN]
    ax.plot(s.index, s.values, marker="o", ms=2, lw=1.1, label=nome)
ax.set_title("(b) Undeclared color", fontsize=7, loc="left", pad=2)
ax.set_xticks(range(2010, 2025, 4))
ax.set_xlabel("Census year", fontsize=6.5); ax.set_ylabel("Undeclared color (%)", fontsize=6.5)
ax.tick_params(labelsize=6)
ax.legend(fontsize=5.5); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec7_undeclared_rate.pdf")
fig.savefig(FIG / "sec7_undeclared_rate.png", dpi=200)
plt.close(fig)

fig, ax = plt.subplots(figsize=(7.0, 2.8))
s = inds["ing"].loc[WIN]
ax.plot(s.index, s["share_preta_bruto"], marker="o", ms=3.5, label="preta / total (conference indicator)")
ax.plot(s.index, s["share_preta_declarado"], marker="s", ms=3.5, label="preta / declared")
ax.plot(s.index, s["share_negra_declarado"], marker="^", ms=3.5, label="negro (preta + parda) / declared [official]")
ax.set_xlabel("Census year"); ax.set_ylabel("Share among entrants (%)")
ax.legend(fontsize=8); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec7_three_indicators_entrants.pdf")
fig.savefig(FIG / "sec7_three_indicators_entrants.png", dpi=200)
plt.close(fig)

# ============================================================
# SECAO 8 - tendencia + horizonte de paridade
# ============================================================
def serie_regiao(d, base, definicao, regiao=None):
    dd = d if regiao is None else d[d["co_regiao"] == regiao]
    g = dd.groupby("ano_arquivo").agg(
        total=(f"qt_{base}", "sum"), preta=(f"qt_{base}_preta", "sum"),
        parda=(f"qt_{base}_parda", "sum"), cornd=(f"qt_{base}_cornd", "sum"))
    decl = g["total"] - g["cornd"]
    if definicao == "preta":
        return 100 * g["preta"] / decl
    return 100 * (g["preta"] + g["parda"]) / decl

rows = []
for b, nome in SERIES.items():
    for definicao, meta in (("preta", META_PRETA), ("negra", META_NEGRA)):
        for reg in [None, 1, 2, 3, 4, 5]:
            s = serie_regiao(df, b, definicao, reg).loc[WIN].dropna()
            x, y = s.index.values.astype(float), s.values
            r = stats.linregress(x, y)
            if r.slope > 0:
                ano_par = (meta - r.intercept) / r.slope
            else:
                ano_par = np.inf
            valor_2040 = r.slope * HORIZONTE + r.intercept
            rows.append({
                "series": nome, "definition": definicao,
                "region": "Brasil" if reg is None else REGIOES[reg],
                "beta_pp_ano": round(r.slope, 4), "R2": round(r.rvalue**2, 3),
                "p_value": f"{r.pvalue:.2e}", "std_err": round(r.stderr, 4),
                "share_2024": round(y[-1], 2), "benchmark": meta,
                "gap_2024_pp": round(meta - y[-1], 2),
                "parity_year": int(np.ceil(ano_par)) if np.isfinite(ano_par) and ano_par <= HORIZONTE else None,
                "projected_2040": round(valor_2040, 2),
                "residual_gap_2040_pp": round(meta - valor_2040, 2),
                "converges_by_2040": bool(np.isfinite(ano_par) and ano_par <= HORIZONTE),
            })
trend = pd.DataFrame(rows)
trend.to_csv(OUT / "sec8_trend_parity.csv", index=False)
print("\n== SECAO 8: tendencia e paridade (Brasil) ==")
print(trend[trend["region"] == "Brasil"].to_string(index=False))

# figura: Brasil, entrants, duas definicoes, com projecao ate 2040
plt.rcParams.update({'font.size': 7, 'axes.labelsize': 7, 'axes.titlesize': 7, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5, 'legend.fontsize': 6})
fig, ax = plt.subplots(figsize=(4.4, 1.8))
for definicao, meta, cor, rot in (("preta", META_PRETA, "#222222", "preta"),
                                  ("negra", META_NEGRA, "#B07AA1", "negro")):
    s = serie_regiao(df, "ing", definicao).loc[WIN]
    r = stats.linregress(s.index.values.astype(float), s.values)
    xs = np.arange(2010, HORIZONTE + 1)
    ax.plot(s.index, s.values, "o", ms=4, color=cor, label=f"{rot} (observed)")
    ax.plot(xs, r.slope * xs + r.intercept, "--", lw=1.3, color=cor,
            label=f"{rot} trend (R2={r.rvalue**2:.2f})")
    ax.axhline(meta, ls=":", lw=1.1, color=cor)
    ax.annotate(f"benchmark {meta}%", (2035.4, meta), fontsize=6, color=cor,
                va="bottom", ha="right")
ax.set_xlim(2010, HORIZONTE); ax.set_ylim(0, 60)
ax.set_xlabel("Year"); ax.set_ylabel("Share among entrants (%)")
ax.legend(fontsize=6, loc="center right", ncol=2, bbox_to_anchor=(0.99, 0.42)); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(FIG / "sec8_parity_horizon_entrants.pdf")
fig.savefig(FIG / "sec8_parity_horizon_entrants.png", dpi=200)
plt.close(fig)

print(f"\nArquivos em: {OUT} e {FIG}")
