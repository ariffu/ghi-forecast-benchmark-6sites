# -*- coding: utf-8 -*-
"""Tahap 94: sisa asimetri pagi–sore k_c cerah — jam logger bergeser atau efek fisis pagi (embun/kabut)?
Clear-sky interval digeser δ menit (−12…+12); δ yang membuat pagi = sore dicari per kelas elevasi dan per tahun, juga per sumber GHI (logger saja). Hanya membaca."""
import os, numpy as np, pandas as pd, pvlib
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
HERE = os.path.dirname(os.path.abspath(__file__)); V6 = r"C:\Users\ariff\Documents\Balai_data_v6"
META = dict(banten=(-6.26147, 106.7509, 27), bengkulu=(-3.8607, 102.3381, 9), jambi=(-1.60111, 103.4944, 24), jogja=(-7.731064, 110.353578, 182), kalbar=(0.07489, 109.1905, 2), semarang=(-6.9847, 110.3812, 6))
t1 = pd.date_range("2021-12-31 23:30", "2026-01-01 00:59", freq="1min", tz="Etc/GMT-7"); D = range(-12, 13, 2); R = []
for s, (la, lo, alt) in META.items():
    loc = pvlib.location.Location(la, lo, tz="Etc/GMT-7", altitude=alt); c1 = loc.get_clearsky(t1, model="ineichen", linke_turbidity=pvlib.clearsky.lookup_linke_turbidity(t1, la, lo, interp_turbidity=True)).ghi
    d = pd.read_parquet(os.path.join(V6, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "ghi_wm2", "solar_elev_deg", "kt"]); idx = pd.DatetimeIndex(d.ts_wib).tz_localize("Etc/GMT-7")
    src = pd.read_parquet(os.path.join(V6, "provenance", f"{s}_provenance.parquet"), columns=["ts_wib", "ghi_sumber"]).ghi_sumber.to_numpy()
    ghi = d.ghi_wm2.to_numpy(float); el = d.solar_elev_deg.to_numpy(float); hr = idx.hour.to_numpy(); ok = ~np.isnan(d.kt.to_numpy(float)); yr = idx.year.to_numpy()
    roll = c1.rolling(10).mean()                                            # rata-rata menit [x−9, x]
    cs0 = roll.reindex(idx + pd.Timedelta(minutes=9)).to_numpy()
    with np.errstate(all="ignore"): k0 = pd.Series(np.where(ok & (cs0 > 50), ghi / cs0, np.nan))
    base = ((k0.rolling(6, center=True, min_periods=6).std() < 0.03) & k0.rolling(6, center=True, min_periods=6).mean().between(0.85, 1.15)).to_numpy()   # periode cerah ditetapkan sekali, pada δ = 0
    for dl in D:
        cs = roll.reindex(idx + pd.Timedelta(minutes=9 + dl)).to_numpy()      # interval [t+δ, t+9+δ]
        with np.errstate(all="ignore"): kc = np.where(ok & (cs > 50), ghi / cs, np.nan)
        for lab, m0 in (("semua", base), ("logger", base & (src == "logger"))):
            for lo_, hi_ in ((10, 20), (20, 40), (40, 60), (60, 90)):
                m = m0 & (el > lo_) & (el <= hi_); am, pm = m & (hr < 12), m & (hr >= 12)
                if am.sum() > 30 and pm.sum() > 30: R.append(dict(stasiun=s, sumber=lab, el=f"{lo_}-{hi_}", delta=dl, beda=np.nanmedian(kc[am]) - np.nanmedian(kc[pm]), n_pagi=int(am.sum()), n_sore=int(pm.sum())))
        if dl == 0:
            for y in (2022, 2023, 2024, 2025):
                m = base & (yr == y) & (el > 20) & (el <= 40); am, pm = m & (hr < 12), m & (hr >= 12)
                if am.sum() > 30 and pm.sum() > 30: R.append(dict(stasiun=s, sumber=f"tahun {y}", el="20-40", delta=0, beda=np.nanmedian(kc[am]) - np.nanmedian(kc[pm]), n_pagi=int(am.sum()), n_sore=int(pm.sum())))
    print(s, "selesai", flush=True)
T = pd.DataFrame(R); T.to_csv(os.path.join(HERE, "d1b_geser.csv"), index=False)
def nol(g):
    g = g.sort_values("delta"); x, y = g.delta.to_numpy(float), g.beda.to_numpy(float); i = np.where(np.sign(y[:-1]) != np.sign(y[1:]))[0]
    return round(float(x[i[0]] - y[i[0]] * (x[i[0] + 1] - x[i[0]]) / (y[i[0] + 1] - y[i[0]])), 1) if len(i) else np.nan
Z = T[~T.sumber.str.startswith("tahun")].groupby(["stasiun", "sumber", "el"]).apply(nol).unstack("el"); print("δ (menit) yang membuat k_c cerah pagi = sore; positif = clear-sky digeser lebih lambat:"); print(Z.to_string())
print("asimetri pada δ = 0 (interval benar), elevasi 20–40°, per tahun:"); print(T[T.sumber.str.startswith("tahun")].pivot(index="stasiun", columns="sumber", values="beda").round(3).to_string())
print("n slot cerah logger, δ = 0:"); print(T[(T.delta == 0) & (T.sumber == "logger")].pivot(index="stasiun", columns="el", values="n_pagi").to_string())
