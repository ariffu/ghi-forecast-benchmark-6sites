# GHI Forecast Benchmark — 6 Sites (hour-ahead)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22929571.svg)](https://doi.org/10.5281/zenodo.22929571)

Analysis code and derived per-site results supporting the manuscript:

> **Hour-ahead irradiance forecasting in the humid tropics: model choice versus data sources at six Indonesian stations.**
> Ariffudin, A. Sopaheluwakan, A. Sudarmaji, S. A. Pawiro (submitted).

Six BMKG climatological stations in Indonesia, named by province: Banten, Bengkulu, Jambi, Yogyakarta, West Kalimantan and Central Java · 2022–2025 · 10-min grid · hour-ahead GHI.

The study asks whether hour-ahead predictability in the humid tropical Maritime Continent is limited by model choice or by the information available to the models, and which data source carries that information. It is a test of predictability and data value under one controlled, leakage-free protocol, not a model ranking.

**No observational data are distributed here** (see *Data availability*).

> **Version 2.0.0** replaces the layout of v1.0.x. The `pipeline/` folder is a copy of the working directory that produced every number in the manuscript (scripts and result folders side by side). See `CHANGELOG.md`.

## Study design (summary)

| Aspect | Setting |
|---|---|
| **Targets** | Primary: mean GHI over the hour after the origin, $\bar G(t)=\frac16\sum_{j=1}^{6}G(t+10j)$. Secondary: instantaneous GHI at $t+60$ min. Models are ranked only within each target. |
| **Split** | Chronological: train 2022–2023 · validation 2024 · test 2025; walk-forward check at Bengkulu |
| **Evaluation mask** | Daytime origins (solar elevation > 5°); sensitivity: target also in daylight, measured GHI only |
| **Baseline** | Smart persistence with the Ineichen–Perez clear-sky model (monthly Linke turbidity, pvlib) |
| **Satellite data** | Himawari-8/9 L2 cloud product (CLP): mean optical thickness, cloud-top height and effective radius of cloudy pixels within ±30 km, and a cloud flag (mean optical thickness ≥ 1). The file labelled $t-10$ min is used at origin $t$ (no look-ahead); steps without a valid retrieval are set to missing before lags/rolling statistics. |
| **Predictors** | 43, retained from 104 candidates by rules fixed before any model was evaluated: core (18), satellite cloud CLP (8), SYNOP (6), surface meteorology AWS (11) |
| **Architectures (8)** | LightGBM, CatBoost, XGBoost, MLP, LSTM, Transformer, LSTM-hybrid, Transformer-hybrid at all six sites; ridge regression as a linear reference |
| **Source ablation** | LightGBM on core, core + CLP / AWS / SYNOP cloud, and AWS or SYNOP cloud on top of core + CLP |
| **Uncertainty** | Paired bootstrap resampling whole forecast days (2,000 resamples); differences < 0.002 in R² treated as practically negligible |
| **Robustness** | Five training seeds for all neural networks; random search of 30 configurations for LightGBM and the LSTM; satellite latency; SYNOP as-of alignment; spatial texture of the cloud field; post-hoc decomposition of AWS subgroups |

## Repository layout

```
README.md  CHANGELOG.md  LICENSE  CITATION.cff  .zenodo.json  environment.yml  .gitignore  .gitattributes
pipeline/  stage scripts (NN_*.py), shared helpers (_common.py, _blockboot.py, _multiseed.py), runners
           (run_all.py, run_rerun_P2.py) and one result folder per stage (CSV/JSON/MD only)
figures/   manuscript figures Fig1–Fig6 and supplementary figures FigS1–FigS4 (EPS + PNG), numbered as in the paper
```

Comments and design notes inside the scripts and in some `DESAIN_*.md` / `RINGKASAN_*.md` files are in Indonesian; the design notes record decision rules fixed before the corresponding results were computed.

## Stage → script → results (`pipeline/`)

