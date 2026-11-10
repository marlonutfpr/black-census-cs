# Numeros do texto que os outros scripts nao escrevem: peso e marcacao de rede da categoria 7 (Especial) e
# sensibilidade das parcelas a move-la para o publico, grau academico por ano, tecnologos por cor, lider publico x
# privado por ano e decomposicao da vantagem publica de 2010, decomposicao log da alta preta/total, representacao
# relativa ao Censo 2022 e limites sob a nao declaracao, ingressantes de 2024 por categoria administrativa e
# Kruskal-Wallis entre grupos de intensidade de cota com outras formas de tratar empates.
# Sustenta no manuscrito:
#  - Secao 4.3: categoria 7 (peso em 2012-2014, rede marcada no arquivo, variacao das parcelas ao move-la para o
#    publico em 2012-2014 e desde 2015) e ausencia de licenciaturas na area geral CINE 6 em 2010-2024;
#  - Secao 6, RQ2: parcela dos ingressantes pretos e brancos em cursos tecnologos e diferenca por ano;
#  - Secao 6, RQ4: lider publico x privado por ano nas bases total e declarada, com a categoria 7 dos dois lados,
#    e decomposicao da vantagem publica de 2010 (base total) em nao declaracao e composicao, em log (como na
#    Secao 4.4) e nas formas aditivas;
#  - Secao 7: decomposicao log 2010-2024 e 2010-2014, representacao de negros e brancos relativa ao Censo 2022
#    e limites das parcelas de 2024 sob a nao declaracao;
#  - Secao 10: p-valores de Kruskal-Wallis (todos os grupos, so tercis, sem cota x com cota), empates de
#    intensidade nos cortes dos tercis e ingressantes de 2024 por categoria administrativa;
#  - Secao 11: limites da razao de representacao negro/branco de 2024 sob a nao declaracao.
# Mesmas definicoes de run_robustez.py e run_recomposicao.py: publico = categorias 1-3 e privado = as demais
# (inclusive a 7 e as ofertas sem categoria); base total divide por qt_ing, base declarada por qt_ing - qt_ing_cornd;
# negro = preta + parda; benchmarks exatos do Censo 2022 (IBGE) fixos no codigo; grupos de cota como na Tabela 12
# (ofertas com qt_ing > 0 e ao menos um declarado, grupo "0" sem ingressantes via cota e tercis por pd.qcut).
# O desempate aleatorio dos tercis e calculado pela distribuicao exata (enumeracao de todas as atribuicoes
# igualmente provaveis), sem sorteio.
# Uso: python analysis/run_complementos.py   (sem argumentos)
# Entrada: pkl de build_dataset.py, na variavel de ambiente CENSO_PKL (padrao analysis/data/computacao_2009_2024.pkl);
#   nao le nenhum outro arquivo.
# Saidas em analysis/output/: comp_numeros_texto.txt (o mesmo texto impresso na tela) e comp_series_anuais.csv
#   (uma linha por ano, 2010-2024, com as series por tras dos numeros pontuais).

import os
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("CENSO_PKL", ROOT / "analysis" / "data" / "computacao_2009_2024.pkl"))
OUT = ROOT / "analysis" / "output"
OUT.mkdir(parents=True, exist_ok=True)
YEARS = list(range(2009, 2025))
WIN = list(range(2010, 2025))

CAT_ADM = {1: "Public-Federal", 2: "Public-State", 3: "Public-Municipal",
           4: "Private for-profit", 5: "Private non-profit",
           6: "Private (strictly particular)", 7: "Special",
           8: "Private community", 9: "Private confessional"}
CAT_COL = {1: "federal", 2: "estadual", 3: "municipal", 4: "privada_lucrativa", 5: "privada_sem_fins",
           6: "privada_particular", 7: "especial", 8: "privada_comunitaria", 9: "privada_confessional"}
GRAU = {1: "bacharelado", 2: "licenciatura", 3: "tecnologo"}

# Censo 2022, populacao residente: total, branca, preta, parda (mesmos valores de run_robustez.py)
TOT, BRA, PRE, PAR = 203080756, 88252121, 20656458, 92083286
POP_NEGRA, POP_BRANCA = 100 * (PRE + PAR) / TOT, 100 * BRA / TOT

MED = ("preta_total", "preta_decl", "negro_total", "negro_decl")
TAB = ("preta_total", "preta_decl", "negro_decl")  # bases da Tabela tab:groups
CI = ["qt_ing", "qt_ing_preta", "qt_ing_parda", "qt_ing_cornd"]
LAB = np.array(["T1", "T2", "T3"])

df = pd.read_pickle(DATA).rename(columns={"ano_arquivo": "ano"})
w = df[df.ano.isin(WIN)]
S = pd.DataFrame(index=pd.Index(WIN, name="ano"))
log = []


def nota(txt):
    log.append(str(txt))
    print(txt, flush=True)


def fp(p):
    """p-valor com 4 casas, ou em notacao cientifica abaixo de 0.0001."""
    return f"{p:.4f}" if p >= 1e-4 else f"{p:.1e}"


def por_ano(s, fmt=".2f", anos=WIN):
    return "; ".join(f"{a}: {s[a]:{fmt}}" for a in anos)


def shares(g, base="qt_ing"):
    # identica a run_recomposicao.py, mais negro sobre o total
    decl = g[base] - g[f"{base}_cornd"]
    return pd.DataFrame({"preta_total": 100 * g[f"{base}_preta"] / g[base], "preta_decl": 100 * g[f"{base}_preta"] / decl,
                         "negro_total": 100 * (g[f"{base}_preta"] + g[f"{base}_parda"]) / g[base],
                         "negro_decl": 100 * (g[f"{base}_preta"] + g[f"{base}_parda"]) / decl})


