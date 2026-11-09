---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "DIKUNCI — persetujuan pengguna 2026-11-08 (\"Ya, bangun V6.5\")"
---

# Tahap 102 — V6.5: meteorologi beracuan SYNOP, logika diperbaiki

Dasar: `Balai_data_v6_3` (beku). V6.4 tidak dipakai sebagai dasar karena koreksinya cacat ([[RINGKASAN_101]]). Hasil: `C:\Users\ariff\Documents\Balai_data_v6_5`. Langkah tahap 100 ([[DESAIN_100]]) tetap berlaku, dengan lima perubahan.

1. **Deret mayoritas-SYNOP dibangun ulang seluruhnya** dengan isian kausal SYNOP, x̂(t) = S(t0) + x̄(t) − x̄(t0), umur ≤ 3 jam.
   - Kriteria: ≥ 50% slot laporan tahun latih adalah sisipan atau rekonstruksi kausal V6. Calon: suhu/RH Banten, suhu/RH/angin Jambi.
   - Tekanan Jambi juga dibangun ulang, karena seluruh deretnya QFF dan berisi blok +4 hPa. Acuannya S* = QFF − reduksi hipsometrik.
   - x̄ = klimatologi deret lama tahun latih pada slot yang berasal dari SYNOP.
   - Tidak ada koreksi bias untuk deret ini. Arah angin Jambi tidak diubah.
2. **Rekonstruksi kausal V6 (`aws_kausal_*`) di stasiun logger dikoreksi seperti logger**, karena x(t0) = nilai AWS, sehingga levelnya logger. Hanya isian V6.3 (`aws_isi_synop_*`, sudah di level SYNOP) dan sisipan yang tidak dikoreksi.
3. **Sisipan harus berupa lonjakan.**
   - Tekanan: |AWS − SYNOP| < 0,05 dan |AWS − rata-rata dua tetangga| ≥ 0,5·|c|.
   - Angin knot: |AWS − kt| < 0,02 dan |AWS − rata-rata tetangga| > 0,3·AWS.
   - Kesamaan tanpa lonjakan bukan sisipan.
4. **QC laporan SYNOP, kausal.** Laporan dibuang bila menyimpang dari laporan sebelumnya (≤ 3 jam) DAN dari AWS mentah pada saat yang sama melebihi batas: tekanan 2 hPa (pasang ≤ 0,6 hPa/jam), suhu 4 °C, RH 25%. Laporan yang dibuang tidak dipakai untuk bias maupun isian.
5. **Angin.**
   - k dibatasi 0,5–2,0.
   - Lonjakan logger satu slot dikosongkan sebelum k ditaksir: x_t > 8 m/s, x_t > 3 × rata-rata tetangga, dan kedua tetangga < x_t/2.

## Amandemen 1 (2026-11-08, sebelum audit)

Build pertama menghitung fraksi hanya di slot jam laporan. Akibatnya angin Banten (53% jam laporan berisi sisipan knot) ikut dibangun ulang, padahal slot di antara laporan adalah logger. Kriteria diganti: fraksi slot sisipan atau rekonstruksi di **semua slot elevasi > 5° tahun latih**.

## Amandemen 2 (2026-11-08, sebelum audit akhir)

Uji lompatan build kedua: RH Banten melompat > 10% pada 21.10 dan 22.00 (361 slot) di luar jam laporan. Sebabnya klimatologi bulan × menit-hari pada malam hari dihitung dari sedikit slot, sehingga bising. Klimatologi untuk semua isian kausal kini dihaluskan melingkar ±30 menit (7 slot), berbobot jumlah data. Lompatan tepat di jam laporan tetap dibiarkan, karena itu informasi laporan baru, dan memperhalusnya secara kausal berarti menunda informasi.

## Amandemen 3 (2026-11-08)

Penghalusan saja belum cukup. Di Banten, slot yang berasal dari SYNOP pukul 20–23 hanya 0–6 per jam (laporan berakhir 19.00), sehingga klimatologi malam rusak. Klimatologi deret yang dibangun ulang kini dihitung dari semua slot tahun latih. Hanya bentuk siklus harian yang dipakai (x̄(t) − x̄(t0)), jadi offset level logger saling meniadakan.

## Syarat lolos (audit ulang)

- Lompatan 10 menit per deret (tekanan > 1 hPa, suhu > 2 °C, RH > 10%, angin > 5 m/s) tidak lebih banyak daripada V6.3, kecuali yang dijelaskan.
- Bulan menyimpang dari SYNOP tidak lebih banyak daripada V6.4.
- Uji kausalitas lolos.
- Rangkaian uji tahap 95/98 untuk radiasi dan satelit identik.
- `_common.prepare` P2F berjalan dengan 44 prediktor.
