---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-06
status: "DESAIN TERKUNCI sebelum database dibangun — Jambi CLP menyusul setelah unduhan selesai"
---

# Tahap 93 — database Versi 6

Permintaan pengguna 2026-11-06 ("Ya, siapkan versi baru"): gabungkan perbaikan tahap 91–92 dan kotak CLP Jambi ke satu versi data baru, lalu hitung ulang semua analisis sekali.

Basis: `Balai_data_v5_final87` (hanya-baca, tidak diubah). Keluaran: `C:\Users\ariff\Documents\Balai_data_v6` dengan susunan sama (`00_data`, `00_data_rawfill`, `provenance`, `SHA256.txt`, `README.md`). Kolom dan tipe tetap 124 dan sama, supaya `_common.prepare()` tidak berubah.

## Perbaikan

| Kode | Perbaikan | Stasiun | Sumber bukti |
|---|---|---|---|
| P1 | Suhu, RH, tekanan: slot hasil interpolasi linear antar jam bulat diganti x(t₀) + [x̄(bulan, t) − x̄(bulan, t₀)], dengan t₀ titik terukur terakhir dan x̄ klimatologi slot tahun latih 2022–2023; kosong bila t − t₀ > 3 jam; RH dibatasi 0–100% | Enam stasiun, hanya slot yang terdeteksi segaris (toleransi 0,006) | [[RINGKASAN_91]], [[RINGKASAN_92]] |
| P2 | Kecepatan dan arah angin: slot segaris diganti nilai terukur terakhir; sin dan cos dihitung ulang | Enam stasiun, slot segaris | [[RINGKASAN_91]] |
| P3 | CLP Bengkulu: semua kolom `clp_*` dikosongkan pada slot t yang di tabel sumber DB v2 (`bengkulu.ghi_forecast_1h_train_3h_rollback_2021_2025`, label t − 10) berstatus `fail_clp_sentinel_or_missing` | Bengkulu | [[bengkulu-clp-terisi]] |
| P4 | `clp_cer_um` = 0 dikosongkan (jari-jari efektif 0 µm tidak fisis; di Banten dan Kalbar kondisi yang sama sudah kosong) | Enam stasiun | [[RINGKASAN_91]] |
| P5 | CLP Jambi diganti kotak 11×11 berpusat di ASRS (−1,602; 103,485) dari ekstraksi ulang pengguna; skala ganda sejak 13 Maret 2022 dibalik, x = (x_csv − offset)/skala; t = T + 10; `clp_cloud_present_int` = COT ≥ 1; kosong bila tidak ada retrieval | Jambi | [[jambi-kotak-19km]] — **menunggu unduhan selesai** |

Sesudah P1–P5, semua kolom turunan AWS dan CLP dihitung ulang dengan definisi DB v2 (`turunan_lain` di `86_basis_final.py`, diverifikasi pada V5 lebih dulu).

`00_data_rawfill` menerima P1, P2, dan P5 (kotak Jambi baru, retrieval kosong = 0 seperti rawfill lama), tetapi tidak P3 dan P4, karena maksud rawfill adalah nilai CLP tersimpan tanpa penyamaran.

## Tidak diubah

- SYNOP (pengodean okta dan Ch Banten janggal, tetapi tanpa sumber pembanding yang sah; SYNOP menambah ≤ 0,002 R²). Dicatat sebagai batasan.
- Radiasi, GHI, DHI, DNI, reflected: sama dengan V5.
- Koordinat kotak Bengkulu (geser satu piksel): kotak V5 tidak lebih buruk menurut tahap 90.

## Validasi

1. Uji T1–T5 tahap 91 diulang pada V6: pola segaris AWS di antara jam bulat mendekati nol di keenam stasiun; isi CLP Bengkulu menurut elevasi setara stasiun lain; CER = 0 tidak ada; kolom turunan cocok dengan definisinya; struktur dan tipe sama dengan V5.
2. Kolom selain yang diperbaiki identik dengan V5 (byte demi nilai).
3. Provenance baru per slot: `aws_kausal_suhu`, `aws_kausal_rh`, `aws_kausal_tekanan`, `aws_kausal_angin`, `clp_gagal_dikosongkan`, `cer_nol_dikosongkan`, `clp_jambi_asrs`.

