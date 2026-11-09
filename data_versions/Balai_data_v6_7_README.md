# Database Versi 6.7 (tahap 105) — BEKU 2026-11-08

Dibangun dari `Balai_data_v6_6` (tidak diubah). Satu perbaikan: arah angin saat tenang atau tidak diketahui. Desain: `solardata_new_v2/paper_v2_clpbanten/105_v6_7_arah/DESAIN_105.md`; skrip `q1_bangun_v67.py`; laporan `RINGKASAN_105.md`.

## Perubahan terhadap V6.6

`aws_wind_dir_sin` = `aws_wind_dir_cos` = 0 dan `aws_wind_dir_deg` kosong ("tanpa arah") bila:

1. kecepatan angin < 0,5 m/s (calm);
2. arah tercatat tepat 0 (kode calm SYNOP; utara sejati = 360);
3. arah hanya ditahan lebih dari 60 menit tanpa pengamatan arah.

Sebelumnya calm tersimpan sebagai 0° (utara: sin 0, cos 1). Hanya ketiga kolom arah yang berubah. sin² + cos² ∈ {0, 1}, dan ketersediaan sin/cos tetap 100%.

| Stasiun | Origin tanpa arah | calm | kode 0 | ditahan > 60 menit |
|---|---|---|---|---|
| Banten | 11,1% | 8,7 | 2,4 | 0,0 |
| Bengkulu | 3,0% | 2,9 | 0,0 | 0,1 |
| Jambi | 25,2% | 23,0 | 2,2 | 0,0 |
| Yogyakarta | 6,4% | 6,3 | 0,0 | 0,0 |
| Kalbar | 24,8% | 15,3 | 0,0 | 9,5 |
| Jawa Tengah | 8,1% | 5,3 | 0,1 | 2,7 |

Provenance: `arah_tanpa_arah` (0 ada arah, 1 calm, 2 kode 0, 3 ditahan > 60 menit).

## Cara memakai

```
DATA_DIR=C:\Users\ariff\Documents\Balai_data_v6_7\00_data
CLEARSKY_DIR=C:\Users\ariff\Documents\Balai_data_v6_7\clearsky
CLP_EKSTRA_DIR=C:\Users\ariff\Documents\Balai_data_v6_7\clp_ekstra
FEATSET=P2F
```

44 prediktor; baseline tidak berubah. Semua isi dan catatan README V6.6 tetap berlaku: meteorologi mulus, lengkap, dan kausal; kolom SYNOP as-of 60 menit; radiasi dan CLP identik dengan V6.5.
