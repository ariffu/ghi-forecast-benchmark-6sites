---
tags: [disertasi, prediksi-radiasi, eksperimen, clear-sky, paper-v3, clpbanten-v2]
created: 2026-10-07
modified: 2026-10-07
---

# Model langit cerah dan smart persistence standar — desain terkunci (ditulis SEBELUM hasil)

> [!important] Latar
> Audit v3 ([[AUDIT_v3_Kemiripan_Model]]) menemukan bahwa database memakai GHI langit cerah = 1100 × sin(elevasi) secara eksak, tanpa massa udara dan kekeruhan. Akibatnya $k_t$ = GHI/(1100 sin h) adalah indeks kecerahan berskala, dan "smart persistence" sebenarnya persistensi indeks kecerahan. Penulis memutuskan (2026-10-07) memakai model langit cerah dan smart persistence yang lazim di literatur.

## Definisi baru
- **Model langit cerah:** Ineichen–Perez (Ineichen & Perez 2002), lewat `pvlib` 0.15 (Holmgren et al. 2018). Kekeruhan Linke dari klimatologi bulanan Remund et al. (2003), yaitu berkas `LinkeTurbidities.h5` bawaan pvlib, diinterpolasi harian. Massa udara dan posisi matahari dihitung pvlib (SPA).
- **Ketinggian stasiun:** `pvlib.location.lookup_altitude` (dataset bawaan), nilai negatif dibulatkan ke 0. Database tidak menyimpan ketinggian.
- **Waktu evaluasi:** pada label waktu (WIB = UTC+7), sama dengan `solar_elev_deg` di database (selisih median dengan pvlib 0,08°).
- **Indeks langit cerah:** $k_c$ = GHI / GHI$_{cs}$. Domainnya sama dengan $k_t$ database (terdefinisi bila $k_t$ terdefinisi, elevasi ≳ 1°); dipotong ke [0, 2] untuk meredam ledakan nilai dekat matahari terbit/terbenam. Fraksi yang terpotong dilaporkan.
- **Smart persistence (standar):** $\hat{y}_{SP}$ = $k_c(t)$ × rerata GHI$_{cs}$ pada t+10 … t+60 menit (target rata-rata jam), dan $k_c(t)$ × GHI$_{cs}$(t+60) untuk target sesaat.
- **Prediktor:** himpunan 43 tetap, nama kolom tetap. Kolom `kt` dan turunannya (perubahan 10–60 menit, rerata/simpangan baku bergulir, `kt_std_3h`) dihitung ulang dari $k_c$ dengan definisi database yang sudah direproduksi eksak:
  - `shift` untuk lag/perubahan;
  - `rolling(n, min_periods=1)` untuk rerata;
  - simpangan baku ddof = 1.
  - `clear_sky_ghi` dan `clear_sky_ghi_h1` diganti GHI$_{cs}$ Ineichen–Perez pada t dan t+60.
- **Kelas kondisi langit** (stratifikasi, uji tekstur awan, diagnostik waktu CLP) tetap memakai indeks kecerahan lama (`kt_clearness` = GHI/(1100 sin h), ambang 0,30/0,65), supaya definisinya tidak berubah.
- **Target tidak berubah** (rerata GHI terukur t+10 … t+60), begitu juga mask (elevasi > 5°), split, hiperparameter, dan himpunan prediktor.

## Implementasi
- `55_clearsky_ineichen.py` → `55_clearsky/` dan cache `00_clearsky/{situs}_ineichen.parquet`.
- `_common.apply_clearsky()` dengan saklar `CLEARSKY=IP|SIMPLE`. `SIMPLE` mereproduksi definisi lama untuk arsip.
- `00_data/` tidak diubah, sehingga SHA yang dikunci paper footprint tetap sah.

## Cek wajib
1. Mode `SIMPLE` mereproduksi kolom database secara eksak (fungsi turunan sama).
2. Pada hari cerah, median $k_c$ siang (elevasi > 20°) berada di 0,85–1,15, dan variasi diurnal $k_c$ lebih datar daripada $k_t$.
3. R² dan RMSE smart persistence baru dilaporkan berdampingan dengan versi lama.
4. Registri: R² smart persistence pipeline = perhitungan ulang independen dari cache langit cerah (C11 baru).

## Ekspektasi (sebelum hasil)
- Smart persistence menjadi lebih kuat, terutama pagi dan sore, sehingga skill model terhadap smart persistence turun.
- R² model ML berubah kecil, karena target tetap dan model fleksibel; kesimpulan naskah diperkirakan bertahan.
- Hasil dilaporkan apa adanya, termasuk bila berbeda dari ekspektasi.
