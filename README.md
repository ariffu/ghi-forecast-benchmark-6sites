# GHI Forecast Benchmark — 6 Sites (hourly-ahead)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22929571.svg)](https://doi.org/10.5281/zenodo.22929571)

Analysis code and derived per-site results supporting the manuscript:

> **Hourly-ahead global horizontal irradiance forecasting in the humid tropics: satellite cloud dominance and model convergence.**
> Ariffudin, A. Sopaheluwakan, A. Sudarmaji, S. A. Pawiro (under review).

Six BMKG climatological stations in Indonesia, named by province: Banten, Bengkulu, Jambi, Yogyakarta, West Kalimantan and Central Java · 2022–2025 · 10-min grid · hourly-ahead (t + 1 h) GHI.

This is a benchmark of machine-learning and deep-learning architectures under one controlled, anti-leakage protocol. It does not claim a universally best model: the central result is that model families converge on a common ceiling, that satellite cloud information dominates, and that surface meteorology is redundant.

**No observational data are distributed here** (see *Data availability*).

## Study design (summary)

| Aspect | Setting |
|---|---|
| **Target** | `y_h1` (instantaneous GHI at t + 1 h) and `y_mean` (hourly mean over t + 10…60 min). **Headline = `y_mean`**. The two targets are reported side by side and never compared directly, because averaging reduces target variance and mechanically raises R². |
| **Split** | Chronological: train 2022–2023 · validation 2024 · test 2025 |
| **Leaked columns excluded** | `ghi_actual_h1..h6`, `smart_persist*`, `ghi_origin`, `has_source_row` |
| **Evaluation mask** | **Protocol A** (origin solar elevation > 5°, headline). **B** (target also in daylight) and **C** (measured slots only) are sensitivity checks. |
| **Predictors** | 104 canonical predictors in five tiers: T1 core radiation/geometry/history (55), T2 Himawari-8/9 cloud properties CLP (10), T3 SYNOP (14), T4 surface meteorology AWS (21), T5 experimental accelerations (4). Aerosol predictors excluded. |
| **Architectures (8)** | LightGBM, CatBoost, XGBoost, MLP, LSTM, Transformer, LSTM-hybrid, Transformer-hybrid, replicated at all six sites |
| **Metrics** | R², MAE, RMSE, skill vs smart persistence (`kt_now × clear_sky(t + Δ)`), skill vs a climatology–persistence-optimal reference (Yang et al. 2020); paired bootstrap CIs |
| **Probabilistic** | Quantile LightGBM + residual-per-hour Gaussian (PICP, PINAW, CRPS, PIT), then split-conformal calibration with a dedicated 2024 calibration set |
| **SYNOP alignment test** | SYNOP contribution re-estimated with an as-of alignment (latest report carried forward ≤ 50 min, no look-ahead) |

## Repository layout

```
README.md  LICENSE  CITATION.cff  .zenodo.json  environment.yml  .gitignore  .gitattributes
scripts/   one script per stage (table below) + _common.py (shared helpers)
results/   derived CSVs, one folder per stage
figures/   manuscript figures: Fig1 (map), Fig2_workflow, Fig03–Fig10, FigS01–FigS04 (PNG + PDF; EPS as Fig1–Fig10, FigS1–FigS4)
data/      empty; place bengkulu_full.parquet here if you have it (not distributed)
```

### Stage → script → results

| Stage | Script(s) | Results |
|---|---|---|
| 0 — extraction & sanity | `00_extract_bengkulu.py` | — |
| 1 — baseline (point + hourly mean) | `01_baseline_v3.py`, `01b_timeseries_mean.py` | `01_baseline/` |
| 1b — walk-forward stability | `01b_walkforward_mean.py` | `01_baseline/bengkulu_walkforward_mean.csv` |
| 2 — feature ranking & selection | `02_feature_ranking_v2.py`, `02b_feature_ranking_mean.py` | `02_feature_ranking_mean/` |
| 3 — source ablation + bootstrap | `03_ablation_mean.py` | `03_ablation_mean/` |
| 4 — 8-architecture head-to-head (Bengkulu) | `04_arch_mean.py` | `04_arch_mean/` |
| 4b — 8 architectures × 6 sites | `04b_arch_6situs.py`, `04b_seq_6situs_mean.py`, `04b_merge_mean.py` | `04b_arch_6situs_mean/`, `04b_arch_6situs/` (point target), `04c_mean_6situs/` |
| 6 — sky / season / hour stratification | `06_strat_mean.py`, `06_strat_mean_plot.py` | `06_strat_mean/` |
| 7/8 — six-site replication + ablation | `07_replication.py`, `07b_replication_ablation_mean.py` | `07_replication/` |
| 9 — evaluation-protocol sensitivity | `09_sens_mean.py` | `09_sensitivity_mean/` |
| 11 — probabilistic diagnostics | `11_probabilistic_mean.py`, `17_si_prob_cache_bengkulu.py` | `11_probabilistic_mean/` |
| 12b — split-conformal calibration | `12b_conformal_split_mean.py` | `12b_conformal_split_mean/` |
| 13 — skill vs CP-optimal reference | `13_reference_skill.py`, `13b_reference_skill_6situs.py` | `13_reference_skill_6situs/` |
| 18 — SYNOP as-of alignment test | `18_synop_asof_test_bengkulu.py`, `18b_synop_asof_6situs.py` | `18_synop_asof/6situs/synop_asof_6situs.csv` |
| Figures | `make_fig2_workflow.py` (Fig. 2), `16_final_figs_release_en.py` (Fig. 3–10, Fig. S1–S4) | `figures/` |
| 10 — multi-horizon (**not part of the paper**) | `10_multihorizon.py` | — |

