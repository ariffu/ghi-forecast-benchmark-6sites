---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "DIKUNCI — persetujuan pengguna 2026-11-08 (\"ya perbaiki dulu ... pastikan data hujan AWS akumulasi 24 jam reset 07:00 WIB ... sinkronisasikan dulu baru kerjakan perbaikan\")"
---

# Tahap 107 — V6.8: hujan AWS disinkronkan dengan SYNOP

Dasar: `Balai_data_v6_7` (beku). Hasil: `C:\Users\ariff\Documents\Balai_data_v6_8`.

## Sinkronisasi (`s1_sinkron_hujan.py`, sebelum perbaikan)

**Konvensi.**
- Hujan AWS adalah akumulasi 24 jam yang reset 07.00 WIB (00 UTC). Data mentah Banten: kumulatif ditahan sampai slot 07.00, lalu reset di 07.10.
- Satu hari hujan = (07.00 kemarin, 07.00 hari ini]. Slot 10 menit berlabel t berisi hujan (t − 10, t].
- Konvensi ini cocok paling baik dengan SYNOP di semua stasiun, dibanding label [t, t + 10).

**Periode SYNOP** (berakhir di jam laporan T):
- RR "last" 3 jam pada 10, 13, 16, 19 WIB;
- RR6 pada 13 dan 19 WIB;
- RR24 pada 07 WIB.

**AWS lawan SYNOP** (rasio jumlah, r):

| Stasiun | 3 jam | 6 jam | 24 jam |
|---|---|---|---|
| Banten | — | 0,99 (0,98) | — (RR24 asli tidak tersedia) |
| Bengkulu | 0,92 (0,88) | 0,92 (0,89) | 0,94 (0,90) |
| Jambi | 0,99 (0,91) | 1,01 (0,94) | 0,95 (0,95) |
| Yogyakarta | 0,68 (0,89) | 0,69 (0,93) | 0,91 (0,90), termasuk hitung ganda 07.00 |
| Kalbar | 0,74 (0,94) | 0,75 (0,95) | 0,96 (0,96) |
| Jawa Tengah | 0,96 (0,93) | 0,97 (0,95) | 1,23 (0,80); RR24 SYNOP sering 0 saat AWS hujan |

Perbedaan manual–otomatis diterima apa adanya, tanpa penskalaan (keputusan pengguna).

**Slot 07.00.**
- Yogyakarta: nilai slot 07.00 = 1,01 × jumlah 23 jam 50 menit sebelumnya (median), dan 231 hari cocok dalam 10%. Akumulasi harian tercatat sebagai hujan 10 menit, sehingga dihitung ganda.
- Jawa Tengah 3 hari, Bengkulu 2 hari; stasiun lain tidak.

**Isian non-kausal.**
- Hujan AWS yang kosong pernah diisi dengan membagi mundur laporan SYNOP (`rr_src` = `synop_disagg`): Yogyakarta 15.841 slot (1.785 mm), Jawa Tengah 8.140 slot (326 mm).
- Pembagian mundur memasukkan hujan dari laporan yang datang kemudian ke slot yang lebih awal (bocor sampai 3 jam).

## Perbaikan

1. **Hitung ganda 07.00** (semua stasiun). Bila v(07.00) ≥ 0,5·S dan S > 0,5 mm, dengan S = jumlah slot (07.00 kemarin, 06.50], maka v(07.00) := max(v(07.00) − S, 0). Artinya, akumulasi 24 jam dikurangi hujan yang sudah tercatat, sehingga yang tersisa adalah hujan 06.50–07.00.
2. **Isian `synop_disagg` diganti isian kausal maju.** Slot t diisi laju rata-rata periode laporan SYNOP terakhir T ≤ t: RR3(T)/18 bila t − T < 180 menit; bila tidak ada, RR6(T)/36 bila t − T < 360 menit. Bila laporan terakhir menyatakan 0, slot = 0. Bila tidak ada laporan dalam jendela itu, slot kosong (tidak diketahui). Jumlah hujan tetap terjaga, hanya bergeser satu periode ke depan. Isian `zero_fill` (0 bila SYNOP menyatakan tidak hujan) dipertahankan.
3. **`aws_rain_sum_180m`** dihitung ulang (rolling 18 slot, min_periods = 1).

Kolom lain tidak berubah. Provenance baru: `hujan_koreksi_0700`, `hujan_isi_maju`.

## Amandemen 1 (2026-11-08, sebelum validasi)

Aturan v(07.00) ≥ 0,5·S terlalu longgar: Bengkulu 21 slot dan Jambi 6 slot ikut terkoreksi, padahal sinkronisasi hanya menemukan 2 hari yang benar-benar ganda di Bengkulu, sehingga hujan pagi sungguhan bisa terhapus. Aturan diperketat menjadi 0,8·S ≤ v(07.00) ≤ 1,2·S + 0,2 (nilai 07.00 ≈ jumlah 24 jam).

## Amandemen 2 (2026-11-08, sebelum validasi)

Sesudah amandemen 1, Yogyakarta masih punya 38 hari dengan slot 07.00 seperti hitung ganda. Nilai 07.00 di hari-hari itu sama dengan jumlah slot yang **diukur logger** (rasio 1,00), bukan jumlah semua slot, karena sebagian slot 24 jam sebelumnya adalah isian SYNOP yang tidak ikut terhitung di pencacah AWS. Pembanding S kini = jumlah slot logger (`rr_src` = ok) di Yogyakarta dan Jawa Tengah; stasiun lain memakai semua slot.

## Amandemen 3 (2026-11-08, sebelum validasi)

Sesudah amandemen 2, slot 07.00 Yogyakarta masih berisi hujan pada 503 hari (392 mm, 4,7% total), sedangkan slot 06.50 hanya 17 hari dan 07.10 hanya 76 hari. Ini residu pencacah yang tidak bisa direkonstruksi persis, karena nilai kumulatif aslinya tidak tersedia. Di Yogyakarta, slot 07.00 diganti nilai slot 06.50 (persistensi kausal) di semua hari dan ditandai `hujan_koreksi_0700`. Stasiun lain memakai aturan amandemen 2.

## Validasi

- Sinkronisasi diulang: slot 07.00 tidak lagi menyerupai jumlah harian.
- Siklus harian hujan Yogyakarta kembali sore.
- Kausalitas: isian maju di slot t identik bila SYNOP sesudah t dihapus.
- Hanya 2 kolom hujan yang berubah.
- Pipeline P2F berjalan dengan 44 prediktor.