def share(g, base, grupo):
    # identica a run_robustez.py
    num = g[f"{base}_preta"] if grupo == "preta" else (
        g[f"{base}_preta"] + g[f"{base}_parda"] if grupo == "negra" else g[f"{base}_branca"])
    return 100 * num / (g[base] - g[f"{base}_cornd"])


def razao(negra, branca):
    """Razao de representacao: (negra / populacao negra) / (branca / populacao branca)."""
    return (negra / POP_NEGRA) / (branca / POP_BRANCA)


def setor(d, publicas):
    return shares(d.assign(pub=d.tp_categoria_administrativa.isin(publicas)).groupby(["ano", "pub"])[CI].sum()).unstack("pub")


def kw_tercis(bruto, lab):
    """Kruskal-Wallis so entre tercis, como kw_ter em run_robustez.py (sem filtro de tamanho)."""
    terc = [bruto[lab == q] for q in LAB if (lab == q).any()]
    return stats.kruskal(*terc).pvalue if len(terc) >= 2 else np.nan


def tam(lab):
    return "/".join(str(int((lab == q).sum())) for q in LAB)


def cortes_exatos(v):
    """Quantis 1/3 e 2/3 com interpolacao linear (como pd.qcut), mas com a posicao (n-1)k/3 exata."""
    s = np.sort(v)
    n = len(s)
    out = []
    for k in (1, 2):
        h = Fraction((n - 1) * k, 3)
        j = h.numerator // h.denominator
        f = float(h - j)
        out.append(s[j] if f == 0 else s[j] + f * (s[j + 1] - s[j]))
    return out


def tercis_blocos(v, cortes, lados):
    """Tercis com cada bloco empatado no corte inteiro de um lado: 'b' (baixo, intervalo fechado a direita) ou
    'c' (cima, fechado a esquerda)."""
    lab = np.full(len(v), "T1", dtype=object)
    for k, (e, lado) in enumerate(zip(cortes, lados), start=1):
        acima = v > e if lado == "b" else v >= e
        lab[acima] = LAB[k]
    return lab


def atribuicoes(idx, rot):
    """Todas as formas distintas de distribuir os rotulos rot (com repeticao) entre as ofertas idx."""
    labs, cont = np.unique(rot, return_counts=True)

    def rec(resto, k):
        if k == len(labs):
            yield []
            return
        for esc in combinations(resto, int(cont[k])):
            sobra = [i for i in resto if i not in esc]
            for r in rec(sobra, k + 1):
                yield [(i, labs[k]) for i in esc] + r

    return list(rec(list(idx), 0))


def desempate_exato(v, br, pub):
    """Tercis de tamanho igual (pd.qcut sobre as posicoes 1..n) com a ordem das ofertas empatadas em iq ao acaso.
    Em vez de sortear, enumera todas as atribuicoes igualmente provaveis dos blocos empatados que cruzam um limite
    de tercil e devolve o p-valor do KW so entre tercis e as ofertas que mudam em relacao ao publicado em cada uma."""
    n = len(v)
    ordem = np.argsort(v, kind="stable")
    vs = v[ordem]
    vaga = np.asarray(pd.qcut(np.arange(1, n + 1, dtype=float), 3, labels=list(LAB)).astype(str))
    base = np.empty(n, dtype=object)
    base[ordem] = vaga
    blocos = []
    for val in np.unique(vs):
        pos = np.flatnonzero(vs == val)
        if len(set(vaga[pos])) > 1:
            blocos.append(atribuicoes(ordem[pos], vaga[pos]))
    ps, mud = [], []
    for combo in product(*blocos):
        lab = base.copy()
        for atrib in combo:
            for i, q in atrib:
                lab[i] = q
        ps.append(kw_tercis(br, lab))
        mud.append(int((lab != pub).sum()))
    return np.array(ps), np.array(mud)


nota(f"base: {len(df)} ofertas de curso, edicoes {df.ano.min()}-{df.ano.max()}; janela 2010-2024")

# ======================================================================================================
# Secao 4.3: categoria 7 (Especial)
# ======================================================================================================
nota("\n== Secao 4.3: categoria 7 (Especial) ==")
tot = w.groupby("ano").qt_ing.sum()
c7 = w[w.tp_categoria_administrativa == 7].groupby("ano").qt_ing.sum().reindex(WIN, fill_value=0)
peso7 = 100 * c7 / tot
S["ing_total"] = tot
S["ing_cat7"] = c7
S["pct_ing_cat7_especial"] = peso7
nota(f"edicoes com ofertas da categoria 7: {sorted(int(a) for a in df.loc[df.tp_categoria_administrativa == 7, 'ano'].unique())}")
nota("ingressantes da categoria 7 (% dos ingressantes do ano): " + "; ".join(f"{a}: {int(c7[a])} ({peso7[a]:.2f}%)" for a in WIN))
nota(f"% dos ingressantes na categoria 7: 2012-2014 {peso7.loc[2012:2014].min():.2f}-{peso7.loc[2012:2014].max():.2f}; "
     f"2015-2024 {peso7.loc[2015:2024].min():.2f}-{peso7.loc[2015:2024].max():.2f}")

# Marcacao de rede (tp_rede) por categoria administrativa, todas as edicoes
rede = df.dropna(subset=["tp_rede"]).groupby("tp_categoria_administrativa").tp_rede.unique()
nota(f"valores de tp_rede por categoria (todas as edicoes): { {int(c): sorted(int(x) for x in v) for c, v in rede.items()} }")
r7 = df[df.tp_categoria_administrativa == 7]
nota(f"categoria 7: {len(r7)} linhas; tp_rede informado em {int(r7.tp_rede.notna().sum())} "
     f"(valores { {int(k): int(n) for k, n in r7.tp_rede.value_counts().items()} }); tp_rede ausente em {int(r7.tp_rede.isna().sum())}")
