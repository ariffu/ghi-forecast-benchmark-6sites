---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — Balai_data_v6_2 beku (SHA256, hanya-baca, 39 berkas, 878 MB); Manuskrip V6 belum dibangun"
---

# Tahap 96 — ringkasan: database V6.2

Desain: [[DESAIN_96]] (dengan amandemen 1). Audit dasar: [[RINGKASAN_95]]. Skrip `f1_bangun_v62.py` (build) dan `f2_validasi.py`. Laporan build `f1_laporan.json`, validasi `f2_validasi.csv`. V6.1 tidak diubah.

## Perbaikan

| No | Perbaikan | Hasil |
|---|---|---|
| F1 | Clear-sky dan QC Bengkulu dengan koordinat −3,864930; 102,311998 | Rasio clear-sky baru/lama median 1,0006 (0,969–1,031). 81 slot QC Bengkulu berubah kode (fajar/senja dan uji neraca). |
| F2 | `clp_ekstra/`: fraksi awan, zenit pindai, bendera SZA | Median fraksi awan siang 0,58 (Jawa Tengah) sampai 0,76 (Jambi). Saat COT ada, fraksi selalu ≥ 1/121; saat COT kosong di siang hari, fraksi 0. Bendera: sekitar 79.000 slot < 70°, 12.100–12.400 slot 70–80°, 13.500–14.100 slot ≥ 80° per stasiun. |
| F3 | Lonjakan dan blok tekanan 1–6 slot dikosongkan | Lihat tabel di bawah. |
| F4 | `qc_uji` bit 8: k_d < 0,1 (elevasi > 30°, GHI > 300) | Bengkulu 1.742 slot (854 nilai ukur, 888 hasil neraca; 2025 terbanyak, 847), Kalbar 331, Yogyakarta 59, Banten 49, Jawa Tengah 44, Jambi 15. |
| F5 | README dengan catatan audit | Selesai. |

Tekanan yang dikosongkan (sama di `00_data` dan `00_data_rawfill`):

| Stasiun | Slot | Satu slot | Blok 2–6 slot | % siang | Tahun terbanyak |
|---|---|---|---|---|---|
| Banten | 1.928 | 435 | 1.493 | 1,60 | 2023 (1.698) |
| Bengkulu | 5.300 | 1.194 | 4.106 | 4,68 | 2024 (2.692), 2025 (2.550) |
| Kalbar | 918 | 360 | 558 | 0,86 | 2022 (727) |
| Jawa Tengah | 259 | 71 | 188 | 0,02 | 2022–2023 |
| Jambi | 54 | 20 | 34 | 0,02 | 2022 |
| Yogyakarta | 42 | 13 | 29 | 0,03 | 2024 |

Lonjakan Bengkulu hanya terjadi pukul 07–19, kira-kira ±2,2 hPa per slot, terutama 2024–2025. Pola ini menunjukkan gangguan logger atau pencampuran sumber, bukan cuaca. Hanya 42 slot dikosongkan di dua stasiun sekaligus. Masih tersisa blok yang lebih panjang dari 60 menit (misalnya Banten dan Bengkulu 10 Jun 2022, keduanya naik sekitar 3,4 hPa); sesuai desain, blok seperti itu tidak dibuang.

## Validasi

- Di `00_data` dan `00_data_rawfill` hanya tiga kolom tekanan yang berubah. Nilai tekanan yang tersisa identik dengan V6.1.
- `provenance` = V6.1 ditambah `aws_lonjakan_tekanan` (jumlahnya cocok). Clear-sky berubah hanya di Bengkulu. Bit 0–7 QC identik dengan V6.1 di lima stasiun lain.
- `_common.prepare` dengan V6.2 berjalan di keenam stasiun: 43 prediktor. Jambi base_mean 376,001 (sama dengan V6.1, karena tidak ada perubahan radiasi di Jambi).

## Dampak pada naskah

- Prediktor tekanan (`aws_pressure_hpa`, `aws_pressure_delta_60m`) kini lebih bersih, terutama di Bengkulu dan Banten. Angka model akan sedikit berbeda dari V6.1.
- Fraksi awan belum menjadi prediktor. Memakainya mengubah protokol P2, jadi harus diputuskan sebelum pelatihan.
- Tabel 1: koordinat Bengkulu dan Jambi harus diganti.
