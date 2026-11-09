---
tags: [disertasi, prediksi-radiasi, audit, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — perbaikan V6.2 terbukti; dua cacat sensor baru (angin Bengkulu, tekanan Banten) perlu keputusan sebelum running uji"
---

# Tahap 98 — audit V6.2 sebelum running uji

Sasaran: `Balai_data_v6_2` (hanya dibaca). Uji tahap 95 dijalankan ulang (`e1`–`e4b`, disalin oleh `h0_salin_uji95.py`) dan ditambah uji baru (`h1_v62_cek.py`, `h2_sensor_macet.py`). Keluaran: CSV dan `log_*.txt` di folder ini.

## Dokumentasi JAXA (P-Tree: userguide, FAQ, README_HimawariGeo)

- CLP versi 1.0 (dirilis 31 Okt 2018). Produk ini hanya siang hari ("CLP cannot be calculated without solar radiance"), resolusi 5 km pada grid 2401 × 2401, 10 menit.
- `hhmm` pada nama berkas adalah **awal observasi**, dalam UTC. Konvensi naskah t = T + 10 sudah sesuai, karena pindaian selesai sebelum t.
- Algoritma: Kawamoto et al. (2001) dan Nakajima & Nakajima (1995); masker awan Ishida & Nakajima (2009); jenis awan menurut definisi ISCCP. Tidak ada ATBD.
- Retrieval "Failed" terjadi pada awan sangat tipis atau sangat tebal dan pada sunglint. Ekstraksi hanya menghitung piksel yang retrievalnya berhasil.
- Latensi CLP tidak dinyatakan. Untuk aerosol, JAXA menyebut 2–5 jam. Konsekuensinya, prakiraan 1 jam di naskah adalah uji dengan ketersediaan satelit ideal; ini perlu ditulis sebagai keterbatasan operasional.
- JAXA meminta kredit "P-Tree System, JAXA" dan sitasi makalah algoritmanya di naskah.

## Lolos

- **Struktur:** 39 berkas cocok dengan SHA256; grid, kesejajaran, dan skema 124 kolom utuh.
- **Hasil uji tahap 95 sama dengan V6.1**, kecuali yang memang diperbaiki:
  - Hanya angka radiasi Bengkulu yang bergeser sangat kecil (k_c > 1,3 turun 0,013 poin).
  - Langkah tekanan > 2 hPa turun 85–97%: Banten 1.289 → 74, Bengkulu 1.240 → 43, Kalbar 844 → 153.
  - Pasang S2 tidak berubah (amplitudo ±0,01 hPa), jadi saringan tidak merusak sinyal tekanan nyata.
- **Fraksi awan fisis** (tahun latih):
  - k_c turun monoton dengan fraksi di keenam stasiun, dari 0,89–1,02 (fraksi < 0,05) ke 0,39–0,50 (fraksi > 0,95).
  - Fraksi × COT berkorelasi lebih kuat dengan k_c daripada COT saja di lima stasiun (Spearman −0,55 sampai −0,67), sesuai k_c ≈ (1 − f) + f·T(COT).
  - Saat mendung tebal (k_c < 0,15), median fraksi 0,85–0,96 dan hanya 0,1–7% slot yang fraksinya < 0,5. Jadi kegagalan retrieval awan tebal tidak membuat fraksi meremehkan awan secara berarti.
  - Siklus harian wajar: puncak 10–11 WIB di Banten, Yogyakarta, Kalbar, dan Jambi; Bengkulu pagi (awan pesisir).
- **Kebocoran waktu (44 prediktor):**
  - Prediktor CLP berkorelasi paling kuat dengan k_c pada t−30 sampai t+10. `clp_cloud_frac` memuncak pada t−10 atau t.
  - Yang memuncak pada t+60 hanya pola harian deterministik (clear-sky masa depan, pasang tekanan). `clp_cot_delta_60m` memuncak pada t+30 karena tren awan memang meramalkan.
  - Tidak ada tanda kebocoran.
- **Koordinat Bengkulu:** simetri k_c cerah hampir tak berubah (−0,047 → −0,045 pada elevasi 20–40°). Sisa asimetrinya berasal dari kanal atau efek pagi, bukan koordinat.

## Cacat baru — perlu keputusan sebelum running uji

1. **Anemometer Bengkulu rusak Jul 2024–Mar 2025.**
   - Kecepatan angin siang = 0 di 24–68% slot per bulan (Nov 2024 66%, Jan 2025 68%).
   - Median per tahun turun dari 1,45–1,61 m/s (2022–2023) ke 0,37 (2024) dan 0,48 (2025).
   - Angin nol berjam-jam di siang hari di stasiun pesisir tidak fisis. Periode ini mengenai tahun validasi dan uji.
   - `aws_wind_speed_ms` adalah prediktor P2.
2. **Tekanan Banten datar Jan–Apr 2022.** 10.344 slot bernilai sama ≥ 3 jam, terpanjang 20,8 jam. Pasang S2 (±1,3 hPa) tidak memungkinkan tekanan datar selama itu, jadi ini nilai yang ditahan atau diisi. Periode ini tahun latih.

Usulan V6.3:
- Kosongkan angin Bengkulu yang bernilai 0 di siang hari pada periode rusak, atau seluruh periode Jul 2024–Mar 2025.
- Kosongkan tekanan yang datar ≥ 3 jam di semua stasiun (Banten 10.344 slot, lainnya ≤ 176).

## Konfirmasi dengan SYNOP Stasiun Klimatologi Bengkulu 2024–2025 (berkas pengguna `job_13401.csv`)

Skrip `h3_synop_bengkulu.py` (+ cek `h3b`, `h3c`, keluaran `H8_synop_bengkulu_bulanan.csv`).

- **Isi berkas:** 9.505 laporan per jam, 00–12 UTC (07–19 WIB). Kecepatan dalam knot (iw = 4). Angin dan tekanan QFF identik dengan SYNOP di database. Ada 2 baris kode hilang 9999 (ff dan suhu); kode ini juga ada di `synop_wind_speed_kt` database, tetapi kolom itu bukan prediktor.
- **Jam benar:** suhu SYNOP lawan suhu AWS memberi RMSE terkecil pada geseran 0 menit (0,56 °C). Label SYNOP UTC + 7 sejajar dengan slot AWS.
- **Anemometer dikonfirmasi rusak.**
  - Jan–Jun 2024: AWS normal (r 0,80–0,84; AWS/SYNOP ≈ 0,8).
  - **Jul 2024–Mar 2025:** AWS = 0 padahal SYNOP ≥ 2 m/s di 12–56% laporan; rerata AWS 0,06–0,66 m/s lawan SYNOP 2,2–3,5 m/s.
  - **Apr–Agu 2025:** tidak lagi nol, tetapi membaca terlalu rendah (rasio 0,32–0,66).
  - Sep 2025 normal kembali (rasio 0,76–0,79). Arah angin saat bergerak cocok (median selisih 13°).
- **Tekanan Bengkulu — saringan V6.2 salah sasaran.**
  - Pada jam-jam yang slot :00-nya dibuang, nilai :00 itu justru cocok dengan QFE SYNOP (median selisih 0,3 hPa). Yang meleset adalah slot logger di sekitarnya (:50 dan :10, +1,6 sampai +2,0 hPa).
  - Logger menyimpang > 1 hPa (median +1,26) dari QFE di 30–55% jam pada **Apr 2024–Agu 2025** (2.662 dari 8.771 jam), dan normal kembali Sep 2025.
  - Jadi masalahnya adalah offset logger, bukan lonjakan :00.
- **Suhu dan RH AWS sehat:** bias suhu −0,2 °C (RMSE 0,4); RH ±1% kecuali Jul 2025 (−3,1%) dan Des 2025 (+3,0%).
- Anemometer dan tekanan rusak bersamaan, lalu pulih bersamaan pada Sep 2025. Ini menunjukkan gangguan pada logger atau perawatan AWS dalam periode yang sama.

Usulan V6.3 diperbarui:
1. **Angin Bengkulu:** kosongkan kecepatan, arah, dan turunannya pada Jul 2024–Agu 2025 (dikonfirmasi SYNOP).
2. **Tekanan Bengkulu:**
   - Kembalikan nilai :00 yang dibuang V6.2.
   - Kosongkan slot logger pada jam yang offset-nya > 1 hPa dari QFE SYNOP (rata-rata QFE jam itu dan jam berikutnya).
   - Saringan lonjakan V6.2 tetap berlaku di stasiun lain.
3. **Tekanan Banten:** kosongkan nilai datar ≥ 3 jam (Jan–Apr 2022).

## Catatan naskah (tidak perlu diubah)

- **Yogyakarta:** okta, CM, dan CH SYNOP kosong pada 2022–2023 dan terisi pada 2024–2025 (sudah begitu sejak V5). Ketiga prediktor ini tidak bisa dipelajari model di Yogyakarta.
- **Kalbar:** arah angin AWS kosong seluruhnya (sejak V5).
- **Jambi:** angin dari SYNOP; tenang (0 m/s, arah 0) di 19% slot siang. Resolusinya knot (1,03 dan 1,54 m/s).
- **Bengkulu:** `aws_pressure_delta_60m` kosong 12% di validasi dan uji, tetapi hanya 0,2% di latih, akibat saringan lonjakan 2024–2025.
- **CER** tersedia untuk rata-rata 26–32 piksel lebih sedikit daripada COT di 80–85% slot, jadi CER kotak dirata-ratakan dari subset piksel. CTT dan CTH tersedia persis di piksel yang punya COT.
- **RH:** Kalbar 98,1% datar di 4,35% slot siang 2023 (saturasi sensor).
