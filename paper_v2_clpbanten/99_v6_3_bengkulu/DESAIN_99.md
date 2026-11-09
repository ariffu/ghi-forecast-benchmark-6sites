---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "DIKUNCI — permintaan pengguna 2026-11-08 (perbaikan Bengkulu dulu; angin dan tekanan diisi SYNOP, bukan dikosongkan)"
---

# Tahap 99 — V6.3: angin dan tekanan Bengkulu diisi dari SYNOP

Dasar: `Balai_data_v6_2` (beku, tidak diubah). Hasil: `C:\Users\ariff\Documents\Balai_data_v6_3`. Bukti kerusakan: [[RINGKASAN_98]] (SYNOP Stasiun Klimatologi Bengkulu, berkas pengguna `job_13401.csv`, 2024–2025).

## Mengapa diisi kausal, bukan diinterpolasi

SYNOP hanya ada tiap jam pada 07–19 WIB. Interpolasi linear antara dua laporan memakai laporan berikutnya, sehingga nilai slot t memuat informasi sampai 50 menit ke masa depan (kebocoran tahap 91). Karena itu dipakai cara 2 tahap 92:

x̂(t) = kal(S(t0)) + [x̄(bulan, t) − x̄(bulan, t0)]

- t0 = laporan SYNOP terakhir ≤ t; slot dikosongkan bila umur laporan > 3 jam.
- x̄ = klimatologi AWS tahun latih 2022–2023 per bulan × menit-hari. Komponen ini membawa siklus harian, misalnya pasang tekanan dan angin laut.
- kal = kalibrasi SYNOP → AWS dari tahun latih 2022–2023.

Akurasi pada periode AWS sehat (`i1_uji_isian.py`):

| Variabel | Umur laporan ≤ 60 menit | 70–180 menit | Pembanding: perubahan logger dalam 60 menit |
|---|---|---|---|
| Tekanan | RMSE 0,33–0,34 hPa, r 0,98 | RMSE 0,53–0,60 hPa | 0,68 hPa |
| Angin | RMSE 0,61–0,69 m/s, r 0,72–0,80 | RMSE 0,84–0,85 m/s | 0,76 m/s |

## Aturan

| Variabel | Periode diganti | Dasar periode (perbandingan SYNOP per bulan) | Kalibrasi |
|---|---|---|---|
| `aws_wind_speed_ms` | 1 Jul 2024 – 31 Agu 2025 | AWS = 0 saat SYNOP ≥ 2 m/s > 5%, atau rasio rerata AWS/SYNOP < 0,7 | AWS = 0,712·S + 0,358 (regresi 2022–2023), dipotong ≥ 0 |
| `aws_pressure_hpa` | 1 Apr 2024 – 31 Agu 2025 | jam dengan \|logger − QFE\| > 1 hPa > 5% per bulan | QFE + (−0,022) hPa (selisih AWS − QFE 2022–2023; QFE 2022–2023 = QFF database − 1,0) |

- Semua slot dalam periode diganti dengan isian. Logger di periode itu tidak dipakai, termasuk malam hari: offset logger berubah-ubah ±1–2 hPa dan tidak terverifikasi. Malam (umur > 3 jam) menjadi kosong.
- Arah angin AWS **tidak diubah**: baling-baling tetap bekerja (selisih median dengan SYNOP 13° saat angin bertiup, 23,5° saat mangkuk AWS terbaca 0).
- Turunan dihitung ulang dengan definisi tahap 86/93: `aws_wind_speed_roll_180m_mean`, `aws_pressure_lag_60m`, `aws_pressure_delta_60m`.
- Sumber SYNOP: 2024–2025 dari `job_13401.csv` (ff knot × 0,514444; QFE); 2022–2023 dari kolom SYNOP database. Nilai angin dan QFF di berkas identik dengan database. Kode 9999 dibuang.
- Berlaku untuk `00_data` dan `00_data_rawfill`.
- `provenance`: kolom baru `aws_isi_synop_angin` dan `aws_isi_synop_tekanan`. Saringan lonjakan V6.2 (`aws_lonjakan_tekanan`) di dalam periode tekanan digantikan.
- Stasiun lain identik dengan V6.2. Perbaikan tekanan Banten (datar Jan–Apr 2022) menyusul sebelum V6.3 dibekukan.

## Amandemen 1 (2026-11-08): tekanan datar, diisi dari SYNOP database

Keputusan pengguna: "Ya, pakai SYNOP DB".

- **Deteksi.** Tekanan AWS yang bernilai sama persis ≥ 18 slot (≥ 3 jam) dianggap tidak fisis. Pasang S2 (±1,3 hPa) membuat tekanan selalu berubah ≥ 0,1 hPa dalam 1–2 jam. Aturan berlaku di keenam stasiun: Banten 10.344 slot (Jan–Apr 2022, kebanyakan malam), Jawa Tengah 176, Yogyakarta 83, Jambi 73, Kalbar dan Bengkulu 0.
- **Isian.** Cara 2 yang sama:
  - S = `synop_pressure_hpa` database (QFF).
  - Kalibrasi = median(AWS − SYNOP) tahun latih di luar slot datar. Banten −3,25 hPa (IQR −3,35 sampai −3,10), Jawa Tengah −0,47, Yogyakarta −0,21, Jambi 0,00.
  - x̄ = klimatologi AWS tahun latih di luar slot datar.
  - Kosong bila umur laporan > 3 jam.
- **Cakupan.** Hanya slot yang terdeteksi datar yang diganti. Turunan lag/delta 60 menit dihitung ulang. Kolom provenance baru: `aws_isi_synop_tekanan_datar`.

## Amandemen 2 (2026-11-08): Banten Jan–Mar 2022 seluruhnya QFF

Validasi amandemen 1 menemukan 254 langkah > 2 hPa di Banten, kebanyakan di batas isian. Sebabnya: pada Jan–Mar 2022, slot Banten yang tidak datar berisi QFF SYNOP mentah. Median (AWS − SYNOP − kalibrasi) per bulan adalah +3,2 hPa pada Jan, Feb, dan Mar 2022, dan ≤ 0,5 hPa di bulan lain. Nilai datar 1008,9 adalah nilai yang ditahan di antara laporan.

- **Aturan.** Seluruh slot Banten 1 Jan – 31 Mar 2022 diganti isian kausal SYNOP database, bersama slot datar ≥ 3 jam di luar periode itu. Kalibrasi dan klimatologi dihitung dari tahun latih di luar kedua himpunan tersebut. Isian amandemen 1 untuk Banten dihitung ulang dari tekanan V6.2.
- **Provenance.** `aws_isi_synop_tekanan` = True untuk periode ini; kolom ini kini ada di keenam stasiun (False bila tidak dipakai).
- **Yogyakarta tidak diubah.** AWS menyimpang −0,6 sampai −1,8 hPa dari SYNOP per bulan pada Apr 2024 – Des 2025, tetapi tidak jelas instrumen mana yang salah. Dicatat sebagai keterbatasan.

## Validasi

1. Hanya kolom angin dan tekanan Bengkulu yang berubah; kolom lain dan stasiun lain identik dengan V6.2.
2. Di jam laporan dalam periode, isian = kalibrasi(SYNOP) persis.
3. Kausalitas: isian di slot t tidak berubah bila semua laporan SYNOP sesudah t dihapus.
4. Perbandingan bulanan dengan SYNOP diulang: rasio dan korelasi kembali normal.
5. `_common.prepare` P2F berjalan untuk Bengkulu.
