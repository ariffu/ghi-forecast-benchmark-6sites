---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — Balai_data_v6_4 BEKU 2026-11-08 (SHA256, hanya-baca, 40 berkas); database aktif untuk running uji"
---

# Tahap 100 — ringkasan: V6.4, meteorologi beracuan SYNOP

Desain: [[DESAIN_100]]. Skrip:
- `j1_banding_bulanan.py`: diagnosis V6.3.
- `j2_bangun_v64.py`: build, termasuk uji kausalitas tiga titik potong per stasiun.
- `j3_banding_v64.py`: diagnosis ulang.
- `j4_validasi.py`.

README database: `C:\Users\ariff\Documents\Balai_data_v6_4\README.md`.

## Temuan yang diperbaiki

- **Satuan angin Banten:** 7.795 slot jam laporan berisi angin SYNOP dalam knot di kolom m/s. Kini 0.
- **Konvensi tekanan:**
  - SYNOP Banten, Bengkulu, Kalbar, dan Jawa Tengah = QFF; Yogyakarta = QFE.
  - AWS Jambi ternyata QFF, bukan tekanan sensor. Seluruh deret Jambi digeser −2,76 hPa (hipsometrik, h = 24 m).
  - Sisipan QFF di jam laporan di stasiun lain diganti tekanan setara sensor.
- **Drift dan kerusakan sensor**, dikoreksi bias kausal 7 hari terhadap SYNOP atau diisi SYNOP per minggu:
  - tekanan Yogyakarta Apr 2024 – Des 2025;
  - suhu Kalbar Mar 2024 – Des 2025;
  - Kalbar rusak sejak akhir Nov 2025;
  - RH Jawa Tengah Jul–Sep 2022 dan RH Yogyakarta Agu–Des 2025;
  - anemometer Jawa Tengah Des 2022;
  - arah Jawa Tengah 2022–2025;
  - Bengkulu Mei 2022.

## Dua kesalahan yang ditemukan dan dibetulkan selama build

1. Slot yang sudah berasal dari SYNOP (rekonstruksi kausal V6) ikut dikoreksi dengan bias yang ditaksir dari segelintir slot logger, sehingga rasio angin Jambi menjadi sekitar 1,9. Kini slot SYNOP tidak dikoreksi.
2. Slot sisipan (isi = SYNOP) ikut digeser oleh bias, sehingga suhu Jambi Nov–Des 2025 menjadi SYNOP + 2,1 °C. Kini slot sisipan tidak dikoreksi.

## Hasil

- **Bulan menyimpang dari SYNOP:** 96 → 7 (suhu 24 → 0, RH 11 → 0, tekanan 27 → 1, angin 25 → 5, arah 9 → 1). Sisa angin: rasio 1,3 di Kalbar dan Jawa Tengah pada bulan-bulan dengan banyak laporan tenang SYNOP.
- Siklus harian suhu dan pasang S2 tetap wajar. RH 0–100, angin ≥ 0.
- Hanya 14–18 kolom meteorologi AWS yang berubah. `clearsky`, `qc`, dan `clp_ekstra` identik dengan V6.3.
- `_common.prepare` P2F: 44 prediktor di keenam stasiun; baseline tidak berubah.

## Catatan

- Angin AWS kini di level SYNOP (10 m, standar WMO), bukan level sensor AWS asli. Faktor koreksi tercatat di `met_bias_angin`.
- Banten: slot logger suhu/RH sedikit (sebagian besar deret dari SYNOP), sehingga bias logger kadang tidak tertaksir (median residu bulanan sampai 0,53 °C dan 3,5%).
