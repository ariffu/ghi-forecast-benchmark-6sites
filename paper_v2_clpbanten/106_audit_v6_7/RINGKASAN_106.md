---
tags: [disertasi, prediksi-radiasi, audit, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — V6.7 lolos fisis, literatur, dan siklus harian, kecuali artefak hujan 07.00 Yogyakarta (dan kecil Bengkulu); usulan V6.8"
---

# Tahap 106 — audit komprehensif V6.7 (fisis, literatur, siklus harian)

Sasaran: `Balai_data_v6_7` (hanya dibaca). Skrip:
- `r0_salin_uji.py`: menyalin seluruh rangkaian uji tahap 95–104, yaitu `e1`–`e4b`, `h2`, `k1_meteo_v67`, `r1_khusus_v67`, `r3_audit_v67`, `r4_banding_v67`, `r5_h1_cek`.
- `p1_diurnal.py`: audit siklus harian baru.

Keluaran: CSV dan `log_*.txt`.

## Rangkaian uji lama: lolos, identik dengan V6.6

- Struktur dan hash (39 berkas).
- Radiasi R1–R9 dan satelit C1–C7.
- Meteorologi M1–M5: 0 langkah, 100% terisi, dalam batas WMO; Td ≤ T; S2.
- Fisis K2, siklus harian logger O4, SYNOP as-of O5.
- 0 lompatan, 100% ketersediaan, 44 prediktor, bulan menyimpang SYNOP 6.
- Tanpa kebocoran.
- Satu-satunya beda (O1): sin/cos = 0 di slot tanpa arah, sesuai desain tahap 105.
- Sensor macet: arah angin tidak lagi datar. Yang tersisa hanya hujan kecil Yogyakarta 2022 dan RH jenuh Kalbar 2023.

## Siklus harian terhadap literatur (`P1_diurnal.csv`, waktu matahari semu AST)

| Variabel | Harapan literatur | Hasil |
|---|---|---|
| GHI | puncak dekat 12.00 AST | 11.30–12.00 di lima stasiun. Banten 10.30, karena awan sore kuat (k_c pagi 0,72 lawan sore 0,56); **di hari cerah Banten memuncak 12.07**, jadi jam benar. GHI mulai > 5 W m⁻² tepat saat matahari terbit (selisih 0 menit). |
| k_c | pagi > sore di darat tropis (Yang & Slingo 2001; Mori et al. 2004; Qian 2008) | lolos di keenam stasiun (pagi 0,71–0,80, sore 0,56–0,75) |
| Fraksi difus | minimum dekat siang; sore ≥ pagi | lolos, kecuali minimum Banten 09.00 (awan sore) |
| Fraksi awan, COT CLP | maksimum siang–sore | naik sampai sore (puncak di batas 16.30–17.00 AST) di keenam stasiun; CTH sore > pagi di keenam stasiun |
| Okta SYNOP | maksimum siang–sore | lolos, kecuali Jambi 07.00 (pengodean okta Jambi janggal sejak tahap 91) |
| Hujan | puncak 13–21 AST di darat (Mori 2004; Qian 2008; Yamanaka 2016) | Banten 15, Bengkulu 17, Jambi 16, Kalbar 21, Jawa Tengah 19 lolos. **Yogyakarta 07** — artefak, lihat temuan. |
| Suhu | maks 12–15, min 04–07, amplitudo 4–10 °C | maks 13–14, min 05.30–06.00, amplitudo 5,7–7,1 °C |
| RH | kebalikan suhu | min 12.30–14.00, maks 05.30–07.30 |
| Tekanan | S2 puncak sekitar 10 dan 22, lembah sekitar 04 dan 16 (Dai & Wang 1999) | puncak 08.30–09.00 dan 22.00–23.00, lembah 03.30–04.00 dan 15.00–15.50; puncak pagi sedikit lebih awal karena tumpang-tindih dengan S1 |
| Kecepatan angin | maks 11–17, min malam | maks 13.00–15.00, min 02.30–06.30 |
| Arah angin | sirkulasi darat–laut di pesisir | Bengkulu siang 231° (dari laut barat daya), malam 72° (dari darat), putaran 159°. Jawa Tengah siang 332° (dari Laut Jawa), malam 158°, putaran 174°. Yogyakarta siang 241° (angin laut dari selatan-barat daya), putaran 96°. Jambi (pedalaman) 47°; Banten tidak berputar. |
| Visibilitas | minimum pagi | minimum 05.00 di keenam stasiun |

## Temuan

**Hujan 07.00 Yogyakarta adalah akumulasi, bukan hujan 10 menit.**
- Slot 07.00 memuat 2.084 mm, yaitu 21% seluruh hujan 4 tahun.
- Terjadi pada 518 hari (36% hari), misalnya 15,7 mm dalam 10 menit saat RR24 SYNOP 26,7 mm. Nilainya tidak sama dengan RR24 (cocok hanya 0,8%), jadi tampaknya pembacaan atau sisa akumulasi pukul 07.00.
- Bengkulu memiliki gejala yang sama tetapi kecil: 250 mm (2,1%), 87 hari.
- Stasiun lain tidak (sebaran hujan per slot rata).
- Total hujan harian AWS sendiri cocok dengan RR24 SYNOP: rasio 0,90–1,25, r 0,79–0,96.
- `aws_rain_mm` dan `aws_rain_sum_180m` adalah prediktor P2. Origin 07.00–09.50 di Yogyakarta membawa "hujan" palsu dari semalam.

**Usulan V6.8:** slot 07.00 Yogyakarta dan Bengkulu diganti nilai slot 06.50 (persistensi kausal), ditandai di provenance. `aws_rain_sum_180m` dihitung ulang. Data lain tidak berubah.

## Catatan naskah

- Puncak GHI rata-rata Banten 10.30 AST adalah iklim awan sore, bukan galat jam.
- Okta Jambi berpuncak 07.00 (pengodean janggal); dicatat sebagai keterbatasan.
