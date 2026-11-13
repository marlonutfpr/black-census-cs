# Valida as razoes defasadas (concluintes(t) / ingressantes(t-k)) contra a conclusao real das turmas, com os
# Indicadores de Fluxo da Educacao Superior do INEP (trajetoria; coortes 2015, 2016 e 2017, acompanhadas ate 2024).
# Os indicadores nao trazem raca: o teste vale para todos os estudantes e para contrastes entre estratos.
# Apoia, no manuscrito, a Secao 6.4 (RQ7): derivacao de k na abertura da secao (identidade de NU_ANO_INTEGRALIZACAO e
# distribuicao do prazo de integralizacao) e o teste contra coortes acompanhadas (Tabela 11, razoes contra as turmas), os
# contrastes entre setores e modalidades (k adotado e k=3 para tecnologo), o teste nulo (serie mecanica), o cenario do
# curso de entrada e o de conclusao atrasada; e os numeros por segmento da Secao 7 (Discussao). A serie mecanica de
# val_teste_nulo.csv e desenhada na Fig. 9 por run_section_9.py, que por isso deve rodar depois deste script.
# Uso: python analysis/run_validacao_trajetoria.py <pasta com indicadores_trajetoria_es_AAAA_2024.zip>
# Entradas:
#  - na pasta do argumento: indicadores_trajetoria_es_2015_2024.zip, indicadores_trajetoria_es_2016_2024.zip e
#    indicadores_trajetoria_es_2017_2024.zip (SHA-256 em analysis/data/checksums_sha256.txt);
#  - pkl de build_dataset.py, na variavel de ambiente CENSO_PKL (padrao analysis/data/computacao_2009_2024.pkl).
# Saidas em analysis/output/: val_nacional.csv, val_tempo_conclusao.csv, val_prazo_integralizacao.csv, val_contrastes.csv,
#  val_estratos.csv, val_efeito_curso.csv, val_contrastes_k_antigo.csv, val_contrastes_agregados.csv, val_segmentos.csv,
#  val_teste_nulo.csv e val_numeros_texto.txt.

import glob
import io
import os
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("CENSO_PKL", ROOT / "analysis" / "data" / "computacao_2009_2024.pkl"))
OUT = ROOT / "analysis" / "output"
OUT.mkdir(parents=True, exist_ok=True)
PASTA = sys.argv[1]
COORTES = (2015, 2016, 2017)
GRAU = {1: "Bachelor", 3: "Technologist"}
# k = prazo - 1, derivado de NU_ANO_INTEGRALIZACAO (identidade conferida abaixo). Adotado depois de ver estes dados,
# em lugar do k=3 anterior para tecnologo; portanto a concordancia em k=2 nao e um teste fora da amostra.
NOMINAL = {"Technologist": 2, "Bachelor": 4}
ANTIGO = {"Technologist": 3, "Bachelor": 4}  # k considerado antes destes dados (k=3 para tecnologo), mantido como sensibilidade
log = []


def nota(txt):
    log.append(str(txt))
    print(txt, flush=True)


censo = pd.read_pickle(DATA).rename(columns={"ano_arquivo": "ano"})
censo = censo[censo.tp_grau_academico.isin(GRAU)].copy()
censo["grau"] = censo.tp_grau_academico.astype(int).map(GRAU)
censo["setor"] = np.where(censo.tp_categoria_administrativa.isin([1, 2, 3]), "Public", "Private")
censo["modal"] = censo.tp_modalidade_ensino.astype("Int64").map({1: "On-site", 2: "Distance"})
for c in ("qt_ing", "qt_conc"):
    censo[c] = censo[c].astype(float)