Earlier per-stage plotting scripts (`S3_target_effect.py`, `06_strat_mean_plot.py`) are kept for provenance; the manuscript figures are produced by `16_final_figs_release_en.py`. Fig. 1 (station map) is included as a finished figure only.

### Manuscript item → results

| Manuscript item | Source in `results/` |
|---|---|
| Table 3, Fig. 3 (baseline, Bengkulu) | `01_baseline/`, `04_arch_mean/` |
| Fig. 4 (importance and selection) | `02_feature_ranking_mean/` |
| Table 4, Fig. 5 (source ablation, Bengkulu) | `03_ablation_mean/` |
| Table 5, Fig. 6 (architectures, Bengkulu) | `04_arch_mean/` |
| Fig. 7 (stratification) | `06_strat_mean/` |
| Tables 6–7, Fig. 8 (six-site architectures) | `04b_arch_6situs_mean/`, `04b_arch_6situs/`, `04c_mean_6situs/` |
| Table 8, Fig. 9 (six-site replication and ablation) | `07_replication/`, `04c_mean_6situs/` |
| Table 9, Fig. S2, Table S5 (skill vs references) | `13_reference_skill_6situs/` |
| Table 10, Fig. 10 (conformal calibration) | `12b_conformal_split_mean/` |
| Table S2 (SYNOP alignment) | `18_synop_asof/6situs/` |
| Table S3, Fig. S1 (evaluation protocols) | `09_sensitivity_mean/` |
| Table S6, Fig. S3 (probabilistic diagnostics) | `11_probabilistic_mean/` |
| Table S7, Fig. S4 (target effect) | `04b_arch_6situs/`, `04b_arch_6situs_mean/` |

## Running

```bash
conda env create -f environment.yml
conda activate ghi-benchmark-6sites
python scripts/00_extract_bengkulu.py      # then the remaining stages in numerical order
python scripts/make_fig2_workflow.py figures
python scripts/16_final_figs_release_en.py
```

All paths resolve relative to the repository root (`results/`, `figures/`, `data/`); nothing needs editing.

**Data prerequisite.** No observational data are distributed, so the pipeline cannot be re-run from this repository alone:

- with `data/bengkulu_full.parquet` (available on request), the Bengkulu stages run;
- with the environment variable `GHI_DB` pointing to the analytical DuckDB database (`std.*` schema), all six sites run. The database is opened with `read_only=True`, and the scripts stop with an error if `GHI_DB` is unset or wrong instead of silently creating an empty database.

**Prediction archives.** Some scripts (`01b_timeseries_mean.py`, `13_reference_skill.py`, `13b_reference_skill_6situs.py`, `16_final_figs_release_en.py`, `17_si_prob_cache_bengkulu.py`, `18*`) read or write saved prediction archives (`*.npz`, `*.npy`) that are not shipped; they can be regenerated with the earlier stage scripts. The derived CSVs and figures are included.

## Data availability

- **BMKG station data** (harmonised) are available from the corresponding author on reasonable request; raw observations are not redistributed here.
- **Himawari-8/9 cloud products** (JAXA L2 CLP) are available through the JAXA P-Tree system: https://www.eorc.jaxa.jp/ptree/
- **This repository** holds the analysis code and derived per-site results, archived on Zenodo under the concept DOI **10.5281/zenodo.22929571** (always resolves to the latest version).

## Citation

See `CITATION.cff`. A citation for the journal article will be added once it is published.

## License

Code and derived results: CC BY 4.0 (see `LICENSE`).
