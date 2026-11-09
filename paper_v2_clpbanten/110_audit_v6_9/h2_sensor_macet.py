# -*- coding: utf-8 -*-
"""Tahap 110 (salinan untuk V6.9) (salinan uji tahap 98 untuk V6.4) H6: sensor macet (nilai sama ≥ 6 jam, termasuk nol) per stasiun × tahun × variabel AWS pada siang hari;
H7 fraksi awan saat mendung tebal (k_c < 0,15, elevasi > 30°) — uji kegagalan retrieval awan sangat tebal (FAQ JAXA 'Failed')."""
import os, numpy as np, pandas as pd
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 300)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_9"
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; R6, R7 = [], []
for s in S:
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet")); ts = pd.DatetimeIndex(d.ts_wib); el = d.solar_elev_deg.to_numpy(float); siang = el > 10
    for c in ("aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_wind_dir_deg", "aws_rain_mm", "aws_ghi_wm2"):
        x = pd.to_numeric(d[c], errors="coerce"); g = (x != x.shift()).cumsum(); r = x.groupby(g).transform("size").to_numpy(); macet = (r >= 36) & x.notna().to_numpy()
        if c == "aws_rain_mm": macet &= (x.to_numpy() != 0)       # hujan nol berjam-jam itu wajar
        for y in range(2022, 2026):
            m = siang & (ts.year == y) & x.notna().to_numpy()
            if m.sum() == 0: continue
            v = x.to_numpy()[m & macet]
            R6.append(dict(stasiun=s, var=c, tahun=y, isi_siang=int(m.sum()), macet_siang_pct=round(100 * float(macet[m].mean()), 2), nilai_macet=str(pd.Series(v).round(2).value_counts().head(3).to_dict()) if len(v) else ""))
    cs = pd.read_parquet(os.path.join(V, "clearsky", f"{s}_ineichen.parquet")).ghi_cs.to_numpy(); e = pd.read_parquet(os.path.join(V, "clp_ekstra", f"{s}_clp_ekstra.parquet"))
    with np.errstate(all="ignore"): kc = np.where((el > 30) & (cs > 50), d.ghi_wm2.to_numpy(float) / cs, np.nan)
    f = e.clp_cloud_frac.to_numpy(); ok = np.isfinite(kc) & np.isfinite(f) & (e.qc_clp_sza.to_numpy() == 0)
    for lo, hi in ((0, 0.15), (0.15, 0.3), (0.3, 0.5)):
        m = ok & (kc >= lo) & (kc < hi)
        R7.append(dict(stasiun=s, kc=f"{lo}-{hi}", n=int(m.sum()), frac_median=round(float(np.median(f[m])), 3), frac_lt0_5_pct=round(100 * float((f[m] < 0.5).mean()), 1), frac_lt0_2_pct=round(100 * float((f[m] < 0.2).mean()), 1),
                       cot_median=round(float(np.nanmedian(d.clp_cot.to_numpy(float)[m])), 1), cot_eq150=int((d.clp_cot.to_numpy(float)[m] >= 149.99).sum())))
T6 = pd.DataFrame(R6); T6.to_csv(os.path.join(HERE, "H6_sensor_macet.csv"), index=False); print("== H6 macet siang > 2%:"); print(T6[T6.macet_siang_pct > 2].to_string(index=False))
T7 = pd.DataFrame(R7); T7.to_csv(os.path.join(HERE, "H7_frac_mendung.csv"), index=False); print("== H7"); print(T7.to_string(index=False))