nota(f"categoria 7, linhas por edicao: { {int(a): int(n) for a, n in r7.groupby('ano').size().items()} }; "
     f"com tp_rede ausente: { {int(a): int(n) for a, n in r7[r7.tp_rede.isna()].groupby('ano').size().items()} }")

# Variacao das parcelas ao mover a categoria 7 do privado para o publico (alternativa menos oficial, em p.p.)
of, al = setor(w, [1, 2, 3]), setor(w, [1, 2, 3, 7])
dif = al - of
for m in MED:
    for lado, chave in (("pub", True), ("priv", False)):
        S[f"{m}_{lado}"] = of[m][chave]
        S[f"{m}_{lado}_c7pub"] = al[m][chave]
        S[f"var_c7pub_{m}_{lado}"] = dif[m][chave]
for m in MED:
    nota(f"variacao ao mover a categoria 7 para o publico, {m} (pub/priv, p.p.): "
         + "; ".join(f"{a}: {dif[m][True][a]:+.2f}/{dif[m][False][a]:+.2f}" for a in WIN))
for m in MED:
    d15, d12 = dif[m].loc[2015:2024].abs(), dif[m].loc[2012:2014].abs()
    nota(f"{m}: max |variacao| 2015-2024 pub {d15[True].max():.2f} ({d15[True].idxmax()}), priv {d15[False].max():.2f} "
         f"({d15[False].idxmax()}); 2012-2014 pub {d12[True].max():.2f} ({d12[True].idxmax()}), priv {d12[False].max():.2f} ({d12[False].idxmax()})")


def maior(anos, medidas, lados):
    return max(((abs(dif[m][l][a]), m, "pub" if l else "priv", a) for m in medidas for l in lados for a in anos), key=lambda x: x[0])


for rot, meds in (("bases da Tabela tab:groups (preta_total, preta_decl, negro_decl)", TAB), ("com negro_total (base fora da tabela)", MED)):
    x15 = maior(range(2015, 2025), meds, (True, False))
    x12 = maior(range(2012, 2015), meds, (True,))
    x12p = maior(range(2012, 2015), meds, (False,))
    nota(f"{rot}: max |variacao| 2015-2024, dois setores {x15[0]:.2f} ({x15[1]}, {x15[2]}, {x15[3]}); "
         f"2012-2014 publico {x12[0]:.2f} ({x12[1]}, {x12[3]}), privado {x12p[0]:.2f} ({x12p[1]}, {x12p[3]})")

# ======================================================================================================
# Secao 4.3: grau academico por ano (licenciaturas e ofertas sem grau informado)
# ======================================================================================================
nota("\n== Secao 4.3: grau academico por edicao (linhas e ingressantes) ==")
gr = df.assign(grau=df.tp_grau_academico.astype("float").map(GRAU).fillna("sem_grau"))
tg = gr.pivot_table(index="ano", columns="grau", values="qt_ing", aggfunc=["size", "sum"], fill_value=0)
tg.columns = [f"{'linhas' if a == 'size' else 'ing'}_{b}" for a, b in tg.columns]
tg = tg.reindex(YEARS, fill_value=0)
for c in ("linhas_licenciatura", "ing_licenciatura", "linhas_sem_grau", "ing_sem_grau"):
    if c not in tg:
        tg[c] = 0
tg = tg[[f"{a}_{b}" for b in ("bacharelado", "licenciatura", "tecnologo", "sem_grau") for a in ("linhas", "ing") if f"{a}_{b}" in tg]]
nota(tg.to_string())
lic = tg.linhas_licenciatura
nota(f"licenciaturas: edicoes com linhas { {int(a): int(n) for a, n in lic[lic > 0].items()} }, "
     f"ingressantes { {int(a): int(n) for a, n in tg.ing_licenciatura[lic > 0].items()} }; linhas em 2010-2024: {int(lic.loc[WIN].sum())}")
sg = tg.loc[WIN, "linhas_sem_grau"]
pct_sg = 100 * tg.loc[WIN, "ing_sem_grau"] / tot
nota(f"sem grau informado: 2009 {int(tg.loc[2009, 'linhas_sem_grau'])} linhas / {int(tg.loc[2009, 'ing_sem_grau'])} ingressantes; "
     f"2010-2024 {int(sg.sum())} linhas / {int(tg.loc[WIN, 'ing_sem_grau'].sum())} ingressantes; todas as edicoes "
     f"{int(tg.linhas_sem_grau.sum())} linhas / {int(tg.ing_sem_grau.sum())} ingressantes")
nota(f"sem grau, linhas por edicao 2010-2024: { {a: int(sg[a]) for a in WIN} }")
nota(f"sem grau, % dos ingressantes: max 2010-2024 {pct_sg.max():.2f} ({pct_sg.idxmax()}); max 2016-2024 {pct_sg.loc[2016:].max():.4f}")
for c in ("linhas_licenciatura", "ing_licenciatura", "linhas_sem_grau", "ing_sem_grau"):
    S[c] = tg.loc[WIN, c]
S["pct_ing_sem_grau"] = pct_sg