| Stage | Script(s) | Results folder |
|---|---|---|
| 00 — model frames from the harmonised database (CLP masking, $t-10$ min alignment, uniform cloud flag) | `00_build_data.py` | `00_data/` (QC and provenance only) |
| 55 — Ineichen–Perez clear-sky cache | `55_clearsky_ineichen.py` | `55_clearsky/` |
| 01 — baselines, walk-forward | `01_baseline_v3.py`, `01b_walkforward_v2.py`, `01b_walkforward_mean.py`, `01b_timeseries_mean.py` | `01_baseline/` |
| 02 — SHAP ranking and selection curve | `02_feature_ranking_v2.py`, `02b_feature_ranking_mean.py` | `02_feature_ranking_mean/`, `02_feature_ranking_v2/` |
| 03 — source ablation (Bengkulu) | `03_ablation_mean.py` | `03_ablation_mean/` |
| 04 — eight architectures, Bengkulu (all learn the residual) | `04_arch_mean.py` | `04_arch_mean/` |
| 04b/04c — eight architectures × six sites | `04c_mean_6situs.py`, `04c_mean_6situs_xgb_mlp.py`, `04b_seq_6situs_mean.py`, `04b_merge_mean.py`, `04b_arch_6situs.py`, `04b_arch_6situs_plot.py` | `04b_arch_6situs_mean/`, `04b_arch_6situs/`, `04c_mean_6situs/` |
| 06 — stratification by sky condition, hour, season | `06_strat_mean.py`, `06_strat_mean_plot.py` | `06_strat_mean/` |
| 07b — six-site source ablation | `07b_replication_ablation_mean.py` | `07_replication/` |
| 09 — evaluation-protocol sensitivity | `09_sens_mean.py` | `09_sensitivity_mean/` |
| 13b — skill vs climatology–persistence-optimal reference | `13b_reference_skill_6situs.py` | `13_reference_skill_6situs/` |
| 18b — SYNOP as-of alignment | `18b_synop_asof_6situs.py` | `18_synop_asof/` |
| 19 — treatment of missing satellite retrievals | `19_sens_clp_fill.py` | `19_sens_clp_fill/` |
| 27 — daily-block bootstrap of all key differences | `27_block_bootstrap.py` | `27_block_bootstrap/` |
| 28 — spatial texture of the cloud field | `28_clp_spatial.py` | `28_clp_spatial/` |
| 31/33 — timing (latency) of the satellite predictors | `31_clp_lag_sensitivity.py`, `33_verify_B.py` | `31_clp_lag/` |
| 36/37 — multi-seed neural runs | `36_multiseed_neural.py`, `37_multiseed_analysis.py` | `36_multiseed/` |
| 50 — predictor-set evaluation (104 → 43) | `50_evaluasi_prediktor.py` (run with `FEATSET=P0`) | `50_prediktor/` |
| 60 — skill vs smart persistence and ridge reference | `60_skill_linear.py` | `60_skill_linear/` |
| 61 — hyperparameter-tuning check (Bengkulu) | `61_tuning_bengkulu.py` | `61_tuning/` |
| 62 — observed vs predicted (CatBoost, six sites) | `62_scatter_6situs.py` | `62_scatter_6situs/` |
| 63 — AWS subgroups on top of CLP (post hoc) | `63_aws_subkelompok.py` | `63_aws_subkelompok/` |
| 64 — clearness index used for sky classes | `64_kt_referensi.py` | `64_kt_referensi/` |
| Figures | `15_final_figs_mean_en.py`, `16_final_figs_release_en.py`, `make_fig2_workflow.py`, `62_scatter_6situs.py`, `S3_target_effect.py` | `figures/` |
| Not used in the manuscript (kept for provenance) | `11_probabilistic_mean.py`, `12b_conformal_split*.py` | `11_probabilistic_mean/`, `12b_conformal_split*/` |

## Manuscript item → results

