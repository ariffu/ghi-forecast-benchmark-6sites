# Database Versi 6.5 (tahap 102) — BEKU 2026-11-08

Dibangun dari `Balai_data_v6_3` (tidak diubah); menggantikan V6.4, yang koreksinya cacat (audit tahap 101). Meteorologi AWS (suhu, RH, tekanan, kecepatan dan arah angin) beracuan SYNOP di keenam stasiun.

Dokumen terkait di `solardata_new_v2/paper_v2_clpbanten/`:
- desain dan tiga amandemen: `102_v6_5/DESAIN_102.md`;
- dasar langkah: `100_meteo_synop/DESAIN_100.md`;
- laporan: `102_v6_5/RINGKASAN_102.md`;
- skrip: `102_v6_5/l1_bangun_v65.py`.

## Yang dilakukan

1. **Satuan dan konvensi.**
   - Angin SYNOP knot × 0,514444 → m/s. Sisipan knot di slot AWS Banten (5.269, harus tampak sebagai lonjakan) dikonversi.
   - Tekanan acuan di ketinggian sensor: S* = SYNOP + c. Nilai c: Banten −3,25, Bengkulu −1,02, Kalbar −0,55, Jawa Tengah −0,54 (SYNOP QFF), Yogyakarta −0,27 (SYNOP QFE). Jambi memakai reduksi hipsometrik (−2,76).
2. **QC laporan SYNOP (kausal).** Laporan yang menyimpang dari laporan sebelumnya dan dari AWS saat itu melebihi batas (tekanan 2 hPa, suhu 4 °C, RH 25%) tidak dipakai. Jumlahnya 1–19 laporan per variabel per stasiun.
3. **Deret mayoritas-SYNOP dibangun ulang** dengan isian kausal SYNOP (umur ≤ 3 jam):
   - Banten suhu/RH (83/81% slot siang latih berasal dari SYNOP);
   - Jambi suhu/RH/angin (90/86/85%) dan tekanan Jambi (QFF, berisi blok +4 hPa).
4. **Deret logger dikoreksi bias kausal 7 hari** terhadap SYNOP: suhu/RH/tekanan aditif, angin × k (0,5–2,0), arah diputar. Rekonstruksi V6 ikut dikoreksi. Isian V6.3 dan sisipan SYNOP tidak dikoreksi. Lonjakan angin logger satu slot dibuang (Banten 25).
5. **Minggu rusak** diganti isian kausal SYNOP (arah: dikosongkan).
   - Bengkulu: angin Jul 2024 – Agu 2025 dihitung ulang di level SYNOP.
   - Kalbar: suhu Agu–Des 2025; semua variabel akhir Nov–Des 2025.
   - Yogyakarta: tekanan 24 minggu.
   - Jawa Tengah: arah 27 minggu.
6. Klimatologi isian dihaluskan ±30 menit dari semua slot tahun latih. Turunan lag/delta/rolling dan sin/cos dihitung ulang.

## Hasil audit (tahap 102)

- **Bulan menyimpang dari SYNOP:** V6.3 82 → V6.5 6 (sisa: rasio angin 1,3 di bulan dengan banyak laporan tenang; arah Jawa Tengah Des 2022).
- **Lompatan 10 menit** di deret yang dibangun ulang semuanya tepat di jam laporan, yaitu informasi laporan baru. Di luar jam laporan: 0. Lompatan deret logger setara atau di bawah V6.3, kecuali angin Jawa Tengah dan Kalbar (penskalaan k ke level SYNOP).
- **Bagian lain identik dengan V6.3:** `clearsky`, `qc`, `clp_ekstra`, dan semua kolom non-meteorologi. Radiasi dan satelit identik dengan audit sebelumnya.
- **Pipeline P2F:** 44 prediktor di keenam stasiun. Suhu/RH Banten kosong di 6% origin (06.30–06.50, sebelum laporan SYNOP pertama), sama di semua split.

## Cara memakai

```
DATA_DIR=C:\Users\ariff\Documents\Balai_data_v6_5\00_data
CLEARSKY_DIR=C:\Users\ariff\Documents\Balai_data_v6_5\clearsky
CLP_EKSTRA_DIR=C:\Users\ariff\Documents\Balai_data_v6_5\clp_ekstra
FEATSET=P2F
```

## Provenance baru (per variabel v)

- `met_bias_v`: koreksi yang diterapkan;
- `met_isi_v`: minggu yang diisi SYNOP;
- `met_sisipan_v`: slot sisipan SYNOP;
- `met_bangun_ulang_v`: deret dibangun ulang dari SYNOP;
- `met_synop_dibuang_{tekanan,suhu,rh}`: laporan SYNOP yang dibuang QC;
- `met_lonjakan_angin`: lonjakan angin yang dibuang.

Angin AWS berada di level SYNOP. Catatan README V6.2 dan V6.3 tetap berlaku, kecuali butir tekanan Yogyakarta dan konvensi tekanan, yang kini sudah diperbaiki.
