# Database Versi 6 (tahap 93) — BEKU 2026-11-08

Dibuat 2026-11-06 sampai 2026-11-08 dari `Balai_data_v5_final87`, yang tidak diubah. Folder ini hanya-baca; hash di `SHA256.txt`. Perubahan berikutnya harus menjadi versi baru.

Desain: `solardata_new_v2/paper_v2_clpbanten/93_versi6/DESAIN_93.md` (dengan amandemen 1 dan 2). Skrip: `c1_bangun_v6.py` (P1–P4), `c6_clp_6lokasi.py` (P5, keenam stasiun), `c2_validasi_v6.py` dan `c7_clp_cek.py` (validasi), `c5_validasi_6lokasi.py` (validasi ekstraksi ulang CLP).

## Beda dengan V5

| Kode | Perbaikan | Slot siang yang berubah (bukan jam bulat) |
|---|---|---|
| P1 | Suhu, RH, tekanan hasil interpolasi linear antar laporan SYNOP diganti nilai kausal: laporan terakhir + selisih klimatologi slot (tahun latih 2022–2023); kosong bila laporan terakhir > 3 jam | Suhu Banten 82%, Jambi 92%; RH Banten 80%, Jambi 87%; Jawa Tengah 5–7%; RH Kalbar 5,5%; lainnya < 0,3% |
| P2 | Angin hasil interpolasi diganti nilai terukur terakhir | Jambi 86%, Jawa Tengah 2,9%, lainnya < 0,2% |
| P3 | CLP Bengkulu dikosongkan pada slot yang ditandai gagal oleh tabel sumber DB v2 | 7.577 slot (5.147 di elevasi > 5°) |
| P4 | CER = 0 dikosongkan | 31.715 slot (Bengkulu, Jambi, Jawa Tengah, Yogyakarta) |
| P5 | Semua kolom `clp_*` keenam stasiun dari ekstraksi ulang pengguna (`6lokasi_output_chips.zip`, kotak ±30 km; Jambi kini berpusat di ASRS −1,602; 103,485). Slot tanpa berkas Himawari (setiap hari 09.50 WIB, malam) atau tanpa retrieval kosong | Jambi seluruhnya; lima stasiun lain sama dengan V5 pada 99,6–100% slot berisi, ditambah slot isian V5 yang kini kosong (Bengkulu 3.026, Yogyakarta 3.978, Kalbar 2.428, Jawa Tengah 5.306) |

P5 mencakup P3: 7.576 dari 7.577 slot gagal Bengkulu juga tanpa retrieval di ekstraksi ulang.

Pusat kotak: Banten −6,2615; 106,7508; Bengkulu −3,86; 102,31 (sama dengan V5, 3,1 km dari koordinat Tabel 1); Jambi −1,602; 103,485; Yogyakarta −7,731; 110,354; Kalbar 0,075; 109,19 (grid 10×11); Jawa Tengah −6,9847; 110,3806.

Suhu dan RH tetap bersumber SYNOP sesuai keputusan pengguna. Yang diubah hanya pengisian di antara laporan, supaya nilai pada origin t tidak memakai laporan sesudah t.

Radiasi (GHI, DHI, DNI, reflected), `kt`, clear-sky, SYNOP, dan semua kolom lain identik dengan V5. Kolom turunan AWS dan CLP dihitung ulang dengan definisi DB v2.

`00_data_rawfill` menerima P1, P2, dan P5 dengan konvensi rawfill: berkas ada tetapi tanpa retrieval → COT, CTH, CER, flag = 0 (CTT kosong); tanpa berkas → kosong di keenam stasiun. P4 tidak diterapkan di rawfill.

`provenance/{stasiun}_provenance.parquet` menambah penanda per slot: `aws_kausal_suhu`, `aws_kausal_rh`, `aws_kausal_tekanan`, `aws_kausal_angin`, `clp_gagal_dikosongkan`, `cer_nol_dikosongkan`, `clp_jambi_asrs`.

## Yang belum diperbaiki

- Pengodean SYNOP Banten (okta 0 pada 15% laporan, Ch = 0 pada 68%) dan Ch Jambi: tidak ada sumber pembanding yang sah.
- Kotak CLP Bengkulu bergeser satu piksel ke barat: menurut tahap 90 tidak lebih buruk.
