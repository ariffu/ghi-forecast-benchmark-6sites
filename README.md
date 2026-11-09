# GHI Forecast Benchmark — 6 Sites (hour-ahead)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22929571.svg)](https://doi.org/10.5281/zenodo.22929571)

Analysis code and derived per-site results supporting the manuscript:

> **Himawari-8/9 cloud retrievals improve hour-ahead irradiance forecasts in Indonesia when the sky changes.**
> Ariffudin, A. Sopaheluwakan, A. Sudarmaji, S. A. Pawiro (submitted).

The study covers six BMKG climatological stations in Indonesia, named by province: Banten, Bengkulu, Jambi, Yogyakarta, West Kalimantan and Central Java. It uses a 10-min grid for 2022–2025 and forecasts hour-ahead GHI.

It asks whether hour-ahead skill in the humid tropical Maritime Continent is limited by the model or by the information available to it, and when the most informative source, Himawari-8/9 cloud properties, adds skill. It is a test of predictability and data value under one controlled, leakage-free protocol, not a model ranking.

**No observational data are distributed here** (see *Data availability*).

> **Version 3.0.0** accompanies manuscript version 6. Every number in that manuscript and its Online Resource 1 was recomputed from database version 6.10 and can be traced to a script and a result file in this repository. The layout mirrors the authors' working directory, so the relative paths inside the scripts resolve. See `CHANGELOG.md`.

## Study design (summary)

| Aspect | Setting |
|---|---|
| **Target** | Mean GHI over the hour after the origin, $\bar G(t)=\frac16\sum_{j=1}^{6}G(t+10j)$; the GHI of a 10-min slot is the mean of 1-min logger values |
| **Split** | Chronological: train 2022–2023 · validation 2024 · test 2025; expanding-window walk-forward check at Bengkulu |
| **Origins** | Daytime (solar elevation > 5°) |
| **Reference forecasts** | Smart persistence (Ineichen–Perez clear-sky irradiance with monthly Linke turbidity, averaged over each 10-min slot); optimal convex combination of climatology and persistence (Yang et al. 2020) |
| **Satellite data** | Himawari-8/9 L2 cloud product (CLP) in an 11 × 11-pixel box (±30 km; 10 × 11 at West Kalimantan) centred on each station: mean optical thickness, cloud-top height and effective radius of cloudy pixels, cloud fraction, and a cloud flag. The file labelled $t-10$ min is used at origin $t$; steps without a valid retrieval are set to missing. |
| **Surface data** | AWS meteorology checked against the co-located SYNOP observations and rebuilt with a causal estimator (no value depends on later observations); SYNOP reports, including total cloud cover N, are kept for 50 min |
| **Predictors** | 44 in four groups: core (18), satellite cloud CLP (9), SYNOP (6), surface meteorology AWS (11) |
| **Architectures (8)** | LightGBM, CatBoost, XGBoost, MLP, LSTM, Transformer, LSTM-hybrid, Transformer-hybrid at all six sites; five seeds; ridge regression as linear reference |
| **Source ablation** | LightGBM, repeated with CatBoost: core; core + CLP, AWS or SYNOP cloud; AWS or SYNOP cloud on top of core + CLP |
| **Uncertainty** | Paired bootstrap over whole test days (2,000 resamples); differences < 0.002 in R² treated as practically negligible |
| **Supporting analyses** | Convergence diagnostics and stacking; synthetic-signal control; hyperparameter search (30 configurations each for LightGBM and the LSTM); satellite latency; box statistics; missing-retrieval treatment; logger-only evaluation sample; SHAP attribution |

## Repository layout

```
README.md  CHANGELOG.md  LICENSE  CITATION.cff  .zenodo.json  environment.yml  .gitignore  .gitattributes
paper_v2_clpbanten/
  _common.py, _blockboot.py        data preparation, predictor sets, targets, split; daily-block bootstrap
  27_block_bootstrap.py, 18b_*, 63_*, 01b_*, 02b_*, 61_*, 28_*, 31_*
                                   stage scripts whose code is reused by the analysis (see Manuskrip_versi6/analisis)
  93_versi6/ … 112_audit_v6_10/    build and audit of database versions 6 to 6.10 (scripts, design and summary notes, aggregate checks)
  113_kotak_chips/                 CLP box statistics, verified pixel by pixel against Himawari chips
  114_pendukung_v610/              supporting analyses recomputed on version 6.10 (walk-forward, SHAP, synthetic-signal
                                   control, hyperparameter search, predictor selection)
Manuskrip_versi6/
  protokol/                        training of 8 architectures × 5 seeds × 6 stations, metrics per run, result checklist
  analisis/                        manuscript analyses, figures, table filling and the number checker (v6_05_cek_angka.py)
  pipeline/                        source ablation, CLP fill, SYNOP, box statistics, latency, ridge, CP reference, AWS subgroups
  hasil/                           derived results for the text, tables and figures (CSV/JSON)
  DESAIN_v6.md                     run order and design notes
training mirip/07_sinyal_sintetis.py   original synthetic-signal control (copied into stage 114 a3)
data_versions/                     README of each database version (6 to 6.10) and of the box statistics
figures/                           Fig1–Fig5 and FigS1–FigS2 of the manuscript (PNG, PDF)
```

