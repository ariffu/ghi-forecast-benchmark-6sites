---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — Balai_data_v6_3 BEKU 2026-11-08 (SHA256, hanya-baca, 40 berkas); siap running uji"
---

# Tahap 99 — ringkasan: V6.3 (Bengkulu dan Banten)

Desain: [[DESAIN_99]] dengan amandemen 1 (tekanan datar) dan amandemen 2 (Banten Jan–Mar 2022). Skrip:
- `i1_uji_isian.py`: akurasi isian.
- `i2_bangun_v63.py`: build Bengkulu.
- `i3_cek_synop_v63.py`: cek ulang dengan SYNOP.
- `i4_tekanan_datar.py`: tekanan datar.
- `i6_banten_qff2022.py`: Banten.
- `i5_validasi.py`: validasi akhir.

README database: `C:\Users\ariff\Documents\Balai_data_v6_3\README.md`.

## Isian kausal SYNOP

| Stasiun | Variabel | Periode | Terisi | Kalibrasi |
|---|---|---|---|---|
| Bengkulu | angin | Jul 2024 – Agu 2025 | 38.857 / 61.488 slot (origin 96,9%) | 0,712·S + 0,358 |
| Bengkulu | tekanan | Apr 2024 – Agu 2025 | 47.138 / 74.592 (origin 96,9%) | QFE − 0,022 |
| Banten | tekanan | Jan–Mar 2022 | 8.190 / 12.960 (origin 94,5%) | QFF − 3,25 |
| Banten, Jawa Tengah, Jambi, Yogyakarta | tekanan datar ≥ 3 jam di luar periode | 2022–2025 | 653, 56, 73, 45 | per stasiun |

Akurasi isian pada periode sehat (umur laporan ≤ 60 menit): tekanan RMSE 0,33 hPa (r 0,98), angin 0,61–0,69 m/s (r 0,72–0,80).

## Temuan yang mengubah rencana

- Saringan lonjakan V6.2 di Bengkulu membuang nilai :00 yang benar. Yang salah adalah logger di menit :10–:50. Sekarang seluruh periode memakai SYNOP.
- Banten Jan–Mar 2022 bukan hanya datar: seluruh periode berisi QFF SYNOP mentah (+3,2 hPa) yang ditahan di antara laporan. Mengisi slot datar saja memunculkan 254 langkah > 2 hPa; sesudah seluruh periode diganti, tersisa 85 (V6.2: 74).
- Yogyakarta: AWS menyimpang −0,6 sampai −1,8 hPa dari SYNOP pada Apr 2024 – Des 2025. Tidak diubah, karena tidak jelas instrumen mana yang salah.

## Validasi

- Kausalitas: isian sebelum titik potong identik dengan isian penuh (Bengkulu 3 titik, Banten 3 titik).
- `clearsky`, `qc`, dan `clp_ekstra` identik dengan V6.2. Kolom yang berubah hanya angin dan tekanan beserta turunannya. Kalbar identik dengan V6.2.
- Tekanan datar ≥ 3 jam tersisa 0 di keenam stasiun. Pasang S2 1,27–1,48 hPa, puncak 09.27–09.51.
- Rasio angin AWS/SYNOP Bengkulu di periode isian 0,84–0,87 (sehat sekitar 0,8).
- `_common.prepare` P2F: 44 prediktor di keenam stasiun. Tekanan kosong di origin uji ≤ 1,6%, angin ≤ 1,6%, fraksi awan 7,8–8,5%.
