---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "DIKUNCI — permintaan pengguna 2026-11-08: perbaiki keganjilan meteorologi dengan SYNOP sebagai acuan; tekanan dibedakan QFF/QFE/sensor; satuan angin disamakan"
---

# Tahap 100 — V6.4: meteorologi AWS beracuan SYNOP

Dasar: `Balai_data_v6_3` (beku, tidak diubah). Hasil: `C:\Users\ariff\Documents\Balai_data_v6_4`. Variabel: suhu, RH, tekanan, kecepatan angin, arah angin AWS di keenam stasiun. Radiasi, CLP, dan kolom SYNOP tidak diubah. Tidak ada keputusan dari skor model.

## Temuan pendorong (`j1_banding_bulanan.py`, jam laporan, V6.3)

- **Satuan angin.** SYNOP = knot di semua stasiun. Di Banten, 62% slot jam laporan berisi angin SYNOP dalam knot tanpa konversi (AWS = kt persis), di antara nilai logger m/s. Jambi: angin AWS = SYNOP × 0,514444 (sudah m/s).
- **Konvensi tekanan.** Selisih AWS − SYNOP tahun latih dibanding harapan hipsometrik:
  - Banten −3,25 (harapan QFF −3,07), Bengkulu −1,02 (−1,03), Kalbar −0,55 (−0,23), Jawa Tengah −0,47 (−0,68): SYNOP = QFF.
  - Yogyakarta −0,21 (QFF akan −20,2): SYNOP = QFE.
  - **Jambi 0,00:** AWS = SYNOP QFF, bukan tekanan sensor (harapan −2,76).
- **Keganjilan per bulan.**
  - Tekanan Yogyakarta −0,6 sampai −1,7 dan +0,9 hPa (Apr 2024 – Des 2025).
  - Suhu Kalbar −0,8 sampai −1,6 °C (Mar 2024 – Des 2025).
  - Kalbar sejak 26 Nov 2025 rusak di semua variabel (suhu −2 sampai −3 °C, RH +5%, angin r 0,11).
  - RH Jawa Tengah −6 sampai −8% (Jul–Sep 2022) dan RH Yogyakarta −2,6 sampai −4% (Agu–Des 2025).
  - Angin Jawa Tengah Des 2022 rusak (AWS 0 saat SYNOP ≥ 2 m/s, 55%); arah Jawa Tengah bergeser 20–64° dari SYNOP sejak Okt 2022.

## Langkah

**0. Satuan dan konvensi.**
- Angin SYNOP: knot × 0,514444 → m/s; kode ≥ 200 dibuang.
- Slot AWS di jam laporan yang berisi SYNOP knot (|AWS − kt| < 0,02, kt ≥ 1, |AWS − kt·0,514444| > 0,05) dikonversi × 0,514444.
- Tekanan acuan di ketinggian sensor: S* = SYNOP + c.
  - c = median(AWS − SYNOP) tahun latih pada slot logger (bukan slot sisipan SYNOP).
  - Jambi tidak punya slot logger, jadi c = reduksi hipsometrik −QFF·(1 − exp(−g·h/(R·T_v))) dengan h = 24 m dan suhu SYNOP.
  - Slot tekanan AWS yang sama persis dengan SYNOP di stasiun QFF (|c| > 0,3) adalah sisipan QFF, dan diganti S*.

**1. Koreksi bias kausal.**
- Residu di jam laporan:
  - suhu, RH: e = AWS − SYNOP (acuan c = 0);
  - tekanan: e = AWS − S*;
  - kecepatan angin: rasio k = ΣSYNOP / ΣAWS (laporan dengan SYNOP ≥ 1 m/s);
  - arah: δ = rata-rata sirkular (SYNOP − AWS) (SYNOP ≥ 2 m/s, AWS ≥ 0,5 m/s).
- Estimasi = median (atau rasio, atau rata-rata sirkular) laporan dalam 7 hari ke belakang, sampai dan termasuk t, minimal 20 laporan. Kurang dari itu, estimasi terakhir dipakai; sebelum ada estimasi sama sekali, nilai netral (0, 1, 0°). Slot sisipan tidak ikut dihitung.
- Koreksi: suhu/RH/tekanan AWS − b(t); angin AWS × k(t), k dibatasi 0,5–2,5; arah AWS + δ(t).
- Hasilnya, AWS berada di level SYNOP (suhu, RH, angin) atau di level tekanan sensor yang konsisten dengan SYNOP (tekanan). Variasi 10 menit logger tetap dipertahankan.

**2. Kerusakan → isian kausal SYNOP (cara 2 tahap 92).**
- Kriteria per stasiun × minggu ISO × variabel, sesudah langkah 1, pada jam laporan:
  - tekanan: > 20% |res| > 1 hPa;
  - suhu: > 20% |res| > 1,5 °C;
  - RH: > 20% |res| > 10%;
  - angin: AWS mentah = 0 saat SYNOP ≥ 2 m/s pada > 5% laporan, atau r(AWS, SYNOP) < 0,4;
  - arah: median |res| > 45°.
- Minggu yang gagal diganti x̂(t) = S*(t0) + x̄(bulan, t) − x̄(bulan, t0), dengan x̄ = klimatologi AWS terkoreksi tahun latih di luar minggu gagal; kosong bila umur > 3 jam.
- Arah tidak diisi, hanya dikosongkan. Rata-rata klimatologi arah tidak bermakna.

**3. Turunan dihitung ulang** dengan definisi tahap 86/93: lag/delta/rolling suhu, RH, tekanan, angin; sin/cos arah.

**4. Provenance.** Kolom baru per variabel (`suhu`, `rh`, `tekanan`, `angin`, `arah`):
- `met_bias_{v}`: koreksi yang diterapkan;
- `met_isi_{v}`: True bila diisi atau dikosongkan;
- `met_sisipan_{v}`: True bila slot sisipan SYNOP.

Kolom isian V6.3 tetap ada.

## Validasi

1. Kausalitas: hasil di slot t identik bila SYNOP sesudah t dihapus (tiga titik potong per stasiun).
2. Residu bulanan AWS − SYNOP sesudah perbaikan: median ≈ 0 (suhu, RH), ≈ c (tekanan), rasio ≈ 1 (angin).
3. Pasang S2 dan siklus harian suhu tetap wajar.
4. Kolom lain identik dengan V6.3.
5. `_common.prepare` P2F berjalan di keenam stasiun.
