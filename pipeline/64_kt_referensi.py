# -*- coding: utf-8 -*-
"""Tahap 64 — indeks kecerahan k_t untuk kelas kondisi langit (audit bahasa M3, LAPORAN §31).

k_t (kolom `kt` database, `kt_clearness` di _common) = GHI / (1100 W m⁻² · sin h); hanya dipakai untuk kelas langit (06_strat_mean),
bukan prediktor. Tahap ini (1) memverifikasi rumus itu pada data, (2) membandingkan rujukan 1100·sin h dengan GHI langit cerah
Ineichen–Perez yang dipakai smart persistence, per situs, untuk origin siang (elevasi > 5°).
Keluaran: 64_kt_referensi/rasio_kt.csv. Jalankan: PYTHONIOENCODING=utf-8 python -u 64_kt_referensi.py
"""
import os, sys, numpy as np, pandas as pd
B = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, B)
import _common
assert _common.CLEARSKY == "IP"
OUT = os.path.join(B, "64_kt_referensi"); os.makedirs(OUT, exist_ok=True)
rows = []
for s in ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]:
    df, feats, yr = _common.prepare(s)
    m = (df.solar_elev_deg > 5) & df.kt_clearness.notna() & df.ghi_wm2.notna() & (df.clear_sky_ghi > 0)
    ref = 1100.0 * np.sin(np.radians(df.solar_elev_deg[m]))
    err = (df.kt_clearness[m] - df.ghi_wm2[m] / ref).abs().max(); assert err < 1e-9, f"{s}: kt bukan GHI/(1100 sin h) (selisih {err})"
    r = ref / df.clear_sky_ghi[m]
    rows.append(dict(site=s, n=int(m.sum()), ratio_median=r.median(), ratio_q25=r.quantile(.25), ratio_q75=r.quantile(.75),
                     ratio_median_elev60=r[df.solar_elev_deg[m] > 60].median()))
R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "rasio_kt.csv"), index=False); print(R.round(3).to_string(index=False))
