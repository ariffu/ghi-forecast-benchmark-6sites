---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "DIKUNCI — keputusan pengguna 2026-11-08 (\"tambahkan fraksi awan dalam prediktor\"), sebelum pelatihan apa pun pada V6.2"
---

# Tahap 97 — himpunan prediktor P2F (44 = P2 + fraksi awan)

## Keputusan

Himpunan prediktor naskah V6 menjadi **P2F** = 43 prediktor P2 (tahap 50) ditambah satu: `clp_cloud_frac`.

Dasarnya fisis, bukan skor model. COT kotak (`clp_cot`) adalah rata-rata piksel berawan saja (audit tahap 95, C4), sehingga jumlah awan tidak terwakili. Di bawah langit berawan sebagian, k_c ≈ (1 − f) + f·T(COT): fraksi f dan COT saling melengkapi. Keputusan diambil sebelum model apa pun dilatih pada V6.2. Tidak ada uji skor yang dijalankan untuk memilihnya.

## Definisi

- Sumber: `Balai_data_v6_2/clp_ekstra/{s}_clp_ekstra.parquet`.
  - Pipeline `00_data`: kolom `clp_cloud_frac`, kosong bila tidak ada berkas atau SZA ≥ 80°.
  - Pipeline `00_data_rawfill`: kolom `clp_cloud_frac_raw`, sesuai konvensi rawfill (berkas ada tanpa retrieval → 0).
- Waktu t = T + 10, sama dengan `clp_*` lain. Tanpa turunan (lag, delta, rolling): hanya nilai sesaat, sama seperti `clp_cer_um`.
- Kelompok ablasi: awalan `clp_`, sehingga masuk kelompok CLP (D) secara otomatis di `27_block_bootstrap.groups`.

## Implementasi

- `_common.py`:
  - `FEATSET=P2F` mengaktifkan P2F. Nilai bawaannya tetap `P2`, agar V5 dan V6.1 bisa direproduksi.
  - `CLP_EKSTRA_DIR` wajib diisi bila memakai P2F.
  - `prepare` menggabungkan kolom fraksi menurut `ts_wib` setelah pemeriksaan 104 kandidat; `featset` memberi 44.
  - `P2_AKTIF` = daftar prediktor aktif.
- Pemeriksaan `FEATSET == "P2"` di skrip analisis tahap 60–80c diganti `FEATSET in ("P2", "P2F")`. Builder naskah V3 (49, 52) tidak diubah, karena khusus untuk 43 prediktor.

## Pelaporan

Ablasi kelompok CLP otomatis memuat fraksi. Naskah V6 menambah satu ablasi pra-terdaftar, P2F lawan P2 (tanpa fraksi), dengan CatBoost 5 seed, dan hasilnya dilaporkan apa pun hasilnya.
