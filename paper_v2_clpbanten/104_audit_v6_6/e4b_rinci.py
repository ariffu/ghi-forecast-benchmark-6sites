# -*- coding: utf-8 -*-
"""Tahap 104 (salinan untuk V6.6) (salinan uji tahap 98 untuk V6.4) (salinan uji tahap 95 untuk V6.2) rincian M dan C1: langkah tekanan, runtun RH, geseran hujan Yogyakarta, pergantian satelit."""
import os, re, io, zipfile, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_6"
for s in ("banten", "bengkulu", "kalbar", "jambi"):
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "aws_pressure_hpa", "aws_rh_pct"]); ts = pd.DatetimeIndex(d.ts_wib)
    p = d.aws_pressure_hpa.to_numpy(float); dp = np.abs(np.diff(p, prepend=np.nan)); j = dp > 2
    print(s, "langkah tekanan > 2 hPa:", int(j.sum()), "menit:", pd.Series(ts[j].minute).value_counts().head(3).to_dict(), "tahun:", pd.Series(ts[j].year).value_counts().sort_index().to_dict(), "median langkah", round(float(np.median(dp[j])), 2) if j.any() else None)
    rh = pd.Series(d.aws_rh_pct.to_numpy(float)); g = (rh != rh.shift()).cumsum(); r = rh.groupby(g).transform("size"); m = (r >= 36) & rh.notna()
    print("   RH runtun ≥ 6 jam: nilai", rh[m].round(1).value_counts().head(4).to_dict(), "jam mulai", pd.Series(ts[m.to_numpy()].hour).value_counts().head(3).to_dict())
d = pd.read_parquet(os.path.join(V, "00_data", "jogja_full.parquet"), columns=["ts_wib", "aws_rain_mm", "ghi_wm2", "solar_elev_deg"]); ts = pd.DatetimeIndex(d.ts_wib)
cs = pd.read_parquet(os.path.join(V, "clearsky", "jogja_ineichen.parquet")).ghi_cs.to_numpy(); el = d.solar_elev_deg.to_numpy(float)
kc = pd.Series(np.where((el > 20) & (cs > 50), d.ghi_wm2.to_numpy(float) / cs, np.nan), index=ts); rain = d.aws_rain_mm.astype(float).set_axis(ts)
out = {}
for k in range(-12, 13, 3):
    rr = rain.shift(k); m = (rr > 0.2) & kc.notna(); out[k * 10] = (round(float((kc[m] > 0.9).mean()), 3), round(float(kc[m].median()), 3))
print("Yogyakarta hujan digeser (menit: proporsi k_c>0,9, median k_c):", out)
for s in ("banten", "kalbar"):
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "aws_rain_mm", "ghi_wm2", "solar_elev_deg"]); ts = pd.DatetimeIndex(d.ts_wib)
    cs = pd.read_parquet(os.path.join(V, "clearsky", f"{s}_ineichen.parquet")).ghi_cs.to_numpy(); el = d.solar_elev_deg.to_numpy(float)
    kc = pd.Series(np.where((el > 20) & (cs > 50), d.ghi_wm2.to_numpy(float) / cs, np.nan), index=ts); rain = d.aws_rain_mm.astype(float).set_axis(ts)
    print(s, "hujan digeser:", {k * 10: round(float(kc[(rain.shift(k) > 0.2) & kc.notna()].median()), 3) for k in range(-6, 7, 2)})
z = zipfile.ZipFile(r"C:\Users\ariff\Documents\6lokasi_output_chips.zip"); F = sorted(n for n in z.namelist() if re.search(r"sta6009_bengkulu/CLP_.*\.csv$", n))
C = pd.concat([pd.read_csv(io.BytesIO(z.read(n))).reindex(columns=["file_timestamp_utc", "source_file"]) for n in F]); C["tu"] = pd.to_datetime(C.file_timestamp_utc); C["sat"] = C.source_file.str.extract(r"NC_(H0\d)_")[0]
for a, b, lab in (("2022-12-12", "2022-12-15", "H08→H09"), ("2025-10-11", "2025-10-14", "H09→H08"), ("2025-11-25", "2025-11-28", "H08→H09")):
    x = C[(C.tu >= a) & (C.tu < b)].dropna(subset=["sat"]); ch = x[x.sat != x.sat.shift()]
    print("C1", lab, " | ".join(f"{t} {v}" for t, v in zip(ch.tu, ch.sat)))