Comments, design notes (`DESAIN_*.md`) and summaries (`RINGKASAN_*.md`) are in Indonesian. Design notes record decision rules fixed before the corresponding results were computed. Several scripts are generated copies of earlier scripts. Their headers and `asal_*.json` files record the SHA-256 of the source and every text replacement.

## Running the analysis

The scripts read the database through environment variables:

```
DATA_DIR=<…>/Balai_data_v6_10/00_data
CLEARSKY_DIR=<…>/Balai_data_v6_10/clearsky
CLP_EKSTRA_DIR=<…>/Balai_data_v6_10/clp_ekstra
FEATSET=P2F
```

Some scripts also contain absolute paths to the authors' local data folders (for example `C:\Users\ariff\Documents\Balai_data_v6_10`, the Himawari box extraction archives and the box statistics `Balai_kotak_v6_10`); adapt them to your copy.

Run order (see `Manuskrip_versi6/DESAIN_v6.md`):

1. `Manuskrip_versi6/protokol/jalankan.ps1 pohon|nn`, then `protokol/04_daftar_periksa.py`;
2. `Manuskrip_versi6/analisis/01_pipeline_v6.py`;
3. `paper_v2_clpbanten/114_pendukung_v610/jalankan.ps1 a1 … a5`;
4. `analisis/v6_01_analisis_tanpa_latih.py`, `v6_02_data_dan_sampel.py`;
5. `v6_08_gambar_alur_kerja.py`, `v6_13_gambar_peta.py`, `v6_03_gambar.py`;
6. `v6_04_isi_tabel.py`;
7. `v6_05_cek_angka.py`, which recomputes every number quoted in the text from the result files.

Training and the stage-114 runs are resumable: completed model × seed combinations are skipped.

## Manuscript item → results

| Manuscript item | Source |
|---|---|
| Table 1 (stations, logger and measured shares) | `Manuskrip_versi6/hasil/sumber_ghi.csv` |
| Table 3, Tables S4–S6 (accuracy, errors, seeds) | `Manuskrip_versi6/protokol/hasil/daftar_periksa/` (`tabel3_baru.csv`, `catboost_baru.csv`, `tabelS4_baru.csv`, `tabelS6b_baru.csv`, `uji_berpasangan_per_seed.csv`), `protokol/hasil/{pohon,nn}/metrik_*.csv` |
| Table 4, Fig. 4 (source ablation) | `Manuskrip_versi6/pipeline/27_block_bootstrap/replication_ablation_block.csv`, `hasil/ablasi_catboost_residual.csv` |
| Fig. 3, Table S7, Fig. S1 (convergence) | `Manuskrip_versi6/hasil/a_konvergensi.csv`, `hasil/angka_gambar.json` |
| Fig. 5, Table S10 (where the satellite helps) | `Manuskrip_versi6/hasil/b_galat_kelas.csv`, `hasil/c_clp_kelas.csv` |
| Table S1 (CLP fill, box statistics, latency) | `Manuskrip_versi6/pipeline/19_sens_clp_fill/`, `28_clp_spatial/`, `31_clp_lag/` |
| Table S2 (predictors and availability) | generated by `analisis/v6_04_isi_tabel.py` |
| Table S8 (synthetic-signal control) | `paper_v2_clpbanten/114_pendukung_v610/a3_sintetis/` |
| Table S9 (CatBoost ablation) | `Manuskrip_versi6/hasil/ablasi_catboost_residual.csv` |
| Table S11 (hyperparameter search, walk-forward) | `paper_v2_clpbanten/114_pendukung_v610/a4_tuning/`, `a1_walkforward_bengkulu.csv` |
| Table S12 (sources of GHI, logger-only sample) | `Manuskrip_versi6/hasil/sumber_ghi.csv`, `hasil/sampel_logger.csv` |
| Fig. S2 (SHAP, Bengkulu) | `paper_v2_clpbanten/114_pendukung_v610/a2_shap/` |
| Numbers quoted in the text | `Manuskrip_versi6/hasil/angka_*.json` and the files above, checked by `analisis/v6_05_cek_angka.py` |

## Data availability

**Not distributed:**
- station observations;
- the harmonised database (`Balai_data_v6_10`) and the model frames;
- clear-sky caches;
- prediction archives (`*.npz`, `*.npy`), which contain observed values;
- trained models;
- the Himawari box extraction archives;
- the manuscript and the authors' document builder.

The harmonised BMKG station data are available from the corresponding author on reasonable request. Himawari-8/9 cloud products are available through the JAXA P-Tree system (https://www.eorc.jaxa.jp/ptree/).

## Environment

See `environment.yml`: Python 3.14 with LightGBM, CatBoost, XGBoost, PyTorch (CPU), scikit-learn, pandas, pyarrow, DuckDB and pvlib.

## License and citation

Code and results are released under CC BY 4.0 (see `LICENSE`). Please cite the Zenodo record (concept DOI 10.5281/zenodo.22929571; see `CITATION.cff`).
