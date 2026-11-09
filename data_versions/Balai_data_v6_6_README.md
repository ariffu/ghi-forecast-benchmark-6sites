# Database Versi 6.6 (tahap 103) — BEKU 2026-11-08

Dibangun dari `Balai_data_v6_5` (tidak diubah). Meteorologi AWS 10 menit dikoreksi terhadap SYNOP per jam dengan **penaksir kausal yang mulus dan lengkap**. Desain: `solardata_new_v2/paper_v2_clpbanten/103_meteo_mulus/DESAIN_103.md`; laporan `RINGKASAN_103.md`; skrip `n2_bangun_v66.py`.

## Penaksir (suhu, RH, tekanan, kecepatan angin)

Per slot 10 menit, hanya memakai data ≤ t (tidak ada interpolasi antarlaporan, yang bocor ke masa depan):

1. **Rambat:** x⁻(t) = x(t−1) + perubahan klimatologi bulan × menit-hari (tahun latih, dihaluskan ±30 menit).
2. **Logger sehat ada** (nilai terkoreksi V6.5): diikuti, dengan bobot naik bertahap selama 60 menit sesudah logger kembali.
3. **Tanpa logger:** koreksi dari laporan SYNOP baru (sesudah QC V6.5) disebar 60 menit.
4. **Batas laju perubahan total per 10 menit:** suhu 1,5 °C, RH 7,5%, tekanan 0,5 hPa, angin 3 m/s.
5. **Tanpa slot kosong** sesudah pengamatan pertama (1 Jan 2022 07.00). Malam tanpa pengamatan dirambatkan dengan siklus harian.

## Lainnya

- **Arah angin:** arah AWS; bila tidak ada, arah SYNOP ≤ 60 menit; bila tidak ada juga, arah terakhir. Kalbar kini terisi dari SYNOP (sebelumnya kosong).
- **Kolom SYNOP prediktor** (visibilitas, okta, CL, CM, CH, ww): nilai laporan berlaku 60 menit. Ketersediaannya di origin naik dari 16% menjadi 92–100%. Sisa kosong: 06.30–06.50 (laporan pertama 07.00) dan kode yang memang tidak dilaporkan, misalnya CH saat tertutup awan bawah.
- Turunan lag/delta/rolling dan sin/cos dihitung ulang.

## Hasil audit

| | V6.5 | V6.6 |
|---|---|---|
| Lompatan 10 menit (suhu > 2 °C, RH > 10%, tekanan > 1 hPa, angin > 5 m/s), jumlah 24 deret | 5–2.078 per deret | **0** |
| Ketersediaan suhu/RH/tekanan/angin di origin | 94–100% | **100%** (99,99% Banten: slot sebelum pengamatan pertama) |
| Bulan menyimpang dari SYNOP | 6 | 6 |
| Uji kausalitas (3 titik potong per stasiun) | lolos | lolos |

- **Harga kemulusan:** informasi laporan SYNOP baru diserap dalam 60 menit, dan perubahan nyata yang sangat cepat (misalnya pendinginan hujan) terbagi ke beberapa slot. RMSE terhadap SYNOP di jam laporan naik di stasiun yang deretnya berasal dari SYNOP (Banten suhu 0,18 → 0,80 °C, RH 0,6 → 4,1%; Jambi suhu 0,03 → 0,52 °C). Di stasiun logger kenaikannya ≤ 0,1 °C dan ≤ 0,3% RH.
- `clearsky`, `qc`, `clp_ekstra`, radiasi, dan CLP identik dengan V6.5.
- Tidak ada pola kebocoran baru.
- **Pipeline P2F:** 44 prediktor. Kekosongan > 1% yang tersisa di origin uji hanya CLP (tidak ada berkas atau retrieval), turunan k_c, dan kolom SYNOP pada 06.30–06.50.

## Cara memakai

```
DATA_DIR=C:\Users\ariff\Documents\Balai_data_v6_6\00_data
CLEARSKY_DIR=C:\Users\ariff\Documents\Balai_data_v6_6\clearsky
CLP_EKSTRA_DIR=C:\Users\ariff\Documents\Balai_data_v6_6\clp_ekstra
FEATSET=P2F
```

## Provenance baru

- `mulus_mode_{suhu,rh,tekanan,angin}`: 0 = logger, 1 = koreksi SYNOP, 2 = rambat tanpa pengamatan;
- `mulus_dibatasi_*`: batas laju aktif;
- `mulus_mode_arah`: 0 AWS, 1 SYNOP, 2 ditahan;
- `synop_asof_umur_mnt`: umur laporan SYNOP.

Catatan README V6.5 tetap berlaku.
