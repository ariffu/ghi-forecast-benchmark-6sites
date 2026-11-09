---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "DESAIN — dikunci sebelum V6.2 dibangun; disetujui pengguna 2026-11-08 (\"Ya, bangun V6.2\")"
---

# Tahap 96 — database V6.2

Dasar: `Balai_data_v6_1` (beku, tidak diubah). Hasil: `C:\Users\ariff\Documents\Balai_data_v6_2`. Lima perbaikan dari audit tahap 95 ([[RINGKASAN_95]]). Tidak ada keputusan yang diambil dari skor model.

## Prinsip

- Skema `00_data` tetap 124 kolom, karena `_common.prepare` mengunci 104 kandidat prediktor. Kolom CLP baru ditaruh di folder terpisah `clp_ekstra/`.
- Protokol P2 (43 prediktor) tidak berubah. Apakah fraksi awan dipakai sebagai prediktor adalah keputusan terpisah, diambil sebelum pelatihan.
- Nilai yang dibuang menjadi kosong, tidak diinterpolasi (interpolasi memakai nilai masa depan).

## Perbaikan

| No | Perbaikan | Aturan | Berkas yang berubah |
|---|---|---|---|
| F1 | Koordinat Bengkulu | −3,864930; 102,311998; ketinggian 9 m. Clear-sky interval [t, t+9] dihitung ulang dengan cara tahap 94; bendera QC Bengkulu dihitung ulang dengan zenit baru | `clearsky/bengkulu_ineichen.parquet`, `clearsky/provenance.json`, `qc/bengkulu_qc.parquet` |
| F2 | Fraksi awan dan zenit CLP | dari `6lokasi_output_chips.zip`: `clp_cloud_frac` = CLOT_count/total_pixels (121; Kalbar 110), waktu t = T + 10; kosong bila tidak ada berkas; `clp_sza_scan_deg` = zenit matahari pada T + 5 menit (perkiraan waktu pindai) di koordinat stasiun; `qc_clp_sza` 0 (< 70°), 1 (70–80°), 2 (≥ 80°), 9 (tanpa berkas). `clp_cloud_frac` dikosongkan bila `qc_clp_sza` = 2, karena retrieval berhenti dan fraksi 0 bukan berarti cerah | `clp_ekstra/{s}_clp_ekstra.parquet` (baru) |
| F3 | Lonjakan tekanan | slot t dibuang bila a = x_t − x_{t−1} dan b = x_{t+1} − x_t sama-sama > 1,5 hPa dalam nilai mutlak, berlawanan tanda, dan \|x_{t+1} − x_{t−1}\| < 0,5·min(\|a\|, \|b\|) (naik lalu kembali dalam satu slot). Turunan `aws_pressure_lag_60m` dan `aws_pressure_delta_60m` dihitung ulang dengan definisi tahap 86/93. Berlaku untuk `00_data` dan `00_data_rawfill`; asal dicatat di `provenance` kolom `aws_lonjakan_tekanan` | `00_data`, `00_data_rawfill`, `provenance` |
| F4 | DHI mencurigakan | `qc_uji` menjadi uint16; bit 8 = k_d < 0,1 pada elevasi > 30° dan GHI > 300 W m⁻² (zenit tengah interval). Berlaku untuk keenam stasiun. Nilai DHI tidak diubah | `qc/{s}_qc.parquet` |
| F5 | Dokumentasi | README memuat catatan audit tahap 95 (Linke Remund, k_c > 1,3 di matahari rendah, malam = 0, `nett_wm2`, konvensi tekanan, RH jenuh, okta, paralaks, `solar_elev_deg` Jambi/Bengkulu, AOD) | `README.md` |

Ambang F3 (1,5 hPa per 10 menit dan harus kembali) jauh di atas perubahan tekanan nyata yang naik lalu turun dalam satu slot. Lompatan tekanan badai yang tidak kembali tidak terbuang.

## Amandemen 1 (2026-11-08, sebelum pelatihan apa pun)

Pemeriksaan sesudah build pertama menemukan blok tekanan yang melompat 3–5 hPa, bertahan 2–6 slot, lalu kembali mendadak. Contoh: Banten 19 Mar 2022 13.40–14.30 pada 1004,7 hPa di antara 1008,8; Bengkulu 10 Jun 2022 06.40–07.30 naik 3,3 hPa lalu turun 4,3 hPa. Tekanan nyata tidak berubah seperti itu. F3 diperluas: blok 1–6 slot (≤ 60 menit) dibuang bila lompatan masuk dan keluar sama-sama > 1,5 hPa, berlawanan tanda, dan nilai sesudah blok kembali ke dalam 0,5·min(lompatan) dari nilai sebelum blok. Dasarnya fisis, bukan skor model.

## Validasi

1. Semua kolom selain yang tercantum di atas identik dengan V6.1.
2. Clear-sky Bengkulu baru dicocokkan dengan hitungan tahap 95 (S3).
3. `_common.prepare` berjalan untuk keenam stasiun dengan `DATA_DIR` dan `CLEARSKY_DIR` V6.2: 104 kandidat, 43 prediktor.
4. Jumlah lonjakan per stasiun dibandingkan dengan audit tahap 95.
5. Lalu SHA256 dan hanya-baca.
