---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — Balai_data_v6_8 BEKU 2026-11-08; hujan AWS disinkronkan dengan SYNOP; database aktif untuk running uji"
---

# Tahap 107 — ringkasan: V6.8, hujan

Desain: [[DESAIN_107]] dengan amandemen 1–3. Skrip:
- `s1_sinkron_hujan.py`: sinkronisasi sebelum perbaikan.
- `s2_bangun_v68.py`: build dan uji kausalitas.
- `s3_sinkron_v68.py`: sinkronisasi sesudah.
- `s4_diurnal_v68.py`: siklus harian.

README database: `C:\Users\ariff\Documents\Balai_data_v6_8\README.md`.

## Sinkronisasi

- **Data mentah Banten** membuktikan konvensi AWS: kumulatif ditahan sampai 07.00, reset 07.10. Satu hari hujan = (07.00 kemarin, 07.00]; slot t = hujan (t − 10, t]. Konvensi ini cocok paling baik dengan SYNOP 3/6/24 jam di semua stasiun.
- **Yogyakarta:** slot 07.00 = jumlah hujan logger 24 jam sebelumnya (rasio 1,00), sehingga dihitung ganda (2.084 mm, 21% hujan).
- **Isian SYNOP mundur** (Yogyakarta 15.844 slot, Jawa Tengah 8.140 slot) memakai laporan yang datang kemudian.

## Perbaikan dan hasil

| | V6.7 | V6.8 |
|---|---|---|
| Hujan slot 07.00 Yogyakarta | 2.084 mm (21,2%) | 77 mm (1,0%) |
| Puncak hujan Yogyakarta | 07 AST | 16 AST |
| AWS/SYNOP 24 jam Yogyakarta | 0,91 (termasuk hitung ganda) | 0,74 |
| Isian non-kausal | 23.984 slot | 0 (isian maju kausal) |
| Hujan kosong di origin uji | 0 | Yogyakarta 0,35%, Jawa Tengah 0,2% (tanpa laporan dalam jendela) |

- Bengkulu, Jambi, dan Jawa Tengah: 2–3 hari hitung ganda dibuang. Banten dan Kalbar tidak berubah.
- Siklus harian hujan di keenam stasiun kini sesuai literatur (puncak 15–21 AST).

## Tiga amandemen (semua sebelum validasi akhir, tanpa skor model)

1. Aturan hitung ganda diperketat dari ≥ 0,5·S menjadi 0,8–1,2·S, karena aturan longgar ikut menghapus hujan pagi sungguhan di Bengkulu dan Jambi.
2. Pembanding S = jumlah slot logger saja, karena pencacah AWS tidak menghitung isian SYNOP.
3. Residu slot 07.00 Yogyakarta (503 hari) diganti nilai slot 06.50.

## Catatan naskah

- Perbedaan manual–otomatis diterima tanpa penskalaan: Yogyakarta AWS sekitar 25% di bawah SYNOP, Kalbar 3–6 jam sekitar 25% di bawah, RR24 SYNOP Jawa Tengah meragukan.
- Isian maju menurunkan korelasi periode 3–6 jam Yogyakarta (0,89 → 0,72); itu harga kausalitas.