## Amandemen 1 (2026-11-06, sebelum model apa pun dilatih)

Validasi pertama menemukan RH Jambi bernilai interpolasi yang dibulatkan ke 0,1 (misalnya 90,2; 89,3; 88,5), sehingga toleransi 0,006 meloloskannya. Toleransi kini mengikuti resolusi kolom: tol = maks(0,006; resolusi/2 + 0,001), dengan resolusi 1; 0,1; atau 0,01 bila ≥ 95% nilai kelipatannya, selain itu 0. Kalibrasi pada data 10 menit asli (`c2c_toleransi.py`): RH Bengkulu dan Yogyakarta tetap 0,01–0,24% segaris pada toleransi 0,051, sedangkan suhu naik ke 1–3%. Karena itu toleransi besar hanya dipakai bila resolusinya memang 0,1. Dalam data V5 hanya RH Jambi yang beresolusi 0,1 (96% segaris).

Pada uji segaris di V6, slot yang sudah diganti nilai kausal bisa tampak hampir segaris karena kenaikan klimatologi dalam satu jam hampir lurus. Ukuran kebocoran yang tersisa adalah slot segaris yang **tidak berubah dari V5**.

## Amandemen 2 (2026-11-08, sebelum model naskah dilatih)

Pengguna menyerahkan ekstraksi ulang CLP keenam stasiun (`Documents\6lokasi_output_chips.zip`, 1.461 hari per stasiun, kotak 11×11 atau 10×11 Kalbar, ±30 km; skala sudah benar). Validasi `c5_validasi_6lokasi.py`: timestamp = nama berkas 100%, cocok dengan piksel chips 71 hari (r 1,0000, RMSE 0 di lima stasiun; Kalbar 10×11 sudah dibuktikan tahap 88), dan sama dengan V5 pada 99,6–100% slot berisi di lima stasiun selain Jambi. Pusat Bengkulu −3,86; 102,31 (3,1 km dari Tabel 1) adalah pusat yang memang dipakai V5.

Validasi yang sama menemukan V5 berisi CLP di slot **tanpa berkas Himawari**: setiap hari pukul 09.50 WIB (berkas 02.40 UTC tidak ada) di Bengkulu, Yogyakarta, Kalbar, dan Jawa Tengah (1.447 slot per stasiun), 20–33% di antaranya sama dengan rata-rata slot sebelum dan sesudah (memakai berkas berikutnya), ditambah nilai malam konstan (misalnya COT 35,0) dan slot berkas-ada-tanpa-retrieval (Jawa Tengah 1.281, Kalbar 499, Yogyakarta 312).

Karena itu **P5 diperluas ke keenam stasiun**: semua kolom `clp_*` diambil dari ekstraksi ulang dengan konvensi P5 (t = T + 10; kosong bila tidak ada berkas atau tidak ada retrieval; `clp_cloud_present_int` = COT ≥ 1; CER = 0 kosong). P3 tercakup dengan sendirinya (7.576 dari 7.577 slot Bengkulu juga tanpa retrieval di ekstraksi ulang). Skrip `c6_clp_6lokasi.py` menggantikan `c3_clp_jambi.py`. Provenance menambah `clp_sumber_ulang`.

## Sesudah P5

Database dibekukan, hash ditulis, lalu seluruh rantai analisis naskah dijalankan ulang (delapan arsitektur × lima seed × enam stasiun, `01_pipeline`, analisis, tabel, checker) sebagai Manuskrip Versi 6. Sebelum itu hanya **pratinjau** CatBoost lima seed di enam stasiun pada V6 tanpa P5, untuk melihat arah dampak; angkanya tidak untuk naskah.