def le_coorte(c):
    """Le a planilha da coorte c e devolve as linhas das areas 06 ou dos cursos de computacao do censo na entrada."""
    arq = glob.glob(f"{PASTA}/indicadores_trajetoria_es_{c}_2024.zip")[0]
    z = zipfile.ZipFile(arq)
    nome = [n for n in z.namelist() if n.endswith(".xlsx")][0]
    ws = openpyxl.load_workbook(io.BytesIO(z.read(nome)), read_only=True).worksheets[0]
    cursos_c = set(censo.loc[censo.ano == c, "co_curso"].dropna().astype(int))
    cab, linhas, total = None, [], 0
    for row in ws.iter_rows(values_only=True):
        if cab is None:
            if row[0] == "CO_IES":
                cab = [str(x).strip().replace(" ", "") for x in row]
                i_cine, i_curso = cab.index("CO_CINE_AREA_GERAL"), cab.index("CO_CURSO")
            continue
        if row[i_curso] is None:
            continue
        total += 1
        if str(row[i_cine]).zfill(2) == "06" or int(row[i_curso]) in cursos_c:
            linhas.append(row)
    d = pd.DataFrame(linhas, columns=cab)
    for col in ("TP_CATEGORIA_ADMINISTRATIVA", "CO_CURSO", "CO_REGIAO", "TP_GRAU_ACADEMICO", "TP_MODALIDADE_ENSINO", "NU_ANO_INGRESSO", "NU_ANO_REFERENCIA",
                "NU_PRAZO_INTEGRALIZACAO", "NU_ANO_INTEGRALIZACAO", "NU_PRAZO_ACOMPANHAMENTO", "QT_INGRESSANTE", "QT_PERMANENCIA", "QT_CONCLUINTE", "QT_DESISTENCIA", "QT_FALECIDO", "TCA"):
        d[col] = pd.to_numeric(d[col], errors="coerce")
    d["area06"] = d.CO_CINE_AREA_GERAL.astype(str).str.zfill(2) == "06"
    d["no_censo"] = d.CO_CURSO.astype(int).isin(cursos_c)
    nota(f"coorte {c}: {total} linhas no arquivo, {len(d)} de computacao, {d.CO_CURSO.nunique()} cursos; area 06 {int(d.area06.sum())}, no censo {int(d.no_censo.sum())}; anos {int(d.NU_ANO_REFERENCIA.min())}-{int(d.NU_ANO_REFERENCIA.max())}")
    return d


traj = pd.concat([le_coorte(c) for c in COORTES], ignore_index=True)
traj = traj[traj.no_censo & traj.TP_GRAU_ACADEMICO.isin(GRAU)].copy()
traj["grau"] = traj.TP_GRAU_ACADEMICO.astype(int).map(GRAU)
traj["setor"] = np.where(traj.TP_CATEGORIA_ADMINISTRATIVA.isin([1, 2, 3]), "Public", "Private")
traj["modal"] = traj.TP_MODALIDADE_ENSINO.map({1: "On-site", 2: "Distance"})
traj["c"] = traj.NU_ANO_INGRESSO.astype(int)
traj["r"] = traj.NU_ANO_REFERENCIA.astype(int)
censo["regiao"] = censo.co_regiao.astype("Int64")
traj["regiao"] = traj.CO_REGIAO.astype("Int64")
nota(f"coortes presentes: {sorted(traj.c.unique())}")

# Ingressantes de cada curso, uma vez por coorte
ing_curso = traj.drop_duplicates(["c", "CO_CURSO"])


def ing_t(chaves):
    return ing_curso.groupby(["c"] + chaves).QT_INGRESSANTE.sum()


