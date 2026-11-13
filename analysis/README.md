# Analysis scripts of the extended version

These scripts produce the census-based tables and figures of the extended
version of the DATA 2026 paper, *From Microdata to Evidence: An Analytical
Data Platform for Auditing Racial Equity in Brazilian Computing Higher
Education*, and most of the numbers quoted in its text: the lessons
from sixteen census editions (Section 5.2) and the results of Section 6: the
answers to RQ1–RQ4 under the declared basis (Section 6.1), the official
definition and undeclared color (Section 6.2), trends and parity horizons
(Section 6.3), lagged completion ratios and their test against INEP's
followed cohorts (Section 6.4) and affirmative-action uptake (Section 6.5),
plus point numbers quoted in the Discussion (Section 7) and Threats to
Validity (Section 8).

The scripts read the raw INEP files directly, aligned by column name. The
database and the dashboard use an earlier consolidation (319,196 course
offerings); the paper's results come from these scripts (331,023 offerings,
2009–2024).

## Data

The INEP files are public but are not redistributed here. Download them and
check them against [`data/checksums_sha256.txt`](data/checksums_sha256.txt).

| Source | Files | Accessed |
|---|---|---|
| [Microdados do Censo da Educação Superior](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior), editions 2009–2024 | rename each zip to `micro_<year>.zip` | 12 October 2026 |
| [Indicadores de Fluxo da Educação Superior](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/indicadores-de-fluxo-da-educacao-superior), trajectory indicators for the 2015, 2016 and 2017 cohorts followed up to 2024 | keep the names `indicadores_trajetoria_es_<cohort>_2024.zip` | 4 November 2026 |

```bash
cd <folder with the zips>
sha256sum -c --ignore-missing <repo>/analysis/data/checksums_sha256.txt
```

Run it in each folder that holds some of the files; all nineteen should end
up reported as `OK`.

The base is frozen at the 2024 edition. INEP occasionally re-releases files;
a re-released file will fail the checksum and may change the numbers.

By default the census zips are read from `dados/microdados/` at the
repository root (git-ignored); any other folder can be passed as an argument.

## Requirements

Python 3.13.2 with the versions pinned in
[`requirements.txt`](requirements.txt):

```bash
pip install -r analysis/requirements.txt
```

numpy 1.26.4 has no binary wheel for Python 3.13, so pip compiles it from
source, which needs a C/C++ compiler. Other recent versions should give the
same numbers, possibly with differences in the last digits; byte-for-byte
equality with the versioned outputs was checked only with the versions above.
The dashboard has its own `requirements.txt` at the repository root.

## Running

Run from the repository root, in this order. Steps 2 to 9 read the
consolidated dataset through the `CENSO_PKL` environment variable (default
`analysis/data/computacao_2009_2024.pkl`), except `run_robustez.py`, which
reads the zips itself.

```bash
python analysis/build_dataset.py [zip_dir] [out_pkl]       # 1. consolidated dataset
python analysis/run_robustez.py [zip_dir]                  # 2. reads the zips directly
python analysis/run_sections_7_8.py                        # 3.
python analysis/run_section_10.py                          # 4.
python analysis/run_figuras_extras.py                      # 5.
python analysis/run_validacao_trajetoria.py <flow_dir>     # 6. folder with the flow-indicator zips
python analysis/run_section_9.py                           # 7. needs output/val_teste_nulo.csv from step 6
python analysis/run_recomposicao.py                        # 8. needs outputs of steps 2, 4 and 5
python analysis/run_complementos.py                        # 9. needs only the dataset; any time after step 1
```

If `build_dataset.py` writes the dataset elsewhere, set `CENSO_PKL` to that
path before steps 3 to 9. On a desktop, steps 1, 2 and 6 take one to two
minutes each and the others a few seconds.

## What each script supports

