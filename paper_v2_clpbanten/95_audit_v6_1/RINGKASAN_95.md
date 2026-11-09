---
tags: [disertasi, prediksi-radiasi, audit, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — V6.1 tidak diubah; 5 temuan berat untuk V6.2, sisanya catatan naskah"
---

# Tahap 95 — audit ulang V6.1 (fisis, literatur, satelit)

Desain: [[DESAIN_95]]. Skrip: `e1_struktur.py`, `e2_radiasi.py`, `e2b_rinci.py`, `e3_satelit.py`, `e4_meteo.py`, `e4b_rinci.py`. Keluaran: CSV S1–S3, R1–R9, R_rinci, C1–C7, M1–M5, dan `log_e*.txt`. V6.1 hanya dibaca. Tidak ada model yang dilatih.

Koordinat Stasiun Klimatologi Bengkulu dari pengguna: −3,864930; 102,311998.

## Lolos

- **Struktur:** ke-33 berkas cocok dengan `SHA256.txt`. Grid 10 menit lengkap (210.384 baris), tanpa duplikat. `clearsky/`, `qc/`, `provenance/`, dan `00_data_rawfill` sejajar.
- **Posisi matahari:** `solar_elev_deg` dihitung pada awal slot (geseran 0 menit, RMSE 0,11° terhadap SPA).
- **Jam AWS:** pasang tekanan S2 1,27–1,48 hPa dengan puncak pukul 09.28–09.51 waktu matahari, sesuai klimatologi tropis Dai & Wang (1999). Jam tekanan benar di keenam stasiun.
- **CLP, fisis:**
  - Rentang valid: COT ≤ 150, CTT 188–300 K, CTH ≤ 16,6 km.
  - Laju CTT–CTH 6,3–6,7 K km⁻¹ (atmosfer baku 6,5), dengan CTT pada 0 km 303–306 K (setara suhu permukaan).
  - Tidak ada retrieval malam.
  - Satu versi produk (L2CLP010).
  - Satelit sesuai jadwal JMA: H09 sejak 13 Des 2022, H08 sejak 12 Okt 2025, H09 lagi sejak 26 Nov 2025. Pergantiannya terjadi dalam beberapa jam dari pengumuman JMA.
  - Berkas 02.40 UTC hilang 99% (housekeeping); jam lain hilang 0,75%.
- **CTH lawan SYNOP:** saat hanya ada awan tinggi (CH), median CTH 8,1–8,4 km (Banten, Jambi). Saat hanya ada awan rendah (CL), 1,7–4,6 km.
- **Radiasi:**
  - Albedo siang cerah 0,18–0,22, stabil antartahun.
  - GHI harian 4,0–5,5 kWh m⁻² hari⁻¹. Tahun 2023 paling cerah di lima stasiun (kecuali Jambi), dan hujan 2023 juga terendah di lima stasiun (kecuali Kalbar), sesuai El Niño. Sinyal iklimnya konsisten.
  - Lama penyinaran Banten paling cocok dengan ambang DNI 120 W m⁻², persis definisi WMO.
- **SYNOP:** Td ≤ T di semua laporan; RH Magnus dari T dan Td cocok (median selisih ≤ 0,03%).
- **Hujan:** tidak ada bukti jam hujan bergeser. k_c terendah sekitar 0–30 menit sebelum hujan tercatat, wajar karena awan konvektif datang lebih dulu.

## Temuan berat (perlu V6.2)

1. **Koordinat Bengkulu.**
   - Koordinat pengguna berjarak 0,59 km dari pusat kotak CLP (jadi CLP sudah benar) dan 2,93 km dari Tabel 1 (Tabel 1 salah).
   - Clear-sky dan bendera QC V6.1 memakai Tabel 1. Dampaknya kecil: rasio clear-sky median 1,0006, pagi −0,14%, sore +0,45%, ekstrem ±3% di matahari sangat rendah.
   - Perbaikan: clear-sky/QC V6.2 dan Tabel 1 naskah.
2. **COT kotak adalah rata-rata piksel berawan saja.**
   - `CLOT_mean` dirata-ratakan hanya dari piksel yang punya retrieval; piksel cerah tidak ikut.
   - Fraksi awan kotak (`CLOT_count`/121) ada di sumber tetapi tidak masuk database. Saat COT ada, median fraksi awan 0,59–0,76, dan 21–41% slot fraksinya < 0,5.
   - Akibatnya, awan tersebar dan mendung dengan COT yang sama tidak bisa dibedakan. `clp_cloud_present_int` (COT ≥ 1) praktis berarti "ada piksel berawan".
   - Jenis awan (`CLTYPE`) juga ada di sumber tetapi tidak di database.
   - Usulan V6.2: tambahkan kolom `clp_cloud_frac`. Menambahkannya sebagai prediktor mengubah protokol P2 (43 prediktor), jadi harus diputuskan sebelum pelatihan.
3. **Lonjakan tekanan satu slot tidak tersaring.** Contoh: Kalbar 1 Jan 2022 08.20, 1005,9 hPa di antara 1010,6 dan 1010,4.
   - Banten 1.778 slot, terutama 2023 pada menit 20–40.
   - Bengkulu 1.589 slot, terutama 2024–2025 pada menit 00.
   - Kalbar 936 slot, terutama 2022.
   - Tekanan dan Δ60 menit adalah prediktor P2. Usulan: uji langkah WMO pada V6.2.
4. **DHI Bengkulu terlalu rendah.** Pada elevasi > 30°, k_d < 0,1 di 5,3% slot ukur (2025: 6,3%), dengan persentil 1 sebesar 0,07. Di atmosfer tropis, batas bawah fisis k_d sekitar 0,1 (Rayleigh + aerosol). Ini sejalan dengan neraca 2025 yang gagal 1,34%. DHI adalah prediktor P2. Usulan: tandai di QC V6.2.
5. **COT/CER pada zenit matahari 70–80°.** Median COT naik 1,4–2 kali dan CER turun. Ini bias retrieval bispektral di matahari rendah yang dikenal di literatur. Pita ini mencakup sekitar 12% slot siang (06.30–07.30 dan 16.30–17.30). Di atas 80°, retrieval praktis berhenti. Usulan: bendera SZA di V6.2.

## Catatan untuk naskah (data tidak perlu diubah)

- **Clear-sky Linke Remund.** Median k_c cerah (dipilih dari DHI/GHI ukur, bukan dari model):
  - Banten dan Jawa Tengah 0,97, Yogyakarta 0,98, Bengkulu 1,00, Kalbar 1,03, Jambi 1,07.
  - Linke yang cocok dengan data lebih rendah 1,3 dari Remund di Jambi. Di Banten dan Jawa Tengah lebih tinggi 0,6–0,7, terutama Mei–Nov (aerosol musim kemarau).
  - Skala k_c antarstasiun berbeda ±3–7%. Pilihannya: kalibrasi Linke dari tahun latih, atau aerosol MERRA-2/CAMS (kelompok B).
- **k_c > 1,3** muncul di 0,4–1,8% slot siang. Kebanyakan pada elevasi 5–15° (06–07 dan 16–17), dari logger, dan berkelanjutan, bukan lonjakan tunggal; maksimum 4,0. Pada matahari rendah k_c tidak stabil (galat kosinus, clear-sky kecil). Pipeline memotong di 2,0.
- **Malam:** ≥ 95% nilai radiasi malam dipaksa 0, sehingga offset termal pyranometer tidak bisa dinilai. Reflected malam Banten dan Kalbar sampai 2,5–2,9 W m⁻².
- **Kalbar:** k_t < 0,2 dengan k_d < 0,8 di 0,79% slot (DHI terlalu rendah saat mendung). k_d > 1,05 muncul di Kalbar 1,06% dan Yogyakarta 1,39%, kebanyakan pada GHI 20–50 W m⁻².
- **`nett_wm2`** sama persis dengan GHI − reflected, yaitu neto gelombang pendek, bukan radiasi neto total. Bukan prediktor.
- **Penyinaran** hanya ada di Banten dan Kalbar. Kalbar biner (0/10) dan cocok dengan DNI > 120 hanya 65% pada 2022–2024 (2025: 91%). Bukan prediktor.
- **Konvensi tekanan campur:**
  - AWS Jambi = SYNOP tekanan permukaan laut: 1010,6 hPa, padahal tekanan stasiun pada 24 m seharusnya 1007,1.
  - SYNOP Yogyakarta adalah tekanan stasiun.
  - SYNOP Banten dan Bengkulu adalah tekanan permukaan laut.
  - Selisihnya konstan per stasiun.
- **RH jenuh:** Bengkulu 100% konstan ≥ 6 jam (7.393 slot), Kalbar 98,1–98,2%, Jambi bilangan bulat 95–97%. Ini saturasi sensor kapasitif di malam hari.
- **Okta SYNOP lawan fraksi awan CLP:** Spearman 0,33 (Banten) sampai 0,66. Banten datar pada okta 1–7, dan Jambi okta 0 memberi fraksi 0,59. Ini sejalan dengan temuan tahap 91 bahwa pengodean okta janggal.
- **Paralaks:** sudut zenit satelit 36–45°. Pergeseran awan median 4–9 km dan persentil 90 9–12 km, ke barat. Masih di dalam kotak ±30 km, tidak dikoreksi; sebut di metode.
- **`solar_elev_deg`:** Jambi masih dihitung dari koordinat lama (paling cocok dengan geseran +1 menit), Bengkulu dari Tabel 1. Dipakai untuk saringan elevasi > 5°; dampaknya diabaikan.
- **AOD:** hanya Banten (26,5%) dan Kalbar (5%); tidak dipakai model.

## Usulan V6.2 (belum dikerjakan)

1. Clear-sky dan QC Bengkulu dengan koordinat pengguna.
2. Kolom `clp_cloud_frac` (dan bendera SZA > 70°) dari sumber ekstraksi ulang.
3. Saringan lonjakan tekanan (uji langkah satu slot).
4. Bendera DHI Bengkulu k_d < 0,1.
5. Dokumentasi butir-butir catatan di README.

Butir 2 menyentuh protokol prediktor dan perlu keputusan pengguna sebelum pelatihan.
