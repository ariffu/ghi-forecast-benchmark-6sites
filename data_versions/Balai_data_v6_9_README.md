# Database Versi 6.9 (tahap 109) — BEKU 2026-11-08

Dibangun dari `Balai_data_v6_8` (tidak diubah). Satu perbaikan: okta (N), CM, CH SYNOP Yogyakarta yang hilang di database diisi dari berkas SYNOP Stasiun Klimatologi DI Yogyakarta (Mlati) 2022–2025 dari pengguna (`synop staklim mlati 22-25.csv`). Laporan: `solardata_new_v2/paper_v2_clpbanten/109_synop_awan/RINGKASAN_109.md`; skrip `v2_bangun_v69.py`.

## Perubahan terhadap V6.8

- **Yang diubah:** `synop_cloud_cover_oktas`, `synop_cm`, `synop_ch` Yogyakarta. Laporan yang sebelumnya kosong diisi dari berkas: okta 11.799, CM 11.827, CH 11.611 laporan, terutama 2022 – pertengahan 2024.
- **Konflik:** nilai database yang sudah ada dipertahankan. Database dan berkas sama 99,9%; konflik hanya 2–7 laporan.
- **As-of:** nilai laporan berlaku 60 menit (aturan V6.6).
- **Origin terisi:** okta 91,6–91,8%, CM 91,4–91,8%, CH 78,9–90,6% di setiap tahun. Kekosongan di tahun latih turun dari 100% menjadi 8–10%, setara stasiun lain. Sisanya 06.30–06.50 (laporan pertama 07.00) dan CH yang tidak teramati.
- **Siklus harian okta:** 4,9 (08 WIB) naik ke 6,0 (17 WIB).
- **Provenance baru:** `synop_awan_dari_berkas`.
- **Kolom dan stasiun lain** identik dengan V6.8.

Catatan cek okta Jambi (tahap 109): database = sumber 100%. Puncak okta pagi berasal dari stratokumulus pagi (CL = 5), jadi fisis; catatan "janggal" sebelumnya ditarik.

## Cara memakai

```
DATA_DIR=C:\Users\ariff\Documents\Balai_data_v6_9\00_data
CLEARSKY_DIR=C:\Users\ariff\Documents\Balai_data_v6_9\clearsky
CLP_EKSTRA_DIR=C:\Users\ariff\Documents\Balai_data_v6_9\clp_ekstra
FEATSET=P2F
```

44 prediktor. Semua isi, audit (tahap 108), dan catatan README V6.8 tetap berlaku.
