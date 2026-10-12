---
tags: [disertasi, prediksi-radiasi, eksperimen, seleksi-prediktor, clpbanten-v2]
created: 2026-10-06
modified: 2026-10-08
status: "SELESAI — P2 (43) lolos K1 dan K3; DIADOPSI 2026-10-06; diulang dengan Ineichen–Perez 2026-10-08: P2 tetap lolos"
---

# Ringkasan tahap 50 — evaluasi himpunan prediktor

> [!success] Hasil
> **43 prediktor (P2) setara dengan 104.** Himpunan ringkas lolos kriteria validasi di keenam situs (K1), selisih R² uji 2025 tetap di bawah ambang naskah 0,002 untuk LightGBM maupun CatBoost (K2), dan ketiga kesimpulan ablasi bertahan (K3). Desain dan aturan keputusan dikunci sebelum hasil: [[DESAIN_TERKUNCI_50]].

## Mengapa 104 terlalu banyak
Inventaris data latih (2022–2023, 6 situs) menunjukkan bahwa 61 dari 104 prediktor kosong, duplikat, tidak relevan untuk horizon 1 jam, atau sudah terwakili prediktor lain:

| Aturan | Isi | n |
|---|---|---:|
| R1 | kosong/konstan di semua situs, atau hanya ada di 2 dari 6 situs (`is_day_*`, hujan 24 jam dan penyinaran SYNOP, `sunshine_*`) | 6 |
| R2 | duplikat dengan nama lain (net ≡ GHI, elevasi ≡ GHI cerah, `ghi_cs_t60` ≡ `elev_sin_t60` ≡ GHI cerah t+1 jam, `kt_std_1h` ≡ `kt_roll_60m_std`, CTT ≈ CTH) | 7 |
| R3 | algoritme posisi matahari kedua (Cooper) | 3 |
| R4 | geometri jam ke-2 s.d. ke-6 (warisan desain multi-horizon) | 16 |
| R5 | besaran yang diukur dua kali (meteorologi SYNOP vs AWS, sensor GHI kedua di AWS, arah angin dalam derajat sekaligus sin/cos) | 8 |
| R6 | level ter-lag yang **eksak** = level saat ini − perubahannya (sisa numerik 0 di semua situs), riwayat GHI yang sudah terwakili $k_t$, lag/rerata bergulir meteorologi permukaan | 21 |

P1 "bersih" = 104 − R1…R5 = **64**; P2 "ringkas" = P1 − R6 = **43**.

## K1 — pemilihan (validasi 2024, LightGBM)
ΔR² validasi terhadap P0, P2: −0,0008 s.d. +0,0021; P1: −0,0008 s.d. +0,0021. Keduanya ≥ −0,002 di keenam situs → **P2 terpilih** (terkecil yang lolos).

## K2 — uji 2025 (ΔR² terhadap 104 prediktor, CI blok harian)
| Situs | LightGBM P2 | CatBoost P2 | RMSE CatBoost 104 → 43 (W m⁻²) |
|---|---:|---:|---|
| Banten | +0,0006 | −0,0017* | 92,3 → 92,9 |
| Bengkulu | −0,0004 | −0,0007 | 89,4 → 89,7 |
| Jambi | −0,0010* | −0,0013* | 90,8 → 91,3 |
| Yogyakarta | −0,0002 | −0,0009 | 109,8 → 110,1 |
| Kalimantan Barat | +0,0011* | +0,0003 | 99,8 → 99,6 |
| Jawa Tengah | −0,0002 | +0,0001 | 96,2 → 96,2 |

\* interval blok harian tidak memuat nol. Semua |ΔR²| < 0,002, jadi menurut ambang naskah semuanya **setara**. Kerugian terbesar CatBoost (Banten, −0,0017) setara dengan +0,6 W m⁻² RMSE.

## K3 — kesimpulan naskah dalam P2 (ablasi LightGBM, ΔR²)
| Situs | CLP | AWS | SYNOP cloud | AWS di atas CLP | SYNOP cloud di atas CLP |
|---|---:|---:|---:|---:|---:|
| Banten | +0,0125* | +0,0057* | −0,0002 | +0,0060* | 0,0000 |
| Bengkulu | +0,0168* | +0,0003 | +0,0001 | +0,0009 | 0,0000 |
| Jambi | +0,0248* | +0,0014 | +0,0010* | −0,0006 | +0,0003 |
| Yogyakarta | +0,0286* | +0,0013 | +0,0009* | +0,0017 | +0,0007 |
| Kalimantan Barat | +0,0180* | +0,0036* | −0,0003 | +0,0022* | −0,0005* |
| Jawa Tengah | +0,0152* | +0,0030* | +0,0007* | +0,0015* | +0,0006* |

Dengan 104 prediktor (naskah): CLP +0,0129 s.d. +0,0275; AWS di atas CLP maks +0,0061 (Banten); SYNOP cloud maks +0,0011. **Ketiga kriteria K3 terpenuhi**: CLP signifikan 6/6, AWS di atas CLP ≤ 0,01, SYNOP cloud ≤ 0,002. Hasil P1 (64) serupa (`ablasi_himpunan.csv`).

## Usulan Tabel 2 naskah (P2)
| Group | Content | n |
|---|---|---:|
| Core | GHI, DHI, DNI and reflected irradiance at the origin; clearness index $k_t$ with its 10-, 20-, 30- and 60-min changes, 30- and 60-min rolling means and standard deviations and 3-h standard deviation; clear-sky GHI at the origin and for the target hour; solar declination and equation of time | 18 |
| Satellite cloud (CLP) | cloud optical thickness (with 60-min change and 3-h mean), cloud-top height (60-min lag and 3-h mean), effective radius and cloud flag | 8 |
| SYNOP | total cloud cover, low/middle/high cloud type, visibility and present weather | 6 |
| Surface meteorology (AWS) | temperature, relative humidity and pressure (each with its 60-min change), wind speed and direction (sine, cosine), 10-min and 3-h rainfall | 11 |
| **Total** | | **43** |

