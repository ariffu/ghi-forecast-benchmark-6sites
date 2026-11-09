---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — Balai_data_v6_6 BEKU 2026-11-08; meteorologi mulus (0 lompatan), lengkap (100% origin), kausal; database aktif untuk running uji"
---

# Tahap 103 — ringkasan: V6.6, meteorologi mulus dan lengkap

Desain: [[DESAIN_103]] dengan amandemen 1. Skrip:
- `n1_audit_v65.py`: diagnosis.
- `n2_bangun_v66.py`: build dan uji kausalitas.
- `n3_audit_v66.py`: lompatan, ketersediaan, identik, pipeline.
- `n4_banding_v66.py`: SYNOP bulanan.
- `n5_h1_cek.py`: kebocoran.

README database: `C:\Users\ariff\Documents\Balai_data_v6_6\README.md`.

## Hasil

| Syarat | Hasil |
|---|---|
| 0 lompatan di atas ambang (suhu 2 °C, RH 10%, tekanan 1 hPa, angin 5 m/s) | **lolos**: 0 di 24 deret; maksimum per 10 menit 1,5 / 7,5 / 0,5 / 3,0 |
| Ketersediaan meteorologi AWS ≥ 99,9% | **lolos**: 100% slot sesudah pengamatan pertama; arah Kalbar 0 → 99,99%; arah Jawa Tengah 87 → 99,99% |
| Kolom SYNOP terisi bila ada laporan ≤ 60 menit | **lolos**: origin 16% → 92–100%; okta/CM/CH Yogyakarta 2022–2023 tetap kosong (tidak ada laporan) |
| Kausalitas | **lolos** (3 titik potong × 6 stasiun) |
| Bulan menyimpang dari SYNOP ≤ V6.5 | **lolos** (6 = 6) |
| Radiasi/CLP identik | **lolos** |
| Pipeline P2F | **lolos** (44 prediktor) |

## Komposisi mode

- Banten suhu/RH: 54% koreksi SYNOP dan 46% rambat malam (tanpa logger sehat).
- Jambi: 99,9% koreksi SYNOP (laporan 24 jam).
- Bengkulu tekanan/angin: 63–70% logger.
- Stasiun lain: 88–99,8% logger.

## Harga kemulusan

Laporan SYNOP diserap dalam 60 menit, dan perubahan > batas laju dibagi ke beberapa slot. Akibatnya, RMSE terhadap laporan saat itu naik di stasiun yang deretnya berasal dari SYNOP:
- Banten: suhu 0,18 → 0,80 °C, RH 0,6 → 4,1%.
- Jambi: suhu 0,03 → 0,52 °C, RH 0 → 2,6%, tekanan 0,06 → 0,30 hPa, angin 0 → 0,56 m/s.

Di stasiun logger kenaikannya kecil (suhu ≤ 0,07 °C, RH ≤ 0,3%, tekanan ≤ 0,07 hPa). Mengurangi harga ini berarti menerima lompatan di jam laporan, atau memakai interpolasi yang bocor.

## Catatan

- Rambat malam Banten (sampai sekitar 12 jam tanpa pengamatan) hanya siklus harian klimatologis; dipakai oleh fitur lag/rolling di origin pagi.
- Kekosongan di origin uji yang tersisa (> 1%) bukan meteorologi AWS: CLP (tidak ada berkas atau retrieval) 7,5–8,5%, CER 12–16%, turunan k_c, dan kolom SYNOP 06.30–06.50.
