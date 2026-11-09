# Changelog

## v3.0.0 — 2026-11-09

Accompanies manuscript version 6, *Himawari-8/9 cloud retrievals improve hour-ahead irradiance forecasts in Indonesia when the sky changes*. Every number in that manuscript was recomputed from database version 6.10; the numbers of v2.0.0 no longer match the manuscript.

**Layout**
- `pipeline/` (v2.0.0) is replaced by a copy of the working directories that produced manuscript version 6: `paper_v2_clpbanten/` (shared helpers, reused stage scripts, database stages 93–113, supporting analyses in stage 114), `Manuskrip_versi6/` (training protocol, analysis, results), `training mirip/` (synthetic-signal control) and `data_versions/` (README of each database version). Relative paths inside the scripts resolve in this layout.
- Figures renamed to their manuscript numbers (`Fig1`–`Fig5`, `FigS1`–`FigS2`), PNG and PDF.

**Data changes (database 6.10)**
- Radiation series identical to the harmonised series behind the previous manuscript version.
- Clear-sky irradiance averaged over each 10-min slot, like GHI.
- Himawari-8/9 CLP re-extracted at all six stations from boxes of 11 × 11 pixels centred on the station coordinates (Jambi now at the radiometer site), with the box cloud fraction.
- AWS meteorology checked against SYNOP (units and pressure levels matched, causal 7-day bias correction) and rebuilt with a causal estimator; rainfall from the AWS 24-h accumulation (reset at 00 UTC); SYNOP reports kept for 50 min; total cloud cover N at all stations.

**Method changes**
- 44 predictors: the 43 of v2.0.0 plus the CLP cloud fraction.
- All eight architectures trained with one protocol (residual target, five seeds), as in the manuscript.
- Box statistics rebuilt from the version-6 extraction (stage 113, verified pixel by pixel against Himawari chips); six statistics, because the cloud fraction is now a predictor.
- Supporting analyses recomputed on version 6.10 (stage 114): walk-forward test, SHAP attribution, synthetic-signal control, hyperparameter search (default = the main protocol, reproduced exactly) and predictor-selection check.
- A number checker (`Manuskrip_versi6/analisis/v6_05_cek_angka.py`) recomputes every number quoted in the manuscript from the result files.

**Not distributed** (unchanged policy): station observations, the harmonised database and model frames, clear-sky caches, prediction archives (`*.npz`, `*.npy`), trained models, the Himawari extraction archives, the manuscript and the authors' document builder.

## v2.0.0 — 2026-10-12

Complete pipeline behind the revised manuscript *Hour-ahead irradiance forecasting in the humid tropics: model choice versus data sources at six Indonesian stations*. The numbers in v1.0.x no longer match the manuscript.

**Layout**
- `scripts/` + `results/` replaced by `pipeline/`, a copy of the working directory in which every stage script writes its own result folder. The released code is the code that produced the manuscript numbers; the only edits replace the authors' local database paths in `00_build_data.py`, `28_clp_spatial.py` and `55_clearsky_ineichen.py` with required environment variables (`GHI_DB`, `GHI_DB_OLD`); the scripts stop with a message if they are unset.
- Figures renamed to their manuscript numbers (`Fig1`–`Fig6`, `FigS1`–`FigS4`).

**Method changes reflected in the results**
- Model frames are built from the harmonised database (`00_build_data.py`): the Himawari-8/9 file labelled $t-10$ min is used at origin $t$ at every station; steps without a valid retrieval are set to missing before lags and rolling statistics; the CLP cloud flag is recomputed uniformly as mean optical thickness ≥ 1 (the source database used different definitions at different stations).
- Clear-sky irradiance and smart persistence use the Ineichen–Perez model with a monthly Linke turbidity climatology (stage 55), replacing $1100\,\sin h$.
- 43 predictors in four groups, retained from 104 candidates by rules fixed in advance (stage 50).
- Confidence intervals from a paired bootstrap resampling whole forecast days (stage 27); 0.002 in R² as the threshold of practical relevance.
- New analyses: ridge-regression reference and skill against smart persistence (60), multi-seed neural runs (36/37), hyperparameter-tuning check (61), satellite latency (31), missing-retrieval treatment (19), spatial texture of the cloud field (28), observed-vs-predicted figure (62), post-hoc AWS subgroups (63), clearness-index reference (64).
- The probabilistic and conformal layers (11, 12b) are kept for provenance but are no longer part of the manuscript.

**Not distributed** (unchanged policy): station observations, model frames (`00_data*/`), clear-sky caches, prediction archives (`*.npz`, `*.npy`, which contain observed values), trained models, and the authors' document builders.

## v1.0.1 — 2026-09-25

Updated README, `CITATION.cff` and `.zenodo.json`; removed intermediate diagnostic figures (`figures/01_*`–`08_*`), keeping the manuscript figures.

## v1.0.0 — 2026-09-24

Initial six-site release.
