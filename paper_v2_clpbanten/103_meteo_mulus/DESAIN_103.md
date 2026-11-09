---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "DIKUNCI — permintaan pengguna 2026-11-08: meteorologi AWS 10 menit dikoreksi SYNOP per jam tanpa loncatan tajam, ketersediaan lengkap"
---

# Tahap 103 — V6.6: meteorologi mulus, kausal, dan lengkap

Dasar: `Balai_data_v6_5` (beku) untuk nilai logger terkoreksi dan bendera, `Balai_data_v6_3` untuk SYNOP mentah (lewat `l1_bangun_v65.proses`, yang memberi acuan SYNOP sesudah QC). Hasil: `C:\Users\ariff\Documents\Balai_data_v6_6`.

## Audit V6.5 yang mendorong (`n1_audit_v65.py`)

- **Lompatan 10 menit** (suhu > 2 °C, RH > 10%, tekanan > 1 hPa, angin > 5 m/s): 5–2.078 per deret, misalnya RH Jawa Tengah 1.218 dan tekanan Kalbar 2.078. Di deret berbasis SYNOP, setiap laporan baru membuat lompatan.
- **Ketersediaan:**
  - Kolom SYNOP prediktor (visibilitas, okta, CL, CM, CH, ww) hanya di slot jam laporan: 16% origin.
  - Suhu/RH Banten 63% slot (malam kosong), 94% origin.
  - Arah angin Kalbar 0%; arah Jawa Tengah 87%.
  - Tekanan/angin Bengkulu 86–89% slot.

## Prinsip

Kemulusan tidak dicapai dengan interpolasi antarlaporan, karena interpolasi memakai laporan berikutnya (bocor sampai 50 menit, tahap 91). Semua langkah di bawah kausal: nilai di slot t hanya memakai data ≤ t.

## Penaksir kausal (suhu, RH, tekanan, kecepatan angin; semua stasiun)

Keadaan x(t) diperbarui per slot:

1. **Prediksi:** x⁻(t) = x(t−1) + [x̄(bulan, t) − x̄(bulan, t−1)]. x̄ = klimatologi V6.5 tahun latih, dihaluskan ±30 menit, sehingga siklus harian ikut terbawa saat tidak ada pengamatan.
2. **Bila logger sehat ada di t**, target = nilai logger terkoreksi V6.5. Bobot naik 1/6, 2/6, … 1 selama 6 slot sesudah logger kembali tersedia.
   - Logger sehat = bukan deret yang dibangun ulang, bukan minggu rusak, bukan isian V6.3, bukan sisipan.
3. **Bila tidak ada logger dan ada laporan SYNOP di t** (acuan S* sesudah QC): koreksi p = S* − x⁻(t) disebar rata ke 6 slot (60 menit), mulai slot t. Laporan baru mengganti sisa koreksi lama.
4. **Batas laju:** |x(t) − x⁻(t)| ≤ suhu 1,5 °C, RH 7,5%, tekanan 0,5 hPa, angin 3,0 m/s per 10 menit. Sisa selisih dikejar di slot berikutnya.
5. **Mulai:** dari pengamatan pertama. Sesudahnya tidak ada slot kosong; malam tanpa pengamatan dirambatkan dengan siklus harian. RH dibatasi 0–100, angin ≥ 0.

Konsekuensinya: perubahan nyata yang sangat cepat (misalnya pendinginan hujan 3 °C dalam 10 menit) terserap dalam 2–3 slot, dan informasi laporan SYNOP masuk penuh dalam 60 menit. Itu harga kausalitas.

## Arah angin

Arah AWS V6.5 bila ada. Bila tidak, arah SYNOP laporan terakhir ≤ 60 menit; bila tidak ada juga, arah terakhir yang diketahui (persistensi). Kalbar seluruhnya dari SYNOP. Tidak ada batas laju (besaran melingkar).

## Kolom SYNOP prediktor (visibilitas, okta, CL, CM, CH, ww)

Nilai laporan terakhir berlaku 60 menit (as-of; laporan per jam), sehingga slot :10–:50 terisi. Slot tanpa laporan dalam 60 menit (malam, 06.30–06.50) tetap kosong, karena tidak ada pengamatan. Kode tidak diubah.

## Turunan

Lag/delta/rolling suhu, RH, tekanan, angin, dan sin/cos arah dihitung ulang (definisi tahap 86/93).

## Provenance

Per variabel: `mulus_mode_{v}` (0 = logger, 1 = rambatan + koreksi SYNOP, 2 = rambatan tanpa pengamatan), `mulus_dibatasi_{v}` (batas laju aktif), `synop_asof` (umur laporan, menit).

## Syarat lolos

1. Lompatan 10 menit di atas ambang audit (suhu 2, RH 10, tekanan 1, angin 5) = 0 di semua deret.
2. Ketersediaan suhu, RH, tekanan, angin, dan arah ≥ 99,9% slot sesudah pengamatan pertama.
3. Kolom SYNOP terisi di semua slot yang punya laporan ≤ 60 menit.
4. Uji kausalitas lolos.
5. Bulan menyimpang dari SYNOP tidak lebih banyak daripada V6.5.
6. Radiasi dan CLP identik dengan V6.5.
7. `_common.prepare` P2F berjalan dengan 44 prediktor.

## Amandemen 1 (2026-11-08, sesudah audit build pertama)

Build pertama: lompatan 0 di lima stasiun, tetapi suhu/RH Banten masih 124 (maks 4,2 °C), karena klimatologi malam Banten di V6.5 kosong sehingga langkah siklus harian melompat. Perbaikan: (a) bentuk siklus harian dihitung dari V6.5, slot kosong diambil dari V6.3; (b) batas laju diterapkan pada perubahan total per slot |x(t) − x(t−1)|, bukan hanya pada koreksi.
