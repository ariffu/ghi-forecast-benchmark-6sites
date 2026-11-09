---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — Balai_data_v6_1 beku (SHA256, hanya-baca); parquet identik dengan V6; Manuskrip V6 belum dibangun"
---

# Tahap 94 — ringkasan: V6.1, kelompok A

Desain: [[DESAIN_94]]. Database `C:\Users\ariff\Documents\Balai_data_v6_1` (README di sana). V6 tidak diubah; `00_data`, `00_data_rawfill`, dan `provenance` V6.1 hash-identik dengan V6. Skrip `d1_clearsky.py`, `d1b_geser.py`, `d2_qc.py`, `d2b_neraca.py`, `d2c_rasio.py`, `d3_cek.py`, `d3b.py`, `d3c.py`, `d4_persistence.py`.

## A1. Clear-sky interval

Clear-sky lama dihitung pada titik t, sedangkan GHI adalah rata-rata [t, t+9]. Rasio clear-sky interval/titik: pagi 1,039–1,043, siang 1,000, sore 0,958–0,962. Clear-sky baru dirata-ratakan dari nilai per menit, dengan koordinat dan ketinggian metadata. Ketinggian pvlib lama salah di Bengkulu (138 lawan 9 m), Yogyakarta (278 lawan 182 m), dan Jawa Tengah (26 lawan 6 m); efeknya ≤ 0,3%.

**Validasi** (`d1_validasi_clearsky.csv`): asimetri k_c cerah pagi−sore pada elevasi 10–40° turun dari +0,03…+0,04 menjadi sekitar nol di Banten, Yogyakarta, dan Jawa Tengah. Sisa asimetri terbalik (−0,01 sampai −0,05) tidak berasal dari jam yang bergeser (`d1b_geser.csv`): geseran yang menghapusnya hanya −1 sampai +0,4 menit pada 10–40° dan berubah-ubah antar-elevasi dan antartahun. Pengecualian: Bengkulu −0,045 tetap setiap tahun, setara sekitar 3 menit, atau efek pagi seperti embun dan kabut pantai.

Konvensi interval juga dikonfirmasi oleh neraca nilai ukur (`d2c_rasio.csv`): rasio GHI/(DHI + DNI μ) pagi−sore hampir nol dengan μ rata-rata [t, t+9] di Jambi, Yogyakarta, Kalbar, dan Jawa Tengah (−0,014 sampai +0,002), sedangkan dengan μ awal t +0,013 sampai +0,040. Banten dan Bengkulu lebih cocok dengan μ awal t, yaitu selisih waktu kanal DHI/DNI di bawah satu slot.

**Dampak pada baseline** (`d4_persistence.csv`, uji 2025): R² smart persistence naik di keenam stasiun.

| Stasiun | R² SP lama → baru | Bias pagi (< 09) lama → baru, W m⁻² |
|---|---|---|
| Banten | 0,7220 → 0,7273 | +14,0 → +3,4 |
| Bengkulu | 0,8350 → 0,8377 | +5,3 → −6,3 |
| Jambi | 0,7349 → 0,7387 | +12,9 → +4,0 |
| Yogyakarta | 0,7300 → 0,7347 | +11,3 → +0,6 |
| Kalbar | 0,8022 → 0,8049 | +5,9 → −3,8 |
| Jawa Tengah | 0,8396 → 0,8428 | +8,2 → −1,8 |

Baseline yang lebih kuat akan sedikit menurunkan angka skill model di naskah.

## A2. Bendera QC

Kode asal per slot dan bit uji BSRN (README V6.1). Temuan:

- **Neraca tertutup persis** (dihitung, bukan diukur) kini terdeteksi dengan elevasi awal t: Bengkulu 67.728 slot (DNI tahun latih dan hampir seluruh 2023–2024), Jambi 19.261, Kalbar 14.559, Banten 5.142, Jawa Tengah 4.874, Yogyakarta 4.677.
- **Uji neraca dengan zenit tengah interval:** 335–1.122 slot siang per stasiun gagal, hampir semuanya nilai ukur logger pada elevasi 20–45°. Dengan elevasi awal slot tidak ada yang gagal, karena tahap 85 memperbaiki data dengan konvensi itu. Klaim naskah "all daytime values pass the radiation-budget test" bergantung pada konvensi zenit.
- Batas mungkin fisis tidak dilanggar; batas sangat jarang DHI dilanggar di 0–42 slot per stasiun.

## A3–A6. Pemeriksaan

- **A3 kalibrasi:** persentil 95 bulanan k_c GHI (elevasi > 30°) 1,02 (Banten) sampai 1,14 (Jambi), tren −1,3 sampai +0,7% per tahun, jadi GHI stabil. Selisih antarstasiun bisa dari Linke klimatologi atau kalibrasi, belum bisa dipisahkan. DNI: Jawa Tengah turun sekitar 3% per tahun (sesuai temuan tahap 83), Banten berfluktuasi antar-triwulan (persentil 95 0,78–1,00), Kalbar triwulan III 2022 dari DB v2 rendah. DNI ≈ 0 saat k_c > 0,8 hanya 1–273 slot per stasiun (Jambi terbanyak, triwulan II 2023), dengan DHI/GHI ≈ 1, mungkin nyata.
- **A4 horizon:** tidak ada sektor azimut dengan median k_c < 0,8 pada elevasi 2–15° di hari cerah; tidak terdeteksi halangan.
- **A5 satelit:** median COT per kelas k_c pada jendela H08 (Okt–Nov 2025) berada di antara nilai tahun-tahun H09 dan H08 sebelumnya; variasi antartahun (2022–2025) lebih besar dari selisih antarsatelit. Tidak terdeteksi lompatan.
- **A6 metadata** (`d3_A6_metadata.csv`): Banten, Kalbar, dan Yogyakarta cocok dengan catatan alat di DB v2 (≤ 0,06 km). Bengkulu dan Jawa Tengah tanpa catatan alat. Pusat CLP Bengkulu 3,1 km dari Tabel 1 masih perlu dikonfirmasi pengguna.

## Langkah berikutnya

Bangun Manuskrip Versi 6 dari V6.1 (`DATA_DIR` dan `CLEARSKY_DIR`). Perbarui naskah: Tabel 1 (Jambi; Bengkulu setelah dikonfirmasi), §2.1 (AWS SYNOP kausal, slot CLP tanpa berkas, clear-sky interval), kalimat uji neraca (sebut konvensi zenit), dan angka AWS di Abstrak.
