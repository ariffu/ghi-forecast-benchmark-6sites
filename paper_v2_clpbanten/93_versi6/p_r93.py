p = "RINGKASAN_93.md"; t = open(p, encoding="utf-8").read()
t = t.replace('status: "BERJALAN — P1–P4 diterapkan dan tervalidasi di Balai_data_v6; P5 (CLP Jambi) menunggu unduhan; database belum beku"',
              'status: "BEKU 2026-11-08 — Balai_data_v6 lengkap (P1–P5), tervalidasi, SHA256 ditulis, hanya-baca; Manuskrip V6 belum dibangun"')
a = t.index("## P5: uji kering CLP Jambi"); b = t.index("## Pratinjau CatBoost")
p5 = """## P5: CLP keenam stasiun dari ekstraksi ulang (amandemen 2)

Pengguna menyerahkan ekstraksi ulang keenam stasiun (`Documents\6lokasi_output_chips.zip`, 1.461 hari per stasiun, kotak ±30 km, skala sudah benar). Validasi `c5_validasi_6lokasi.py`:

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

"""
t = t[:a] + p5 + t[b:]
t = t.replace("## Pratinjau CatBoost lima seed (V6 tanpa P5; bukan angka naskah)", "## Pratinjau CatBoost lima seed (V6 sebelum P5; bukan angka naskah)")
a = t.index("## Langkah berikutnya"); t = t[:a] + """## Langkah berikutnya

1. Bangun Manuskrip Versi 6 dari `Balai_data_v6`: delapan arsitektur × lima seed × enam stasiun, `01_pipeline`, analisis, gambar, tabel, checker.
2. Perbarui naskah: Tabel 1 (koordinat Jambi; periksa juga Bengkulu), §2.1 (suhu dan RH dari SYNOP dengan pengisian kausal; slot tanpa berkas Himawari dan CER tanpa retrieval kosong), dan angka AWS di Abstrak.
"""
open(p, "w", encoding="utf-8").write(t); print("ok")