# ======================================================================================================
# Secao 6, RQ2: tecnologos por cor
# ======================================================================================================
nota("\n== Secao 6, RQ2: ingressantes de cada grupo em cursos tecnologos (% do grupo no ano) ==")
BG = {"todos": "qt_ing", "preta": "qt_ing_preta", "parda": "qt_ing_parda", "branca": "qt_ing_branca"}
tot_g = df.groupby("ano")[list(BG.values())].sum()
tec_g = df[df.tp_grau_academico == 3].groupby("ano")[list(BG.values())].sum()
inf_g = df[df.tp_grau_academico.notna()].groupby("ano")[list(BG.values())].sum()
tt = pd.DataFrame({k: 100 * tec_g[b] / tot_g[b] for k, b in BG.items()}).loc[WIN]
ti = pd.DataFrame({k: 100 * tec_g[b] / inf_g[b] for k, b in BG.items()}).loc[WIN]
tt["dif_preta_branca"] = tt.preta - tt.branca
tt["dif_preta_branca_grau_informado"] = ti.preta - ti.branca
nota("denominador: todas as ofertas do ano (como run_robustez.py); ultima coluna: so ofertas com grau informado")
nota(tt.round(2).to_string())
dd = tt.dif_preta_branca
nota(f"2024: preta {tt.loc[2024, 'preta']:.2f}, branca {tt.loc[2024, 'branca']:.2f}, parda {tt.loc[2024, 'parda']:.2f}, todos {tt.loc[2024, 'todos']:.2f}")
nota(f"diferenca preta - branca 2020-2024 (p.p.): {por_ano(dd, '.2f', range(2020, 2025))}; faixa {dd.loc[2020:].min():.2f}-{dd.loc[2020:].max():.2f}")
dr = tt.preta.round(1) - tt.branca.round(1)
nota(f"mesma diferenca a partir das parcelas arredondadas a uma casa, 2020-2024: {por_ano(dr, '.1f', range(2020, 2025))}")
pre18 = dd.loc[2010:2017]
nota(f"diferenca 2010-2017: {por_ano(dd, '.2f', range(2010, 2018))}")
nota(f"maior |diferenca| 2010-2017 sem 2014: {pre18.drop(2014).abs().max():.2f} ({pre18.drop(2014).abs().idxmax()}); 2014: {dd[2014]:.2f}; "
     f"2018: {dd[2018]:.2f}; 2019: {dd[2019]:.2f}")
mud_inf = (tt.dif_preta_branca_grau_informado - dd).abs()
nota(f"denominador so com grau informado: maior mudanca da diferenca 2010-2024 {mud_inf.max():.2f} p.p. ({mud_inf.idxmax()}); "
     f"2020-2024 {mud_inf.loc[2020:].max():.2f}; 2013 {tt.loc[2013, 'dif_preta_branca_grau_informado']:.2f}, 2014 {tt.loc[2014, 'dif_preta_branca_grau_informado']:.2f}")
for k in BG:
    S[f"tec_pct_{k}"] = tt[k]
S["tec_dif_preta_branca"] = tt.dif_preta_branca
S["tec_dif_preta_branca_grau_informado"] = tt.dif_preta_branca_grau_informado

# ======================================================================================================
# Secao 6, RQ4: publico x privado por ano
# ======================================================================================================
nota("\n== Secao 6, RQ4: publico x privado por ano (oficial: categoria 7 privada; c7pub: categoria 7 publica) ==")
gs = w.assign(pub=w.tp_categoria_administrativa.isin([1, 2, 3])).groupby(["ano", "pub"])[CI].sum()
und = (100 * gs.qt_ing_cornd / gs.qt_ing).unstack("pub")
S["nao_declarado_pub"] = und[True]
S["nao_declarado_priv"] = und[False]
for m in ("preta_total", "negro_total", "preta_decl", "negro_decl"):
    ref = " (referencia; base fora da Tabela tab:groups)" if m == "negro_total" else ""
    for rot, s in (("oficial", of), ("c7pub", al)):
        nota(f"{m} {rot}{ref} (pub/priv): " + "; ".join(f"{a}: {s[m][True][a]:.2f}/{s[m][False][a]:.2f}" for a in WIN))
        nota(f"  publico acima: {[a for a in WIN if s[m][True][a] > s[m][False][a]]}; privado acima: {[a for a in WIN if s[m][False][a] > s[m][True][a]]}")
lead = of["preta_total"][True][2010] - of["preta_total"][False][2010]
nota(f"vantagem publica em preta_total 2010: {of['preta_total'][True][2010]:.2f} - {of['preta_total'][False][2010]:.2f} = {lead:.2f} p.p. "
     f"(a partir dos valores arredondados a uma casa: {round(of['preta_total'][True][2010], 1) - round(of['preta_total'][False][2010], 1):.1f})")

# Decomposicao da vantagem publica de 2010 na base total: total = cobertura x composicao declarada, com
# cobertura c = 1 - cornd/ing e composicao d = grupo/declarados. Diferenca pub - priv dividida em parte de
# cobertura (nao declaracao) e parte de composicao; tres ordens: Shapley (pesos medios), contrafactual com a
# cobertura do privado aplicada ao publico, e com a cobertura do publico aplicada ao privado.
g10 = gs.loc[2010]
c = 1 - g10.qt_ing_cornd / g10.qt_ing
nota(f"2010: nao declarado pub/priv {100 * (1 - c[True]):.1f}/{100 * (1 - c[False]):.1f} (cobertura {c[True]:.3f}/{c[False]:.3f})")
for grupo, num in (("preta", g10.qt_ing_preta), ("negro", g10.qt_ing_preta + g10.qt_ing_parda)):
    d_ = 100 * num / (g10.qt_ing - g10.qt_ing_cornd)
    t_ = c * d_
    vt = t_[True] - t_[False]
    sh_cob = (c[True] - c[False]) * (d_[True] + d_[False]) / 2
    sh_com = (d_[True] - d_[False]) * (c[True] + c[False]) / 2
    cf1 = (c[True] - c[False]) * d_[True]
    cf2 = (c[True] - c[False]) * d_[False]
    ref = " (referencia)" if grupo == "negro" else ""
    nota(f"{grupo}{ref}: total pub/priv {t_[True]:.2f}/{t_[False]:.2f} (vantagem {vt:.2f} p.p.); declarado pub/priv {d_[True]:.2f}/{d_[False]:.2f}")
    nota(f"  Shapley: nao declaracao {sh_cob:.2f} ({100 * sh_cob / vt:.1f}%), composicao {sh_com:.2f} ({100 * sh_com / vt:.1f}%)")
    nota(f"  contrafactual publico com a cobertura do privado: nao declaracao {cf1:.2f} ({100 * cf1 / vt:.1f}%), composicao {vt - cf1:.2f}")
    nota(f"  contrafactual privado com a cobertura do publico: nao declaracao {cf2:.2f} ({100 * cf2 / vt:.1f}%), composicao {vt - cf2:.2f}")
    # Metodo da Secao 4.4: log(total_pub / total_priv) = log(c_pub / c_priv) + log(d_pub / d_priv)
    lg = np.log(c[True] / c[False]) / np.log(t_[True] / t_[False])
    nota(f"  log (metodo da Secao 4.4, sobre a razao pub/priv): nao declaracao {100 * lg:.1f}%, composicao {100 * (1 - lg):.1f}%")

