# GHI Forecast Benchmark — 6 Sites (hourly-ahead)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
<!-- Replace XXXXXXX with the CONCEPT DOI once Zenodo has archived Release v1.0.0 -->

Analysis scripts and derived per-stage results supporting the manuscript:

> **Hourly-ahead global horizontal irradiance forecasting in the humid tropical Maritime Continent: satellite cloud optical properties dominate, surface meteorology is redundant, and model families converge on a predictability limit.**
> Ariffudin, A. Sopaheluwakan, A. Sudarmaji, S. A. Pawiro (under review).

Six BMKG climatological stations in Indonesia (Banten, Bengkulu, Jambi, Yogyakarta, West Kalimantan, Semarang) · 2022–2025 · 10-min grid · hourly-ahead (t + 1 h) GHI.

This is a benchmark of machine-learning and deep-learning architectures under one controlled, anti-leakage protocol. It does not claim a universally best model: the central result is that model families converge on a data-limited predictability ceiling, that satellite cloud information dominates, and that surface meteorology is redundant.

## Study design (summary)

| Aspect | Setting |
|---|---|
| **Target** | `y_h1` (instantaneous GHI at t + 1 h) and `y_mean` (hourly mean over t + 10…60 min). **Headline = `y_mean`**. The two targets are reported side by side and never compared directly, because averaging reduces target variance and mechanically raises R². |
| **Split** | Chronological: train 2022–2023 · validation 2024 · test 2025 |
| **Leaked columns excluded** | `ghi_actual_h1..h6`, `smart_persist*`, `ghi_origin`, `has_source_row` |
| **Evaluation mask** | **Protocol A** (origin solar elevation > 5°, headline). **B** (target also in daylight) and **C** (measured slots only) are sensitivity checks. |
| **Predictors** | 5 tiers (104 canonical): core radiation/geometry (55), Himawari-8/9 cloud optical properties CLP (10), SYNOP cloud (4), surface meteorology AWS (21), experimental (4). AOD excluded (0 % non-null at Bengkulu). |
| **Architectures (8)** | LightGBM, CatBoost, XGBoost, MLP, LSTM, Transformer, LSTM-hybrid, Transformer-hybrid, replicated at all six sites |
| **Metrics** | R², MAE, RMSE, skill vs smart persistence (`kt_now × clear_sky(t + Δ)`), skill vs a climatology–persistence-optimal reference (Yang et al. 2020); paired bootstrap CIs |
| **Probabilistic** | Quantile LightGBM + residual-per-hour Gaussian (PICP, PINAW, CRPS, PIT), then conformalized quantile regression with a dedicated 2024 split-calibration set |

## Repository layout

```
README.md  LICENSE  CITATION.cff  .zenodo.json  environment.yml  .gitignore
scripts/   one script per stage (table below) + _common.py (shared helpers)
results/   derived CSVs, one folder per stage
figures/   Fig1.eps (six-site map) + stage figures (PNG)
data/      empty; place bengkulu_full.parquet here if you have it (not distributed)
```

### Stage → script → results → figure

| Stage | Script(s) | Results | Figure file(s) |
|---|---|---|---|
| 0 — extraction & sanity | `00_extract_bengkulu.py` | — | — |
| 1 — baseline (point + hourly mean) | `01_baseline_v3.py`, `01b_timeseries_mean.py` | `01_baseline/baseline_v3.csv` | `01_scatter_mean.png`, `01_timeseries_mean.png` |
| 1b — walk-forward stability | `01b_walkforward_mean.py` | `01_baseline/bengkulu_walkforward_mean.csv` | — |
| 2 — feature ranking & selection | `02_feature_ranking_v2.py`, `02b_feature_ranking_mean.py` | `02_feature_ranking_mean/` | `02_shap_top15_mean.png`, `02_selection_curve_mean.png` |
| 3 — source ablation + bootstrap | `03_ablation_mean.py` | `03_ablation_mean/` | `03_ablation_delta_mean.png` |
| 4 — 8-architecture head-to-head (Bengkulu) | `04_arch_mean.py` | `04_arch_mean/` | `04_arch_bar_mean.png` |
| 4b — 8 architectures × 6 sites | `04b_arch_6situs.py`, `04b_seq_6situs_mean.py`, `04b_merge_mean.py` | `04b_arch_6situs_mean/`, `04b_arch_6situs/` (point target) | `04b_arch_6situs_bar_mean.png`, `04b_arch_spread_6situs_mean.png` |
| 6 — sky / season / hour stratification | `06_strat_mean.py`, `06_strat_mean_plot.py` | `06_strat_mean/` | `06_r2_by_hour_mean.png`, `06_skill_regime_mean.png` |
| 7/8 — six-site replication + ablation | `07_replication.py`, `07b_replication_ablation_mean.py` | `07_replication/` | `08_replication_baseline.png`, `08_replication_ablation_mean.png` |
| 9 — evaluation-protocol sensitivity | `09_sens_mean.py` | `09_sensitivity_mean/` | `09_variants_6situs.png`, `09_hourly_r2_senja.png` |
| 11 — probabilistic diagnostics | `11_probabilistic_mean.py` | `11_probabilistic_mean/` | `11_interval_fan_mean.png`, `11_picp_by_hour_mean.png`, `11_pit_bengkulu_mean.png` |
| 12b — conformal recalibration (split) | `12b_conformal_split_mean.py` | `12b_conformal_split_mean/` | `12b_picp_conformal_6situs_split_mean.png` |
| 13 — skill vs CP-optimal reference | `13_reference_skill.py`, `13b_reference_skill_6situs.py` | `13_reference_skill_6situs/` | `13b_reference_skill_6situs.png` |
| Target effect (point vs mean) | `S3_target_effect.py` | `04b_arch_6situs/`, `04b_arch_6situs_mean/` | `S3_target_effect_6situs.png` |
| 10 — multi-horizon (**not part of the paper**) | `10_multihorizon.py` | — | — |

## Running

```bash
conda env create -f environment.yml
conda activate ghi-benchmark-6sites
python scripts/00_extract_bengkulu.py      # then the remaining stages in numerical order
```

All paths resolve relative to the repository root (`results/`, `figures/`, `data/`); nothing needs editing.

**Data prerequisite.** No observational data are distributed, so the pipeline cannot be re-run from this repository alone:

- with `data/bengkulu_full.parquet` (available on request), the Bengkulu stages run;
- with the environment variable `GHI_DB` pointing to the analytical DuckDB database (`std.*` schema), all six sites run. The database is opened with `read_only=True`, and `_common.py` raises an error if `GHI_DB` is unset or wrong instead of silently creating an empty database.

**Prediction archives.** `01b_timeseries_mean.py`, `13_reference_skill.py` and `13b_reference_skill_6situs.py` read saved prediction archives (`*.npz`) that are not shipped; they can be regenerated with the earlier stage scripts. Their derived CSVs and figures are included.

## Data availability

- **BMKG station data** are available from the corresponding author on reasonable request; raw observations are not redistributed here.
- **Himawari-8/9 cloud products** (JAXA L2 CLP) are available through the JAXA P-Tree system: https://www.eorc.jaxa.jp/ptree/
- **This repository** holds the analysis scripts and derived per-stage results, archived on Zenodo under the concept DOI **10.5281/zenodo.XXXXXXX** (always resolves to the latest version).

## Citation

See `CITATION.cff`. A citation for the journal article will be added once it is published.

## License

Code and derived results: CC BY 4.0 (see `LICENSE`).
