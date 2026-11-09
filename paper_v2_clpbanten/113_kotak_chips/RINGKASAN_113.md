---
tags: [disertasi, prediksi-radiasi, clp, manuskrip-v6]
created: 2026-11-08
status: "SELESAI — Balai_kotak_v6_10 beku; kotak, waktu, dan nilai (periode berskala) terverifikasi dengan chips_supplement_6; tahap 28 V6 memakai 6 fitur kotak"
---

# Tahap 113 — statistik kotak CLP untuk Manuskrip V6 (pengganti data tahap 28 lama)

Keputusan pengguna (2026-11-08): bangun ulang statistik kotak dari chips, memakai `C:\Users\ariff\Documents\chips_supplement_6.zip`.

## Isi chips_supplement_6.zip

- 1.390 berkas harian `CHIPS_SUPPLEMENT_<tanggal>.npz`, 13 Mar 2022 – 31 Des 2025. Hari 1 Jan – 12 Mar 2022 tidak ada.
- Per stasiun dan waktu: CLOT, CLTT, CLTH, CLER_23 (int16) dan CLTYPE (uint8). Chip berukuran 24×24 piksel 0,05° (±0,6°), dengan sumbu lat/lon.
- Kunci waktu `HHMM` 06.00–18.00 adalah waktu berkas dalam WIB (T).
- **Pengodean nilai berganti pada 2024-06-01:**
  - **13 Mar 2022 – 31 Mei 2024 (811 hari):** nilai fisis dipotong ke bilangan bulat (COT 6,06 → 6, CTH 12,65 km → 12, CTT 218,1 K → 218). Faktor skala `meta` tidak berlaku.
  - **1 Jun 2024 – 31 Des 2025 (579 hari):** int16 berskala benar (raw × skala + offset, sesuai `meta`).
  - Bila chips dipakai sebagai sumber nilai, presisi data latih (2022–2023) akan berbeda dari data uji (2025).

## Z1/Z2 — kotak dan waktu

Pencarian semua jendela pada 24 hari sampel (`z1_cocok.py`) menemukan, untuk tiap stasiun, satu jendela seukuran kotak CSV (11×11; Kalbar 10×11) dengan geseran waktu 0. Pada jendela itu, jumlah piksel COT sah = CLOT_count CSV di 100% baris. Jendela tetangganya hanya cocok 28–41%.

Verifikasi seluruh 1.390 hari (`z2_verifikasi.py`, `z2_verifikasi.json`):
- CLOT_count = jumlah piksel COT sah di **100%** dari 99.794 slot berkas per stasiun (Jawa Tengah 99.793).
- Uji "dipotong ke bawah" min/maks hanya cocok 58%, karena berlaku sampai 31 Mei 2024 saja.

**Periode berskala (Jun 2024 – Des 2025, 12 hari sampel):** mean, std (ddof = 0), min, dan maks piksel chip untuk COT dan CTH sama dengan CSV di 100% baris dan keenam stasiun. Jadi statistik CSV adalah statistik piksel jendela itu, dengan simpangan baku populasi.

Kesimpulan: **kotak dan waktu chips = kotak dan waktu `clp_cot` V6.10.** Pusatnya:

| Stasiun | Pusat kotak |
|---|---|
| Banten | −6,2615; 106,7508 |
| Bengkulu | −3,86; 102,31 |
| Jambi | −1,602; 103,485 (ASRS) |
| Yogyakarta | −7,731; 110,354 |
| Kalbar | 0,075; 109,19 |
| Jawa Tengah | −6,9847; 110,3806 |

## Z3 — Balai_kotak_v6_10 (beku)

`C:\Users\ariff\Documents\Balai_kotak_v6_10`: 6 parquet, README, SHA256, laporan; hanya-baca.

**Sumber nilai** adalah CSV kotak `6lokasi_output_chips.zip` (presisi penuh, 1.461 hari), bukan nilai chip:
- CLOT_mean CSV = `clp_cot` V6.10 persis di semua slot dan keenam stasiun;
- tidak ada hari skala ganda.

Nilai chip tidak dipakai, karena sebelum Juni 2024 berupa bilangan bulat terpotong, sehingga simpangan baku CTH (median ~2 km, resolusi 1 km) dan COT kecil rusak. Pada periode chips berskala, CSV terbukti sama dengan piksel chip.

**Konvensi:** t = T + 10. Fitur kosong bila tidak ada berkas; statistik COT/CTH kosong bila kotak tanpa piksel berawan, sama dengan `clp_cot`.

| Fitur | Definisi |
|---|---|
| `clps_cot_std`, `clps_cot_min`, `clps_cot_max` | CLOT_std/min/max kotak |
| `clps_cth_std` | CLTH_std |
| `clps_cloud_frac` | = `clp_cloud_frac` V6.10 |
| `*_lag_60m` | geser 6 slot |

## Z4 — validasi

- **V1:** SHA256 cocok, hanya-baca.
- **V2 kausal:** statistik berasal dari baris CSV yang sama dengan `clp_cot`, sehingga waktunya identik dan kausalitasnya terjamin oleh konstruksi. Kurva korelasi lag dengan k_c datar (beda puncak lawan lag 0 ≤ 0,03), jadi lag puncak tidak bermakna sebagai uji.
- **V3 fisis:** min ≤ `clp_cot` ≤ maks di semua slot; std tidak negatif; std tidak pernah kosong saat berawan; std CTH maks 6,6–7,1 km; lag benar.
- **V4 siklus harian:** median std CTH 1,4–2,6 km. Naik pukul 11–14 WIB (awan konvektif bertingkat) dan turun sore dan pagi di keenam stasiun.
- **V5 banding data lama:** lima stasiun r = 1,0000 dengan data tahap 28 lama. Jambi r = 0,90–0,97, karena kotak kini di ASRS, bukan 19 km ke timur. Jadi perubahan nyata terhadap tahap 28 lama hanya Jambi, ditambah pengeluaran fraksi.

## Dampak ke Manuskrip V6

`Manuskrip_versi6/analisis/01_pipeline_v6.py` (generator `00_siapkan_pipeline_v6.py`) membaca `Balai_kotak_v6_10`. SPAT V6 terdiri dari 6 fitur; `clps_cloud_frac` dikeluarkan karena identik dengan prediktor ke-44. Pipeline memastikannya dengan assert `clps_cloud_frac` = `clp_cloud_frac`.

Jadi E1/E2 V6 menguji informasi sebaran kotak di luar rata-rata COT dan fraksi awan.