for rot, s, col in (("oficial", of, "negro_decl_vantagem_privada"), ("c7pub", al, "negro_decl_vantagem_privada_c7pub")):
    v_ = s["negro_decl"][False] - s["negro_decl"][True]
    S[col] = v_
    nota(f"negro_decl, vantagem privada {rot} (priv - pub, p.p.): " + "; ".join(f"{a}: {v_[a]:+.2f}" for a in WIN))
    nota(f"  privado acima: {[a for a in WIN if v_[a] > 0]}; por menos de 1 p.p.: {[a for a in WIN if 0 < v_[a] < 1]}; "
         f"por 1 p.p. ou mais: {[a for a in WIN if v_[a] >= 1]}")

# ======================================================================================================
# Secao 7: decomposicao log e representacao relativa a populacao
# ======================================================================================================
nota("\n== Secao 7: decomposicao log da alta preta/total ==")
CN = [f"qt_ing{s}" for s in ("", "_preta", "_parda", "_branca", "_cornd")]
nac = df.groupby("ano")[CN].sum()
pt = 100 * nac.qt_ing_preta / nac.qt_ing
pdcl = share(nac, "qt_ing", "preta")
# log(preta/total) = log(preta/declarados) + log(declarados/total); a parte atribuida a queda da nao declaracao e
# 1 - log(razao declarada) / log(razao total), como em run_robustez.py
for a, b in ((2010, 2024), (2010, 2014)):
    lt, ld = np.log(pt[b] / pt[a]), np.log(pdcl[b] / pdcl[a])
    lc = np.log((1 - nac.qt_ing_cornd[b] / nac.qt_ing[b]) / (1 - nac.qt_ing_cornd[a] / nac.qt_ing[a]))
    nota(f"{a}-{b}: preta/total {pt[a]:.3f} -> {pt[b]:.3f} ({pt[b] / pt[a]:.3f}x); preta/declarados {pdcl[a]:.3f} -> {pdcl[b]:.3f}; "
         f"parte da nao declaracao {100 * (1 - ld / lt):.1f}% (log cobertura {lc:.4f} / log total {lt:.4f})")
S["nac_preta_total"] = pt
S["nac_preta_decl"] = pdcl
S["nac_nao_declarado"] = 100 * nac.qt_ing_cornd / nac.qt_ing
S["decomp_log_nao_declaracao_desde_2010"] = pd.Series({b: 100 * (1 - np.log(pdcl[b] / pdcl[2010]) / np.log(pt[b] / pt[2010])) for b in WIN if b != 2010})

nota("\n== Secao 7: representacao relativa ao Censo 2022 e limites sob a nao declaracao ==")
neg, bran = share(nac, "qt_ing", "negra"), share(nac, "qt_ing", "branca")
nota(f"benchmarks: negra {POP_NEGRA:.2f}% branca {POP_BRANCA:.2f}%")
nota(f"2024: negra/declarados {neg[2024]:.2f}%, sobre a populacao {neg[2024] / POP_NEGRA:.3f}; branca/declarados {bran[2024]:.2f}%, "
     f"sobre a populacao {bran[2024] / POP_BRANCA:.3f}; razao negra/branca {razao(neg[2024], bran[2024]):.3f}")
S["nac_negro_decl"] = neg
S["nac_branca_decl"] = bran
S["negro_sobre_pop"] = neg / POP_NEGRA
S["branca_sobre_pop"] = bran / POP_BRANCA
S["razao_negro_branco"] = razao(neg, bran)
# Limites: parcelas sobre o total de ingressantes do ano, com os nao declarados atribuidos todos ou nenhum ao grupo
# (mesma construcao de rob_undeclared.csv)
un = nac.qt_ing_cornd
lim = pd.DataFrame({"preta_lim_inf": 100 * nac.qt_ing_preta / nac.qt_ing, "preta_lim_sup": 100 * (nac.qt_ing_preta + un) / nac.qt_ing,
                    "negro_lim_inf": 100 * (nac.qt_ing_preta + nac.qt_ing_parda) / nac.qt_ing,
                    "negro_lim_sup": 100 * (nac.qt_ing_preta + nac.qt_ing_parda + un) / nac.qt_ing,
                    "branca_lim_inf": 100 * nac.qt_ing_branca / nac.qt_ing, "branca_lim_sup": 100 * (nac.qt_ing_branca + un) / nac.qt_ing})
l24 = lim.loc[2024]
nota(f"2024: nao declarados {100 * un[2024] / nac.qt_ing[2024]:.2f}% do total; preta {l24.preta_lim_inf:.2f}-{l24.preta_lim_sup:.2f}%; "
     f"negra {l24.negro_lim_inf:.2f}-{l24.negro_lim_sup:.2f}%; branca {l24.branca_lim_inf:.2f}-{l24.branca_lim_sup:.2f}%")
for c_ in lim.columns:
    S[c_] = lim[c_]

# ======================================================================================================
# Secao 10: Kruskal-Wallis entre grupos de intensidade de cota e empates nos cortes dos tercis
# ======================================================================================================
nota("\n== Secao 10: Kruskal-Wallis por grupos de intensidade de cota e empates nos cortes dos tercis ==")
# Mesma selecao e mesmas variaveis do bloco de cotas de run_robustez.py
d = w[w.qt_ing > 0].copy()
for c_ in ("qt_ing", "qt_ing_cornd", "qt_ing_preta", "qt_ing_parda", "qt_ing_reserva_vaga"):
    d[c_] = pd.to_numeric(d[c_], errors="coerce").astype(float)