def compara(chaves):
    """Razao defasada do censo e conclusao real da mesma turma, por estrato."""
    linhas = []
    i_t = ing_t(chaves)
    conc_t = traj.groupby(["c", "r"] + chaves).QT_CONCLUINTE.sum()
    ic = censo.groupby(["ano"] + chaves).qt_ing.sum()
    cc = censo.groupby(["ano"] + chaves).qt_conc.sum()
    for idx in i_t.index:
        c, est = idx[0], idx[1:]
        for k in range(0, 7):
            t = c + k
            if t > 2024:
                continue
            ii = (c,) + est
            it = (t,) + est
            if ii not in ic.index or it not in cc.index:
                continue
            ate_k = sum(conc_t.get((c, r) + est, 0.0) for r in range(c, t + 1))
            final = sum(conc_t.get((c, r) + est, 0.0) for r in range(c, 2025))
            h7 = sum(conc_t.get((c, r) + est, 0.0) for r in range(c, c + 8))  # horizonte comum: anos 0 a 7 desde a entrada
            linhas.append({"c": c, **dict(zip(chaves, est)), "k": k, "t": t, "ing_censo": ic[ii], "ing_traj": i_t[idx], "conc_censo_t": cc[it],
                           "conc_turma_em_t": conc_t.get((c, t) + est, 0.0), "razao": 100 * cc[it] / ic[ii], "real_ate_k": 100 * ate_k / i_t[idx],
                           "real_final": 100 * final / i_t[idx], "real_h7": 100 * h7 / i_t[idx], "conc_final": final, "conc_h7": h7})
    return pd.DataFrame(linhas)


nac = compara(["grau"])
nac["erro_vs_final"] = nac.razao - nac.real_final
nac["erro_vs_k"] = nac.razao - nac.real_ate_k
nac["parcela_turma_no_num"] = 100 * nac.conc_turma_em_t / nac.conc_censo_t
nac["ing_traj_sobre_censo"] = 100 * nac.ing_traj / nac.ing_censo
nac.round(2).to_csv(OUT / "val_nacional.csv", index=False)
nota("\n== Nacional, razao x conclusao real ==")
nota(nac[["grau", "c", "k", "t", "razao", "real_ate_k", "real_final", "erro_vs_final", "parcela_turma_no_num", "ing_traj_sobre_censo"]].sort_values(["grau", "c", "k"]).round(1).to_string(index=False))

# Tempo ate a conclusao e prazo oficial
acum = traj.groupby(["grau", "c", "r"]).QT_CONCLUINTE.sum().reset_index()
acum = acum.merge(ing_t(["grau"]).rename("ing").reset_index(), on=["grau", "c"])
acum["anos"] = acum.r - acum.c
acum["tcan"] = 100 * acum.QT_CONCLUINTE / acum.ing
acum["tca"] = acum.groupby(["grau", "c"]).tcan.cumsum()
acum.round(2).to_csv(OUT / "val_tempo_conclusao.csv", index=False)
piv = acum.pivot_table(index=["grau", "anos"], columns="c", values="tca").round(1)
nota("\n== Conclusao acumulada real por anos desde a entrada ==\n" + piv.to_string())
piv2 = acum.pivot_table(index=["grau", "anos"], columns="c", values="tcan").round(1)
nota("\n== Conclusao anual real ==\n" + piv2.to_string())
pz = ing_curso.groupby(["grau", "NU_PRAZO_INTEGRALIZACAO"]).QT_INGRESSANTE.sum().reset_index()
pz["pct"] = 100 * pz.QT_INGRESSANTE / pz.groupby("grau").QT_INGRESSANTE.transform("sum")
pz.round(2).to_csv(OUT / "val_prazo_integralizacao.csv", index=False)
nota("\n== Prazo de integralizacao (prazo minimo mais bonus, nota do INEP de 2017), % dos ingressantes ==\n" + pz[pz.pct >= 0.5].round(1).to_string(index=False))
ident = (traj.NU_ANO_INTEGRALIZACAO == traj.NU_ANO_INGRESSO + traj.NU_PRAZO_INTEGRALIZACAO - 1)
nota(f"NU_ANO_INTEGRALIZACAO = ingresso + prazo - 1 em {int(ident.sum())} de {len(ident)} linhas")
# A nota metodologica do INEP (2017) define o prazo de integralizacao como PMI + bonus e o acompanhamento como 2 x PMI
pa = ing_curso.groupby(["grau", "NU_PRAZO_INTEGRALIZACAO", "NU_PRAZO_ACOMPANHAMENTO"]).QT_INGRESSANTE.sum().reset_index()
pa["pct"] = 100 * pa.QT_INGRESSANTE / pa.groupby("grau").QT_INGRESSANTE.transform("sum")
nota("\n== Prazo de integralizacao x prazo de acompanhamento, % dos ingressantes ==\n" + pa[pa.pct >= 0.5].round(1).to_string(index=False))
# Identidade por curso e coorte: quem sai sem concluir nem falecer so pode estar em QT_DESISTENCIA
ultimo = traj.sort_values("r").groupby(["c", "CO_CURSO"]).agg(ing=("QT_INGRESSANTE", "first"), perm=("QT_PERMANENCIA", "last"), conc=("QT_CONCLUINTE", "sum"), des=("QT_DESISTENCIA", "sum"), fal=("QT_FALECIDO", "sum"))
falhas = int(((ultimo.perm + ultimo.conc + ultimo.des + ultimo.fal) != ultimo.ing).sum())
nota(f"identidade ingressantes = permanencia + conclusao + desistencia + falecimento: {falhas} falhas em {len(ultimo)} paineis curso-coorte")

