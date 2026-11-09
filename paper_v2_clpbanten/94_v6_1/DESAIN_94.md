---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "DESAIN TERKUNCI sebelum dibangun — kelompok A (tanpa data baru)"
---

# Tahap 94 — database V6.1: clear-sky interval, bendera QC, dan pemeriksaan kaidah

Permintaan pengguna 2026-11-08 ("Ya, kerjakan A dulu"). V6 (`Balai_data_v6`, beku) tidak diubah. Hasil: `C:\Users\ariff\Documents\Balai_data_v6_1`, berisi `00_data` dan `00_data_rawfill` identik dengan V6 (hash dicek), ditambah `clearsky/`, `qc/`, `provenance/`, `README.md`, dan `SHA256.txt`.

## A1. Clear-sky interval

- GHI tiap slot adalah rata-rata [t, t+9]. Clear-sky Ineichen–Perez dihitung per menit pada t, t+1, …, t+9 lalu dirata-ratakan, juga DNI dan DHI cerah.
- Linke Remund (2003), `interp_turbidity=True`, tetap sama dengan tahap 55.
- Koordinat dan ketinggian dari metadata stasiun (Tabel 1), kecuali Jambi yang memakai ASRS (−1,60111; 103,4944). Ketinggian: Banten 27, Bengkulu 9, Jambi 24, Yogyakarta 182, Kalbar 2, Jawa Tengah 6 m.
- Tidak ada kolom parquet yang berubah. `_common.py` mendapat variabel lingkungan `CLEARSKY_DIR`; nilai bawaan tetap `00_clearsky`, sehingga V5 bisa direproduksi.
- **Validasi:** pada hari cerah (median k_c siang > 0,9, simpangan < 0,06), k_c pagi dan sore pada elevasi yang sama seharusnya setara. Asimetri pagi−sore dibandingkan antara clear-sky lama dan baru; median k_c hari cerah harus mendekati 1.

## A2. Bendera QC per slot (gaya BSRN, Long & Shi 2008)

Satu kolom per variabel radiasi (`qc_ghi`, `qc_dhi`, `qc_dni`, `qc_refl`):

| Kode | Arti |
|---:|---|
| 0 | Diukur logger, lolos uji |
| 1 | Diukur, sumber sekunder (portal, DB v2, tabel 10 menit, trapesium) |
| 2 | Diperbaiki ke batas fisis (tahap 85) |
| 3 | Dihitung atau dimodelkan (estimasi AWS, model DHI, DNI dari neraca, albedo, label model DB v2, neraca tertutup persis) |
| 8 | Malam (elevasi ≤ 0) |
| 9 | Kosong |

Ditambah kolom bit `qc_uji` dari uji BSRN pada nilai akhir: batas mungkin fisis (PPL), batas sangat jarang (ERL), neraca GHI/(DHI + DNI cos Z) dalam ±8% (Z < 75°) atau ±15% (75–93°) bila GHI > 50, dan rasio difus DHI/GHI < 1,05 (Z < 75°) atau < 1,10. Nilai tidak diubah; bendera hanya menerangkan.

## A3–A6. Pemeriksaan (dilaporkan, data tidak diubah)

- **A3 kalibrasi dan drift:** per stasiun per bulan, persentil 95 k_c (clear-sky baru) pada elevasi > 30°, untuk GHI; juga DNI terhadap DNI cerah. Lompatan > 5% antarbulan atau tren > 3% per tahun dicatat.
- **A4 horizon dan bayangan:** saat cerah (k_c jam itu 0,9–1,1, simpangan rendah), median k_c per sektor azimut 10° pada elevasi 2–15°. Sektor dengan median < 0,8 di dua tahun atau lebih ditandai.
- **A5 homogenitas satelit:** hubungan CLP–radiasi per periode satelit (H08 s.d. 12 Des 2022, H09, H08 12 Okt–26 Nov 2025, H09): median COT dan fraksi berawan per kelas k_c, dibandingkan pada bulan kalender yang sama (Oktober–November 2022, 2024, 2025).
- **A6 metadata:** tabel koordinat dan ketinggian per sumber (Tabel 1, `dim_site`, pusat kotak CLP, registri DB v2, pvlib), ditandai mana yang belum terverifikasi.

Aturan: tidak ada perbaikan yang dipilih dari skor model. Temuan A3–A6 hanya diperbaiki dalam versi berikutnya atas keputusan pengguna.
