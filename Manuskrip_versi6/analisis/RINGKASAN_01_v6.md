---
tags: [disertasi, prediksi-radiasi, manuskrip-v6]
created: 2026-11-08
status: "SELESAI — pelatihan protokol baku dan analisis 01 V6 lengkap; tabel, gambar, dan teks naskah V6 belum"
---

# Hasil running Manuskrip V6 (V6.10, P2F 44 prediktor)

## Pelatihan protokol baku (`protokol/hasil`)

- **Pohon:** 90/90 model.
- **NN:** 150/150 model.
- **Waktu jalan:** pohon 1.465 detik; NN 9.820 detik (grup A) dan 9.308 detik (grup B).

**Banding dengan V5** (`Manuskrip_versi5/protokol/hasil`), rata-rata 5 seed:

| Kelompok model | Selisih R² V6 − V5 | Catatan |
|---|---|---|
| Pohon | −0,003 … +0,003 | Jambi naik ~0,003; skill turun ≤ 0,012 di Banten, Bengkulu, Jawa Tengah |
| NN | −0,003 … +0,006 | Yogyakarta LSTM_hybrid +0,006, MLP +0,004 |

Pemeriksaan reproduksi: CatBoost FULL di analisis 01 = protokol baku seed 42 (+0,00000) di keenam stasiun.

## Analisis 01 (`pipeline/`, `hasil/`), 1.043 detik, tanpa galat

### Tahap 27 — ablasi LightGBM, ΔR² dengan block bootstrap harian

| Efek | V6 | V5 |
|---|---|---|
| ΔCLP | **0,012–0,029**, semua bermakna | 0,012–0,025 |
| ΔAWS\|CLP | bermakna di Banten (0,0047), Yogyakarta (0,0015), Kalbar (0,0024); lainnya ~0 | Banten 0,0063 |
| ΔSYNOP\|CLP | −0,0004 … +0,0004 (nol) | nol |

Jambi naik 0,024 → 0,029; ini konsisten dengan kotak CLP yang kini di ASRS.

### Ablasi CatBoost residual

Polanya sama dengan LightGBM: ΔCLP 0,013–0,028; ΔAWS|CLP Banten 0,004, Kalbar 0,003.

### Tahap 63 — subkelompok AWS

Manfaat AWS di Banten tetap berasal dari angin: Δ 0,0047 (V5 0,0061). Subkelompok lain ~0.

### Tahap 19 — isian CLP

Varian rawfill (COT = 0) ≈ varian masked; beda ≤ 0,001.

### Tahap 31 — latensi CLP

ΔCLP pada V0 / L10 / L20:

| Stasiun | V0 | L10 | L20 |
|---|---|---|---|
| Banten | 0,0209 | 0,0169 | 0,0140 |
| Bengkulu | 0,0183 | 0,0148 | 0,0127 |
| Jambi | 0,0341 | 0,0287 | 0,0233 |
| Yogyakarta | 0,0278 | 0,0240 | 0,0213 |
| Kalbar | 0,0193 | 0,0163 | 0,0138 |
| Jawa Tengah | 0,0145 | 0,0124 | 0,0102 |

Porsi yang hilang dari V0 ke L10 adalah **14–19%** (V5: 14–23%).

### Tahap 28 — statistik kotak (Balai_kotak_v6_10, 6 fitur)

| Uji | Hasil V6 | V5 |
|---|---|---|
| E1 | −0,0005 … +0,0015 | ≤ 0,0016 |
| E2 | −0,0001 … +0,0023 | ≤ 0,003 |

Hanya Bengkulu E2 yang memenuhi aturan "bermakna" (0,0023, CI blok 0,0012–0,0034). Jadi sebaran kotak hampir tidak menambah informasi di luar rata-rata COT dan fraksi awan.

### Tahap 18b — SYNOP dibawa maju

Varian "orig" dan "asof" hampir sama, sesuai dugaan, karena V6.10 sudah membawa SYNOP 60 menit. SYNOP di atas CLP: |Δ| ≤ 0,001.

### Tahap 13b — referensi CP

| Stasiun | α | RMSE referensi (W m⁻²) |
|---|---|---|
| Banten | 0,33 | 113,3 |
| Bengkulu | 0,29 | 105,9 |
| Jambi | 0,43 | 114,1 |
| Yogyakarta | 0,40 | 125,1 |
| Kalbar | 0,35 | 120,4 |
| Jawa Tengah | 0,28 | 104,0 |

Nilainya hampir sama dengan V5. RMSE persistensi turun 1–1,3 W m⁻².

### Tahap 60 — Ridge

R² 0,816–0,887.

## Implikasi untuk teks naskah

Pesan utama V5 tetap berlaku di V6:
- CLP memberi tambahan bermakna di keenam stasiun;
- AWS hanya bermakna kecil (angin Banten);
- SYNOP nol di atas CLP;
- latensi memakan sebagian tambahan CLP.

Yang perlu diubah:
- angka-angka di atas;
- kalimat uji SYNOP dibawa maju;
- kalimat statistik kotak, termasuk fraksi awan kini prediktor dan 6 fitur kotak;
- Tabel 1 (koordinat Bengkulu dan Jambi);
- §2.1 (meteorologi beracuan SYNOP, isian kausal, clear-sky interval, konvensi hujan, okta N).

**Belum dikerjakan:** padanan `04b`, `v4_01`, `v4_03`, `v4_04`, `05`, `v4_06` untuk tabel, gambar, cek angka, dan dokumen V6.
