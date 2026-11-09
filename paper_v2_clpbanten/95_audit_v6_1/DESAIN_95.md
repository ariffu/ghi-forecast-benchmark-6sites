---
tags: [disertasi, prediksi-radiasi, audit, clpbanten-v2]
created: 2026-11-08
status: "DESAIN — dikunci sebelum uji dijalankan"
---

# Tahap 95 — audit ulang komprehensif database V6.1

Sasaran: `C:\Users\ariff\Documents\Balai_data_v6_1` (beku, hanya-baca). Audit ini hanya membaca. Temuan yang menuntut perubahan data dicatat untuk versi berikutnya (V6.2); V6.1 tidak diubah. Tidak ada model yang dilatih, dan tidak ada keputusan data yang diambil dari skor model.

Koordinat Stasiun Klimatologi Bengkulu dari pengguna (2026-11-08): **−3,864930; 102,311998**.

## Kriteria dan rujukan

| Kode | Uji | Kriteria | Rujukan |
|---|---|---|---|
| S1 | Struktur | grid 10 menit lengkap 2022–2025, unik, urut; hash cocok `SHA256.txt`; `clearsky/` dan `qc/` sejajar dengan `00_data` | kaidah dataset |
| S2 | Posisi matahari | `solar_elev_deg` dicocokkan dengan pvlib (SPA) untuk mencari koordinat dan acuan waktu yang dipakai | Reda & Andreas (2004) |
| S3 | Koordinat | jarak metadata (Tabel 1), clear-sky, pusat kotak CLP, dan koordinat pengguna; dampak koordinat Bengkulu baru pada clear-sky | — |
| R1 | Batas fisis dan neraca | PPL, ERL, neraca ±8%/±15%, rasio difus, per stasiun × tahun × kode asal | Long & Shi (2008); Long & Dutton (2010) |
| R2 | Malam | nilai GHI/DHI/DNI saat elevasi < 0 (offset termal) | Long & Shi (2008) |
| R3 | Peningkatan awan | sebaran k_c > 1; k_c 10 menit > 1,3 dianggap mencurigakan | Gueymard (2017); Yordanov et al. (2013) |
| R4 | Kecocokan clear-sky | median k_c periode cerah per elevasi; Linke yang membuat k_c cerah = 1 dibanding Linke Remund | Ineichen (2006); Remund et al. (2003) |
| R5 | Lama penyinaran | menit penyinaran slot terhadap DNI > 120 W m⁻² | WMO CIMO Guide (WMO-No. 8) |
| R6 | Albedo | reflected/GHI siang cerah 0,1–0,3; stabil antartahun | — |
| R7 | Fraksi difus | k_d terhadap k_t di luar selubung fisis (k_t > 0,7 dengan k_d > 0,6; k_t < 0,2 dengan k_d < 0,8) | Erbs et al. (1982); Engerer (2015) |
| R8 | Total harian | GHI harian rata-rata per tahun 3,5–6 kWh m⁻² hari⁻¹ untuk Indonesia | — |
| R9 | Radiasi neto | malam negatif; siang ≤ GHI | — |
| C1 | Satelit | identitas satelit dari nama berkas cocok jadwal JMA (H09 sejak 13 Des 2022 05 UTC; H08 12 Okt–26 Nov 2025) | JMA |
| C2 | Ketersediaan | slot tanpa berkas per jam UTC (02.40 dan 14.40 = housekeeping) | JMA |
| C3 | Rentang fisis | COT 0–150, CTT 180–315 K, CTH 0–20 km, CER 0–100 µm; laju CTT–CTH ≈ 6–7 K km⁻¹ | JAXA CLP; atmosfer baku |
| C4 | Agregasi kotak | apakah COT kotak = rata-rata piksel berawan saja; fraksi awan (count/total) ada di sumber tetapi tidak di database | — |
| C5 | Zenit matahari | proporsi retrieval COT/CER pada SZA > 70° (retrieval bispektral tidak andal di matahari rendah) | Nakajima & King (1990); Grosvenor et al. (2018) |
| C6 | Geometri pandang | sudut zenit satelit dan pergeseran paralaks h·tan(VZA) per stasiun | — |
| C7 | Konsistensi silang | CTH lawan jenis awan SYNOP (CL/CM/CH); fraksi awan lawan okta | WMO-No. 306 |
| M1 | Meteorologi AWS | batas WMO dan uji langkah; suhu, RH, tekanan, angin, hujan | WMO-No. 8; Zahumenský (2004) |
| M2 | Titik embun | Td ≤ T; RH dari T dan Td (Magnus) cocok dengan RH SYNOP | Alduchov & Eskridge (1996) |
| M3 | Tekanan | tekanan rata-rata sesuai ketinggian stasiun (hipsometrik); pasang S2 amplitudo ≈ 1–1,5 hPa, puncak ≈ 10 dan 22 LST | Dai & Wang (1999) |
| M4 | Hujan–radiasi | hujan > 0 pada jam dengan k_c > 0,9 | — |
| M5 | Aerosol | asal dan rentang `aod_500nm`, `angstrom_exp` | — |

Keluaran: CSV per kelompok dan `RINGKASAN_95.md`.
