---
tags: [disertasi, prediksi-radiasi, eksperimen, tuning, hiperparameter, paper-v3, clpbanten-v2]
created: 2026-10-08
modified: 2026-10-08
status: "DESAIN TERKUNCI — ditulis sebelum hasil tahap 61"
---

# Tahap 61 — uji tuning hiperparameter (desain terkunci, ditulis SEBELUM hasil)

> [!important] Latar
> Naskah v3 menyatakan bahwa hiperparameter ditetapkan di awal dan sengaja tidak di-tuning per arsitektur. Bagian keterbatasan karena itu mengakui bahwa konvergensi arsitektur "cannot exclude the possibility that all models were similarly under-optimised" ([[LAPORAN_Rerun_v2_clpbanten]] §28). Penulis memutuskan (2026-10-08) menjalankan uji tuning kecil, yaitu opsi 7 dari `copilot/projects/paper_v3/outputs/DRAF_Revisi_Klaim_Prediktabilitas.md`.

## Rancangan
- **Situs dan data:** Bengkulu, target rata-rata jam, residual terhadap smart persistence. Data, split, 43 prediktor, dan 14 kanal × 12 langkah **identik** dengan `04_arch_mean.py`.
- **Model:** LightGBM (wakil model pohon, model acuan uji pasangan) dan LSTM murni (wakil jaringan saraf sekuensial; selisihnya dengan LightGBM signifikan di Bengkulu).
- **Pencarian:** acak, **30 konfigurasi per model**: konfigurasi bawaan + 29 sampel acak (`numpy.random.default_rng(2026)`). Konfigurasi dipilih dengan **R² validasi 2024**. Early stopping tetap pada validasi seperti pipeline: LightGBM 100 ronde; LSTM ≤ 40 epoch, patience 6.
- **Ruang LightGBM:**
  - learning rate log-uniform [0,01; 0,1];
  - jumlah daun {15, 31, 63, 127, 255};
  - min. sampel per daun {10, 20, 50, 100, 200};
  - subsample dan colsample uniform [0,5; 1,0];
  - L1 dan L2 log-uniform [10⁻³; 10];
  - maks. 5.000 pohon (bawaan tetap 3.000 agar reproduksi persis).
- **Ruang LSTM:**
  - hidden {32, 64, 96, 128, 192};
  - lapis {1, 2, 3};
  - dropout antar-lapis uniform [0; 0,4] (diabaikan bila 1 lapis);
  - lebar kepala {32, 64, 128};
  - learning rate log-uniform [2·10⁻⁴; 3·10⁻³];
  - batch {128, 256, 512}.
  - Jendela input (12 langkah) dan kanal **tidak** diubah, karena keduanya bagian dari desain input, bukan hiperparameter.
- **Seed:**
  - setiap konfigurasi LSTM dilatih dengan seed 42, ditetapkan tepat sebelum model dibangun (prosedur tahap 36);
  - konfigurasi LSTM terpilih dilatih ulang dengan seed 1–4, sehingga ada 5 realisasi;
  - pembanding bawaan = 5 realisasi tahap 36 (run pipeline + seed 1–4);
  - LightGBM hanya dengan seed 42, karena praktis deterministik.

## Uji reproduksi (wajib lolos sebelum pencarian)
- LightGBM bawaan = `04_arch_mean` (R² dan prediksi).
- LSTM bawaan dengan seed 1 = `36_multiseed/preds/bkl__bengkulu__LSTM__s1.npy` (R² empat desimal sama dan prediksi `allclose`).

## Besaran yang dilaporkan (uji 2025)
- **Δ_LGB** = R²(LightGBM terpilih) − R²(LightGBM bawaan), dengan CI bootstrap blok harian.
- **Δ_LSTM** = rerata R² 5 realisasi (terpilih) − rerata R² 5 realisasi (bawaan), dengan CI bootstrap blok pada prediksi ansambel 5 realisasi.
- Selisih LightGBM − LSTM sebelum dan sesudah tuning, dibandingkan dengan spread 8 arsitektur Bengkulu.
- Hiperparameter terpilih, R² validasi, dan jumlah konfigurasi yang lebih baik daripada bawaan di validasi.

## Aturan tafsir (dikunci)
- **U1** — |Δ_LGB| < 0,005 **dan** |Δ_LSTM| < 0,005. Kalimat keterbatasan "cannot exclude … under-optimised" diganti dengan hasil uji: tuning mengubah R² paling banyak X (Table S12), sehingga konvergensi tidak mungkin artefak hiperparameter yang tidak di-tuning.
- **U3** — max(|Δ_LGB|, |Δ_LSTM|) > 0,01. Kalimat keterbatasan dipertahankan dan ditambah angka (Table S12). Klaim konvergensi dinyatakan berlaku untuk protokol bersama.
- **U2** — selain itu. Angka dilaporkan dengan rumusan netral (mis. "changed R² by at most X, comparable to the spread among architectures"). Kalimat keterbatasan dilunakkan, tidak dihapus.
- Bila tuning membalik urutan (LSTM terpilih > LightGBM terpilih), hal itu dinyatakan eksplisit, apa pun aturannya.
- Hasil dilaporkan apa adanya.

## Implementasi
`61_tuning_bengkulu.py` → `61_tuning/`. Hasil disimpan per konfigurasi, jadi run bisa dilanjutkan bila terputus. Suplemen mendapat **Table S12** (dirujuk pertama kali di paragraf keterbatasan, setelah Table S11). Assert urutan Suplemen (49, 52) dan registri C8 disesuaikan ke S1–S12.