| Script | Paper | Main outputs (`analysis/output/`) |
|---|---|---|
| `build_dataset.py` | Base of 331,023 offerings (Sections 4–5) | `data/computacao_2009_2024.pkl` (not versioned) |
| `run_robustez.py` | Section 5.2 counts; Table 5 (declared-basis sector cells); Tables 7 (except Gap 2040), 8, 9, 10 and 12 (net columns); point numbers in Sections 4.4, 6.1, 6.2, 6.4, 6.5, 7 and 8 | `rob_*.csv`, `rob_numeros_texto.txt` |
| `run_sections_7_8.py` | Fig. 6, Table 6, Table 7 (Gap 2040), Fig. 7 | `sec7_*.csv`, `sec8_trend_parity.csv` |
| `run_section_10.py` | Fig. 10, Table 12 (gross columns), uptake numbers in Section 6.5 | `sec10_policy_uptake.csv`, `sec10_tercis_quota.csv`, `sec10_share_negra_*.csv` |
| `run_figuras_extras.py` | Fig. 8, modality rows of Table 5, cross-checks | `sec10_modality_*.csv`, `sec6_share_by_course.csv`, `figuras_extras_check.txt` |
| `run_validacao_trajetoria.py` | Lag choice and the test against followed cohorts (Section 6.4), Table 11 and the followed-cohort numbers of Section 7 | `val_*.csv`, `val_numeros_texto.txt` |
| `run_section_9.py` | Fig. 9 and the lagged ratios of Section 6.4 | `sec9_cohort_completion.csv` |
| `run_recomposicao.py` | Tables 4 and 5, Figs. 4, 5 and 11, numbers of Section 6.1 | `rec_*.csv`, `rec_numeros_texto.txt` |
| `run_complementos.py` | Numbers the other scripts do not write: category 7 sensitivity and teaching degrees (Section 4.3), technologist shares by color and the yearly public–private comparison (Section 6.1), log decompositions and representation relative to the 2022 Census (Section 6.2), Kruskal–Wallis by year with tie sensitivity and 2024 entrants by administrative category (Section 6.5), bounds of the representation ratio (Section 7) | `comp_numeros_texto.txt`, `comp_series_anuais.csv` |

The section numbers in script and output names (`run_sections_7_8.py`,
`run_section_9.py`, `run_section_10.py`, `sec6_*` to `sec10_*`) follow an
earlier numbering of the paper; the Paper column gives the current sections.

Each script's header lists its inputs and outputs in detail. The
`*_numeros_texto.txt` files hold the point numbers quoted in the text, as
printed on screen. Table 5 combines `rec_regioes.csv` and
`rec_numeros_texto.txt` (`run_recomposicao.py`), `rob_numeros_texto.txt`
(`run_robustez.py`) and `sec10_modality_share_negra.csv`
(`run_figuras_extras.py`); Table 7 combines `rob_parity_windows.csv` with the
Gap 2040 column of `sec8_trend_parity.csv`.

Some outputs are auxiliary and do not appear in the paper:
`sec10_share_negra_organizacao.csv`, `val_estratos.csv`, `val_contrastes.csv`
and the figures `sec7_three_indicators_entrants`,
`sec9_cohort_completion_brazil`, `sec9_disparity_ratio_by_strata`,
`sec10_share_negra_categoria_adm`, `sec6_share_by_course` and
`sec10_modality_evolution`.

## Versioned files

- `output/*.csv`, `output/*.txt`: the tables behind the numbers in the paper.
  They hold aggregates (by year, region, sector, modality, program or cohort),
  never individual records. With the pinned versions, re-running the scripts
  reproduces them byte for byte, apart from line endings on Windows. Figures (`analysis/figures/`) are not
  versioned; the PDFs embed a creation date, so they differ between runs even
  when the content is identical.
- `data/checksums_sha256.txt`: SHA-256 of the nineteen INEP files above.
- `data/mapa_curso_nome.csv`: map from `co_curso` to the most frequent program
  name in the 2024 microdata, used by `run_figuras_extras.py` to name programs.
- `data/rq1_valores_lidos_fig4.csv`: approximate values read from Fig. 4 of
  the conference paper, used by `run_recomposicao.py` to compare its
  reconstruction with the published series (Section 6.1).

## Notes

- Shares are computed on two bases: over all students (total basis) and over
  students with declared color (declared basis). Section 6.2 of the paper (see
  also Section 2.3) explains why the declared basis is the main one.
- The lag `k` of the completion ratios is 2 years for technologist programs
  and 4 for bachelor programs, set from the completion term recorded in the
  flow-indicator files (`val_prazo_integralizacao.csv`); `k = 3` for
  technologist programs is kept as a sensitivity check
  (`val_contrastes_k_antigo.csv`, `rob_k_sensitivity.csv`).
- The national and regional benchmarks (2022 Demographic Census, IBGE) are
  fixed in the code.
