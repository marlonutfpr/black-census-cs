-- ============================================================================
-- Censo da Educação Superior — Cursos de Computação
-- Modelo relacional (SQLite) derivado de dados_censo_computacao_consolidado.csv
--
-- Estratégia:
--   * Dimensões normalizadas (geografia, classificação CINE, IES, curso) com
--     tabelas de lookup para os códigos tipados (tp_*).
--   * Uma tabela fato única `fato_curso_ano`, com PK composta
--     (nu_ano_censo, co_curso), guardando todas as métricas qt_* e os atributos
--     do curso/IES que variam ano a ano.
--
-- Nota: o enforcement de foreign keys é controlado pelo conector
-- (PRAGMA foreign_keys) no momento da carga, não aqui no DDL.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Tabelas de lookup (códigos tipados do INEP)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ref_tp_dimensao (
    codigo     INTEGER PRIMARY KEY,
    descricao  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_tp_organizacao_academica (
    codigo     INTEGER PRIMARY KEY,
    descricao  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_tp_categoria_administrativa (
    codigo     INTEGER PRIMARY KEY,
    descricao  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_tp_rede (
    codigo     INTEGER PRIMARY KEY,
    descricao  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_tp_grau_academico (
    codigo     INTEGER PRIMARY KEY,
    descricao  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_tp_modalidade_ensino (
    codigo     INTEGER PRIMARY KEY,
    descricao  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ref_tp_nivel_academico (
    codigo     INTEGER PRIMARY KEY,
    descricao  TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. Geografia (hierarquia região > UF > município)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS regiao (
    co_regiao  INTEGER PRIMARY KEY,
    no_regiao  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS uf (
    co_uf      INTEGER PRIMARY KEY,
    sg_uf      TEXT NOT NULL,
    no_uf      TEXT NOT NULL,
    co_regiao  INTEGER NOT NULL REFERENCES regiao(co_regiao)
);

CREATE TABLE IF NOT EXISTS municipio (
    co_municipio  INTEGER PRIMARY KEY,
    no_municipio  TEXT NOT NULL,
    in_capital    INTEGER,
    co_uf         INTEGER NOT NULL REFERENCES uf(co_uf)
);

CREATE INDEX IF NOT EXISTS ix_uf_regiao ON uf(co_regiao);
CREATE INDEX IF NOT EXISTS ix_municipio_uf ON municipio(co_uf);

-- ----------------------------------------------------------------------------
-- 3. Classificação CINE (hierarquia área geral > específica > detalhada > rótulo)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cine_area_geral (
    co_cine_area_geral  INTEGER PRIMARY KEY,
    no_cine_area_geral  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cine_area_especifica (
    co_cine_area_especifica  INTEGER PRIMARY KEY,
    no_cine_area_especifica  TEXT NOT NULL,
    co_cine_area_geral       INTEGER NOT NULL REFERENCES cine_area_geral(co_cine_area_geral)
);

CREATE TABLE IF NOT EXISTS cine_area_detalhada (
    co_cine_area_detalhada   INTEGER PRIMARY KEY,
    no_cine_area_detalhada   TEXT NOT NULL,
    co_cine_area_especifica  INTEGER NOT NULL REFERENCES cine_area_especifica(co_cine_area_especifica)
);

CREATE TABLE IF NOT EXISTS cine_rotulo (
    co_cine_rotulo          TEXT PRIMARY KEY,         -- vem como string (ex.: "0613C01")
    no_cine_rotulo          TEXT NOT NULL,
    co_cine_area_detalhada  INTEGER NOT NULL REFERENCES cine_area_detalhada(co_cine_area_detalhada)
);

CREATE INDEX IF NOT EXISTS ix_cine_area_esp_geral ON cine_area_especifica(co_cine_area_geral);
CREATE INDEX IF NOT EXISTS ix_cine_area_det_esp  ON cine_area_detalhada(co_cine_area_especifica);
CREATE INDEX IF NOT EXISTS ix_cine_rotulo_det    ON cine_rotulo(co_cine_area_detalhada);

-- ----------------------------------------------------------------------------
-- 4. IES (Instituição de Ensino Superior) e curso
--
-- O grão real do CSV consolidado é (nu_ano_censo, co_curso, co_municipio,
-- tp_dimensao). O mesmo co_curso aparece em vários municípios (polos de
-- oferta EaD) e sua classificação CINE / nome / IES variam ano a ano
-- (co_cine_rotulo varia em ~42% dos cursos, no_curso em ~67%). Por isso:
--   * `ies` e `curso` guardam só a identidade (códigos).
--   * Atributos que variam no tempo (CINE, IES no ano, modalidade, grau,
--     município de oferta) ficam no FATO.
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ies (
    co_ies  INTEGER PRIMARY KEY
);

-- `no_curso` aqui é apenas um rótulo representativo (grafia mais frequente)
-- para exibição. O valor autoritativo por ano está no fato.
CREATE TABLE IF NOT EXISTS curso (
    co_curso  INTEGER PRIMARY KEY,
    no_curso  TEXT
);

-- ----------------------------------------------------------------------------
-- 5. Fato — uma linha por (ano, curso, município, dimensão)
--
-- PK surrogate (id); a chave natural lógica é
-- (nu_ano_censo, co_curso, co_municipio, tp_dimensao) — verificada como
-- única no CSV (319.196 linhas, 0 duplicatas). Não é declarada UNIQUE
-- porque co_municipio é nulo em ~4.681 linhas e o SQLite trata NULLs como
-- distintos; o índice abaixo cobre a chave para performance.
--
-- Inclui FKs de dimensão (IES, município, CINE) e os atributos do curso/IES
-- no ano. Métricas qt_* agrupadas por bloco temático nos comentários.
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS fato_curso_ano (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nu_ano_censo  INTEGER NOT NULL,
    co_curso      INTEGER NOT NULL REFERENCES curso(co_curso),
    co_ies        INTEGER REFERENCES ies(co_ies),
    co_municipio  INTEGER REFERENCES municipio(co_municipio),
    co_cine_rotulo  TEXT REFERENCES cine_rotulo(co_cine_rotulo),

    -- Atributos do curso/IES no ano (podem variar entre censos)
    tp_dimensao                   INTEGER REFERENCES ref_tp_dimensao(codigo),
    tp_organizacao_academica      INTEGER REFERENCES ref_tp_organizacao_academica(codigo),
    tp_categoria_administrativa   INTEGER REFERENCES ref_tp_categoria_administrativa(codigo),
    tp_rede                       INTEGER REFERENCES ref_tp_rede(codigo),
    in_comunitaria                INTEGER,
    in_confessional               INTEGER,
    tp_grau_academico             INTEGER REFERENCES ref_tp_grau_academico(codigo),
    in_gratuito                   INTEGER,
    tp_modalidade_ensino          INTEGER REFERENCES ref_tp_modalidade_ensino(codigo),
    tp_nivel_academico            INTEGER REFERENCES ref_tp_nivel_academico(codigo),
    co_cine_rotulo2               TEXT,                   -- coluna derivada presente no consolidado

    -- ---------------- Vagas e inscrições ----------------
    qt_curso                      INTEGER,
    qt_vg_total                   INTEGER,
    qt_vg_total_diurno            INTEGER,
    qt_vg_total_noturno           INTEGER,
    qt_vg_total_ead               INTEGER,
    qt_vg_nova                    INTEGER,
    qt_vg_proc_seletivo           INTEGER,
    qt_vg_remanesc                INTEGER,
    qt_vg_prog_especial           INTEGER,
    qt_inscrito_total             INTEGER,
    qt_inscrito_total_diurno      INTEGER,
    qt_inscrito_total_noturno     INTEGER,
    qt_inscrito_total_ead         INTEGER,
    qt_insc_vg_nova               INTEGER,
    qt_insc_proc_seletivo         INTEGER,
    qt_insc_vg_remanesc           INTEGER,
    qt_insc_vg_prog_especial      INTEGER,

    -- ---------------- Ingressantes ----------------
    qt_ing                        INTEGER,
    qt_ing_fem                    INTEGER,
    qt_ing_masc                   INTEGER,
    qt_ing_diurno                 INTEGER,
    qt_ing_noturno                INTEGER,
    qt_ing_vg_nova                INTEGER,
    qt_ing_vestibular             INTEGER,
    qt_ing_enem                   INTEGER,
    qt_ing_avaliacao_seriada      INTEGER,
    qt_ing_selecao_simplifica     INTEGER,
    qt_ing_egr                    INTEGER,
    qt_ing_outro_tipo_selecao     INTEGER,
    qt_ing_proc_seletivo          INTEGER,
    qt_ing_vg_remanesc            INTEGER,
    qt_ing_vg_prog_especial       INTEGER,
    qt_ing_outra_forma            INTEGER,
    qt_ing_0_17                   INTEGER,
    qt_ing_18_24                  INTEGER,
    qt_ing_25_29                  INTEGER,
    qt_ing_30_34                  INTEGER,
    qt_ing_35_39                  INTEGER,
    qt_ing_40_49                  INTEGER,
    qt_ing_50_59                  INTEGER,
    qt_ing_60_mais                INTEGER,
    qt_ing_branca                 INTEGER,
    qt_ing_preta                  INTEGER,
    qt_ing_parda                  INTEGER,
    qt_ing_amarela                INTEGER,
    qt_ing_indigena               INTEGER,
    qt_ing_cornd                  INTEGER,

    -- ---------------- Matriculados ----------------
    qt_mat                        INTEGER,
    qt_mat_fem                    INTEGER,
    qt_mat_masc                   INTEGER,
    qt_mat_diurno                 INTEGER,
    qt_mat_noturno                INTEGER,
    qt_mat_0_17                   INTEGER,
    qt_mat_18_24                  INTEGER,
    qt_mat_25_29                  INTEGER,
    qt_mat_30_34                  INTEGER,
    qt_mat_35_39                  INTEGER,
    qt_mat_40_49                  INTEGER,
    qt_mat_50_59                  INTEGER,
    qt_mat_60_mais                INTEGER,
    qt_mat_branca                 INTEGER,
    qt_mat_preta                  INTEGER,
    qt_mat_parda                  INTEGER,
    qt_mat_amarela                INTEGER,
    qt_mat_indigena               INTEGER,
    qt_mat_cornd                  INTEGER,

    -- ---------------- Concluintes ----------------
    qt_conc                       INTEGER,
    qt_conc_fem                   INTEGER,
    qt_conc_masc                  INTEGER,
    qt_conc_diurno                INTEGER,
    qt_conc_noturno               INTEGER,
    qt_conc_0_17                  INTEGER,
    qt_conc_18_24                 INTEGER,
    qt_conc_25_29                 INTEGER,
    qt_conc_30_34                 INTEGER,
    qt_conc_35_39                 INTEGER,
    qt_conc_40_49                 INTEGER,
    qt_conc_50_59                 INTEGER,
    qt_conc_60_mais               INTEGER,
    qt_conc_branca                INTEGER,
    qt_conc_preta                 INTEGER,
    qt_conc_parda                 INTEGER,
    qt_conc_amarela               INTEGER,
    qt_conc_indigena              INTEGER,
    qt_conc_cornd                 INTEGER,

    -- ---------------- Nacionalidade ----------------
    qt_ing_nacbras                INTEGER,
    qt_ing_nacestrang             INTEGER,
    qt_mat_nacbras                INTEGER,
    qt_mat_nacestrang             INTEGER,
    qt_conc_nacbras               INTEGER,
    qt_conc_nacestrang            INTEGER,

    -- ---------------- Deficiência ----------------
    qt_aluno_deficiente           INTEGER,
    qt_ing_deficiente             INTEGER,
    qt_mat_deficiente             INTEGER,
    qt_conc_deficiente            INTEGER,

    -- ---------------- Financiamento (Ingressantes) ----------------
    qt_ing_financ                 INTEGER,
    qt_ing_financ_reemb           INTEGER,
    qt_ing_fies                   INTEGER,
    qt_ing_rpfies                 INTEGER,
    qt_ing_financ_reemb_outros    INTEGER,
    qt_ing_financ_nreemb          INTEGER,
    qt_ing_prounii                INTEGER,
    qt_ing_prounip                INTEGER,
    qt_ing_nrpfies                INTEGER,
    qt_ing_financ_nreemb_outros   INTEGER,

    -- ---------------- Financiamento (Matriculados) ----------------
    qt_mat_financ                 INTEGER,
    qt_mat_financ_reemb           INTEGER,
    qt_mat_fies                   INTEGER,
    qt_mat_rpfies                 INTEGER,
    qt_mat_financ_reemb_outros    INTEGER,
    qt_mat_financ_nreemb          INTEGER,
    qt_mat_prounii                INTEGER,
    qt_mat_prounip                INTEGER,
    qt_mat_nrpfies                INTEGER,
    qt_mat_financ_nreemb_outros   INTEGER,

    -- ---------------- Financiamento (Concluintes) ----------------
    qt_conc_financ                INTEGER,
    qt_conc_financ_reemb          INTEGER,
    qt_conc_fies                  INTEGER,
    qt_conc_rpfies                INTEGER,
    qt_conc_financ_reemb_outros   INTEGER,
    qt_conc_financ_nreemb         INTEGER,
    qt_conc_prounii               INTEGER,
    qt_conc_prounip               INTEGER,
    qt_conc_nrpfies               INTEGER,
    qt_conc_financ_nreemb_outros  INTEGER,

    -- ---------------- Reserva de vaga (Ingressantes) ----------------
    qt_ing_reserva_vaga           INTEGER,
    qt_ing_rvredepublica          INTEGER,
    qt_ing_rvetnico               INTEGER,
    qt_ing_rvpdef                 INTEGER,
    qt_ing_rvsocial_rf            INTEGER,
    qt_ing_rvoutros               INTEGER,
    qt_ing_rvppi                  INTEGER,
    qt_ing_rvquilo                INTEGER,
    qt_ing_rvrefu                 INTEGER,
    qt_ing_rvpovt                 INTEGER,
    qt_ing_rvidoso                INTEGER,
    qt_ing_rvintern               INTEGER,
    qt_ing_rvmedal                INTEGER,
    qt_ing_rvtrans                INTEGER,

    -- ---------------- Reserva de vaga (Matriculados) ----------------
    qt_mat_reserva_vaga           INTEGER,
    qt_mat_rvredepublica          INTEGER,
    qt_mat_rvetnico               INTEGER,
    qt_mat_rvpdef                 INTEGER,
    qt_mat_rvsocial_rf            INTEGER,
    qt_mat_rvoutros               INTEGER,
    qt_mat_rvppi                  INTEGER,
    qt_mat_rvquilo                INTEGER,
    qt_mat_rvrefu                 INTEGER,
    qt_mat_rvpovt                 INTEGER,
    qt_mat_rvidoso                INTEGER,
    qt_mat_rvintern               INTEGER,
    qt_mat_rvmedal                INTEGER,
    qt_mat_rvtrans                INTEGER,

    -- ---------------- Reserva de vaga (Concluintes) ----------------
    qt_conc_reserva_vaga          INTEGER,
    qt_conc_rvredepublica         INTEGER,
    qt_conc_rvetnico              INTEGER,
    qt_conc_rvpdef                INTEGER,
    qt_conc_rvsocial_rf           INTEGER,
    qt_conc_rvoutros              INTEGER,
    qt_conc_rvppi                 INTEGER,
    qt_conc_rvquilo               INTEGER,
    qt_conc_rvrefu                INTEGER,
    qt_conc_rvpovt                INTEGER,
    qt_conc_rvidoso               INTEGER,
    qt_conc_rvintern              INTEGER,
    qt_conc_rvmedal               INTEGER,
    qt_conc_rvtrans               INTEGER,

    -- ---------------- Situação ----------------
    qt_sit_trancada               INTEGER,
    qt_sit_desvinculado           INTEGER,
    qt_sit_transferido            INTEGER,
    qt_sit_falecido               INTEGER,

    -- ---------------- Procedência escolar ----------------
    qt_ing_procescpublica         INTEGER,
    qt_ing_procescprivada         INTEGER,
    qt_ing_procnaoinformada       INTEGER,
    qt_mat_procescpublica         INTEGER,
    qt_mat_procescprivada         INTEGER,
    qt_mat_procnaoinformada       INTEGER,
    qt_conc_procescpublica        INTEGER,
    qt_conc_procescprivada        INTEGER,
    qt_conc_procnaoinformada      INTEGER,

    -- ---------------- Programas e mobilidade ----------------
    qt_parfor                     INTEGER,
    qt_ing_parfor                 INTEGER,
    qt_mat_parfor                 INTEGER,
    qt_conc_parfor                INTEGER,
    qt_apoio_social               INTEGER,
    qt_ing_apoio_social           INTEGER,
    qt_mat_apoio_social           INTEGER,
    qt_conc_apoio_social          INTEGER,
    qt_ativ_extracurricular       INTEGER,
    qt_ing_ativ_extracurricular   INTEGER,
    qt_mat_ativ_extracurricular   INTEGER,
    qt_conc_ativ_extracurricular  INTEGER,
    qt_mob_academica              INTEGER,
    qt_ing_mob_academica          INTEGER,
    qt_mat_mob_academica          INTEGER,
    qt_conc_mob_academica         INTEGER
);

CREATE INDEX IF NOT EXISTS ix_fato_chave_natural
    ON fato_curso_ano(nu_ano_censo, co_curso, co_municipio, tp_dimensao);
CREATE INDEX IF NOT EXISTS ix_fato_ano        ON fato_curso_ano(nu_ano_censo);
CREATE INDEX IF NOT EXISTS ix_fato_curso      ON fato_curso_ano(co_curso);
CREATE INDEX IF NOT EXISTS ix_fato_ies        ON fato_curso_ano(co_ies);
CREATE INDEX IF NOT EXISTS ix_fato_municipio  ON fato_curso_ano(co_municipio);
CREATE INDEX IF NOT EXISTS ix_fato_cine       ON fato_curso_ano(co_cine_rotulo);
CREATE INDEX IF NOT EXISTS ix_fato_categoria  ON fato_curso_ano(tp_categoria_administrativa);
CREATE INDEX IF NOT EXISTS ix_fato_rede       ON fato_curso_ano(tp_rede);
CREATE INDEX IF NOT EXISTS ix_fato_modalidade ON fato_curso_ano(tp_modalidade_ensino);

-- ----------------------------------------------------------------------------
-- 6. View achatada (compatibilidade com o dashboard Streamlit)
--
-- Reproduz, em SQL, a forma "wide" do CSV consolidado. Útil para queries
-- exploratórias sem precisar fazer todos os joins manualmente.
-- ----------------------------------------------------------------------------

CREATE VIEW IF NOT EXISTS v_censo_consolidado AS
SELECT
    f.*,
    c.no_curso,
    r.co_regiao,
    r.no_regiao,
    u.co_uf,
    u.sg_uf,
    u.no_uf,
    m.no_municipio,
    m.in_capital,
    cr.no_cine_rotulo,
    cad.co_cine_area_detalhada,
    cad.no_cine_area_detalhada,
    cae.co_cine_area_especifica,
    cae.no_cine_area_especifica,
    cag.co_cine_area_geral,
    cag.no_cine_area_geral
FROM fato_curso_ano f
LEFT JOIN curso         c   ON c.co_curso = f.co_curso
LEFT JOIN cine_rotulo   cr  ON cr.co_cine_rotulo = f.co_cine_rotulo
LEFT JOIN cine_area_detalhada  cad ON cad.co_cine_area_detalhada  = cr.co_cine_area_detalhada
LEFT JOIN cine_area_especifica cae ON cae.co_cine_area_especifica = cad.co_cine_area_especifica
LEFT JOIN cine_area_geral      cag ON cag.co_cine_area_geral      = cae.co_cine_area_geral
LEFT JOIN municipio     m   ON m.co_municipio = f.co_municipio
LEFT JOIN uf            u   ON u.co_uf = m.co_uf
LEFT JOIN regiao        r   ON r.co_regiao = u.co_regiao;