d["decl"] = d.qt_ing - d.qt_ing_cornd
d = d[d.decl > 0]
d["neg"] = d.qt_ing_preta + d.qt_ing_parda
d["bruto"] = d.neg / d.decl
d["iq"] = d.qt_ing_reserva_vaga.fillna(0) / d.qt_ing
linhas, medias = [], {}
for ano, g in d.groupby("ano"):
    g = g.copy()
    g["grupo"] = "0"
    pos = g.iq > 0
    if pos.sum() < 30:
        continue
    # Grupos e testes publicados (identicos a run_robustez.py)
    g.loc[pos, "grupo"] = pd.qcut(g.loc[pos, "iq"], 3, labels=list(LAB), duplicates="drop").astype(str)
    grupos_kw = [gg.bruto.values for _, gg in g.groupby("grupo") if len(gg) > 5]
    kw_tod = stats.kruskal(*grupos_kw).pvalue
    terc = [gg.bruto.values for q, gg in g.groupby("grupo") if q != "0"]
    kw_ter = stats.kruskal(*terc).pvalue if len(terc) >= 2 else np.nan
    # Contraste sem cota x com cota (tercis juntos)
    kw_0x = stats.kruskal(g.loc[~pos, "bruto"].values, g.loc[pos, "bruto"].values).pvalue
    com = g[pos]
    v, br, pub = com.iq.values, com.bruto.values, com.grupo.values
    ln = {"ano": ano, "n_cota": len(v), "tam_pub": tam(pub), "kw_todos": kw_tod, "kw_tercis": kw_ter, "kw_0_x_cota": kw_0x,
          "n_distintos": len(np.unique(v)), "n_em_empate": int(pd.Series(v).duplicated(keep=False).sum())}
    # Empates nos cortes com posicao exata
    ce = cortes_exatos(v)
    for k, e in enumerate(ce, start=1):
        ln[f"corte{k}"] = e
        ln[f"empate_corte{k}"] = int((v == e).sum())
    ln["corte_pub_difere"] = bool(any((pub == LAB[0]) != (v <= ce[0])) or any((pub == LAB[2]) != (v > ce[1])))
    # Blocos empatados inteiros de um lado de cada corte: 4 combinacoes (bb = cortes exatos)
    for lados in product("bc", repeat=2):
        lab = tercis_blocos(v, ce, lados)
        nome = "".join(lados)
        ln[f"kw_{nome}"] = kw_tercis(br, lab)
        ln[f"tam_{nome}"] = tam(lab)
        ln[f"mudam_{nome}"] = int((lab != pub).sum())
        if nome == "bb" and ln["corte_pub_difere"]:
            medias[ano] = {"pub": [100 * br[pub == q].mean() for q in LAB], "bb": [100 * br[lab == q].mean() for q in LAB]}
    # Desempates por rank (first depende da ordem das linhas do pkl)
    for m in ("first", "average", "min", "max", "dense"):
        lab = pd.qcut(com.iq.rank(method=m), 3, labels=list(LAB), duplicates="drop").astype(str).values
        ln[f"kw_{m}"] = kw_tercis(br, lab)
        ln[f"tam_{m}"] = tam(lab)
        ln[f"mudam_{m}"] = int((lab != pub).sum())
    # Desempate ao acaso com tercis de tamanho igual: distribuicao exata por enumeracao (atribuicoes igualmente
    # provaveis; quantis da distribuicao discreta, metodo inverted_cdf)
    ps, mud = desempate_exato(v, br, pub)
    ln["desemp_n"] = len(ps)
    ln["desemp_min"] = float(ps.min())
    ln["desemp_p05"] = float(np.quantile(ps, 0.05, method="inverted_cdf"))
    ln["desemp_med"] = float(np.quantile(ps, 0.5, method="inverted_cdf"))
    ln["desemp_p95"] = float(np.quantile(ps, 0.95, method="inverted_cdf"))
    ln["desemp_max"] = float(ps.max())
    ln["desemp_frac_05"] = float((ps < 0.05).mean())
    ln["desemp_mudam_max"] = int(mud.max())
    linhas.append(ln)
t = pd.DataFrame(linhas).set_index("ano")
FP = ["kw_todos", "kw_tercis", "kw_0_x_cota", "kw_bb", "kw_bc", "kw_cb", "kw_cc", "kw_first", "kw_average", "kw_min", "kw_max",
      "kw_dense", "desemp_min", "desemp_p05", "desemp_med", "desemp_p95", "desemp_max"]
fmt = {c_: fp for c_ in FP}

nota("p-valores: KW todos os grupos com mais de 5 ofertas, KW so tercis, KW sem cota x com cota; tamanhos T1/T2/T3 publicados")
nota(t[["n_cota", "tam_pub", "kw_todos", "kw_tercis", "kw_0_x_cota"]].to_string(formatters=fmt))
k12 = t.loc[2012:, "kw_todos"]
nota(f"KW todos < 0.01 em todos os anos desde 2012: {bool((k12 < 0.01).all())}; maior p desde 2012: {fp(k12.max())} ({k12.idxmax()}); "
     f"2010 {fp(t.loc[2010, 'kw_todos'])}, 2011 {fp(t.loc[2011, 'kw_todos'])}")
