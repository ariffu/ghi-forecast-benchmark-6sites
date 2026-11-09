---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "DIKUNCI — persetujuan pengguna 2026-11-08 (\"Ya, perbaiki dulu\")"
---

# Tahap 105 — V6.7: arah angin saat tenang atau tidak diketahui

Dasar: `Balai_data_v6_6` (beku). Hasil: `C:\Users\ariff\Documents\Balai_data_v6_7`. Temuan: [[RINGKASAN_104]] butir 1.

## Masalah

Kode SYNOP arah 0 berarti calm, tetapi tersimpan sebagai 0° (utara), sehingga sin = 0 dan cos = 1. Arah yang ditahan berjam-jam saat tidak ada pengamatan arah juga tidak bermakna.

## Aturan (kausal, per slot)

Arah dinyatakan **tanpa arah**, yaitu `aws_wind_dir_sin` = `aws_wind_dir_cos` = 0 dan `aws_wind_dir_deg` kosong, bila salah satu berlaku:

1. kecepatan angin V6.6 < 0,5 m/s (calm menurut batas WMO untuk anemometer);
2. nilai arah tepat 0 (kode calm SYNOP; utara sejati tercatat 360);
3. arah ditahan (`mulus_mode_arah` = 2) lebih dari 60 menit sejak pengamatan arah terakhir.

Selain itu sin/cos tidak berubah. Pasangan (0, 0) berada di luar lingkaran satuan, sehingga model pohon dapat membedakannya dari arah sungguhan. Ketersediaan sin/cos tetap 100%.

## Validasi

- Hanya `aws_wind_dir_deg`, `aws_wind_dir_sin`, `aws_wind_dir_cos` yang berubah.
- sin² + cos² ∈ {0, 1}.
- Tidak ada slot 0° yang tersisa.
- Pipeline P2F berjalan dengan 44 prediktor.
- Provenance: `arah_tanpa_arah` (0 = arah ada, 1 = calm, 2 = kode 0, 3 = ditahan > 60 menit).
