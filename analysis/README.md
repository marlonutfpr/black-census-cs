# Extended-version analysis scripts (Sections 6–10)

Scripts that generate the tables and figures of the extended version of the
paper (racial composition, trend/parity analysis, cohort completion, and
affirmative-action mechanisms) from the INEP Higher Education Census
microdata (2009–2024), restricted to computing programmes (CINE broad area
6).

## Scripts

| Script | Paper section | Outputs (under `analysis/`) |
|---|---|---|
| `build_dataset.py` | — | Builds `data/computacao_2009_2024.pkl` from the raw INEP zips |
| `run_sections_7_8.py` | 7–8 | Racial spectrum + undeclared-rate tables/figures; trend regression and parity-horizon table/figure |
| `run_section_9.py` | 9 | Synthetic-cohort completion rates and disparity ratios (by funding sector and modality) |
| `run_section_10.py` | 10 | Policy-uptake series, quota-intensity groups vs. representation, breakdown by administrative category |
| `run_figuras_extras.py` | 6, 8, Discussion | Regional trends, per-programme shares (2024), modality evolution + cross-check file |

All scripts resolve paths relative to the repository root
(`ROOT = Path(__file__).resolve().parent.parent`) and write only to
`analysis/output/` (CSV/TXT tables) and `analysis/figures/` (PDF/PNG).
These directories, plus `analysis/data/*.pkl`, are git-ignored.

## Regenerating the dataset

1. Download the INEP Higher Education Census microdata zips (2009–2024) and
   place them as `dados/microdados/micro_<year>.zip` at the repository root
   (the `dados/` directory is git-ignored; see `db/ETL.md` for the
   consolidation conventions).
2. Run:

   ```bash
   python analysis/build_dataset.py
   ```

   This filters computing programmes and writes
   `analysis/data/computacao_2009_2024.pkl`, consumed by the other scripts.

`run_figuras_extras.py` additionally needs `analysis/data/mapa_curso_nome.csv`
(versioned here), a `co_curso → no_curso` map extracted from the 2024
microdata.

## Dependencies

Python 3.9+, with `pandas`, `numpy`, `scipy` and `matplotlib`:

```bash
pip install pandas numpy scipy matplotlib
```

## Usage

Run each script from the repository root, in any order after
`build_dataset.py`:

```bash
python analysis/run_sections_7_8.py
python analysis/run_section_9.py
python analysis/run_section_10.py
python analysis/run_figuras_extras.py
```

Each script prints its computed tables to stdout as a sanity check against
the numbers reported in the paper.
