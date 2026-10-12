---
tags: [disertasi, prediksi-radiasi, eksperimen, multi-seed, clpbanten-v2]
created: 2026-10-05
modified: 2026-10-05
---

# Ringkasan multi-seed model neural (tahap 37)

Desain & aturan: [[DESAIN_TERKUNCI]]. Angka mentah: `r2_ringkas.csv`, `bkl_block.csv`, `six_block.csv`, `spread_6situs.csv`.

## R² per model (rata-rata ± SD 5 realisasi; R0 = pipeline)

| Eksperimen | Situs | Model | R0 | rata-rata | SD | min–maks | ansambel |
|---|---|---|---|---|---|---|---|
| bkl | bengkulu | LSTM | 0.9034 | 0.9036 | 0.0006 | 0.9028–0.9042 | 0.9056 |
| bkl | bengkulu | LSTM_hybrid | 0.9043 | 0.9039 | 0.0008 | 0.9032–0.9051 | 0.9057 |
| bkl | bengkulu | MLP | 0.9073 | 0.9075 | 0.0005 | 0.9069–0.9082 | 0.9080 |
| bkl | bengkulu | Transf_hybrid | 0.9052 | 0.9031 | 0.0020 | 0.9008–0.9052 | 0.9065 |
| bkl | bengkulu | Transformer | 0.9040 | 0.9043 | 0.0022 | 0.9011–0.9067 | 0.9072 |
| six | banten | LSTM | 0.8603 | 0.8601 | 0.0019 | 0.8574–0.8628 | 0.8630 |
| six | banten | LSTM_hybrid | 0.8593 | 0.8603 | 0.0011 | 0.8593–0.8616 | 0.8624 |
| six | banten | MLP | 0.8528 | 0.8519 | 0.0006 | 0.8513–0.8528 | 0.8525 |
| six | banten | Transformer | 0.8622 | 0.8616 | 0.0023 | 0.8577–0.8636 | 0.8659 |
| six | banten | Transformer_hybrid | 0.8607 | 0.8617 | 0.0024 | 0.8589–0.8653 | 0.8657 |
| six | bengkulu | LSTM | 0.9002 | 0.9029 | 0.0016 | 0.9002–0.9042 | 0.9052 |
| six | bengkulu | LSTM_hybrid | 0.9044 | 0.9039 | 0.0008 | 0.9032–0.9051 | 0.9059 |
| six | bengkulu | MLP | 0.8992 | 0.8989 | 0.0004 | 0.8982–0.8992 | 0.8995 |
| six | bengkulu | Transformer | 0.9050 | 0.9045 | 0.0022 | 0.9011–0.9067 | 0.9074 |
| six | bengkulu | Transformer_hybrid | 0.9025 | 0.9026 | 0.0016 | 0.9008–0.9051 | 0.9065 |
| six | jambi | LSTM | 0.8683 | 0.8684 | 0.0008 | 0.8677–0.8697 | 0.8702 |
| six | jambi | LSTM_hybrid | 0.8686 | 0.8686 | 0.0005 | 0.8679–0.8692 | 0.8704 |
| six | jambi | MLP | 0.8644 | 0.8635 | 0.0006 | 0.8627–0.8644 | 0.8641 |
| six | jambi | Transformer | 0.8727 | 0.8717 | 0.0018 | 0.8686–0.8731 | 0.8755 |
| six | jambi | Transformer_hybrid | 0.8717 | 0.8719 | 0.0002 | 0.8717–0.8721 | 0.8750 |
| six | jogja | LSTM | 0.8374 | 0.8386 | 0.0019 | 0.8371–0.8418 | 0.8426 |
| six | jogja | LSTM_hybrid | 0.8426 | 0.8405 | 0.0014 | 0.8393–0.8426 | 0.8429 |
| six | jogja | MLP | 0.8329 | 0.8335 | 0.0016 | 0.8310–0.8350 | 0.8344 |
| six | jogja | Transformer | 0.8456 | 0.8451 | 0.0021 | 0.8429–0.8483 | 0.8488 |
| six | jogja | Transformer_hybrid | 0.8473 | 0.8463 | 0.0021 | 0.8427–0.8475 | 0.8501 |
| six | kalbar | LSTM | 0.8921 | 0.8920 | 0.0006 | 0.8910–0.8925 | 0.8943 |
| six | kalbar | LSTM_hybrid | 0.8915 | 0.8931 | 0.0010 | 0.8915–0.8940 | 0.8950 |
| six | kalbar | MLP | 0.8857 | 0.8844 | 0.0009 | 0.8833–0.8857 | 0.8849 |
| six | kalbar | Transformer | 0.8964 | 0.8946 | 0.0020 | 0.8913–0.8964 | 0.8985 |
| six | kalbar | Transformer_hybrid | 0.8950 | 0.8962 | 0.0011 | 0.8950–0.8976 | 0.8991 |
| six | semarang | LSTM | 0.8824 | 0.8830 | 0.0008 | 0.8821–0.8840 | 0.8850 |
| six | semarang | LSTM_hybrid | 0.8849 | 0.8832 | 0.0010 | 0.8823–0.8849 | 0.8852 |
| six | semarang | MLP | 0.8800 | 0.8788 | 0.0013 | 0.8766–0.8800 | 0.8795 |
| six | semarang | Transformer | 0.8854 | 0.8852 | 0.0014 | 0.8835–0.8870 | 0.8886 |
| six | semarang | Transformer_hybrid | 0.8855 | 0.8857 | 0.0014 | 0.8836–0.8876 | 0.8888 |

