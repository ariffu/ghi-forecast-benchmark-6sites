---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — Balai_data_v6_7 BEKU 2026-11-08; database aktif untuk running uji"
---

# Tahap 105 — ringkasan: V6.7, arah angin saat tenang

Desain: [[DESAIN_105]]. Skrip: `q1_bangun_v67.py` (build, validasi, pipeline). Laporan: `q1_laporan.json`, `log_q1.txt`.

- **Masalah:** calm tersimpan sebagai arah 0° (utara). Kini calm (< 0,5 m/s), kode 0, dan arah yang ditahan > 60 menit dinyatakan "tanpa arah", yaitu sin = cos = 0.
- **Cakupan di origin:** Banten 11,1%, Bengkulu 3,0%, Jambi 25,2%, Yogyakarta 6,4%, Kalbar 24,8%, Jawa Tengah 8,1%.
- **Validasi:**
  - hanya 3 kolom arah yang berubah;
  - sin² + cos² ∈ {0, 1};
  - tidak ada 0° tersisa;
  - sin/cos 100% terisi di origin uji;
  - P2F 44 prediktor; baseline identik.
- **Lain-lain:** hasil audit V6.6 (tahap 104) tetap berlaku untuk V6.7, karena kolom lain identik.