# Situacao ao fim do acompanhamento
fim = traj[traj.r == 2024].groupby(["grau", "c"]).agg(perm=("QT_PERMANENCIA", "sum"))
des = traj.groupby(["grau", "c"]).agg(des=("QT_DESISTENCIA", "sum"), conc=("QT_CONCLUINTE", "sum"), fal=("QT_FALECIDO", "sum")).join(fim).join(ing_t(["grau"]).rename("ing"))
for col in ("des", "conc", "perm", "fal"):
    des[col + "_pct"] = 100 * des[col] / des.ing
nota("\n== Situacao em 2024 ==\n" + des[["ing", "conc_pct", "des_pct", "perm_pct", "fal_pct"]].round(1).to_string())

# Estratos: niveis e contrastes
res_pares = []
for nome, chave, a, b in (("setor", "setor", "Public", "Private"), ("modalidade", "modal", "Distance", "On-site")):
    e = compara(["grau", chave])
    e = e[e.apply(lambda x: x.k == NOMINAL[x.grau], axis=1)]
    w = e.pivot_table(index=["grau", "c"], columns=chave, values=["razao", "real_ate_k", "real_final"])
    for (g, c), row in w.iterrows():
        res_pares.append({"contraste": f"{a}/{b}", "grau": g, "c": c, "razao_a": row["razao"][a], "razao_b": row["razao"][b], "final_a": row["real_final"][a], "final_b": row["real_final"][b],
                          "ate_k_a": row["real_ate_k"][a], "ate_k_b": row["real_ate_k"][b]})
par = pd.DataFrame(res_pares)
par["contraste_razao"] = par.razao_a / par.razao_b
par["contraste_final"] = par.final_a / par.final_b
par["contraste_ate_k"] = par.ate_k_a / par.ate_k_b
par.round(3).to_csv(OUT / "val_contrastes.csv", index=False)
nota("\n== Contrastes entre estratos, k nominal ==\n" + par[["contraste", "grau", "c", "razao_a", "razao_b", "final_a", "final_b", "contraste_razao", "contraste_final", "contraste_ate_k"]].round(2).to_string(index=False))

erro_nivel = (100 * (pd.concat([par.razao_a, par.razao_b]).values / pd.concat([par.final_a, par.final_b]).values - 1))
erro_contraste = 100 * (par.contraste_razao / par.contraste_final - 1)
nota(f"\nerro relativo mediano do nivel (razao x final): {np.median(np.abs(erro_nivel)):.1f}%; do contraste: {np.median(np.abs(erro_contraste)):.1f}%")
nota(f"sinal do contraste preservado em {int(((par.contraste_razao > 1) == (par.contraste_final > 1)).sum())} de {len(par)}")

