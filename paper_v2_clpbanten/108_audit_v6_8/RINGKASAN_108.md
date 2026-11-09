---
tags: [disertasi, prediksi-radiasi, audit, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — V6.8 CLEAR untuk running uji: radiasi, CLP, dan meteorologi lolos fisis dan siklus harian; hanya hujan yang berubah, dan membaik"
---

# Tahap 108 — audit komprehensif V6.8 sebelum running

Sasaran: `Balai_data_v6_8` (hanya dibaca). Skrip:
- `u0_salin_uji.py`: menyalin seluruh rangkaian uji tahap 95–106 (struktur, radiasi, satelit, meteorologi, lompatan, ketersediaan, SYNOP bulanan, kebocoran, siklus harian `p1_diurnal`).
- `u1_hujan_fisis.py`: uji fisis hujan baru.

Pembanding: audit V6.7 (tahap 106).

## Identik dengan V6.7 (lolos)

- **Struktur:** 39 berkas cocok dengan SHA256.
- **Radiasi** R1–R9 dan rinciannya: batas BSRN, neraca, clear-sky, peningkatan awan, albedo, total harian, radiasi neto.
- **Satelit CLP** C1–C7: jadwal Himawari, ketersediaan, rentang dan laju CTT–CTH, agregasi, zenit, paralaks, silang SYNOP. Fraksi awan H1–H3 juga identik.
- **Meteorologi:**
  - K1–K4, O1–O5;
  - 0 lompatan dan 100% ketersediaan;
  - titik embun, antikorelasi suhu–RH, S2;
  - siklus harian logger, SYNOP as-of, arah tanpa arah.
- **Bulan menyimpang dari SYNOP:** 6.

## Siklus harian (waktu matahari semu)

Semua sesuai literatur:
- k_c pagi > sore;
- awan dan CTH naik sore;
- suhu maks 13–14, min sekitar 06;
- RH kebalikan suhu;
- S2 puncak sekitar 09 dan 22.30;
- angin maks 13–15, dengan putaran darat–laut Bengkulu 159° dan Jawa Tengah 174°;
- visibilitas minimum 05.00;
- **hujan puncak 15–21 AST di keenam stasiun** (Yogyakarta 07 → 16).

Pengecualian yang sudah dijelaskan:
- Puncak GHI dan minimum k_d Banten lebih pagi karena awan sore; di hari cerah GHI memuncak 12.07.
- Puncak tekanan pagi Yogyakarta 08.30 (batas 09.00), karena tumpang-tindih S1 dan S2.

## Hujan (satu-satunya yang berubah dari V6.7, dan membaik)

- **Jam hujan dengan k_c > 0,9:** Yogyakarta 10,3% → 3,9%. Stasiun lain tetap 1,6–5,4%.
- **Kebocoran:** prediktor hujan berkorelasi paling kuat dengan k_c pada t−10 sampai t−30, artinya hanya masa lalu.
- **Hujan logger dan fisika** (`U1_hujan_fisis.csv`):
  - k_c saat hujan median 0,06–0,14.
  - Saat hujan: fraksi awan CLP 0,83–0,96, COT 22–33, CTH 10–12 km. Saat kering: 0,56–0,75, sekitar 4, dan 5–9 km.
  - RH saat hujan 85–99% (kering 80–90%).
  - Intensitas maksimum 18–29 mm per 10 menit; tidak ada nilai negatif.
  - Kode cuaca SYNOP presipitasi disertai hujan AWS 60 menit terakhir di 57–78% laporan; kode tanpa presipitasi tetapi AWS > 1 mm hanya 0,6–2,3%.
  - Total tahunan 1.443–3.776 mm, terendah 2023 (El Niño).

## Catatan untuk naskah

- **Isian maju kausal** di celah logger (Yogyakarta 15.844 slot, Jawa Tengah 8.140 slot) sering jatuh di jam cerah (k_c median 0,43–0,49), karena laju hujan periode SYNOP terakhir diteruskan ke depan. Itu harga kausalitas.
- **Resolusi hujan Yogyakarta** bukan kelipatan 0,2 mm (hanya 35% slot logger), berbeda dari penakar 0,2 mm di stasiun lain (88–100%).
- **Catatan lama tetap berlaku:** pergeseran sumber per split (Bengkulu tekanan/angin; Kalbar suhu uji), rambat malam halus, okta Jambi janggal, okta/CM/CH Yogyakarta 2022–2023 kosong.

## Kesimpulan

**V6.8 clear untuk running uji.** Pipeline: `DATA_DIR`/`CLEARSKY_DIR`/`CLP_EKSTRA_DIR` di `Balai_data_v6_8`, `FEATSET=P2F` (44 prediktor).
