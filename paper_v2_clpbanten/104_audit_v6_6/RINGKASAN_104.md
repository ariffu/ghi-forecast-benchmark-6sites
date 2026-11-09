---
tags: [disertasi, prediksi-radiasi, audit, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — V6.6 layak untuk running uji; satu temuan kecil (arah angin saat tenang) disarankan diperbaiki"
---

# Tahap 104 — audit komprehensif V6.6

Sasaran: `Balai_data_v6_6` (hanya dibaca). Skrip:
- `o0_salin_uji.py`: menyalin `e1`–`e4b`, `h2`, `k1` dari tahap 101.
- `o1_khusus_v66.py`: uji khusus O1–O5.

Ditambah uji tahap 103 pada V6.6: `n3` (lompatan, ketersediaan, pipeline), `n4` (SYNOP bulanan), `n5` (fraksi awan, kebocoran, kelengkapan).

## Lolos

- **Struktur:** 39 berkas cocok dengan SHA256; grid, kesejajaran, skema utuh.
- **Radiasi:** R1–R9 identik dengan audit V6.2/V6.4.
- **Satelit:** C1–C6 identik. C7 berubah hanya karena kolom SYNOP kini as-of, sehingga sampelnya lebih banyak; median CTH dan korelasi okta–fraksi tetap.
- **Meteorologi:**
  - Lompatan 10 menit = 0 di 24 deret (`M1`: langkah = 0).
  - Ketersediaan 100%.
  - Tidak ada nilai di luar batas WMO.
  - Titik embun ≤ suhu, dengan Td 18,6–28,1 °C.
  - Antikorelasi harian suhu–RH −0,98 sampai −1,00.
  - Pasang S2 1,30–1,45 hPa, puncak 09.29–09.50.
  - Siklus harian suhu (puncak 12.30–14.20, amplitudo 5,7–7,1 °C) dan RH sama dengan logger asli V6.3 (O4).
- **Turunan:** lag/delta/rolling dan sin/cos konsisten persis dengan kolom dasar (O1).
- **Kolom SYNOP as-of:** nilai :10–:50 sama persis dengan laporan jam itu, umur ≤ 50 menit, laporan asli tidak berubah, kode dalam rentang (O5).
- **Kebocoran waktu 44 prediktor:** tidak ada (n5). Uji kausalitas build lolos.
- **Konsistensi dengan SYNOP:** bulan menyimpang 6, sama dengan V6.5. Selisih AWS − SYNOP di jam laporan: suhu ≤ 0,06 °C, RH ≤ 0,21%.
- **Pipeline P2F:** 44 prediktor di keenam stasiun.

## Temuan

1. **Arah angin saat tenang disandikan 0° (utara).**
   - Di origin, arah = 0 persis: Jambi 11,5% (81% di antaranya kecepatan < 0,5 m/s), Banten 3,6%. Ini warisan SYNOP: arah 0 berarti calm.
   - Akibatnya `aws_wind_dir_sin/cos` (prediktor P2) berisi "utara" saat tidak ada arah.
   - Kalbar (arah dari SYNOP) dan Jawa Tengah menahan arah lama selama calm, sehingga arah datar ≥ 6 jam di 7–31% slot siang Kalbar.
   - **Usulan:** saat tenang (kecepatan < 0,5 m/s atau laporan SYNOP calm), sin = cos = 0 ("tanpa arah"). Ketersediaan tetap 100%.
2. **Segmen rambat tanpa pengamatan terlalu halus.**
   - Simpangan baku perubahan 10 menit 0,02–0,08, lawan 0,2–0,5 di logger.
   - Ini segmen malam (rambat ≥ 3 jam): Banten suhu/RH 46% dari semua slot, tetapi hanya 6% origin; Bengkulu tekanan 17% slot, 1,7% origin.
   - Sifat metode (tanpa pengamatan, hanya siklus harian); fitur lag/rolling pagi Banten ikut memakainya. Catat di naskah; tidak perlu diubah.
3. **Komposisi sumber per split** (tetap seperti V6.5, dicatat di naskah):
   - Bengkulu tekanan/angin: validasi/uji 65–70% koreksi SYNOP.
   - Kalbar suhu uji 38% SYNOP; Yogyakarta tekanan uji 26%.
   - Banten suhu/RH dan Jambi seluruhnya berbasis SYNOP di semua split.

## Catatan tetap

- Kekosongan > 1% di origin uji hanya di luar meteorologi AWS: CLP 7,5–8,5% (tidak ada berkas atau retrieval), CER 12–16%, turunan k_c, kolom SYNOP 06.30–06.50.
- Okta/CM/CH Yogyakarta 2022–2023 tidak pernah dilaporkan.
- RH jenuh Kalbar 2023 (3,7% slot siang di 96–100%).

## Kesimpulan

V6.6 layak dipakai untuk running uji. Temuan 1 kecil, tetapi menyangkut prediktor P2 (sin/cos arah). Memperbaikinya sebelum running (V6.7) akan membuat arah angin fisis.