# Estratos finos: regiao x setor x modalidade
f = compara(["grau", "setor", "modal", "regiao"])
f = f[f.apply(lambda x: x.k == NOMINAL[x.grau], axis=1)]
f = f[(f.ing_traj >= 300) & (f.ing_censo >= 300)]
f.round(2).to_csv(OUT / "val_estratos.csv", index=False)
for g, s in f.groupby("grau"):
    rp = stats.pearsonr(s.razao, s.real_final)
    rs = stats.spearmanr(s.razao, s.real_final)
    nota(f"{g}: {len(s)} estratos-coorte com >=300 ingressantes; Pearson {rp.statistic:.2f}, Spearman {rs.statistic:.2f}; erro mediano {np.median(s.razao - s.real_final):+.1f} p.p.; erro absoluto mediano {np.median(np.abs(s.razao - s.real_final)):.1f} p.p.; acima de 100%: {int((s.razao > 100).sum())}")

# Curso de entrada (exploratorio, nao e decomposicao: a taxa do curso inclui o resultado dos dois grupos).
# Horizonte comum de 7 anos desde a entrada, como nos contrastes agregados.
linhas_r = []
concs = traj[traj.r <= traj.c + 7].groupby(["c", "CO_CURSO"]).QT_CONCLUINTE.sum()
for c in COORTES:
    d = censo[censo.ano == c].copy()
    d["CO_CURSO"] = d.co_curso.astype(float)
    d["negro"] = d.qt_ing_preta.astype(float) + d.qt_ing_parda.astype(float)
    d["preta"] = d.qt_ing_preta.astype(float)
    d["branco"] = d.qt_ing_branca.astype(float)
    d["nd"] = d.qt_ing_cornd.astype(float)
    g = d.groupby(["grau", "setor", "CO_CURSO"])[["negro", "preta", "branco", "nd", "qt_ing"]].sum().reset_index()
    i_c = ing_curso[ing_curso.c == c].set_index("CO_CURSO").QT_INGRESSANTE
    g["final"] = [concs.get((c, x), np.nan) / i_c.get(x, np.nan) if i_c.get(x, 0) > 0 else np.nan for x in g.CO_CURSO]
    g = g[g.final.notna()]
    for recorte, base in (("Brazil", g), ("Public", g[g.setor == "Public"]), ("Private", g[g.setor == "Private"])):
        for grau, s in base.groupby("grau"):
            e = {col: np.average(s.final, weights=s[col]) * 100 for col in ("negro", "preta", "branco", "nd", "qt_ing")}
            linhas_r.append({"c": c, "recorte": recorte, "grau": grau, "esperada_negro": e["negro"], "esperada_branco": e["branco"], "esperada_nd": e["nd"], "esperada_todos": e["qt_ing"],
                             "razao_esperada": e["negro"] / e["branco"], "razao_esperada_preta": e["preta"] / e["branco"], "cobertura_ing": 100 * s.qt_ing.sum() / d[(d.grau == grau) & ((recorte == "Brazil") | (d.setor == recorte))].qt_ing.sum()})


def disp_obs(s, t, k):
    """Razao de disparidade observada no censo (contagens brutas), negro/branco e preta/branco."""
    i, cc = s[s.ano == t - k], s[s.ano == t]
    branco = cc.qt_conc_branca.sum() / i.qt_ing_branca.sum()
    negro = (cc.qt_conc_preta.sum() + cc.qt_conc_parda.sum()) / (i.qt_ing_preta.sum() + i.qt_ing_parda.sum())
    return negro / branco, (cc.qt_conc_preta.sum() / i.qt_ing_preta.sum()) / branco