nota(f"KW so tercis < 0.05 em: {t.index[t.kw_tercis < 0.05].tolist()}; >= 0.05 em: {t.index[t.kw_tercis >= 0.05].tolist()}")
ate18 = [a for a in range(2012, 2019) if a != 2017]
p_ate18 = "; ".join(f"{a}: {fp(t.loc[a, 'kw_tercis'])}" for a in ate18)
nota(f"2012-2018 exceto 2017: KW so tercis >= 0.05 em todos: {bool((t.loc[ate18, 'kw_tercis'] >= 0.05).all())} "
     f"({p_ate18}); KW sem cota x com cota < 0.01 em todos: "
     f"{bool((t.loc[ate18, 'kw_0_x_cota'] < 0.01).all())} (maior {fp(t.loc[ate18, 'kw_0_x_cota'].max())})")

nota("\nempates de iq nos cortes dos tercis (cortes com a posicao (n-1)k/3 exata):")
nota(t[["n_cota", "n_distintos", "n_em_empate", "corte1", "empate_corte1", "corte2", "empate_corte2", "corte_pub_difere"]].round(4).to_string())
e = t.loc[2014]
nota(f"2014: {int(e.n_cota)} ofertas com cota, {int(e.n_distintos)} valores distintos de iq, {int(e.n_em_empate)} ofertas em valores "
     f"repetidos; corte 1 = {e.corte1:.4f} com {int(e.empate_corte1)} ofertas empatadas, corte 2 = {e.corte2:.4f} com "
     f"{int(e.empate_corte2)}; tercis publicados {e.tam_pub}; KW so tercis publicado {e.kw_tercis:.6f}")
nota(f"anos com empates nos cortes (corte 1 + corte 2): "
     + "; ".join(f"{a}: {int(t.loc[a, 'empate_corte1'])}+{int(t.loc[a, 'empate_corte2'])}" for a in t.index if t.loc[a, "empate_corte1"] + t.loc[a, "empate_corte2"] > 0))

nota("\nKW so tercis sob outras formas de tratar empates (bb/bc/cb/cc: bloco empatado de cada corte embaixo ou em cima; "
     "first: tamanhos iguais pela ordem das linhas; desemp: tamanhos iguais com os empatados em ordem ao acaso, "
     "distribuicao exata sobre desemp_n atribuicoes igualmente provaveis)")
nota(t[["kw_tercis", "kw_bb", "kw_bc", "kw_cb", "kw_cc", "kw_first", "desemp_n", "desemp_min", "desemp_p05", "desemp_med", "desemp_p95",
        "desemp_max", "desemp_frac_05"]]
     .to_string(formatters={**fmt, "desemp_frac_05": lambda x: f"{x:.3f}"}))
ident = {m: t.index[t[f"mudam_{m}"] > 0].tolist() for m in ("average", "min", "max", "dense")}
anos_id = sorted(set(sum(ident.values(), [])))
nota(f"rank average/min/max/dense: anos com alguma oferta em tercil diferente do publicado {ident}; "
     f"ofertas que mudam e KW (average x publicado) nesses anos: "
     + "; ".join(f"{a}: mudam {int(t.loc[a, 'mudam_average'])}, KW {fp(t.loc[a, 'kw_average'])} x {fp(t.loc[a, 'kw_tercis'])}" for a in anos_id))
alt = ["kw_bb", "kw_bc", "kw_cb", "kw_cc", "kw_first"]
cruza = {a: [c_ for c_ in alt if (t.loc[a, c_] < 0.05) != (t.loc[a, "kw_tercis"] < 0.05)] for a in t.index}
nota(f"anos em que alguma alternativa muda a leitura a 5%: { {a: c_ for a, c_ in cruza.items() if c_} }")
fr = t.desemp_frac_05
nota(f"anos com desempate ao acaso dividido (fracao com p < 0.05 entre 0 e 1): { {a: round(float(fr[a]), 3) for a in t.index if 0 < fr[a] < 1} }")
sem = [a for a in t.index if all(t.loc[a, c_] == t.loc[a, "kw_tercis"] for c_ in alt) and t.loc[a, "desemp_min"] == t.loc[a, "desemp_max"] == t.loc[a, "kw_tercis"]]
nota(f"anos sem nenhuma mudanca de p-valor em nenhuma alternativa: {sem}")
for a in t.index:
    vals = [t.loc[a, c_] for c_ in alt] + [t.loc[a, "desemp_min"], t.loc[a, "desemp_max"]]
    if a not in sem:
        nota(f"  {a}: publicado {fp(t.loc[a, 'kw_tercis'])}; faixa das alternativas {fp(min(vals))}-{fp(max(vals))}")
nota(f"2014: blocos inteiros {fp(min(t.loc[2014, alt[:4]]))}-{fp(max(t.loc[2014, alt[:4]]))} "
     f"({'; '.join(f'{c_[3:]} {fp(t.loc[2014, c_])}' for c_ in alt[:4])}); first {fp(t.loc[2014, 'kw_first'])} "
     f"(tercis {t.loc[2014, 'tam_first']}, {int(t.loc[2014, 'mudam_first'])} ofertas mudam); ao acaso: {int(t.loc[2014, 'desemp_n'])} "
     f"atribuicoes, mediana {fp(t.loc[2014, 'desemp_med'])}, faixa 5-95% {fp(t.loc[2014, 'desemp_p05'])}-{fp(t.loc[2014, 'desemp_p95'])}, "
     f"faixa completa {fp(t.loc[2014, 'desemp_min'])}-{fp(t.loc[2014, 'desemp_max'])}, p < 0.05 em {100 * t.loc[2014, 'desemp_frac_05']:.1f}% "
     f"({int(round(t.loc[2014, 'desemp_frac_05'] * t.loc[2014, 'desemp_n']))} de {int(t.loc[2014, 'desemp_n'])})")
nota(f"2014, ofertas que mudam de tercil: bb {int(t.loc[2014, 'mudam_bb'])}, bc {int(t.loc[2014, 'mudam_bc'])}, cb {int(t.loc[2014, 'mudam_cb'])}, "
     f"cc {int(t.loc[2014, 'mudam_cc'])}; tamanhos bb {t.loc[2014, 'tam_bb']}, bc {t.loc[2014, 'tam_bc']}, cb {t.loc[2014, 'tam_cb']}, cc {t.loc[2014, 'tam_cc']}")
