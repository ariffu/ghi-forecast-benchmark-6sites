# -*- coding: utf-8 -*-
"""Tahap 94 A1: clear-sky Ineichen–Perez rata-rata interval [t, t+9] dari nilai per menit, koordinat dan ketinggian metadata stasiun.
Keluaran Balai_data_v6_1/clearsky/{s}_ineichen.parquet (ts_wib, ghi_cs, dni_cs, dhi_cs) + validasi simetri pagi–sore. Tidak mengubah 00_clearsky lama."""
import os, json, numpy as np, pandas as pd, pvlib
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = r"C:\Users\ariff\Documents\Balai_data_v6_1\clearsky"; os.makedirs(OUT, exist_ok=True)
V6 = r"C:\Users\ariff\Documents\Balai_data_v6\00_data"; OLD = os.path.join(os.path.dirname(HERE), "00_clearsky")
META = dict(banten=(-6.26147, 106.7509, 27), bengkulu=(-3.8607, 102.3381, 9), jambi=(-1.60111, 103.4944, 24), jogja=(-7.731064, 110.353578, 182), kalbar=(0.07489, 109.1905, 2), semarang=(-6.9847, 110.3812, 6))
t1 = pd.date_range("2022-01-01 00:00", "2026-01-01 00:59", freq="1min", tz="Etc/GMT-7"); prov = {}; V = []
for s, (la, lo, alt) in META.items():
    loc = pvlib.location.Location(la, lo, tz="Etc/GMT-7", altitude=alt); lt = pvlib.clearsky.lookup_linke_turbidity(t1, la, lo, interp_turbidity=True)
    c = loc.get_clearsky(t1, model="ineichen", linke_turbidity=lt)
    g = c.groupby(t1.floor("10min")).mean()                                # rata-rata menit t..t+9
    d = pd.read_parquet(os.path.join(V6, f"{s}_full.parquet"), columns=["ts_wib", "ghi_wm2", "solar_elev_deg", "kt"]); idx = pd.DatetimeIndex(d.ts_wib).tz_localize("Etc/GMT-7")
    g = g.reindex(idx); assert g.notna().all().all(), s
    out = pd.DataFrame({"ts_wib": d.ts_wib.values, "ghi_cs": g.ghi.to_numpy(), "dni_cs": g.dni.to_numpy(), "dhi_cs": g.dhi.to_numpy()}); out.to_parquet(os.path.join(OUT, f"{s}_ineichen.parquet"), index=False)
    old = pd.read_parquet(os.path.join(OLD, f"{s}_ineichen.parquet")).set_index("ts_wib").ghi_cs.reindex(d.ts_wib).to_numpy()
    prov[s] = dict(latitude=la, longitude=lo, altitude_m=alt, linke_min=float(lt.min()), linke_max=float(lt.max()))
    # validasi: k_c pada periode cerah, pagi lawan sore pada elevasi yang sama
    ghi = d.ghi_wm2.to_numpy(float); el = d.solar_elev_deg.to_numpy(float); hr = idx.hour.to_numpy(); ok = ~np.isnan(d.kt.to_numpy(float))
    for lab, cs in (("lama (titik t, dim_site, ketinggian pvlib)", old), ("baru (interval, metadata)", out.ghi_cs.to_numpy())):
        with np.errstate(all="ignore"): kc = np.where(ok & (cs > 50), ghi / cs, np.nan)
        k = pd.Series(kc); cl = (k.rolling(6, center=True, min_periods=6).std() < 0.03) & (k.rolling(6, center=True, min_periods=6).mean().between(0.85, 1.15))
        r = dict(stasiun=s, clear_sky=lab, slot_cerah=int(cl.sum()), kc_median_cerah=round(float(k[cl].median()), 3))
        for lo_, hi_ in ((10, 20), (20, 40), (40, 60)):
            m = cl.to_numpy() & (el > lo_) & (el <= hi_); am, pm = m & (hr < 12), m & (hr >= 12)
            r[f"pagi−sore el{lo_}-{hi_}"] = round(float(np.nanmedian(kc[am]) - np.nanmedian(kc[pm])), 4) if am.sum() > 30 and pm.sum() > 30 else np.nan
        V.append(r)
    print(s, "selesai", flush=True)
json.dump(dict(model="Ineichen–Perez, pvlib " + pvlib.__version__ + ", rata-rata nilai per menit t..t+9 (interval yang sama dengan GHI)", linke="Remund et al. (2003), interp_turbidity=True",
               time="label ts_wib = awal interval, WIB (UTC+7)", sites=prov), open(os.path.join(OUT, "provenance.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
T = pd.DataFrame(V); T.to_csv(os.path.join(HERE, "d1_validasi_clearsky.csv"), index=False); print(T.to_string(index=False))
