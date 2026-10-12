---
tags: [disertasi, prediksi-radiasi, eksperimen, seleksi-prediktor, clpbanten-v2]
created: 2026-10-06
modified: 2026-10-06
---

# Evaluasi himpunan prediktor — desain terkunci (ditulis SEBELUM hasil)

> [!important] Tujuan
> Pembimbing menilai 104 prediktor (dan angka 94 di naskah lama) terlalu banyak. Evaluasi ini menguji apakah himpunan yang jauh lebih kecil memberi akurasi yang sama. Pemangkasan dilakukan dengan **aturan yang ditetapkan sebelum melihat skor**, bukan dengan memilih prediktor berdasarkan hasil uji.

## Temuan inventaris (data latih 2022–2023, 6 situs; dihitung sebelum model apa pun dilatih)
- Prediktor **kosong atau konstan di semua situs**: `is_day_noaa`, `is_day_cooper` (konstan karena mask elevasi > 5°), `synop_rainfall_24h_mm`, `synop_sunshine_h` (≥ 98,5 % kosong).
- Prediktor **hanya ada di 2 dari 6 situs**: `sunshine_slot_min` (Banten, Kalbar), `sunshine_cum_min` (Jogja, Semarang).
- **Duplikat** (|ρ Spearman| ≥ 0,99 di semua situs, besaran sama dengan nama/transformasi lain): `nett_wm2` ≡ `ghi_wm2`; `solar_elev_deg` ≡ `clear_sky_ghi`; `solar_elev_h1` ≡ `clear_sky_ghi_h1` ≡ `ghi_cs_t60` ≡ `elev_sin_t60`; `kt_std_1h` ≡ `kt_roll_60m_std`; `clp_ctt_k` ≈ `clp_cth_km` (0,993).
- Dua algoritme posisi matahari (NOAA dan Cooper) dipakai bersamaan: `kt_cooper`, `solar_elev_cooper_deg`, `clear_sky_ghi_cooper`.
- Geometri untuk jam ke-2 s.d. ke-6 (`solar_elev_h2..h6`, `clear_sky_ghi_h2..h6`, `is_day_h1..h6`) adalah warisan desain multi-horizon; target naskah hanya mencakup t+10 s.d. t+60 menit.
- Besaran yang diukur dua kali: suhu, titik embun, RH, tekanan, dan angin SYNOP (juga diukur AWS); `aws_ghi_wm2` (sensor GHI kedua, tidak ada di Banten); arah angin AWS dalam derajat sekaligus sin/cos.

## Aturan pemangkasan
| Kode | Aturan | Dibuang |
|---|---|---|
| R1 | Tidak informatif: kosong/konstan di data latih semua situs, atau tersedia di kurang dari separuh situs | `is_day_noaa`, `is_day_cooper`, `synop_rainfall_24h_mm`, `synop_sunshine_h`, `sunshine_slot_min`, `sunshine_cum_min` (6) |
| R2 | Duplikat: besaran sama dengan nama atau transformasi monoton lain (|ρ| ≥ 0,99 di semua situs) | `nett_wm2`, `solar_elev_deg`, `solar_elev_h1`, `ghi_cs_t60`, `elev_sin_t60`, `kt_std_1h`, `clp_ctt_k` (7) |
| R3 | Satu algoritme posisi matahari (NOAA) | `kt_cooper`, `solar_elev_cooper_deg`, `clear_sky_ghi_cooper` (3) |
| R4 | Relevansi horizon: hanya geometri periode target (t+10 s.d. t+60 menit) | `solar_elev_h2..h6`, `clear_sky_ghi_h2..h6`, `is_day_h1..h6` (16) |
| R5 | Satu sumber per besaran: AWS untuk meteorologi permukaan, piranometer stasiun untuk GHI | `synop_temp_c`, `synop_dewpoint_c`, `synop_rh_pct`, `synop_pressure_hpa`, `synop_wind_dir_deg`, `synop_wind_speed_kt`, `aws_ghi_wm2`, `aws_wind_dir_deg` (8) |
| R6 | Satu representasi riwayat: riwayat iradiansi lewat $k_t$ saja; riwayat dinyatakan sebagai perubahan (tendensi) dan statistik bergulir, bukan level ter-lag yang sudah ditentukan oleh level saat ini dan perubahannya; meteorologi permukaan sebagai level saat ini + perubahan 60 menit + hujan 3 jam | `ghi_lag_*` (4), `ghi_delta_*` (2), `accel_ghi_20m`, `kt_lag_*` (4), `accel_kt_20m` (= 2·Δ10 − Δ20), `clp_cot_lag_60m`, `aws_temp_lag_*` (3), `aws_rh_lag_60m`, `aws_pressure_lag_60m`, `aws_temp_roll_180m_mean`, `aws_rh_roll_180m_mean`, `aws_wind_speed_roll_180m_mean` (21) |

