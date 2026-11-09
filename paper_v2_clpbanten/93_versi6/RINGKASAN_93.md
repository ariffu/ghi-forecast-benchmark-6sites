---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-06
status: "BEKU 2026-11-08 — Balai_data_v6 lengkap (P1–P5), tervalidasi, SHA256 ditulis, hanya-baca; Manuskrip V6 belum dibangun"
---

# Tahap 93 — ringkasan: database Versi 6

Desain: [[DESAIN_93]] (amandemen 1: toleransi menurut resolusi; amandemen 2: CLP keenam stasiun dari ekstraksi ulang). Database: `C:\Users\ariff\Documents\Balai_data_v6` (README di sana). V5 tidak diubah.

## Yang sudah diterapkan

| Kode | Perbaikan | Slot siang yang berubah (bukan jam bulat) |
|---|---|---|
| P1 | Suhu, RH, tekanan kausal: laporan terakhir + selisih klimatologi slot tahun latih | Suhu Banten 81,8%, Jambi 91,8%; RH Banten 79,6%, Jambi 86,6%; tekanan Jambi 10,5%; Jawa Tengah 5–7%; RH Kalbar 5,5%; Bengkulu dan Yogyakarta < 0,3% |
| P2 | Angin: nilai terukur terakhir | Jambi 85,6%, Jawa Tengah 2,9%, lainnya < 0,2% |
| P3 | CLP Bengkulu dikosongkan pada slot gagal | 7.577 slot, 5.147 di elevasi > 5° (angka 11.772 di [[RINGKASAN_91]] dihitung di tabel sumber, termasuk slot yang di V5 sudah kosong) |
| P4 | CER = 0 dikosongkan | Bengkulu 9.293, Jambi 7.254, Jawa Tengah 15.062, Yogyakarta 106 |

## Validasi (`c2_validasi_v6.py`, `c2_validasi.csv`)

- Struktur, kolom, dan tipe sama dengan V5; radiasi, `kt`, clear-sky identik; kolom lain di luar yang diperbaiki tidak berubah.
- Semua definisi turunan AWS dan CLP mereproduksi V5 100% sebelum diterapkan.
- **Sisa kebocoran** (slot segaris yang tidak berubah dari V5): suhu Banten 0,26%, Jambi 0,16%; RH 0,13–0,24%. Ini setara latar data asli di Bengkulu, Yogyakarta, dan Kalbar (suhu 2–3%, RH 0,5%), yaitu kebetulan segaris, bukan interpolasi.
- CLP Bengkulu menurut elevasi kini setara stasiun lain: 0,5% isi pada 5–7,5° (V5 82%), 32% pada 7,5–10° (V5 100%).
- CER = 0 tidak ada lagi; flag awan cocok 100% dengan COT ≥ 1; RH dalam 0–100%; rentang suhu dan tekanan wajar.

## P5: CLP keenam stasiun dari ekstraksi ulang (amandemen 2)

Pengguna menyerahkan ekstraksi ulang keenam stasiun (`C:\Users\ariff\Documents\6lokasi_output_chips.zip`, 1.461 hari per stasiun, kotak ±30 km, skala sudah benar). Validasi `c5_validasi_6lokasi.py`:

| | Banten | Bengkulu | Jambi | Yogyakarta | Kalbar | Jawa Tengah |
|---|---|---|---|---|---|---|
| Pusat kotak | −6,2615; 106,7508 | −3,86; 102,31 | −1,602; 103,485 | −7,731; 110,354 | 0,075; 109,19 (10×11) | −6,9847; 110,3806 |
| Jarak ke pusat V5 | 0,01 km | 3,1 km dari Tabel 1, **tetapi sama dengan pusat yang dipakai V5** | 20,3 km (kini 1,05 km dari ASRS) | 0,05 km | 0,06 km | 0,07 km |
| Lawan piksel chips 71 hari | r 1,0000, RMSE 0 | 1,0000, 0 | 1,0000, 0 | 1,0000, 0 | 10×11 (tahap 88: RMSE 0) | 1,0000, 0 |
| Slot berisi yang sama dengan V5 | 100% | 99,75% | — | 99,97% | 99,6% | 99,7% |

Timestamp = nama berkas 100%, satelit = nama berkas 100%, tanpa duplikat, nilai dalam rentang produk, CTT–CTH r −0,994 sampai −0,996. Ini bukti pertama bahwa CLP V5 asli selama 4 tahun penuh, bukan hanya 71 hari.

Temuan baru: V5 berisi CLP di slot tanpa berkas Himawari. Setiap hari pukul 09.50 WIB (berkas 02.40 UTC tidak ada) di Bengkulu, Yogyakarta, Kalbar, dan Jawa Tengah, 70–85% berupa salinan slot sebelumnya dan 20–33% rata-rata slot sebelum dan sesudah (memakai berkas 10 menit ke depan). Ada juga nilai malam konstan (misalnya COT 35,0) dan slot berkas-ada-tanpa-retrieval (Jawa Tengah 1.281, Kalbar 499, Yogyakarta 312). Karena itu P5 diperluas ke keenam stasiun.

Hasil penerapan (`c6_clp_6lokasi.py`): hanya kolom `clp_*` yang berubah. Slot yang kini kosong: Bengkulu 3.026 (di luar 7.577 slot P3), Yogyakarta 3.978, Kalbar 2.428, Jawa Tengah 5.306, Banten 1. Validasi akhir (`log_c2_final.txt`, `c7_clp_cek.py`): isi CLP menurut elevasi seragam (5–7,5°: 0%; 7,5–10°: 22–35%; > 15°: 96,6–97,8%), slot 09.50 dan malam kosong, turunan cocok, flag 100%, CER 0 tidak ada, COT ≤ 150.

V6 dibekukan 2026-11-08: 20 berkas, 825 MB, `SHA256.txt`, atribut hanya-baca.

## Pratinjau CatBoost lima seed (V6 sebelum P5; bukan angka naskah)

| Stasiun | V5 | V6 | Selisih rerata (rentang seed) |
|---|---:|---:|---|
| Banten | 0,8474 | 0,8465 | −0,0010 (−0,0011 … −0,0007) |
| Bengkulu | 0,9096 | 0,9091 | −0,0005 (−0,0010 … +0,0002) |
| Jambi | 0,8746 | 0,8752 | +0,0006 (+0,0004 … +0,0009) |
| Yogyakarta | 0,8696 | 0,8697 | +0,0001 |
| Kalbar | 0,8966 | 0,8964 | −0,0001 |
| Jawa Tengah | 0,9036 | 0,9038 | +0,0002 |

Semua perubahan ≤ 0,001. COT palsu Bengkulu hanya menyumbang sekitar 0,0005, dan kebocoran AWS Banten sekitar 0,001.

## Langkah berikutnya

1. Bangun Manuskrip Versi 6 dari `Balai_data_v6`: delapan arsitektur × lima seed × enam stasiun, `01_pipeline`, analisis, gambar, tabel, checker.
2. Perbarui naskah: Tabel 1 (koordinat Jambi; periksa juga Bengkulu), §2.1 (suhu dan RH dari SYNOP dengan pengisian kausal; slot tanpa berkas Himawari dan CER tanpa retrieval kosong), dan angka AWS di Abstrak.
