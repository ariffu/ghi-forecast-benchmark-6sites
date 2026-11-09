---
tags: [disertasi, prediksi-radiasi, eksperimen, clpbanten-v2]
created: 2026-11-08
status: "SELESAI — P2F (44 prediktor) terpasang; belum ada model yang dilatih"
---

# Tahap 97 — ringkasan: fraksi awan sebagai prediktor ke-44

Desain: [[DESAIN_97]].

## Yang berubah

- `_common.py`:
  - `FEATSET=P2F` (P2 + `clp_cloud_frac`), `CLP_EKSTRA_DIR`, `add_clp_ekstra()`, `P2_AKTIF`.
  - Bawaan tetap P2, sehingga V5 dan V6.1 tidak berubah.
- Pemeriksaan `FEATSET == "P2"` diganti `in ("P2", "P2F")` di 11 skrip analisis (`g0_tambal_assert.py`; cadangan `*.bak97`): 60, 61, 62, 63, 69, 70, 77, 80c, `make_fig2_workflow`, `93_versi6/c4`, `92_aws_kausal/b2`. Builder V3 (49, 52) tidak diubah.

## Verifikasi (`g1_cek.py`, `log_g1.txt`)

| Lingkungan | Prediktor | Catatan |
|---|---|---|
| Bawaan (V5) | 43 | Jambi base_mean 379,723, sama dengan sebelumnya |
| V6.2, P2 | 43 | 376,001 |
| V6.2, P2F | 44 di keenam stasiun | fraksi masuk kelompok ablasi CLP; terisi di 91,5–92,5% origin latih dan uji |
| V6.2 rawfill, P2F | 44 | memakai `clp_cloud_frac_raw`, terisi 98% |

Baseline (smart persistence) tidak berubah oleh P2F.

## Cara menjalankan Manuskrip V6

```
DATA_DIR=C:\Users\ariff\Documents\Balai_data_v6_2\00_data
CLEARSKY_DIR=C:\Users\ariff\Documents\Balai_data_v6_2\clearsky
CLP_EKSTRA_DIR=C:\Users\ariff\Documents\Balai_data_v6_2\clp_ekstra
FEATSET=P2F
```

Ablasi pra-terdaftar: P2F lawan P2 (CatBoost 5 seed), dilaporkan apa pun hasilnya.