for r in linhas_r:
    s = censo[censo.grau == r["grau"]]
    if r["recorte"] != "Brazil":
        s = s[s.setor == r["recorte"]]
    r["razao_defasada"], r["razao_defasada_preta"] = disp_obs(s, r["c"] + NOMINAL[r["grau"]], NOMINAL[r["grau"]])
    r["parte_explicada_pct"] = 100 * (1 - r["razao_esperada"]) / (1 - r["razao_defasada"])
rr = pd.DataFrame(linhas_r)
rr.round(3).to_csv(OUT / "val_efeito_curso.csv", index=False)
nota("\n== Razao negro/branco esperada so pelo curso de entrada x razao defasada observada ==\n" + rr[["recorte", "grau", "c", "razao_esperada", "razao_defasada", "parte_explicada_pct", "razao_esperada_preta", "razao_defasada_preta", "cobertura_ing"]].sort_values(["recorte", "grau", "c"]).round(3).to_string(index=False))

# Qual k aproxima melhor a conclusao final, por grau (so verificacao; k vem do prazo oficial)
nota("\n== Erro da razao contra a conclusao final, por k (media das coortes) ==")
nota(nac.groupby(["grau", "k"]).agg(erro_medio=("erro_vs_final", "mean"), erro_abs=("erro_vs_final", lambda s: s.abs().mean()), parcela_turma=("parcela_turma_no_num", "mean")).round(1).to_string())

# Contrastes com o k anterior, como sensibilidade
linhas_b = []
for nome, chave, a, b in (("setor", "setor", "Public", "Private"), ("modalidade", "modal", "Distance", "On-site")):
    e = compara(["grau", chave])
    e = e[e.apply(lambda x: x.k == ANTIGO[x.grau], axis=1)]
    w = e.pivot_table(index=["grau", "c"], columns=chave, values=["razao", "real_final"])
    for (g, c), row in w.iterrows():
        linhas_b.append({"contraste": f"{a}/{b}", "grau": g, "c": c, "contraste_razao": row["razao"][a] / row["razao"][b], "contraste_final": row["real_final"][a] / row["real_final"][b]})
pb = pd.DataFrame(linhas_b)
pb.round(3).to_csv(OUT / "val_contrastes_k_antigo.csv", index=False)
nota("\n== Contrastes com k=3 (tecnologo) e k=4 (bacharelado), sensibilidade ==\n" + pb.round(2).to_string(index=False))

# Contrastes agregados nas tres coortes, com a conclusao em horizonte comum de 7 anos e ate 2024.
# Os 12 contrastes por coorte nao sao independentes (mais de 90% dos ingressantes estao em cursos comuns as coortes).
linhas_p = []
for nome, chave, a, b in (("setor", "setor", "Public", "Private"), ("modalidade", "modal", "Distance", "On-site")):
    e = compara(["grau", chave])
    e = e[e.apply(lambda x: x.k == NOMINAL[x.grau], axis=1)]
    soma = e.groupby(["grau", chave])[["conc_censo_t", "ing_censo", "conc_final", "conc_h7", "ing_traj"]].sum()
    for g in GRAU.values():
        x, y = soma.loc[(g, a)], soma.loc[(g, b)]
        linhas_p.append({"contraste": f"{a}/{b}", "grau": g, "k": NOMINAL[g], "razao_a": 100 * x.conc_censo_t / x.ing_censo, "razao_b": 100 * y.conc_censo_t / y.ing_censo,
                         "real_h7_a": 100 * x.conc_h7 / x.ing_traj, "real_h7_b": 100 * y.conc_h7 / y.ing_traj, "real_2024_a": 100 * x.conc_final / x.ing_traj, "real_2024_b": 100 * y.conc_final / y.ing_traj})
pp = pd.DataFrame(linhas_p)
pp["contraste_razao"] = pp.razao_a / pp.razao_b
pp["contraste_h7"] = pp.real_h7_a / pp.real_h7_b
pp["contraste_2024"] = pp.real_2024_a / pp.real_2024_b
pp.round(3).to_csv(OUT / "val_contrastes_agregados.csv", index=False)
nota("\n== Contrastes agregados nas tres coortes (k=2 tecnologo, k=4 bacharelado) ==\n" + pp.round(3).to_string(index=False))

