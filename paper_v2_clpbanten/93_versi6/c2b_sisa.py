# -*- coding: utf-8 -*-
"""Tahap 93: sisa slot segaris di V6 (RH Jambi, suhu Banten/Jambi): apa polanya, dan apakah memakai nilai sesudah origin. Hanya membaca."""
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
V5 = r"C:\Users\ariff\Documents\Balai_data_v5_final87\00_data"; V6 = r"C:\Users\ariff\Documents\Balai_data_v6\00_data"
def seg(a, idx, tol=0.006):
    h0 = idx.minute == 0; s = pd.Series(a); pv = s.where(h0).ffill().to_numpy(); nx = s.where(h0).bfill().to_numpy(); fr = idx.minute.to_numpy() / 60
    return (~h0) & np.isfinite(a) & (np.abs(a - (pv + (nx - pv) * fr)) < tol) & (np.abs(nx - pv) > tol)
for s, c in (("jambi", "aws_rh_pct"), ("jambi", "aws_temp_c"), ("banten", "aws_temp_c")):
    a = pd.read_parquet(f"{V5}\\{s}_full.parquet", columns=["ts_wib", c, "solar_elev_deg"]); b = pd.read_parquet(f"{V6}\\{s}_full.parquet", columns=["ts_wib", c]); idx = pd.DatetimeIndex(b.ts_wib)
    x5, x6 = a[c].to_numpy(float), b[c].to_numpy(float); day = (a.solar_elev_deg > 5).to_numpy()
    m = seg(x6, idx) & day; sama = m & np.isclose(x5, x6)
    print(f"== {s} {c}: sisa segaris {int(m.sum())}; tidak diubah dari V5 {int(sama.sum())}; per tahun {pd.Series(idx[m].year).value_counts().sort_index().to_dict()}")
    # pola: apakah sisa ada di dalam blok yang menit-menitnya berubah dengan langkah tetap (garis), dan ujungnya jam bulat yang bukan titik terukur?
    i = np.where(m)[0][:3]
    for j in i:
        h = j - (idx[j].minute // 10); print("   ", idx[h], "V5:", np.round(x5[h - 6:h + 13], 2).tolist()); print("    ", " " * len(str(idx[h])), "V6:", np.round(x6[h - 6:h + 13], 2).tolist())
    # garis berlangkah pada lebih dari satu jam: lereng sama dengan jam sebelumnya?
    d1 = pd.Series(x5).diff().to_numpy(); same_slope = m & np.isclose(d1, np.roll(d1, 6), atol=0.003)
    print("   lereng sama dengan 1 jam sebelumnya:", round(float(same_slope.sum() / max(m.sum(), 1)), 3), "| nilai jam bulat ujung kanan pada garis yang menerus 2 jam:", "—")
