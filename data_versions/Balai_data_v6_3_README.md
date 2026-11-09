# Database Versi 6.3 (tahap 99) — BEKU 2026-11-08

Dibangun dari `Balai_data_v6_2` (tidak diubah). Desain dan dua amandemen: `solardata_new_v2/paper_v2_clpbanten/99_v6_3_bengkulu/DESAIN_99.md`; laporan: `RINGKASAN_99.md`. Bukti kerusakan: audit tahap 98 dan SYNOP Stasiun Klimatologi Bengkulu 2024–2025 dari pengguna (`job_13401.csv`, SHA256 faf6796d…).

## Perubahan terhadap V6.2

Semua isian memakai **cara kausal** (tahap 92):

x̂(t) = kal(S(t0)) + [x̄(bulan, t) − x̄(bulan, t0)]

- t0 = laporan SYNOP terakhir ≤ t; slot kosong bila umur laporan > 3 jam.
- x̄ = klimatologi AWS tahun latih 2022–2023.
- kal = kalibrasi dari tahun latih.
- Tidak ada interpolasi linear, karena interpolasi bocor ke masa depan.

| Stasiun | Variabel | Periode | Sumber SYNOP | Kalibrasi | Slot terisi |
|---|---|---|---|---|---|
| Bengkulu | kecepatan angin | 1 Jul 2024 – 31 Agu 2025 (anemometer rusak/membaca rendah) | berkas pengguna, knot × 0,514444 | AWS = 0,712·S + 0,358, ≥ 0 | 38.857 dari 61.488 |
| Bengkulu | tekanan | 1 Apr 2024 – 31 Agu 2025 (offset logger ±1–2 hPa) | berkas pengguna, QFE | QFE − 0,022 | 47.138 dari 74.592 |
| Banten | tekanan | 1 Jan – 31 Mar 2022 (berisi QFF mentah + nilai ditahan) | SYNOP database (QFF) | QFF − 3,25 | 8.190 dari 12.960 |
| Semua | tekanan datar ≥ 3 jam di luar periode di atas | — | SYNOP database | per stasiun | Banten 653, Jawa Tengah 56, Jambi 73, Yogyakarta 45 |

- Slot dalam periode yang tidak terisi (malam, umur > 3 jam) menjadi kosong.
- Pada origin elevasi > 5°: Bengkulu 96,9% terisi, Banten 94,5%.
- Arah angin AWS Bengkulu tidak diubah (baling-baling bekerja).
- Turunan dihitung ulang: `aws_wind_speed_roll_180m_mean`, `aws_pressure_lag_60m`, `aws_pressure_delta_60m`.
- `provenance`: kolom baru `aws_isi_synop_angin`, `aws_isi_synop_tekanan`, `aws_isi_synop_tekanan_datar` (seragam di keenam stasiun).
- `clearsky`, `qc`, dan `clp_ekstra` identik dengan V6.2. Kolom `00_data` lain dan stasiun Kalbar identik dengan V6.2.

## Cara memakai

```
DATA_DIR=C:\Users\ariff\Documents\Balai_data_v6_3\00_data
CLEARSKY_DIR=C:\Users\ariff\Documents\Balai_data_v6_3\clearsky
CLP_EKSTRA_DIR=C:\Users\ariff\Documents\Balai_data_v6_3\clp_ekstra
FEATSET=P2F
```

44 prediktor (P2 + `clp_cloud_frac`, tahap 97).

## Hal yang perlu diketahui pemakai

Semua catatan README V6.2 tetap berlaku. Tambahan:

- **Tekanan Yogyakarta** AWS menyimpang −0,6 sampai −1,8 hPa dari SYNOP per bulan pada Apr 2024 – Des 2025. Instrumen mana yang salah tidak diketahui, jadi tidak diubah.
- **Okta, CM, CH SYNOP Yogyakarta** kosong pada 2022–2023. Arah angin AWS Kalbar kosong seluruhnya.
- **Isian SYNOP** memiliki galat lebih besar daripada logger sehat. Untuk umur laporan ≤ 60 menit: tekanan RMSE 0,33 hPa, angin 0,61–0,69 m/s (uji pada periode sehat Bengkulu).
- **Sisa langkah tekanan > 2 hPa:** Banten 85, Kalbar 153, stasiun lain ≤ 34. Pasang S2 1,27–1,48 hPa dengan puncak 09.27–09.51 di keenam stasiun.
