# -*- coding: utf-8 -*-
"""Tahap 98 (salinan uji tahap 95 untuk V6.2) M1–M5: uji meteorologi AWS/SYNOP dan aerosol pada Balai_data_v6_2 (hanya membaca), plus rincian C1."""
import os, re, io, zipfile, numpy as np, pandas as pd
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 60); pd.set_option("display.max_colwidth", 140)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_2"
META = dict(banten=(-6.26147, 106.7509, 27), bengkulu=(-3.86493, 102.311998, 9), jambi=(-1.60111, 103.4944, 24), jogja=(-7.731064, 110.353578, 182), kalbar=(0.07489, 109.1905, 2), semarang=(-6.9847, 110.3812, 6))
O = {k: [] for k in ("M1", "M2", "M3", "M4", "M5")}
def runs(x, n):   # proporsi nilai dalam runtun sama ≥ n slot
    s = pd.Series(x); g = (s != s.shift()).cumsum(); r = s.groupby(g).transform("size").to_numpy(); return float(((r >= n) & np.isfinite(x)).sum() / max(np.isfinite(x).sum(), 1))
for s, (la, lo, alt) in META.items():
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet")); ts = pd.DatetimeIndex(d.ts_wib); el = d.solar_elev_deg.to_numpy(float)
    cs = pd.read_parquet(os.path.join(V, "clearsky", f"{s}_ineichen.parquet")).ghi_cs.to_numpy()
    # M1 batas dan langkah AWS
    r = dict(stasiun=s)
    for c, lo_, hi_, step, rn in (("aws_temp_c", 10, 42, 4, 36), ("aws_rh_pct", 10, 100, 25, 36), ("aws_pressure_hpa", 900, 1025, 2, 36), ("aws_wind_speed_ms", 0, 40, 15, 36), ("aws_rain_mm", 0, 60, 60, 1000)):
        x = pd.to_numeric(d[c], errors="coerce").to_numpy(float); f = np.isfinite(x); dx = np.abs(np.diff(x, prepend=np.nan))
        r[f"{c}_isi"] = round(float(f.mean()), 3); r[f"{c}_luar"] = int(((x < lo_) | (x > hi_))[f].sum()); r[f"{c}_langkah"] = int((dx > step).sum())
        if c != "aws_rain_mm": r[f"{c}_runtun6j"] = round(runs(np.where(x == 0, np.nan, x) if c == "aws_wind_speed_ms" else x, rn), 4)
    O["M1"].append(r)
    # M2 titik embun SYNOP
    T, Td, RH = (pd.to_numeric(d[c], errors="coerce").to_numpy(float) for c in ("synop_temp_c", "synop_dewpoint_c", "synop_rh_pct"))
    f = np.isfinite(T) & np.isfinite(Td) & np.isfinite(RH)
    es = lambda t: 6.1094 * np.exp(17.625 * t / (t + 243.04)); rh = 100 * es(Td) / es(T)
    ah = pd.to_numeric(d.aws_rh_pct, errors="coerce").to_numpy(float); at = pd.to_numeric(d.aws_temp_c, errors="coerce").to_numpy(float); g = f & np.isfinite(ah)
    O["M2"].append(dict(stasiun=s, n_synop=int(f.sum()), Td_gt_T=int((Td[f] > T[f] + 0.05).sum()), rh_magnus_minus_rh=round(float(np.median(rh[f] - RH[f])), 2), abs_gt5=round(float((np.abs(rh[f] - RH[f]) > 5).mean()), 4),
                        aws_rh_minus_synop=round(float(np.median(ah[g] - RH[g])), 2), aws_T_minus_synop=round(float(np.median(at[g] - T[g])), 2), synop_jam=",".join(sorted(pd.Series(ts[f].strftime("%H")).value_counts().loc[lambda v: v > 200].index))))
    # M3 tekanan dan pasang S2
    p = pd.to_numeric(d.aws_pressure_hpa, errors="coerce"); ps = pd.to_numeric(d.synop_pressure_hpa, errors="coerce")
    exp = 1010.0 * (1 - 2.25577e-5 * alt) ** 5.25588
    pa = p - p.rolling(144, center=True, min_periods=100).mean(); w = pa.notna().to_numpy(); lst = ((ts.hour * 60 + ts.minute + (lo - 105) * 4) % 1440).to_numpy()
    m3 = dict(stasiun=s, ketinggian_m=alt, aws_p_median=round(float(p.median()), 1), harapan_QFE_dari_ketinggian=round(exp, 1), synop_p_median=round(float(ps.median()), 1), synop_minus_aws=round(float((ps - p).median()), 2))
    if w.sum() > 1000:
        for k, nm in ((1, "S1"), (2, "S2")):
            ang = 2 * np.pi * k * lst[w] / 1440; A = np.c_[np.cos(ang), np.sin(ang), np.ones(w.sum())]; co = np.linalg.lstsq(A, pa.to_numpy()[w], rcond=None)[0]
            ph = (np.degrees(np.arctan2(co[1], co[0])) % 360) / 360 * (1440 / k); m3[f"{nm}_amp_hpa"] = round(float(np.hypot(co[0], co[1])), 2); m3[f"{nm}_puncak_LST"] = f"{int(ph) // 60:02d}:{int(ph) % 60:02d}"
    O["M3"].append(m3)
    # M4 hujan saat cerah (per jam)
    rain = pd.to_numeric(d.aws_rain_mm, errors="coerce"); G = d.ghi_wm2.to_numpy(float)
    H = pd.DataFrame({"r": rain.to_numpy(), "G": np.where(el > 20, G, np.nan), "C": np.where(el > 20, cs, np.nan)}, index=ts).resample("1h").agg({"r": "sum", "G": "mean", "C": "mean"})
    kc = H.G / H.C; jh = (H.r > 0.5) & (kc > 0.9); jr = H.r > 0.5
    O["M4"].append(dict(stasiun=s, jam_hujan_gt0_5=int(jr.sum()), jam_hujan_kc_gt0_9=int(jh.sum()), proporsi=round(float(jh.sum() / max((jr & kc.notna()).sum(), 1)), 4), hujan_tahunan_mm=str(rain.groupby(ts.year).sum().round(0).to_dict())))
    # M5 aerosol
    ao, an = pd.to_numeric(d.aod_500nm, errors="coerce"), pd.to_numeric(d.angstrom_exp, errors="coerce")
    O["M5"].append(dict(stasiun=s, aod_isi=round(float(ao.notna().mean()), 3), aod_unik=int(ao.nunique()), aod_min=ao.min(), aod_median=ao.median(), aod_maks=ao.max(), ang_isi=round(float(an.notna().mean()), 3), ang_unik=int(an.nunique()),
                        ang_min=an.min(), ang_maks=an.max(), aod_berubah_per_hari=round(float(ao.groupby(ts.date).nunique().mean()), 2) if ao.notna().any() else np.nan))
    print(s, "selesai", flush=True)
for k, L in O.items():
    T_ = pd.DataFrame(L); T_.to_csv(os.path.join(HERE, f"{k}.csv"), index=False); print("==", k); print(T_.T.to_string() if k == "M1" else T_.to_string(index=False))