# Tamanho dos estratos em que o bacharelado falha
tam = []
for c in COORTES:
    for rot, s in (("Distance", censo[(censo.ano == c) & (censo.grau == "Bachelor") & (censo.modal == "Distance")]), ("Public", censo[(censo.ano == c) & (censo.grau == "Bachelor") & (censo.setor == "Public")])):
        por_ies = s.groupby("co_ies").qt_ing.sum()
        tam.append({"c": c, "estrato": rot, "ing": s.qt_ing.sum(), "cursos": s[s.qt_ing > 0].co_curso.nunique(), "maior_ies_pct": 100 * por_ies.max() / por_ies.sum()})
nota("\n== Estratos do bacharelado ==\n" + pd.DataFrame(tam).round(1).to_string(index=False))

# Conclusao real por segmento (setor x categoria x modalidade), incluindo o segmento privado com fins lucrativos a distancia
traj["segmento"] = np.select([traj.setor == "Public", (traj.TP_CATEGORIA_ADMINISTRATIVA == 4) & (traj.modal == "Distance")], ["Public", "For-profit distance"], default="Other private")
linhas_s = []
for (g, seg, c), s in traj.groupby(["grau", "segmento", "c"]):
    i = s.drop_duplicates("CO_CURSO").QT_INGRESSANTE.sum()
    linhas_s.append({"grau": g, "segmento": seg, "c": c, "ing": i, "cursos": s.CO_CURSO.nunique(), "real_h7": 100 * s[s.r <= c + 7].QT_CONCLUINTE.sum() / i, "real_2024": 100 * s.QT_CONCLUINTE.sum() / i, "perm_2024": 100 * s[s.r == 2024].QT_PERMANENCIA.sum() / i})
seg = pd.DataFrame(linhas_s)
seg.round(2).to_csv(OUT / "val_segmentos.csv", index=False)
nota("\n== Conclusao real por segmento ==\n" + seg.round(1).to_string(index=False))
linhas_m = []
for (g, m, c), s in traj.groupby(["grau", "modal", "c"]):
    i = s.drop_duplicates("CO_CURSO").QT_INGRESSANTE.sum()
    linhas_m.append({"grau": g, "modal": m, "c": c, "ing": i, "real_h7": 100 * s[s.r <= c + 7].QT_CONCLUINTE.sum() / i, "real_2024": 100 * s.QT_CONCLUINTE.sum() / i, "perm_2024": 100 * s[s.r == 2024].QT_PERMANENCIA.sum() / i})
nota("\n== Conclusao real por modalidade ==\n" + pd.DataFrame(linhas_m).round(1).to_string(index=False))