## Aturan & klaim

```json
{
 "realisasi": [
  "pipe",
  "s1",
  "s2",
  "s3",
  "s4"
 ],
 "MLP6_R0_reproduksi": {
  "banten": true,
  "bengkulu": true,
  "jambi": true,
  "jogja": true,
  "kalbar": true,
  "semarang": true
 },
 "R1": {
  "spread_reported": [
   0.0087,
   0.017
  ],
  "spread_seedmean": [
   0.0098,
   0.0164
  ],
  "spread_any_realisation": [
   0.0087,
   0.0189
  ],
  "max_abs_dev": 0.0012,
  "robust": false
 },
 "K5_MLP_within_0.009": {
  "realisasi_lolos": 0,
  "dari": 5,
  "max_gap": 0.0189
 },
 "K6_LSTM_lowest": {
  "per_realisasi": {
   "pipe": 0,
   "s1": 0,
   "s2": 0,
   "s3": 0,
   "s4": 0
  },
  "max_gap": 0.0128,
  "within_0013_all": true
 },
 "neural_beats_tabular_count": 3,
 "n_site_real": 30,
 "best_neural_freq": {
  "Transformer": 15,
  "Transformer_hybrid": 13,
  "LSTM_hybrid": 2
 },
 "R2_bengkulu": {
  "MLP": {
   "klaim": "signifikan lebih rendah",
   "dR2_pipe": -0.0019,
   "dR2_mean": -0.0017,
   "dR2_min": -0.0024,
   "dR2_max": -0.001,
   "dR2_ens": -0.0012,
   "ens_CI": [
    -0.0029,
    0.0004
   ],
   "n_sig": 3,
   "n_sig_arah_klaim": 3,
   "robust": false
  },
  "LSTM": {
   "klaim": "signifikan lebih rendah",
   "dR2_pipe": -0.0058,
   "dR2_mean": -0.0057,
   "dR2_min": -0.0065,
   "dR2_max": -0.005,
   "dR2_ens": -0.0037,
   "ens_CI": [
    -0.0057,
    -0.0016
   ],
   "n_sig": 5,
   "n_sig_arah_klaim": 5,
   "robust": true
  },
  "Transformer": {
   "klaim": "signifikan lebih rendah",
   "dR2_pipe": -0.0052,
   "dR2_mean": -0.0049,
   "dR2_min": -0.0081,
   "dR2_max": -0.0025,
   "dR2_ens": -0.002,
   "ens_CI": [
    -0.0038,
    -0.0001
   ],
   "n_sig": 5,
   "n_sig_arah_klaim": 5,
   "robust": true
  },
  "LSTM_hybrid": {
   "klaim": "signifikan lebih rendah",
   "dR2_pipe": -0.005,
   "dR2_mean": -0.0054,
   "dR2_min": -0.006,
   "dR2_max": -0.0041,
   "dR2_ens": -0.0035,
   "ens_CI": [
    -0.0054,
    -0.0015
   ],
   "n_sig": 5,
   "n_sig_arah_klaim": 5,
   "robust": true
  },
  "Transf_hybrid": {
   "klaim": "signifikan lebih rendah",
   "dR2_pipe": -0.004,
   "dR2_mean": -0.0062,
   "dR2_min": -0.0084,
   "dR2_max": -0.004,
   "dR2_ens": -0.0028,
   "ens_CI": [
    -0.0046,
    -0.0009
   ],
   "n_sig": 5,
   "n_sig_arah_klaim": 5,
   "robust": true
  }
 },
 "K2_bengkulu": {
  "spread_seedmean": 0.0062,
  "spread_reported": 0.0099,
  "top4": [
   "LightGBM",
   "CatBoost",
   "XGBoost",
   "MLP"
  ],
  "top4_range": 0.0017,
  "top4_reported": 0.0028
 },
 "R3": {
  "median_seed_sd": 0.0014,
  "max_seed_sd": 0.0024,
  "median_arch_spread": 0.0101,
  "kecil": true
 },
 "bkl_seed_sd": {
  "LSTM": 0.0006,
  "LSTM_hybrid": 0.0008,
  "MLP": 0.0005,
  "Transf_hybrid": 0.002,
  "Transformer": 0.0022
 }
}
```
