# -*- coding: utf-8 -*-
"""Tahap 94: konvensi zenit mana yang cocok dengan data ukur? Median rasio GHI/(DHI + DNI·μ) pada slot logger (kode 0, GHI > 200, DNI > 100), pagi lawan sore,
untuk μ = sin(elevasi awal t), cos Z tengah t+5, dan rata-rata cos Z per menit [t, t+9]. Rasio yang berpusat 1 pagi dan sore = konvensi yang benar. Hanya membaca."""
import os, numpy as np, pandas as pd, pvlib
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
V6 = r"C:\Users\ariff\Documents\Balai_data_v6"; QC = r"C:\Users\ariff\Documents\Balai_data_v6_1\qc"
META = dict(banten=(-6.26147, 106.7509, 27), bengkulu=(-3.8607, 102.3381, 9), jambi=(-1.60111, 103.4944, 24), jogja=(-7.731064, 110.353578, 182), kalbar=(0.07489, 109.1905, 2), semarang=(-6.9847, 110.3812, 6))
R = []
for s, (la, lo, alt) in META.items():
    d = pd.read_parquet(os.path.join(V6, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "ghi_wm2", "dhi_wm2", "dni_wm2", "solar_elev_deg"]); q = pd.read_parquet(os.path.join(QC, f"{s}_qc.parquet"))
    idx = pd.DatetimeIndex(d.ts_wib).tz_localize("Etc/GMT-7"); G, Dh, Dn = d.ghi_wm2.to_numpy(float), d.dhi_wm2.to_numpy(float), d.dni_wm2.to_numpy(float)
    t1 = pd.date_range(idx[0], idx[-1] + pd.Timedelta(minutes=9), freq="1min"); mu1 = np.cos(np.radians(pvlib.solarposition.get_solarposition(t1, la, lo, altitude=alt).apparent_zenith)).clip(lower=0)
    MU = {"awal t": np.sin(np.radians(d.solar_elev_deg.to_numpy(float))), "tengah t+5": mu1.reindex(idx + pd.Timedelta(minutes=5)).to_numpy(), "rata-rata [t,t+9]": mu1.groupby(t1.floor("10min")).mean().reindex(idx).to_numpy(),
          "awal t−10 (interval berakhir t)": mu1.groupby(t1.floor("10min")).mean().reindex(idx - pd.Timedelta(minutes=10)).to_numpy()}
    ok = (q.qc_ghi.to_numpy() == 0) & (q.qc_dni.to_numpy() == 0) & (q.qc_dhi.to_numpy() == 0) & (G > 200) & (Dn > 100); hr = idx.hour.to_numpy(); el = d.solar_elev_deg.to_numpy(float)
    for lab, mu in MU.items():
        with np.errstate(all="ignore"): r = G / (Dh + Dn * mu)
        for a, b in ((15, 35), (35, 60)):
            m = ok & (el > a) & (el <= b); am, pm = m & (hr < 12), m & (hr >= 12)
            R.append(dict(stasiun=s, mu=lab, el=f"{a}-{b}", pagi=round(float(np.nanmedian(r[am])), 4), sore=round(float(np.nanmedian(r[pm])), 4), n=int(m.sum())))
    print(s, "selesai", flush=True)
T = pd.DataFrame(R); T["pagi−sore"] = (T.pagi - T.sore).round(4); T.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "d2c_rasio.csv"), index=False)
print(T.pivot_table(index=["stasiun", "el"], columns="mu", values="pagi−sore").to_string())
print(T.pivot_table(index=["stasiun", "el"], columns="mu", values="pagi").round(3).to_string())