## Ulangan dengan langit cerah Ineichen–Perez (2026-10-08 05:03)

> [!info] Mengapa diulang
> Sejak 2026-10-07 pipeline memakai GHI langit cerah Ineichen–Perez dan indeks langit cerah $k_c$ (LAPORAN §25, [[DESAIN_CLEARSKY_55]]). Seleksi di atas dihitung dengan definisi lama (1100 · sin h), jadi tahap 50 diulang dengan aturan R1–R6 dan kriteria K1–K3 yang **sama**. Hasil versi lama diarsipkan di `_arsip_P2_cs1100/50_prediktor/`.

**Penyesuaian untuk mode Ineichen–Perez:**
- 104 kandidat: kolom `kt*`, `clear_sky_ghi*`, dan `ghi_cs_t60` memakai Ineichen–Perez. `ghi_cs_t60` di DB identik dengan `clear_sky_ghi_h1`, jadi ikut diganti di `_common.apply_clearsky()`; kolom ini tidak termasuk 43 prediktor. Kolom Cooper (R3) tetap versi DB.
- Uji reproduksi kini terhadap pipeline 43 prediktor: LightGBM T1+CLP (pengelompokan P2) = tahap 07, dan CatBoost P2 = 04c. Hasilnya 12/12 OK; durasi 433 detik.
- R2 membuang elevasi (`solar_elev_deg`, `solar_elev_h1`, `elev_sin_t60`) sebagai duplikat GHI cerah. Dengan Ineichen–Perez hubungannya tidak lagi eksak, karena ada massa udara dan kekeruhan bulanan, tetapi tetap hampir monoton: korelasi peringkat siang hari 0,9954–0,9993. K1 menguji apakah ini berpengaruh.

**K1 (validasi 2024, LightGBM):**
- ΔR² P2 − P0 = −0,0011 s.d. +0,0011; versi lama −0,0008 s.d. +0,0022.
- ΔR² P1 − P0 = −0,0009 s.d. +0,0011.
- K1: P2 lolos, P1 lolos → **P2 terpilih** (sama dengan sebelumnya).

| Situs | Δ val. P2 (IP) | Δ val. P2 (lama) | Uji LightGBM P2 − P0 | Uji CatBoost P2 − P0 | RMSE CatBoost 104 → 43 (W m⁻²) |
|---|---:|---:|---:|---:|---|
| Banten | −0,0011 | −0,0007 | +0,0000 | −0,0013 | 92,5 → 92,9 |
| Bengkulu | −0,0003 | −0,0005 | +0,0003 | −0,0016* | 88,8 → 89,5 |
| Jambi | −0,0005 | −0,0005 | −0,0019* | −0,0012* | 90,7 → 91,1 |
| Yogyakarta | −0,0004 | +0,0001 | +0,0006 | −0,0019* | 109,6 → 110,3 |
| Kalimantan Barat | +0,0011 | +0,0022 | +0,0007 | +0,0006* | 99,5 → 99,2 |
| Jawa Tengah | −0,0009 | −0,0008 | −0,0003 | +0,0004 | 96,1 → 95,9 |

\* interval blok harian tidak memuat nol. Tahun uji hanya dilaporkan.

**K3, ablasi LightGBM dalam P2 (ΔR²):**

| Situs | CLP | AWS | SYNOP cloud | AWS di atas CLP | SYNOP cloud di atas CLP |
|---|---:|---:|---:|---:|---:|
| Banten | +0,0115* | +0,0052* | +0,0002 | +0,0066* | +0,0003 |
| Bengkulu | +0,0152* | −0,0008 | +0,0003 | +0,0015* | +0,0004 |
| Jambi | +0,0243* | +0,0012 | +0,0004 | +0,0002 | +0,0001 |
| Yogyakarta | +0,0290* | +0,0014 | +0,0009* | +0,0006 | +0,0000 |
| Kalimantan Barat | +0,0180* | +0,0040* | −0,0002 | +0,0030* | +0,0000 |
| Jawa Tengah | +0,0149* | +0,0028* | +0,0002 | +0,0013 | +0,0002 |

Kriteria K3: CLP signifikan 6/6 ✔; AWS di atas CLP ≤ 0,01 ✔; SYNOP cloud ≤ 0,002 ✔.

## Batasan
- Hanya LightGBM dan CatBoost. MLP dan model hybrid juga memakai vektor prediktor datar; LSTM/Transformer murni (14 kanal mentah) tidak terpengaruh.
  - *Terbukti setelah adopsi:* MLP 6 situs (target langsung) turun 0,004–0,010 dengan 43 prediktor, konsisten di 5 seed. Model hybrid dan model pohon praktis tidak berubah. Lihat LAPORAN §22.
- Bila P2 diadopsi, **seluruh** angka naskah berubah sedikit, sehingga pipeline perlu dijalankan ulang: 8 arsitektur, multi-seed, ablasi, block bootstrap, SHAP dan kurva seleksi, stratifikasi, serta sensitivitas.

## Berkas
`50_evaluasi_prediktor.py` · `himpunan_prediktor.csv` (keanggotaan dan aturan per prediktor) · `hasil_himpunan.csv` · `ablasi_himpunan.csv` · `keputusan_50.json` · `preds_<situs>.npz` · log `logs/50_evaluasi_prediktor.log` (run Ineichen–Perez, 433 detik; log run 2026-10-06 di `_arsip_P2_cs1100/logs/`).
