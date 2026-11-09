---
tags: [disertasi, prediksi-radiasi, audit, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — V6.10 CLEAR untuk running uji (teknik dataset, fisis, siklus harian lolos); sisa minor: 53 slot DNI mustahil dan 71 slot albedo > 0,5"
---

# Tahap 112 — audit komprehensif V6.10

Sasaran: `Balai_data_v6_10` (hanya dibaca). Skrip:
- `y0_salin_uji.py`: menyalin seluruh rangkaian uji tahap 95–110.
- `y1_teknik_dataset.py`: uji teknik dataset baru (D1–D8).

Pembanding: audit V6.9.

## Teknik dataset (`y1`, D1–D8)

| Uji | Hasil |
|---|---|
| D1 skema | 124 kolom, nama dan tipe identik di 6 stasiun × 2 varian |
| D2 kunci waktu | 210.384 baris per stasiun, unik, urut, langkah tepat 10 menit, WIB tanpa zona, 2022-01-01 00.00 – 2025-12-31 23.50; `site_id` benar |
| D3 kolom kosong/konstan/duplikat | Hanya kolom non-prediktor: `sunshine_*`, `aod_500nm`, `angstrom_exp` kosong di sebagian stasiun; `has_source_row` konstan; duplikat `kt_std_1h` = `kt_roll_60m_std`, `ghi_cs_t60` = `clear_sky_ghi_h1`, `smart_persist` = `smart_persist_h1`. Tidak ada yang masuk 44 prediktor. |
| D4 rentang fisis | 14 slot di luar batas: DNI 1.375–1.396 W m⁻² saat matahari < 5° (Kalbar 2, Jawa Tengah 1), DHI Jambi 1.000–1.039 (8, puncak peningkatan awan dengan GHI 1.005–1.212), reflected Banten 555–564 (2), nett Kalbar −207 (1, malam) |
| D5 turunan dan target | 100% konsisten: `ghi_actual_h1/h6` = GHI(t+60/t+360); lag, delta, rolling GHI/k_c/CLP/hujan/suhu; `clear_sky_ghi_h1` = cs(t+60); `clp_cloud_present_int` = COT ≥ 1 |
| D6 rawfill | Beda dari `00_data` hanya di 9 kolom CLP, sesuai konvensinya |
| D7 split | Latih ≤ 2023, validasi 2024, uji 2025; tidak tumpang-tindih; tidak ada target latih yang masuk 2024; tidak ada prediktor salinan target (kesamaan atau r > 0,995) |
| D8 jejak versi | V6 – V6.10 semua beku dengan SHA256, README, dan hanya-baca |

**Batas fisis yang lebih tepat** (selubung atmosfer sangat bersih, Ineichen Linke 2, +10%): DNI yang benar-benar mustahil hanya **53 slot** dari 4 tahun × 6 stasiun (16 di origin), kebanyakan saat matahari < 5°, karena DNI = (GHI − DHI)/sin h meledak. DNI di atas clear-sky Ineichen (204–1.709 slot) sebagian besar akibat bias Linke Remund (tahap 95), bukan galat. Albedo > 0,5 saat GHI > 200 hanya 71 slot (Kalbar 45).

## Fisis dan siklus harian (rangkaian uji lama)

- **Identik dengan V6.9:**
  - struktur, radiasi R1–R9, satelit C1–C6;
  - meteorologi M1–M5/K1–K4/O1–O4: 0 lompatan, 100% terisi, Td ≤ T, antikorelasi suhu–RH, S2, siklus harian logger;
  - fisis hujan, sensor macet.
- **Yang berubah hanya baris okta Banten dan Bengkulu**, sesuai perbaikan V6.10:
  - **Spearman okta–fraksi awan CLP:** Banten 0,33 → **0,68**, Bengkulu 0,48 → **0,69**; fraksi kini naik monoton dari 0,1 (okta 0) ke 0,94–0,97 (okta 8).
  - **Puncak okta harian:** 17 AST di lima stasiun; Jambi 07 (stratokumulus pagi, tahap 109).
  - **Okta keenam stasiun tanpa kebocoran:** korelasi dengan k_c memuncak pada t−30.
- **Siklus harian semua variabel** tetap sesuai literatur (tahap 106/108): k_c pagi > sore; awan, CTH, dan hujan sore; suhu, RH, S2, angin, angin darat–laut, visibilitas.

## Kesimpulan

**V6.10 clear untuk running uji.** Sisa minor (opsional): 53 slot DNI mustahil dan 71 slot albedo > 0,5 bisa dikosongkan di versi berikutnya. Dampaknya diabaikan, karena hanya 16 origin, dan bendera `qc_uji` sudah menandai sebagian.
