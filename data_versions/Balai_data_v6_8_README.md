# Database Versi 6.8 (tahap 107) — BEKU 2026-11-08

Dibangun dari `Balai_data_v6_7` (tidak diubah). Perbaikan hujan AWS yang disinkronkan dengan SYNOP. Desain dan tiga amandemen: `solardata_new_v2/paper_v2_clpbanten/107_hujan/DESAIN_107.md`; laporan `RINGKASAN_107.md`; skrip `s2_bangun_v68.py`.

## Konvensi hujan (hasil sinkronisasi)

- Hujan AWS adalah akumulasi 24 jam yang reset 07.00 WIB (00 UTC). Satu hari hujan = (07.00 kemarin, 07.00 hari ini].
- Slot 10 menit berlabel t berisi hujan (t − 10, t].
- SYNOP: RR 3 jam (10, 13, 16, 19 WIB), RR 6 jam (13, 19 WIB), RR 24 jam (07 WIB).

## Perubahan terhadap V6.7 (hanya `aws_rain_mm` dan `aws_rain_sum_180m`)

1. **Hitung ganda 07.00 dibuang.** Bila nilai slot 07.00 ≈ jumlah hujan logger 24 jam sebelumnya (0,8–1,2×), nilainya dikurangi jumlah itu. Berlaku di Yogyakarta (296 hari, 1.705 mm), Bengkulu 3, Jambi 2, Jawa Tengah 3. Di Yogyakarta, residu slot 07.00 diganti nilai slot 06.50 (persistensi kausal).
2. **Isian SYNOP mundur diganti isian kausal maju.** Isian lama (`rr_src` = `synop_disagg`, membagi laporan berikutnya ke slot sebelumnya) memakai informasi masa depan. Isian baru = laju periode laporan SYNOP terakhir (RR3/18 selama 3 jam, atau RR6/36 selama 6 jam). Yogyakarta 15.844 slot, Jawa Tengah 8.140 slot. Slot tanpa laporan dalam jendela itu kosong: Yogyakarta 3.062 (0,35% origin uji), Jawa Tengah 3.231 (0,2%).
3. `aws_rain_sum_180m` dihitung ulang.

## Hasil

| Stasiun | AWS/SYNOP 3 jam (r) | 6 jam (r) | 24 jam (r) | Slot 07.00 (% hujan) | Puncak hujan (AST) |
|---|---|---|---|---|---|
| Banten | — | 0,99 (0,98) | — | 0,0 | 15 |
| Bengkulu | 0,92 (0,88) | 0,92 (0,89) | 0,94 (0,90) | 2,0 (hujan pagi pesisir) | 17 |
| Jambi | 0,99 (0,91) | 1,01 (0,94) | 0,95 (0,95) | 0,4 | 16 |
| Yogyakarta | 0,75 (0,72) | 0,76 (0,83) | 0,74 (0,86) | **21,2 → 1,0** | **07 → 16** |
| Kalbar | 0,74 (0,94) | 0,75 (0,95) | 0,96 (0,96) | 0,2 | 21 |
| Jawa Tengah | 0,94 (0,92) | 0,94 (0,94) | 1,22 (0,80) | 0,4 | 18 |

- Perbedaan jumlah manual (SYNOP) dan otomatis (AWS) tidak diskalakan. Yogyakarta AWS sekitar 25% di bawah SYNOP. Kalbar 3–6 jam sekitar 25% di bawah, tetapi harian cocok. RR24 SYNOP Jawa Tengah sering 0 saat AWS hujan.
- Korelasi 3–6 jam Yogyakarta turun (0,89 → 0,72), karena isian maju menggeser hujan celah satu periode ke depan. Itulah harga kausalitas.
- Uji kausalitas isian maju lolos. Pipeline P2F berjalan dengan 44 prediktor.

## Cara memakai

```
DATA_DIR=C:\Users\ariff\Documents\Balai_data_v6_8\00_data
CLEARSKY_DIR=C:\Users\ariff\Documents\Balai_data_v6_8\clearsky
CLP_EKSTRA_DIR=C:\Users\ariff\Documents\Balai_data_v6_8\clp_ekstra
FEATSET=P2F
```

Provenance baru: `hujan_koreksi_0700`, `hujan_isi_maju`. Catatan README V6.6 dan V6.7 tetap berlaku.
