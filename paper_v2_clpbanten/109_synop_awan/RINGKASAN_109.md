---
tags: [disertasi, prediksi-radiasi, audit, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — Jambi sesuai sumber; Yogyakarta okta/CM/CH diisi dari berkas pengguna di Balai_data_v6_9 (BEKU 2026-11-08, database aktif untuk running uji)"
---

# Tahap 109 — cek okta, CL, CM, CH SYNOP Jambi dan Yogyakarta

Berkas pengguna: `Downloads\synop staklim jambi 22-25.csv` (35.006 laporan, per jam, 24 jam) dan `Downloads\synop staklim mlati 22-25.csv` (18.993 laporan, 07–19 WIB). Skrip `v1_cek_okta.py`, keluaran `log_v1.txt` dan `v1_synop_awan_{jambi,jogja}.parquet` (tanpa nama pengamat).

Waktu berkas UTC + 7 = slot WIB database. Kolom berkas: N = `cloud_cover_oktas_m`; CL, CM, CH = `cloud_*_type_*`. Nilai N di berkas cocok dengan sandi SYNOP mentah (Nddff) 100%.

## Jambi: database sudah benar

- **Kecocokan:** N di database = berkas 100% (34.965 laporan); CL, CM, CH 99,5–99,9%.
- **Puncak okta pagi itu fisis, bukan galat.** Okta rata-rata 6,3–6,9 sepanjang hari, tertinggi 06–07 WIB.
  - Pagi (05–07 WIB): CL = 5 (stratokumulus) mendominasi (3.357 dari sekitar 4.400 laporan), sehingga ada lapisan stratokumulus pagi.
  - Siang: CL = 2, 1, 8 (kumulus konvektif).
  - Ini sejalan dengan CLP Jambi yang fraksi awannya tinggi pada 09–10 WIB.
- Catatan "pengodean okta Jambi janggal" (tahap 91, 106) **ditarik**. Okta 0 hanya 58 laporan dalam 4 tahun, sehingga hubungan okta–fraksi CLP di kelas itu tidak bermakna.

## Yogyakarta: database kehilangan data

| | Berkas pengguna | Database V6.8 |
|---|---|---|
| N (okta) terisi 2022 / 2023 / 2024 / 2025 | 99,5 / 99,9 / 99,9 / 100% | **0 / 0 / 51** / 100% |
| CM | 100 / 100 / 99,8 / 99,4% | **0 / 0 / 51** / 99,4% |
| CH | 98 / 98 / 93 / 84% | **0 / 0 / 45** / 84% |
| CL, ww, visibilitas | lengkap | lengkap, sama |

- Di laporan yang ada di keduanya, nilai sama 99,9–100%. Data 2022 – pertengahan 2024 hilang saat ingest database, bukan karena tidak diamati.
- Siklus harian okta Yogyakarta dari berkas: 4,9 (08 WIB) naik ke 6,0 (17 WIB), sesuai konveksi sore.

## Usulan V6.9

1. Isi `synop_cloud_cover_oktas`, `synop_cm`, `synop_ch` Yogyakarta di jam laporan dari berkas pengguna. Nilai yang sudah ada tidak berubah, karena memang sama.
2. Terapkan as-of 60 menit seperti V6.6.

Hanya tiga kolom Yogyakarta yang berubah. Akibatnya ketiga prediktor ini bisa dipelajari model di tahun latih (sebelumnya kosong 100%).

## Hasil V6.9 (`v2_bangun_v69.py`, `v2_laporan.json`)

- **Laporan Yogyakarta yang diisi dari berkas:** okta 11.799, CM 11.827, CH 11.611. Konflik dengan database hanya 6/7/2 laporan; nilai database dipertahankan.
- **Origin terisi:** okta 91,6–91,8% dan CM 91,4–91,8% di setiap tahun; CH 78,9–90,6%. Kekosongan tahun latih kini 8–10% (sebelumnya 100%).
- **Siklus harian okta:** 4,9 (08 WIB) naik ke 6,0 (17 WIB).
- **Validasi:** hanya tiga kolom Yogyakarta yang berubah; pipeline P2F berjalan dengan 44 prediktor; baseline tidak berubah.