# Teste nulo: se negros e brancos tivessem a mesma curva real de conclusao, que razao de disparidade a medida mostraria?
# Curva p_j: conclusao anual real pelos anos desde a entrada, media das coortes. Entradas: contagens brutas, a mesma base
# da razao observada; a variante por parcela entre declarados fica como sensibilidade.
curva = acum.groupby(["grau", "anos"]).tcan.mean() / 100
linhas_n = []
for rec, sub in (("Brazil", censo), ("Public", censo[censo.setor == "Public"]), ("Private", censo[censo.setor == "Private"])):
    for grau, s in sub.groupby("grau"):
        g = s.groupby("ano")[["qt_ing", "qt_ing_preta", "qt_ing_parda", "qt_ing_branca", "qt_ing_cornd"]].sum().astype(float)
        dec = g.qt_ing - g.qt_ing_cornd
        brutas = {"negro": g.qt_ing_preta + g.qt_ing_parda, "preta": g.qt_ing_preta, "branco": g.qt_ing_branca}
        parcelas = {nm: g.qt_ing * v / dec for nm, v in brutas.items()}
        p = curva.loc[grau]
        for k in {NOMINAL[grau], ANTIGO[grau]}:
            for t in range(2017, 2025):
                lin = {"recorte": rec, "grau": grau, "k": k, "ano": t}
                for base, ent in (("bruto", brutas), ("declarado", parcelas)):
                    nulo = {gr: sum(e.get(t - j, np.nan) * pj for j, pj in p.items() if t - j >= 2009) / e[t - k] for gr, e in ent.items()}
                    lin[f"nulo_negro_{base}"] = nulo["negro"] / nulo["branco"]
                    lin[f"nulo_preta_{base}"] = nulo["preta"] / nulo["branco"]
                # Mesma conclusao final, mas uma fracao f dos concluintes negros forma um ano depois
                for f in (0.1, 0.2, 0.3):
                    pf = {j: (1 - f) * p.get(j, 0.0) + f * p.get(j - 1, 0.0) for j in list(p.index) + [int(p.index.max()) + 1]}
                    e = brutas["negro"]
                    num = sum(e.get(t - j, np.nan) * pj for j, pj in pf.items() if t - j >= 2009)
                    lin[f"atraso_{int(f * 100)}"] = (num / e[t - k]) / (sum(brutas["branco"].get(t - j, np.nan) * pj for j, pj in p.items() if t - j >= 2009) / brutas["branco"][t - k])
                lin["obs_negro"], lin["obs_preta"] = disp_obs(s, t, k)
                linhas_n.append(lin)
nulo = pd.DataFrame(linhas_n)
nulo.round(3).to_csv(OUT / "val_teste_nulo.csv", index=False)
nota("\n== Teste nulo: razao de disparidade com a mesma curva de conclusao para os grupos, contra a observada ==")
nota(nulo.groupby(["recorte", "grau", "k"]).agg(nulo_min=("nulo_negro_bruto", "min"), nulo_max=("nulo_negro_bruto", "max"), obs_min=("obs_negro", "min"), obs_max=("obs_negro", "max"), decl_min=("nulo_negro_declarado", "min"), decl_max=("nulo_negro_declarado", "max"),
                                                        preta_nulo_min=("nulo_preta_bruto", "min"), preta_nulo_max=("nulo_preta_bruto", "max"), preta_obs_min=("obs_preta", "min"), preta_obs_max=("obs_preta", "max")).round(3).to_string())
nulo["folga"] = nulo.nulo_negro_bruto - nulo.obs_negro
nulo["folga_preta"] = nulo.nulo_preta_bruto - nulo.obs_preta
nac_n = nulo[(nulo.recorte == "Brazil") & nulo.apply(lambda x: x.k == NOMINAL[x.grau], axis=1)]
nota("\nSerie nacional, k adotado:\n" + nac_n[["grau", "k", "ano", "nulo_negro_bruto", "obs_negro", "folga", "nulo_preta_bruto", "obs_preta", "folga_preta", "atraso_10", "atraso_20", "atraso_30"]].round(3).to_string(index=False))
nota(f"menor folga negro (nulo - observado): {nac_n.folga.min():.3f}; preta: {nac_n.folga_preta.min():.3f}")
for f in ("atraso_10", "atraso_20", "atraso_30"):
    q = nac_n.nulo_negro_bruto - nac_n[f]
    nota(f"{f}: queda em relacao ao nulo, min {q.min():.3f}, media {q.mean():.3f}, max {q.max():.3f}")
d1 = nac_n.groupby("grau").apply(lambda s: np.corrcoef(s.obs_negro.diff().dropna(), s.nulo_negro_bruto.diff().dropna())[0, 1], include_groups=False)
nota(f"correlacao das diferencas anuais, observado x nulo: {d1.round(2).to_dict()}")

(OUT / "val_numeros_texto.txt").write_text("\n".join(log), encoding="utf-8")
print("ok")
