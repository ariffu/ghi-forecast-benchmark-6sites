# Changelog

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
