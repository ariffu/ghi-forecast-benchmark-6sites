# Database Versi 6.10 (tahap 111) — BEKU 2026-11-08

Dibangun dari `Balai_data_v6_9` (tidak diubah). Satu perbaikan: `synop_cloud_cover_oktas` Banten dan Bengkulu ternyata Nh (`cloud_low_cover_oktas`, jumlah awan rendah), bukan tutupan awan total N seperti di stasiun lain. Kini diganti N (`cloud_cover_oktas_m`) dari tabel SYNOP sumber:
- Banten: `banten.synoppondokbetung`, Stasiun Klimatologi Banten/Tangerang Selatan;
- Bengkulu: `bengkulu.synop_bengkulu_quality_final`.

Nilai berlaku 60 menit (aturan V6.6). Audit penemuannya: `solardata_new_v2/paper_v2_clpbanten/110_audit_v6_9/RINGKASAN_110.md`; skrip `111_v6_10_okta/x1_bangun_v610.py`.

| | Banten | Bengkulu |
|---|---|---|
| Kolom lama = Nh | 100% | 100% |
| Okta rata-rata lama (Nh) → baru (N) | 2,23 → 6,01 | 2,45 → 6,09 |
| Okta 8 (laporan) | 0,2% → 21,0% | 0,0% → 19,2% |
| Korelasi okta–k_c (Spearman) | −0,30 → −0,65 | −0,39 → −0,61 |
| Siklus harian N | 5,2 (08) → 6,6 (18 WIB) | 6,4 (07) → 5,6 (13) → 6,8 (18 WIB), pola pesisir |
| Origin terisi per tahun | 93,5–94% | 92–96,6% |

Okta keenam stasiun kini sama-sama N, rata-rata 5,4–6,5. Korelasinya dengan k_c memuncak pada t−30 (masa lalu), jadi tanpa kebocoran. Hanya `synop_cloud_cover_oktas` Banten dan Bengkulu yang berubah; stasiun lain, `clearsky`, `qc`, dan `clp_ekstra` identik dengan V6.9. Provenance baru: `synop_okta_N_sumber`.

## Cara memakai

```
DATA_DIR=C:\Users\ariff\Documents\Balai_data_v6_10\00_data
CLEARSKY_DIR=C:\Users\ariff\Documents\Balai_data_v6_10\clearsky
CLP_EKSTRA_DIR=C:\Users\ariff\Documents\Balai_data_v6_10\clp_ekstra
FEATSET=P2F
```

44 prediktor; baseline tidak berubah. Audit V6.9 (tahap 110) dan semua catatan README V6.6–V6.9 tetap berlaku.