Catatan R6: `clp_cth_lag_60m` dipertahankan karena tidak ada prediktor perubahan CTH. Identitas "lag = level − perubahan" dan `accel_kt_20m` = 2·Δ10 − Δ20 diperiksa numerik oleh skrip dan dicatat di log.

Himpunan kandidat:
- **P0** = 104 prediktor (pembanding; konfigurasi naskah).
- **P1 "bersih"** = P0 − R1…R5 → 64 prediktor.
- **P2 "ringkas"** = P1 − R6 → 43 prediktor.

Pada P1 dan P2 kelompok "eksperimental" dilebur ke inti (sisa anggotanya hanya statistik bergulir $k_t$), sehingga hanya ada empat kelompok: inti, CLP, SYNOP, AWS. Kelompok SYNOP cloud (4) untuk ablasi tidak berubah.

## Model dan protokol (identik dengan pipeline naskah)
- **LightGBM residual**, konfigurasi ablasi (`lgbm()` di `27_block_bootstrap.py`; early stopping pada 2024).
- **CatBoost direct**, konfigurasi model utama (`04c_mean_6situs.py`).
- Target rata-rata jam, mask elevasi > 5°, split 2022–2023 / 2024 / 2025, 6 situs.
- Uji reproduksi sebelum dipakai: LightGBM T1+CLP (kelompok asli) = `07_replication/replication_ablation_mean.csv`; CatBoost P0 = `04c_mean_6situs/baseline_mean_6situs.csv` (assert |ΔR²| < 1e-4).
- ΔR² terhadap P0 dengan block bootstrap harian (`_blockboot.py`, 2000 resampel, seed 11).

## Aturan keputusan (pra-registrasi)
- **K1 — pilihan himpunan.** Dipilih himpunan **terkecil** yang R² validasinya (2024, LightGBM) ≥ R²(P0) − 0,002 di **keenam** situs. Bila P2 gagal di satu situs pun, P1 diuji dengan aturan yang sama; bila keduanya gagal, P0 dipertahankan. Tahun uji 2025 tidak dipakai untuk memilih.
- **K2 — pelaporan.** Untuk himpunan terpilih dilaporkan R² uji 2025 LightGBM dan CatBoost serta ΔR² terhadap P0 (CI blok harian). Selisih |ΔR²| < 0,002 dibaca "setara" (ambang naskah).
- **K3 — kesimpulan naskah.** Ablasi diulang dalam himpunan terpilih (inti, +CLP, +AWS, +SYNOP cloud, +CLP+AWS, +CLP+SYNOP cloud, penuh). Kesimpulan naskah dianggap **bertahan** bila: CLP signifikan di 6/6 situs; tambahan AWS di atas inti+CLP ≤ 0,01 di semua situs; tambahan SYNOP cloud ≤ 0,002 di semua situs. Perubahan arah atau signifikansi dilaporkan apa adanya.
- Model neural (MLP, sequence, hybrid) tidak diuji di sini. Bila himpunan baru diadopsi, seluruh pipeline (8 arsitektur, multi-seed, ablasi, bootstrap, SHAP) wajib dijalankan ulang.

## Berkas
Skrip: `50_evaluasi_prediktor.py`. Keluaran: `50_prediktor/` (`himpunan_prediktor.csv`, `hasil_himpunan.csv`, `ablasi_himpunan.csv`, `RINGKASAN_50.md`). Log: `logs/50_evaluasi_prediktor.log`.