| Manuscript item | Source in `pipeline/` |
|---|---|
| Table 1 (stations, measured fraction) | `09_sensitivity_mean/sensitivity_variants_mean.csv`, `00_data/qc_build.csv` |
| Table 2 (predictor groups), Table S2 | `50_prediktor/himpunan_prediktor.csv` |
| Table 3 (R² and skill, eight architectures, ridge) | `04b_arch_6situs_mean/`, `60_skill_linear/` |
| Fig. 3 (architectures per station) | `04b_arch_6situs_mean/`, `04b_arch_6situs/` |
| Fig. 4 (sky condition and hour, Bengkulu) | `06_strat_mean/` |
| Table 4, Fig. 5 (source contributions, six sites) | `27_block_bootstrap/replication_ablation_block.csv`, `07_replication/` |
| Fig. 6 (SHAP ranking and selection curve) | `02_feature_ranking_mean/` |
| Bengkulu pairwise tests, walk-forward | `27_block_bootstrap/arch_bengkulu_block.csv`, `04_arch_mean/`, `01_baseline/bengkulu_walkforward_mean.csv` |
| Banten wind decomposition (§3.2) | `63_aws_subkelompok/` |
| Clearness-index reference (§2.2) | `64_kt_referensi/` |
| Table S1 (missing retrievals) | `19_sens_clp_fill/`, `27_block_bootstrap/clp_fill_block.csv` |
| Table S3 (model settings) | scripts `04*`, `27_block_bootstrap.py`, `36_multiseed_neural.py`, `60_skill_linear.py` |
| Table S4, Fig. S1 (errors, observed vs predicted) | `60_skill_linear/`, `62_scatter_6situs/` |
| Table S5, Fig. S2 (skill vs reference forecasts) | `13_reference_skill_6situs/`, `60_skill_linear/` |
| Table S6 (training seeds) | `36_multiseed/` |
| Table S7, Fig. S3 (evaluation protocol) | `09_sensitivity_mean/` |
| Table S8 (SYNOP alignment) | `18_synop_asof/6situs/` |
| Table S9 (spatial texture) | `28_clp_spatial/` |
| Table S10, Fig. S4 (target definition) | `04b_arch_6situs/`, `04b_arch_6situs_mean/` |
| Table S11 (satellite timing) | `31_clp_lag/` |
| Table S12 (tuning check) | `61_tuning/` |

## Running

```bash
conda env create -f environment.yml
conda activate ghi-benchmark-6sites
cd pipeline
export GHI_DB=/path/to/solar_harmonised_clpbanten_v2.duckdb      # harmonised database (std.* schema), read-only
export GHI_DB_OLD=/path/to/solar_new.duckdb                       # earlier database, for the QC comparison in stage 00
python -u 00_build_data.py                                         # model frames -> 00_data/
MASK_CLP=0 python -u 00_build_data.py                              # variant with retrieval gaps as stored -> 00_data_rawfill/
python -u 55_clearsky_ineichen.py                                  # clear-sky cache from 00_data/ -> 00_clearsky/
python -u run_all.py                                               # stages 00–16 (stage 00 is rebuilt identically)
```

The remaining stages are listed in order in `run_rerun_P2.py`. That runner also calls the authors' document builders (`20_*`, `21_*`, `38_*`, `49_*`, `52_*`, `53_*`), which assemble the manuscript files and are not part of this repository; run the analysis stages individually instead. Defaults are `FEATSET=P2` (43 predictors) and `CLEARSKY=IP` (Ineichen–Perez).

**Data prerequisite.** No observational data are distributed, so the pipeline cannot be re-run from this repository alone. The database paths are read from the environment variables `GHI_DB` (stages 00, 28, 55) and `GHI_DB_OLD` (stage 00), and the scripts stop with a message if they are unset. `00_build_data.py` checks the SHA-256 of the database and stops if it differs from the one used for the manuscript; it also compares the frames cell by cell with the earlier database given by `GHI_DB_OLD`. Scripts that need saved prediction archives (`*.npz`, `*.npy`; these contain observed values and are not shipped) regenerate them when the earlier stages are run.

## Data availability

- **BMKG station data** (harmonised) are available from the corresponding author on reasonable request; raw observations are not redistributed here.
- **Himawari-8/9 cloud products** (JAXA L2 CLP) are available through the JAXA P-Tree system: https://www.eorc.jaxa.jp/ptree/
- **This repository** holds the analysis code and derived per-site results, archived on Zenodo under the concept DOI **10.5281/zenodo.22929571** (always resolves to the latest version).

## Citation

See `CITATION.cff`. A citation for the journal article will be added once it is published.

## License

Code and derived results: CC BY 4.0 (see `LICENSE`).
