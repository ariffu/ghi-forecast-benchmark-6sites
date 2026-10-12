---
tags: [disertasi, prediksi-radiasi, eksperimen, multi-seed, clpbanten-v2]
created: 2026-10-05
modified: 2026-10-05
---

# Multi-seed model neural — desain terkunci (ditulis SEBELUM hasil)

> [!important] Tujuan
> Menguji apakah klaim naskah tentang model neural (konvergensi arsitektur, "sequence models lebih rendah dari LightGBM")
> bertahan terhadap variasi inisialisasi acak. Pipeline asli melatih setiap model neural **sekali** (seed 42).

## Eksperimen
| Kode | Cakupan | Model | Konfigurasi (identik) |
|---|---|---|---|
| E-A | Bengkulu standalone | MLP, LSTM, Transformer, LSTM_hybrid, Transf_hybrid (target residual) | `04_arch_mean.py` |
| E-B | 6 situs | LSTM, Transformer, LSTM_hybrid, Transformer_hybrid (residual) | `04b_seq_6situs_mean.py` |
| E-B | 6 situs | MLP direct | `04c_mean_6situs_xgb_mlp.py` |
| ref | 6 situs | LightGBM, CatBoost (deterministik, refit + assert reproduksi CSV) | `04c_mean_6situs.py` |

Target point (h1) **tidak** diikutkan (biaya komputasi; klaim naskah tentang arsitektur berbasis target rata-rata jam).

## Realisasi
- **R0** = run pipeline asli: prediksi dari `04_arch_mean/arch_preds_mean.npz` dan `04b_arch_6situs_mean/arch_preds_6situs_mean.npz`;
  MLP 6 situs direplikasi persis (seed 42 sekali, urut situs, 4 thread) dan dibandingkan dengan CSV (dicatat bila beda).
- **R1–R4** = seed 1–4; `torch.manual_seed(s); np.random.seed(s)` tepat sebelum tiap model dibangun.
- Thread: model sequence & MLP Bengkulu = cpu−1 (seperti aslinya); MLP 6 situs = 4 (default saat aslinya dijalankan).

## Aturan tafsir (pra-registrasi)
- **R1 — konvergensi.** Klaim "spread 8 model 0.007–0.013 R²" *robust* bila spread dengan R² rata-rata-seed per model
  di tiap situs berada dalam ±0.003 dari spread yang dilaporkan, dan rentang 6 situs tetap ≤ 0.016.
- **R2 — sequence < LightGBM (Bengkulu, blok harian).** Klaim "model X signifikan lebih rendah dari LightGBM" *robust* bila
  (a) CI blok ΔR² ansambel-seed (rata-rata prediksi 5 realisasi) tidak memuat 0, **dan** (b) ≥ 4 dari 5 realisasi signifikan sendiri-sendiri.
  "Tidak signifikan" (mis. MLP) *robust* bila ≤ 1 dari 5 realisasi signifikan.
- **R3 — derau seed.** Derau seed dianggap *kecil* bila median SD antar-seed (per model×situs) < ½ median spread arsitektur antar-situs.
- Peringkat: dilaporkan deskriptif (frekuensi tiap model menjadi neural terbaik per situs per realisasi); tidak ada uji.
- Ambang resolusi: |ΔR²| < 0.002 tidak ditafsirkan (aturan naskah).
- Ansambel-seed hanya diagnostik ("berapa yang dibuang oleh satu seed"), **bukan** model baru untuk naskah.

## Keluaran
`preds/{exp}__{site}__{model}__{s1..s4|pipe}.npy` (+ `y`, `day`) → `37_multiseed_analysis.py` → CSV, gambar, dan ringkasan aturan.
