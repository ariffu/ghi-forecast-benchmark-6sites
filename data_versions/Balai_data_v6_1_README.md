# Database Versi 6.1 (tahap 94) — BEKU 2026-11-08

`00_data`, `00_data_rawfill`, dan `provenance` identik dengan `Balai_data_v6` (hash dicek sama). V6.1 menambahkan tiga hal sesuai kaidah dataset radiasi dan satelit, tanpa mengubah satu nilai pun di parquet:

1. **`clearsky/`** — Ineichen–Perez dirata-ratakan dari nilai per menit pada interval yang sama dengan pengukuran, [t, t+9]. GHI, DNI, dan DHI cerah tersedia. Koordinat dan ketinggian dari metadata stasiun (Tabel 1), Jambi di ASRS (−1,60111; 103,4944; 24 m). Linke Remund (2003).
2. **`qc/{stasiun}_qc.parquet`** — bendera per slot gaya BSRN:
   - `qc_ghi`, `qc_dhi`, `qc_dni`, `qc_refl`: 0 = diukur logger, 1 = diukur dari sumber sekunder (portal, DB v2, tabel 10 menit, trapesium), 2 = diperbaiki ke batas fisis, 3 = dihitung atau dimodelkan (termasuk neraca yang tertutup persis), 8 = malam, 9 = kosong.
   - `qc_uji`: bit uji Long & Shi (2008) pada nilai akhir dengan zenit tengah interval. Bit 0–2 batas mungkin fisis GHI, DHI, DNI; bit 3–5 batas sangat jarang; bit 6 neraca GHI/(DHI + DNI cos Z) ±8% (Z < 75°) atau ±15%; bit 7 rasio difus.
3. **README dan `SHA256.txt`**; seluruh berkas hanya-baca.

## Cara memakai

Pipeline naskah: `DATA_DIR=C:\Users\ariff\Documents\Balai_data_v6_1\00_data` dan `CLEARSKY_DIR=C:\Users\ariff\Documents\Balai_data_v6_1\clearsky`. Tanpa `CLEARSKY_DIR`, `_common.py` memakai `00_clearsky` lama (titik t) sehingga V5 tetap bisa direproduksi.

## Hal yang perlu diketahui pemakai

- **Clear-sky lama bias waktu.** Clear-sky pada titik t untuk GHI rata-rata [t, t+9] membuat k_c terlalu tinggi sekitar 4% di pagi hari dan terlalu rendah sekitar 4% di sore hari. Dengan clear-sky interval, smart persistence (uji 2025) membaik di keenam stasiun: R² naik 0,003–0,005, dan bias pagi turun dari +5…+14 menjadi −6…+4 W m⁻².
- **Neraca BSRN.** Dengan zenit tengah interval, 295–998 slot siang per stasiun (0,3–1%) gagal uji neraca ±8%, sebagian besar nilai ukur logger pada elevasi 20–45°. Dengan elevasi awal slot (konvensi DB v2 dan tahap 85) tidak ada yang gagal. Klaim "semua nilai lolos uji neraca" hanya berlaku dengan konvensi lama.
- **DNI Bengkulu** di tahun latih dan hampir seluruh 2023–2024 adalah hasil neraca (kode 3, 67.728 slot), bukan ukuran.
- **Selisih waktu kanal di bawah satu slot.** Pada nilai ukur, rasio neraca Banten dan Bengkulu lebih cocok dengan elevasi awal slot daripada interval, dan k_c cerah Bengkulu pagi lebih rendah sekitar 0,045 dari sore setiap tahun (setara sekitar 3 menit). Tidak dikoreksi.
- **Kalibrasi:** persentil 95 k_c GHI per stasiun 1,02–1,14 tanpa drift berarti (−1,3 sampai +0,7% per tahun). DNI kurang stabil: Banten berfluktuasi, Jawa Tengah turun sekitar 3% per tahun.
- **Horizon:** tidak ada sektor azimut dengan k_c cerah rendah (< 0,8) di matahari rendah.
- **Satelit:** tidak ada lompatan hubungan CLP–radiasi yang bisa dipisahkan dari variasi antartahun pada pergantian Himawari-8/9.
- **Metadata:** koordinat Banten, Kalbar, dan Yogyakarta cocok dengan catatan alat di DB v2 (≤ 0,06 km). Bengkulu dan Jawa Tengah tidak punya catatan alat; pusat kotak CLP Bengkulu (−3,86; 102,31) berjarak 3,1 km dari Tabel 1.

Laporan lengkap: `solardata_new_v2/paper_v2_clpbanten/94_v6_1/RINGKASAN_94.md`.
