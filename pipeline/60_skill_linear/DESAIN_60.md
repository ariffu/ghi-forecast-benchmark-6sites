---
tags: [disertasi, prediksi-radiasi, eksperimen, skill, baseline-linear, paper-v3, clpbanten-v2]
created: 2026-10-08
modified: 2026-10-08
status: "DESAIN TERKUNCI — ditulis sebelum hasil tahap 60"
---

# Tahap 60 — skill terhadap smart persistence dan pembanding linear (desain terkunci, ditulis SEBELUM hasil)

> [!important] Latar
> Rekomendasi 1 audit ([[AUDIT_v3_Kemiripan_Model]], LAPORAN §24): R² total didominasi siklus harian yang sudah ditangkap smart persistence, sehingga selisih antar-arsitektur tampak sangat kecil. Penulis memutuskan (2026-10-08) menambahkan **skill terhadap smart persistence** dan **pembanding linear** ke perbandingan arsitektur.

## Metrik
- **Skill** = 1 − RMSE_model / RMSE_SP, dihitung pada himpunan uji yang sama (2025, protokol A, target rata-rata jam). Konvensi ini sama dengan yang sudah dipakai untuk CatBoost (Yang et al. 2020).
- **R² residual** = 1 − SSE_model / Σ(r − r̄)², dengan r = y − ŷ_SP; artinya bagian varians yang tersisa setelah smart persistence yang dijelaskan model. Dilaporkan di Suplemen (Table S4).
- Skill 8 arsitektur dibaca dari CSV pipeline (04c, 04c_xgb_mlp, 04b_seq). Bila prediksi tersimpan (`36_multiseed/preds/six__*__pipe.npy`: CatBoost, LightGBM, MLP, 4 model sekuensial), skill dihitung ulang dan wajib sama dengan CSV (|Δ| < 1e-4). XGBoost tidak menyimpan prediksi, jadi R² residualnya diturunkan dari skill CSV.

## Pembanding linear
- **Ridge regression** pada 43 prediktor yang sama, dengan target **residual** y − ŷ_SP (seperti LightGBM). Prediksi = ŷ_SP + ridge.
- Nilai kosong diganti median data latih; standardisasi memakai rerata dan simpangan baku data latih.
- Penalti α ∈ {10⁻², 10⁻¹, …, 10⁵} (8 nilai), dipilih dengan R² validasi 2024. Model dilatih pada 2022–2023 saja (tanpa refit), sama seperti model lain yang memakai validasi untuk early stopping.
- Uji: bootstrap blok harian berpasangan (`_blockboot.delta_r2`, 2.000 resampel, seed 11) untuk CatBoost − linear dan LightGBM − linear di 6 situs.
- Sebagai pemeriksaan, R² ridge dibandingkan dengan audit 54 (definisi data sama, grid α audit lebih sempit).

## Yang dilaporkan di naskah
- **Tabel 3:** kolom "Linear regression" di samping smart persistence. Tabel memuat dua blok: R² dan skill terhadap smart persistence. Kolom spread tetap untuk 8 arsitektur.
- **§2.2:** satu kalimat definisi pembanding linear, dan rumus skill.
- **§3.1:** R² dan skill linear, selisih CatBoost − linear dengan CI, dan spread 8 arsitektur dalam skill.
- **Diskusi dan kesimpulan** — aturan tafsir dikunci di sini:
  - **(T1)** Bila CatBoost − linear > spread 8 arsitektur di **semua** situs, dan signifikan di semua situs: model nonlinear menambah lebih banyak di atas regresi linear daripada perbedaan di antara mereka sendiri. Klaim "dibatasi informasi, bukan arsitektur" dipersempit menjadi "bukan pilihan **di antara arsitektur nonlinear**", di abstrak, diskusi, dan kesimpulan.
  - **(T2)** Bila tidak: regresi linear sudah mencapai sebagian besar skill, sehingga klaim yang ada diperkuat dan tidak dipersempit.
- **Abstrak:** hanya disesuaikan menurut T1/T2. Angka skill tidak ditambahkan; batas kata dan kalimat angka R² di akhir abstrak tetap.

## Ekspektasi (sebelum hasil)
Dari audit (definisi langit cerah lama): ridge R² 0,79–0,88 vs model terbaik 0,85–0,91, jadi kemungkinan T1. Spread skill antar-arsitektur diperkirakan beberapa kali spread R². Hasil dilaporkan apa adanya.

## Implementasi
`60_skill_linear.py` → `60_skill_linear/`. Runner `run_rerun_P2.py` menjalankannya sebelum 49. Registri: folder ini masuk cek kesegaran C5.