# pd.qcut calcula a posicao do quantil em ponto flutuante; onde isso poe ofertas empatadas no corte em outro tercil
# que os cortes exatos, compara as medias brutas por tercil (colunas "Gross" da Tabela 12)
nota(f"anos em que pd.qcut e os cortes exatos separam ofertas de forma diferente: { {a: int(t.loc[a, 'mudam_bb']) for a in t.index if t.loc[a, 'corte_pub_difere']} } (ofertas)")
for a, mm in medias.items():
    nota(f"  {a}: media negra bruta T1/T2/T3 pd.qcut {'/'.join(f'{x:.2f}' for x in mm['pub'])}; cortes exatos {'/'.join(f'{x:.2f}' for x in mm['bb'])}")
COLS_KW = {"n_cota": "kw_n_ofertas_cota", "tam_pub": "kw_tercis_tamanhos", "kw_todos": "kw_p_todos_grupos", "kw_tercis": "kw_p_so_tercis",
           "kw_0_x_cota": "kw_p_sem_cota_x_com_cota", "n_distintos": "kw_n_valores_distintos_iq", "n_em_empate": "kw_n_ofertas_em_empate",
           "corte1": "kw_corte1_exato", "empate_corte1": "kw_empates_corte1", "corte2": "kw_corte2_exato", "empate_corte2": "kw_empates_corte2",
           "corte_pub_difere": "kw_qcut_difere_cortes_exatos", "kw_bb": "kw_p_tercis_blocos_bb", "kw_bc": "kw_p_tercis_blocos_bc",
           "kw_cb": "kw_p_tercis_blocos_cb", "kw_cc": "kw_p_tercis_blocos_cc", "mudam_bb": "kw_mudam_blocos_bb", "mudam_bc": "kw_mudam_blocos_bc",
           "mudam_cb": "kw_mudam_blocos_cb", "mudam_cc": "kw_mudam_blocos_cc", "kw_first": "kw_p_tercis_rank_first",
           "mudam_first": "kw_mudam_rank_first", "desemp_n": "kw_desempate_n_atribuicoes", "desemp_min": "kw_p_desempate_min",
           "desemp_p05": "kw_p_desempate_p05", "desemp_med": "kw_p_desempate_mediana", "desemp_p95": "kw_p_desempate_p95",
           "desemp_max": "kw_p_desempate_max", "desemp_frac_05": "kw_desempate_frac_p_menor_005",
           "desemp_mudam_max": "kw_desempate_mudam_max"}
for c_, nome in COLS_KW.items():
    S[nome] = t[c_]

# ======================================================================================================
# Secao 10: ingressantes de 2024 por categoria administrativa
# ======================================================================================================
nota("\n== Secao 10: ingressantes de 2024 por categoria administrativa ==")
d24 = df[df.ano == 2024]
t24 = d24.qt_ing.sum()
cat = d24.groupby("tp_categoria_administrativa", dropna=False).agg(linhas=("qt_ing", "size"), ing=("qt_ing", "sum"))
cat["pct"] = 100 * cat.ing / t24
cat.index = [f"{int(c_)} {CAT_ADM.get(int(c_), '?')}" if pd.notna(c_) else "NA" for c_ in cat.index]
nota(cat.round(2).to_string())
luc, fed = d24[d24.tp_categoria_administrativa == 4].qt_ing.sum(), d24[d24.tp_categoria_administrativa == 1].qt_ing.sum()
pub24 = d24[d24.tp_categoria_administrativa.isin([1, 2, 3])].qt_ing.sum()
nota(f"total 2024: {int(t24)} ({t24 / 1000:.1f} mil)")
nota(f"privada lucrativa (4): {int(luc)} ({luc / 1000:.1f} mil), {100 * luc / t24:.2f}%")
nota(f"federal (1): {int(fed)} ({fed / 1000:.1f} mil), {100 * fed / t24:.2f}%")
nota(f"publicas (1-3): {int(pub24)}, {100 * pub24 / t24:.2f}%")
cy = w.groupby(["ano", "tp_categoria_administrativa"]).qt_ing.sum().unstack(fill_value=0)
for c_ in cy.columns:
    if int(c_) != 7:
        S[f"pct_ing_cat{int(c_)}_{CAT_COL.get(int(c_), 'outra')}"] = 100 * cy[c_] / tot
S["pct_ing_publica_1a3"] = 100 * w[w.tp_categoria_administrativa.isin([1, 2, 3])].groupby("ano").qt_ing.sum() / tot

# ======================================================================================================
# Secao 11: limites da razao negro/branco sob a nao declaracao
# ======================================================================================================
nota("\n== Secao 11: limites da razao de representacao negro/branco, 2024 ==")
casos = {
    "negra sem nao declarados, branca com todos (minimo)": (l24.negro_lim_inf, l24.branca_lim_sup),
    "negra com todos, branca sem nao declarados (maximo)": (l24.negro_lim_sup, l24.branca_lim_inf),
    "nenhum grupo recebe nao declarados (base total)": (l24.negro_lim_inf, l24.branca_lim_inf),
    "declarados (ponto)": (neg[2024], bran[2024]),
}
for rot, (n_, b_) in casos.items():
    nota(f"{rot}: negra {n_:.2f}% branca {b_:.2f}% -> razao {razao(n_, b_):.3f}")
S["razao_negro_branco_min"] = razao(lim.negro_lim_inf, lim.branca_lim_sup)
S["razao_negro_branco_max"] = razao(lim.negro_lim_sup, lim.branca_lim_inf)

S.to_csv(OUT / "comp_series_anuais.csv", float_format="%.6g")
(OUT / "comp_numeros_texto.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
