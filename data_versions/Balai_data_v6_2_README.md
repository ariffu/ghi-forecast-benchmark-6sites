# Database Versi 6.2 (tahap 96) — BEKU 2026-11-08

Dibangun dari `Balai_data_v6_1` (tidak diubah) dengan lima perbaikan dari audit tahap 95. Desain dan amandemen: `solardata_new_v2/paper_v2_clpbanten/96_v6_2/DESAIN_96.md`; laporan: `RINGKASAN_96.md` di folder yang sama.

## Isi dan perubahan terhadap V6.1

| Folder | Perubahan |
|---|---|
| `00_data`, `00_data_rawfill` | Hanya `aws_pressure_hpa`, `aws_pressure_lag_60m`, `aws_pressure_delta_60m` yang berubah. Lonjakan dan blok tekanan 1–6 slot yang melompat > 1,5 hPa lalu kembali dikosongkan, dan turunannya dihitung ulang. Skema tetap 124 kolom. |
| `provenance` | Kolom baru `aws_lonjakan_tekanan` (True = tekanan dikosongkan di V6.2). |
| `clearsky` | Bengkulu dihitung ulang dengan koordinat Stasiun Klimatologi Bengkulu −3,864930; 102,311998 (9 m). Stasiun lain identik dengan V6.1. |
| `qc` | Bengkulu dihitung ulang dengan zenit koordinat baru. `qc_uji` kini uint16; bit 0–7 sama dengan V6.1; **bit 8** = k_d < 0,1 pada elevasi > 30° dan GHI > 300 W m⁻² (DHI terlalu rendah untuk atmosfer tropis). Nilai DHI tidak diubah. |
| `clp_ekstra` (baru) | `clp_cloud_frac`: fraksi piksel berawan di kotak ±30 km (CLOT_count/121, Kalbar /110), dikosongkan bila SZA ≥ 80°. `clp_cloud_frac_raw`: tanpa pengosongan itu. `clp_sza_scan_deg`: zenit matahari pada perkiraan waktu pindai T + 5 menit. `qc_clp_sza`: 0 (< 70°), 1 (70–80°, COT/CER bias tinggi), 2 (≥ 80°, retrieval berhenti), 9 (tanpa berkas). Waktu t = T + 10, sama dengan `clp_*` di `00_data`. |

## Cara memakai

Pipeline naskah: `DATA_DIR=C:\Users\ariff\Documents\Balai_data_v6_2\00_data` dan `CLEARSKY_DIR=C:\Users\ariff\Documents\Balai_data_v6_2\clearsky`. Protokol P2 (43 prediktor) tidak berubah. `clp_ekstra` tidak dibaca pipeline; memakainya sebagai prediktor adalah perubahan protokol yang harus diputuskan sebelum pelatihan.

## Hal yang perlu diketahui pemakai (audit tahap 95)

- **COT kotak** (`clp_cot`) adalah rata-rata piksel berawan saja, bukan rata-rata seluruh kotak. Fraksinya ada di `clp_ekstra`. `clp_cloud_present_int` (COT ≥ 1) berarti "ada piksel berawan".
- **Clear-sky Linke Remund** tidak sempurna. Median k_c cerah: Banten dan Jawa Tengah 0,97, Yogyakarta 0,98, Bengkulu 1,00, Kalbar 1,03, Jambi 1,07.
- **k_c > 1,3** muncul di 0,4–1,8% slot siang, terutama pada elevasi 5–15°.
- **Malam:** ≥ 95% nilai radiasi malam dipaksa 0, sehingga offset termal tidak tercatat.
- **`nett_wm2`** = GHI − reflected (neto gelombang pendek), bukan radiasi neto total.
- **Konvensi tekanan:** AWS Jambi = SYNOP tekanan permukaan laut; SYNOP Yogyakarta = tekanan stasiun; SYNOP Banten dan Bengkulu = tekanan permukaan laut.
- **RH jenuh di malam hari:** Bengkulu 100%, Kalbar 98,1–98,2%, Jambi 95–97% (bilangan bulat).
- **Okta SYNOP** Banten dan Jambi janggal terhadap fraksi awan CLP.
- **Paralaks** tidak dikoreksi: sudut zenit satelit 36–45°, pergeseran median 4–9 km ke barat, masih di dalam kotak.
- **`solar_elev_deg`** Jambi masih dari koordinat lama (setara +1 menit), Bengkulu dari Tabel 1 lama. Dipakai untuk saringan elevasi > 5°; dampaknya diabaikan.
- **Penyinaran** hanya ada di Banten dan Kalbar; Kalbar biner dan kurang cocok dengan DNI pada 2022–2024.
- **AOD** hanya ada di Banten (26,5%) dan Kalbar (5%).
- Catatan V6.1 tetap berlaku: DNI Bengkulu hasil neraca (kode 3); uji neraca bergantung pada konvensi zenit; selisih waktu kanal Banten dan Bengkulu di bawah satu slot.
