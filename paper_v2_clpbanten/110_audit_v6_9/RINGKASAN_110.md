---
tags: [disertasi, prediksi-radiasi, audit, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — V6.9 lolos semua uji; temuan baru: okta Banten dan Bengkulu = Nh (awan rendah), bukan N (tutupan total); usulan V6.10"
---

# Tahap 110 — audit komprehensif V6.9

Sasaran: `Balai_data_v6_9` (hanya dibaca). Skrip:
- `w0_salin_uji.py`: menyalin seluruh rangkaian uji tahap 108, yaitu struktur, radiasi, satelit, meteorologi, lompatan, ketersediaan, SYNOP bulanan, kebocoran, siklus harian, dan fisis hujan.
- `w1_synop_awan_jogja.py`: uji baru kolom awan SYNOP.

Pembanding: audit V6.8.

## Lolos

- **Identik dengan V6.8:** struktur (39 berkas), radiasi R1–R9, satelit C1–C6, meteorologi M1–M5/K1–K4/O1–O4, lompatan, siklus harian, fisis hujan.
- **Yang berubah hanya baris Yogyakarta** di C7, H4, H5, O5, dan ketersediaan, sesuai perbaikan V6.9.
- **Okta Yogyakarta tanpa kebocoran:** korelasi dengan k_c memuncak pada t−30, artinya masa lalu.
- **Okta Yogyakarta homogen antartahun** (`W1_synop_awan.csv`):
  - rata-rata 5,0–5,8 (2023 terendah, El Niño);
  - korelasi okta–k_c −0,60 sampai −0,64, sama di tahun dari berkas (2022–2023) dan dari database (2025);
  - korelasi okta–fraksi CLP 0,50–0,76.

## Temuan baru: okta Banten dan Bengkulu bukan tutupan awan total

- **Gejala:** rata-rata `synop_cloud_cover_oktas` Banten 2,0–2,4 dan Bengkulu 2,4–2,6, dengan okta 8 hanya 0,0–0,2%. Stasiun lain 5,2–6,5. Korelasi dengan k_c juga lemah (−0,18 sampai −0,44 lawan −0,49 sampai −0,66).
- **Sebab:** database mengambil `cloud_low_cover_oktas` (Nh, jumlah awan rendah), bukan `cloud_cover_oktas_m` (N, tutupan total). Kecocokan dengan Nh 100%; dengan N hanya 2–3%.
- **N tersedia di sumber, terisi 100%:**
  - Banten: `banten.synoppondokbetung`, Stasiun Klimatologi Banten/Tangerang Selatan, rata-rata 6,01.
  - Bengkulu: `bengkulu.synop_bengkulu_quality_final`, rata-rata 6,06.
- **Stasiun lain** sudah memakai N (Kalbar, Jawa Tengah, Jambi, Yogyakarta; cocok 100%).
- **Akibatnya,** prediktor P2 `synop_cloud_cover_oktas` tidak sebanding antarstasiun, dan di Banten/Bengkulu informasinya lebih lemah.

## Usulan V6.10

`synop_cloud_cover_oktas` Banten dan Bengkulu diganti N (`cloud_cover_oktas_m`) di jam laporan, lalu as-of 60 menit (aturan V6.6). Kolom lain tidak berubah.
