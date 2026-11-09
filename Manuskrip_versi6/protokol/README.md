---
tags: [disertasi, prediksi-radiasi, manuskrip-v6]
created: 2026-11-08
status: "BERJALAN — pelatihan protokol baku V6 dari Balai_data_v6_10 (P2F, 44 prediktor)"
---

# Manuskrip V6: pelatihan protokol baku

**Data:** `C:\Users\ariff\Documents\Balai_data_v6_10` (beku, hanya-baca; lolos audit tahap 112)
- `DATA_DIR=00_data`
- `CLEARSKY_DIR=clearsky`
- `CLP_EKSTRA_DIR=clp_ekstra`
- `FEATSET=P2F`: 43 prediktor V5 ditambah `clp_cloud_frac`

**Skrip:** salinan dari `rerun protokol baku/`, dibuat oleh `00_siapkan_skrip.py`. SHA256 skrip sumber tercatat di `asal_skrip.json`.

Yang ditambah hanya dua hal:
- folder keluaran `hasil/`;
- pemeriksaan lingkungan: skrip berhenti bila data bukan V6.10, FEATSET bukan P2F, atau jumlah prediktor bukan 44.

Model, hiperparameter, seed (42, 1, 2, 3, 4), split (latih ≤ 2023, validasi 2024, uji 2025), dan target residual sama dengan V5.

**Peluncur:** `jalankan.ps1 <pohon|nn> [argumen]`. Proses yang dijalankan 2026-11-08:

| Proses | Perintah | Log |
|---|---|---|
| Pohon (LightGBM, XGBoost, CatBoost), 6 stasiun | `jalankan.ps1 pohon --threads 2` | `log/log_pohon.txt` |
| NN grup A (banten, bengkulu, jambi) | `jalankan.ps1 nn --situs banten bengkulu jambi --threads 3` | `log/log_nn_A.txt` |
| NN grup B (jogja, kalbar, semarang) | `jalankan.ps1 nn --situs jogja kalbar semarang --threads 3` | `log/log_nn_B.txt` |

NN = MLP, LSTM, Transformer, LSTM_hybrid, Transformer_hybrid.

**Bila laptop mati:** jalankan ulang perintah yang sama. Skrip melewati pasangan model × seed yang sudah tercatat di `hasil/pohon/metrik_pohon.csv` dan `hasil/nn/metrik_<situs>.csv`.

**Catatan banding V5:** pembanding yang benar adalah `Manuskrip_versi5/protokol/hasil`, yaitu tahap 86/87. Folder `rerun protokol baku/hasil` berisi data lama, jangan dipakai sebagai pembanding.

Pohon selesai 2026-11-08: 90/90 dalam 1.465 detik. Rata-rata 5 seed, V6 lawan V5:
- **R²:** beda −0,003 sampai +0,003. Jambi naik 0,003 karena kotak CLP kini di ASRS.
- **Skill:** turun 0,00–0,012 di Banten, Bengkulu, dan Jawa Tengah.

**Berikutnya, sesudah pelatihan selesai:** rantai analisis naskah V6, yaitu padanan `Manuskrip_versi5/analisis/01_pipeline_v5.py` … `v4_06` dengan assert P2F dan sumber V6.10.
