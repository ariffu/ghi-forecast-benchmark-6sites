---
tags: [disertasi, prediksi-radiasi, audit, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — V6.4 BELUM layak untuk running uji: radiasi/satelit lolos, tetapi koreksi meteorologi V6.4 memunculkan lompatan baru; usulan V6.5"
---

# Tahap 101 — audit komprehensif V6.4

Sasaran: `Balai_data_v6_4` (hanya dibaca). Skrip:
- `k0_salin_uji.py`: menyalin rangkaian uji tahap 95/98, yaitu `e1`–`e4b`, `h1_cek`, `h2_sensor_macet`.
- `k1_meteo_v64.py`: uji khusus K1–K4.

Keluaran: CSV dan `log_*.txt`.

## Lolos (identik dengan audit V6.2 tahap 98)

- **Struktur:** 39 berkas cocok dengan SHA256.
- **Radiasi:** R1–R9 identik (batas BSRN, neraca, clear-sky, peningkatan awan, albedo, total harian).
- **Satelit CLP:** C1–C7 identik (jadwal satelit, ketersediaan, rentang fisis, agregasi, zenit, paralaks, silang SYNOP). Fraksi awan fisis: k_c turun monoton.
- **Kebocoran waktu 44 prediktor:** tidak ada. Pola t+60 hanya clear-sky/pasang deterministik dan tren COT.
- **Meteorologi, yang membaik:**
  - Anemometer Bengkulu tidak lagi macet (2024: 12,8% → 0).
  - Tekanan datar Banten hilang.
  - Bulan menyimpang dari SYNOP 96 → 7 (tahap 100).
  - Titik embun 18,6–28,2 °C; antikorelasi harian suhu–RH −0,98 sampai −1,00.
  - Pasang S2 1,30–1,48 hPa, puncak sekitar 09.30.
  - Jambi kini di level sensor (median 1007,8 hPa).

## Masalah baru akibat koreksi V6.4 (K1)

Lompatan 10 menit melebihi ambang (tekanan > 1 hPa, suhu > 2 °C, angin > 5 m/s), V6.3 → V6.4:

| Deret | V6.3 | V6.4 | Sebab |
|---|---|---|---|
| Tekanan Banten | 287 | 576 (langkah > 2 hPa: 74 → 407) | Deteksi "sisipan QFF" salah tangkap: AWS kebetulan sama dengan laporan SYNOP yang janggal, lalu diganti S*, sehingga muncul lubang −3,2 hPa satu slot. Contoh: 16 Feb 2023 16.00, SYNOP 1007,8 sedangkan laporan sekitarnya ≈ 1011. |
| Suhu Jambi | 593 | 895 | Slot "logger" Jambi (5–9%, nilai ditahan) digeser bias −2,07 °C yang ditaksir dari segelintir slot rusak, lalu melompat di sebelah slot SYNOP. |
| Tekanan Yogyakarta | 156 | 308 | Slot rekonstruksi kausal V6 di stasiun logger ternyata di level logger (x(t0) = AWS), tetapi tidak dikoreksi. Lompatannya ±1,4 hPa di batas. |
| Angin Banten, Jawa Tengah, Kalbar | 166 / 25 / 13 | 405 / 73 / 41 | Faktor k (sampai 1,6) ikut memperbesar lonjakan logger. Maksimum Banten 17 m/s (23 Agu 2023, SYNOP 5,7 m/s). |

Warisan V6.3 yang belum tersentuh: tekanan AWS Jambi berisi blok yang ditahan datar dengan offset sekitar +4 hPa terhadap SYNOP. Contoh: 20 Okt 2025 07.00–08.50, AWS 1012,1 dan 1012,6 sedangkan SYNOP 1007,7 dan 1009,5. Tendensi 3 jam > 3 hPa muncul 9.883 kali (Banten 5.239), dan sudah ada sejak V6.3.

## Komposisi sumber per split (K3, origin elevasi > 5°)

- Bengkulu tekanan dan angin: latih 96–98% logger; validasi/uji 25–49% logger, sisanya dari SYNOP. Ini pergeseran sumber yang tak terhindarkan karena sensornya rusak; perlu ditulis di naskah.
- Kalbar suhu uji 38% dari SYNOP; Yogyakarta tekanan uji 27%.
- Banten suhu/RH (83%) dan Jambi suhu/RH/angin (87–95%) hampir seluruhnya dari SYNOP di semua split, jadi konsisten.
- Variabilitas 10 menit segmen SYNOP mirip logger, kecuali angin Jambi (logger 0,09 lawan SYNOP 0,34), RH Kalbar (1,67 lawan 0,70), dan tekanan Jawa Tengah (0,15 lawan 0,35).

## Catatan tetap

- Okta/CM/CH Yogyakarta kosong di tahun latih; arah angin Kalbar kosong.
- Jambi angin tenang 9–16% slot siang (SYNOP calm, resolusi knot).
- RH Bengkulu 100% datar 2% siang 2025 (saturasi).

## Usulan V6.5 (perbaikan logika tahap 100)

1. **Deret yang mayoritas dari SYNOP dibangun ulang seluruhnya** dengan isian kausal SYNOP: Banten suhu/RH; Jambi suhu/RH/tekanan/angin. Kriteria: ≥ 50% slot laporan tahun latih adalah sisipan atau rekonstruksi. Ini membuang sisa "logger" yang ditahan, termasuk blok tekanan Jambi +4 hPa.
2. **Slot rekonstruksi kausal V6 di stasiun logger dikoreksi seperti logger**, karena levelnya logger.
3. **Sisipan tekanan hanya diakui bila tampak sebagai lonjakan**: |AWS − SYNOP| < 0,05 dan menyimpang dari dua tetangga ≥ 0,5·|c|. Bila tidak, laporan SYNOP itu dianggap janggal.
4. **QC laporan SYNOP:** laporan yang menyimpang dari kedua laporan tetangga melebihi batas fisis per jam (tekanan 3 hPa, suhu 6 °C, RH 40%) dibuang dari penaksiran bias dan dari isian.
5. **Angin:** faktor k dibatasi 0,5–2,0. Lonjakan logger satu slot (> 3× rata-rata tetangga dan > 8 m/s, lalu kembali) dikosongkan.
