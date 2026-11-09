---
tags: [disertasi, prediksi-radiasi, manuskrip-v6, desain]
created: 2026-11-09
status: "DIKUNCI sebelum run (2026-11-09)"
---

# Tahap 114 — empat analisis pendukung naskah, dihitung ulang dari V6.10

**Alasan:** Naskah V5 memuat empat analisis pendukung yang dihitung dari seri GHI lama (DB v2, sebelum penyeragaman). Pengguna meminta semua angka Manuskrip V6 berasal dari V6.10. Keempatnya dihitung ulang di Bengkulu, seperti di V5, dengan data V6.10 dan P2F (44 prediktor).

## Data

Untuk semua skrip:

| Variabel | Nilai |
|---|---|
| `DATA_DIR` | `Balai_data_v6_10/00_data` |
| `CLEARSKY_DIR` | `Balai_data_v6_10/clearsky` |
| `CLP_EKSTRA_DIR` | `Balai_data_v6_10/clp_ekstra` |
| `FEATSET` | `P2F` |

Split latih 2022–2023, validasi 2024, uji 2025. Origin dengan elevasi matahari > 5°.

## Analisis

| Kode | Sumber | Isi | Perubahan |
|---|---|---|---|
| a1 | `01b_walkforward_mean.py` | Walk-forward 5 lipatan, LightGBM residual | Hanya folder keluaran |
| a2 | `02b_feature_ranking_mean.py` | Peringkat fitur, kurva seleksi, SHAP LightGBM (konfigurasi ablasi) | Hanya folder keluaran |
| a3 | `training mirip/07_sinyal_sintetis.py` | Kontrol sinyal sintetis (LightGBM, BiLSTM) | Lihat di bawah |
| a4 | `61_tuning_bengkulu.py` | Pencarian hiperparameter LightGBM dan LSTM | Lihat di bawah |

**Perubahan a3:**
- assert P2F dan 44 prediktor;
- folder keluaran;
- jumlah thread torch 4.

Sinyal, amplitudo (A = 150), seed, model, dan aturan tafsir T1–T4 tetap.

**Perubahan a4.** Konfigurasi bawaan kini **protokol baku naskah**, bukan protokol lama tahap 36:

- **LightGBM:** 2500 pohon, lr 0,03, 63 daun, median-imputasi, early stopping 200.
- **LSTM:**
  - arsitektur 2 × 96, dropout 0,1, kepala 64;
  - target residual distandarkan;
  - Adam lr 7 × 10⁻⁴, batch 256;
  - ReduceLROnPlateau (0,5; patience 2; min 10⁻⁵);
  - early stopping patience 10, maks 100 epoch, clip 1,0.
- **29 konfigurasi acak:** dari ruang dan urutan rng 2026 yang sama dengan tahap 61. LightGBM memakai 5000 pohon dengan early stopping 200, imputasi median seperti protokol baku.
- **Pelatihan LSTM:** semua konfigurasi dilatih dengan protokol baku. Konfigurasi menentukan hidden, lapisan, dropout, kepala, lr, dan batch.
- **Uji reproduksi (wajib):**
  - LightGBM bawaan harus sama dengan `Manuskrip_versi6/protokol/hasil/pohon/pred_bengkulu_LightGBM_s42.npy`;
  - LSTM bawaan seed 42 harus sama dengan `.../nn/pred_bengkulu_LSTM_s42.npy` (torch 3 thread, seperti run protokol).
- **Pemilihan:** R² validasi 2024 tertinggi. LSTM terpilih dilatih ulang dengan seed 1–4.
- **Pembanding:**
  - LSTM terpilih (rerata 5 seed dan prakiraan ensambel 5 seed) dibandingkan dengan LSTM protokol baku 5 seed;
  - LightGBM terpilih dibandingkan dengan LightGBM protokol baku.
  - CI: bootstrap blok harian (2000, seed 11).

## Aturan

- Hasil tidak dipakai untuk mengubah model utama, prediktor, atau data. Hasil hanya dilaporkan apa adanya di ESM.
- Kontrol sinyal sintetis memakai aturan tafsir T1–T4 tahap asal, ditetapkan sebelum run.
- Kontrol positif "kebocoran sengaja" V5 (GHI t+10 sebagai prediktor) tidak diulang dan dikeluarkan dari naskah V6.

## Addendum 2026-11-09 (sebelum run a5): seleksi prediktor

| Kode | Isi |
|---|---|
| a5 | R² validasi 2024 LightGBM (konfigurasi ablasi) dengan 44 prediktor P2F lawan semua kandidat (104 kolom basis data + `clp_cloud_frac`), enam stasiun |

Analisis ini menggantikan kalimat V5 "seleksi mengubah R² validasi ≤ 0,001" yang dihitung dari data lama. Hasilnya hanya dilaporkan, tidak dipakai mengubah himpunan prediktor.
