# Database Versi 6.4 (tahap 100) — BEKU 2026-11-08

Dibangun dari `Balai_data_v6_3` (tidak diubah). Meteorologi AWS (suhu, RH, tekanan, kecepatan dan arah angin) kini **beracuan SYNOP** di keenam stasiun. Desain: `solardata_new_v2/paper_v2_clpbanten/100_meteo_synop/DESAIN_100.md`; laporan `RINGKASAN_100.md`; skrip `j2_bangun_v64.py`.

## Langkah

0. **Satuan dan konvensi.**
   - Angin SYNOP knot × 0,514444 → m/s. Slot AWS Banten yang berisi angin SYNOP dalam knot tanpa konversi (7.795 slot jam laporan) dikonversi.
   - Tekanan acuan di ketinggian sensor: S* = SYNOP + c.
     - c = median AWS − SYNOP tahun latih: Banten −3,25 (SYNOP QFF), Bengkulu −1,02 (QFF), Kalbar −0,55 (QFF), Jawa Tengah −0,54 (QFF), Yogyakarta −0,27 (SYNOP QFE).
     - **Jambi:** tekanan AWS ternyata QFF, sehingga seluruh deret digeser ke level sensor dengan reduksi hipsometrik (median −2,76 hPa; median tekanan 1010,6 → 1007,8).
   - Sisipan QFF di jam laporan diganti S*.
1. **Koreksi bias kausal** pada slot logger.
   - Suhu, RH, tekanan: dikurangi median residu (AWS − acuan) laporan 7 hari ke belakang.
   - Angin: dikali rasio ΣSYNOP/ΣAWS 7 hari ke belakang.
   - Arah: diputar dengan rata-rata sirkular selisih 7 hari ke belakang.
   - Slot yang sudah berasal dari SYNOP (rekonstruksi kausal V6, isian V6.3, sisipan) tidak dikoreksi.
2. **Minggu rusak** (residu besar sesudah koreksi; angin 0 saat SYNOP ≥ 2 m/s; r < 0,4) diganti isian kausal SYNOP (umur laporan ≤ 3 jam). Arah angin yang rusak dikosongkan. Isian angin Bengkulu V6.3 dihitung ulang di level SYNOP.
3. **Turunan** lag/delta/rolling dan sin/cos arah dihitung ulang.

| Stasiun | Slot diisi SYNOP: suhu / RH / tekanan / angin / arah dikosongkan |
|---|---|
| Banten | 1.440 / 0 / 1.008 / 6.048 / 0 |
| Bengkulu | 4.032 / 2.016 / 4.032 / 62.496 / 1.008 |
| Jambi | 5.040 / 3.024 / 9.360 / 15.408 / 0 |
| Yogyakarta | 0 / 0 / 24.192 / 0 / 0 |
| Kalbar | 22.608 (Agu–Des 2025) / 0 / 4.464 / 13.536 / — |
| Jawa Tengah | 0 / 2.016 / 0 / 4.032 / 24.192 |

Slot yang diisi tetapi berumur > 3 jam (malam) menjadi kosong.

## Hasil

- **Bulan dengan AWS menyimpang dari SYNOP:** 96 di V6.3 (suhu 24, RH 11, tekanan 27, angin 25, arah 9) menjadi 7 di V6.4 (tekanan 1, angin 5, arah 1). Sisa angin: rasio AWS/SYNOP 1,3 saat SYNOP melaporkan tenang (0 knot) sementara AWS masih menangkap angin lemah.
- Median residu bulanan sesudah perbaikan: suhu ≤ 0,04 °C dan RH ≤ 0,7% di empat stasiun (Banten logger: suhu 0,53, RH 3,5 pada bulan dengan sedikit slot logger). Tekanan ≤ 0,1 hPa; rasio angin 0,94–1,06 (Jambi 0,55–1,21).
- Siklus harian wajar: suhu puncak 12.30–14.00 WIB, lembah 05.40–06.10; pasang S2 1,30–1,48 hPa, puncak 09.28–09.51.
- RH di 0–100, angin ≥ 0, sin² + cos² = 1.

## Cara memakai

```
DATA_DIR=C:\Users\ariff\Documents\Balai_data_v6_4\00_data
CLEARSKY_DIR=C:\Users\ariff\Documents\Balai_data_v6_4\clearsky
CLP_EKSTRA_DIR=C:\Users\ariff\Documents\Balai_data_v6_4\clp_ekstra
FEATSET=P2F
```

44 prediktor. `clearsky`, `qc`, dan `clp_ekstra` identik dengan V6.3. Kolom non-meteorologi identik dengan V6.3.

## Provenance baru

Per variabel v ∈ {suhu, rh, tekanan, angin, arah}:
- `met_bias_v`: koreksi yang diterapkan (angin = faktor pengali);
- `met_isi_v`: True bila diisi SYNOP (arah: dikosongkan);
- `met_sisipan_v`: slot jam laporan yang isinya SYNOP.

Semua catatan README V6.2 dan V6.3 tetap berlaku. Pengecualian: catatan "tekanan Yogyakarta menyimpang" dan "konvensi tekanan campur" kini sudah diperbaiki.
