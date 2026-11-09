---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — Balai_data_v6_10 BEKU 2026-11-08; okta keenam stasiun kini tutupan total N; database aktif untuk running uji"
---

# Tahap 111 — V6.10: okta Banten dan Bengkulu = N

Temuan: [[RINGKASAN_110]]. Skrip `x1_bangun_v610.py` (build, cek kolom lama = Nh 100%, pipeline), laporan `x1_laporan.json`, `log_x1.txt`.

| | Banten | Bengkulu |
|---|---|---|
| Laporan N dipakai | 18.958 | 18.590 |
| Okta rata-rata Nh → N | 2,23 → 6,01 | 2,45 → 6,09 |
| Okta 8 | 0,2 → 21,0% | 0,0 → 19,2% |
| Spearman okta–k_c | −0,30 → −0,65 | −0,39 → −0,61 |

- **Siklus harian:** Banten naik ke sore (5,2 → 6,6). Bengkulu tinggi pagi, turun siang, lalu naik sore, sejalan CLP Bengkulu yang berawan pagi.
- **Kebocoran:** korelasi okta dengan k_c memuncak pada t−30 dan melemah ke depan.
- **Cakupan perubahan:** hanya `synop_cloud_cover_oktas` Banten/Bengkulu yang berubah. Berkas lain hash-identik dengan V6.9. P2F 44 prediktor; baseline tidak berubah.
- **Sisa catatan:** satu laporan Banten 23 WIB dan satu laporan Bengkulu 20 WIB di luar jadwal 07–19; diabaikan.
