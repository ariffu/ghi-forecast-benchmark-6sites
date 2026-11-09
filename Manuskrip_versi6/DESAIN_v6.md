---
tags: [disertasi, prediksi-radiasi, manuskrip-v6]
created: 2026-11-08
status: "SELESAI 2026-11-09 — naskah, ESM, gambar, tabel dari V6.10; pemeriksa angka 175 OK; DOCX/PDF dibangun; menunggu persetujuan pembimbing"
---

> [!info] Rantai lengkap (2026-11-09)
> Urutan menjalankan (env V6.10, FEATSET=P2F):
> 1. `protokol/jalankan.ps1 pohon|nn`, lalu `protokol/04_daftar_periksa.py`;
> 2. `analisis/01_pipeline_v6.py`;
> 3. `paper_v2_clpbanten/114_pendukung_v610` (a1–a5: walk-forward, SHAP, sinyal sintetis, pencarian hiperparameter, seleksi prediktor);
> 4. `analisis/v6_01_analisis_tanpa_latih.py`, `v6_02_data_dan_sampel.py`;
> 5. `v6_08_gambar_alur_kerja.py`, `v6_13_gambar_peta.py`, `v6_03_gambar.py`;
> 6. `v6_04_isi_tabel.py`;
> 7. `v6_05_cek_angka.py` (harus lolos);
> 8. `v6_06_bangun_dokumen.py`.
>
> Setiap skrip salinan menyimpan sha256 sumber dan daftar penggantiannya di `asal_*.json`. Perubahan naskah: [[Catatan_Perubahan_v5_ke_v6]].

# Desain Manuskrip V6

**Data:** `Balai_data_v6_10`, beku dan lolos audit tahap 112. Prediktor P2F berjumlah 44: P2 ditambah `clp_cloud_frac`. Logika, hiperparameter, seed, dan split sama dengan V5.

## Rantai

1. **`protokol/`:** pelatihan 8 arsitektur × 5 seed × 6 stasiun. Lihat `protokol/README.md`. Pohon sudah selesai; NN berjalan.
2. **`analisis/01_pipeline_v6.py`:** analisis pendukung (ablasi, isian CLP, SYNOP, latensi, Ridge, referensi CP, subkelompok AWS, ablasi CatBoost). Skrip ini dibuat oleh `analisis/00_siapkan_pipeline_v6.py` dari `01_pipeline_v5.py`. Penggantiannya:
   - assert P2F, 44 prediktor;
   - data V6.10, varian `00_data` dan `00_data_rawfill`;
   - pemuat tahap 18b ditambah `clp_cloud_frac`.

   `clp_cloud_frac` otomatis masuk kelompok CLP pada `groups()`, karena awalan `clp_`.
3. **Sesudah itu:** padanan `04b`, `v4_01`, `v4_03`, `v4_04`, `05`, `v4_06` untuk tabel, gambar, cek angka, dan dokumen. Teks naskah V6 menunggu pembaruan §2.1 dan Tabel 1.

## Catatan untuk tahap yang tidak berubah kodenya

- **Tahap 31 (latensi):** penanganan khusus Kalbar tetap. CLP lima stasiun V6 sama dengan V5. CLP Jambi V6 juga sejalan dengan V5 tanpa geseran: korelasi log COT memuncak di lag 0 (0,965).
- **Tahap 18b (SYNOP dibawa maju):** di V6.10 elemen SYNOP prediktor (okta, CL/CM/CH, visibilitas, ww) sudah berlaku 60 menit (aturan V6.6). Akibatnya varian "orig" dan "asof" hampir sama. Kalimat naskah tentang manfaat as-of perlu ditulis ulang: as-of kini bagian dari database, bukan uji terpisah.

## Tahap 28 (statistik kotak CLP): diputuskan 2026-11-08, dibangun ulang dari chips

Data kotak lama (`28_clp_spatial/data`, ekstraksi lama) diganti dengan **`Balai_kotak_v6_10`**, dibangun di tahap 113 `paper_v2_clpbanten/113_kotak_chips`.

- **Verifikasi chips:** `chips_supplement_6.zip` berisi 1.390 hari (13 Mar 2022 – 31 Des 2025), chip 24×24 piksel 0,05°, 72 waktu WIB T. Untuk tiap stasiun ada satu jendela 11×11 (Kalbar 10×11) yang jumlah piksel COT-nya sama dengan CLOT_count CSV, dengan geseran waktu 0. Artinya kotak dan waktu chips = kotak dan waktu `clp_cot` V6.10.
- **Sumber nilai:** CSV kotak V6 (`6lokasi_output_chips.zip`), presisi penuh, 1.461 hari. CLOT_mean-nya sama persis dengan `clp_cot` V6.10. Nilai chip tidak dipakai karena tersimpan sebagai bilangan bulat terpotong (COT, CTH dalam km, CTT dalam K); simpangan baku CTH (~1 km) tidak bisa dihitung darinya. Faktor skala `meta` di chip tidak berlaku.
- **SPAT V6:** 6 fitur, yaitu `clps_cot_std`, `clps_cot_min`, `clps_cot_max`, `clps_cth_std`, `clps_cloud_frac_lag_60m`, `clps_cot_std_lag_60m`. Fitur `clps_cloud_frac` dikeluarkan karena identik dengan prediktor ke-44 `clp_cloud_frac`, yang sudah ada di T1+CLP dan FULL. Akibatnya uji E1/E2 V6 menjawab pertanyaan yang sedikit berbeda: adakah informasi sebaran kotak di luar rata-rata dan fraksi.
