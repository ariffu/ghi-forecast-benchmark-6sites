---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — Balai_data_v6_5 BEKU 2026-11-08 (SHA256, hanya-baca); lolos audit; database aktif untuk running uji"
---

# Tahap 102 — ringkasan: V6.5

Desain: [[DESAIN_102]] dengan tiga amandemen. Skrip:
- `l1_bangun_v65.py`: build dari V6.3, termasuk uji kausalitas tiga titik potong per stasiun.
- `l0_salin_audit.py`: menyalin audit `m1` (lompatan), `m2` (SYNOP bulanan), `m3` (fraksi awan, kebocoran, kelengkapan), `m4` (sensor macet).
- `m5_identik_pipeline.py`.

README database: `C:\Users\ariff\Documents\Balai_data_v6_5\README.md`.

## Tiga amandemen selama build (semua sebelum audit akhir, tanpa skor model)

1. Fraksi "berasal SYNOP" dihitung di semua slot siang tahun latih, bukan hanya jam laporan. Sebelumnya angin Banten keliru ikut dibangun ulang.
2. Klimatologi isian dihaluskan ±30 menit.
3. Klimatologi deret yang dibangun ulang dihitung dari semua slot tahun latih. Sebelumnya RH Banten melompat pukul 20–22 karena slot SYNOP malam hampir kosong.

## Hasil audit

| Uji | V6.3 | V6.4 | V6.5 |
|---|---|---|---|
| Bulan menyimpang dari SYNOP | 82 | 7 | **6** |
| Lompatan tekanan Banten (> 1 hPa) | 287 | 576 | **216** |
| Lompatan suhu Jambi (> 2 °C) | 593 | 895 | **545** |
| Lompatan tekanan Yogyakarta | 156 | 308 | **116** |
| Lompatan angin Banten (> 5 m/s) | 166 | 405 | **128** |

- **Deret yang dibangun ulang** (suhu/RH Banten; suhu/RH/tekanan/angin Jambi): semua lompatan tepat di jam laporan, yaitu informasi laporan baru; di luar jam laporan 0. Jumlahnya naik (misalnya RH Banten 416 → 793, tekanan Jambi 310 → 577), karena SYNOP per jam sendiri berubah melebihi ambang (tekanan Jambi > 1 hPa antar-laporan di 11% laporan).
- **Deret logger:** lompatan setara V6.3, kecuali angin Jawa Tengah (25 → 94) dan Kalbar (13 → 39), akibat penskalaan k ke level SYNOP.
- **Tidak ada kebocoran waktu** di 44 prediktor. Fraksi awan identik dengan audit sebelumnya.
- **Sensor macet:** angin Jambi tenang 9–16% → 0. Sisa: arah Jambi 0 saat tenang, RH jenuh Bengkulu/Kalbar 2–4%.
- **Identik dengan V6.3:** `clearsky`, `qc`, `clp_ekstra`, kolom non-meteorologi, provenance lama.
- **Pipeline P2F:** 44 prediktor. Suhu/RH Banten kosong 6% origin (06.30–06.50, sebelum laporan pertama).

## Catatan naskah

- Meteorologi AWS beracuan SYNOP; angin di level SYNOP.
- Bengkulu tekanan/angin validasi–uji sebagian besar dari SYNOP (sensor rusak); Kalbar suhu uji 38% dari SYNOP; Yogyakarta tekanan uji 27%.
- Okta/CM/CH Yogyakarta kosong di tahun latih; arah angin Kalbar kosong.
