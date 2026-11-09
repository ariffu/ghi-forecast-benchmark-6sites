# -*- coding: utf-8 -*-
"""Tahap 94: kegagalan uji neraca BSRN menurut konvensi zenit (awal slot t lawan tengah interval t+5 lawan rata-rata cos Z per menit), elevasi, dan kode QC. Hanya membaca."""
import os, numpy as np, pandas as pd, pvlib
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
V6 = r"C:\Users\ariff\Documents\Balai_data_v6"; QC = r"C:\Users\ariff\Documents\Balai_data_v6_1\qc"
META = dict(banten=(-6.26147, 106.7509, 27), bengkulu=(-3.8607, 102.3381, 9), jambi=(-1.60111, 103.4944, 24), jogja=(-7.731064, 110.353578, 182), kalbar=(0.07489, 109.1905, 2), semarang=(-6.9847, 110.3812, 6))
for s, (la, lo, alt) in META.items():
    d = pd.read_parquet(os.path.join(V6, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "ghi_wm2", "dhi_wm2", "dni_wm2", "solar_elev_deg"]); q = pd.read_parquet(os.path.join(QC, f"{s}_qc.parquet"))
    idx = pd.DatetimeIndex(d.ts_wib).tz_localize("Etc/GMT-7"); G, Dh, Dn = d.ghi_wm2.to_numpy(float), d.dhi_wm2.to_numpy(float), d.dni_wm2.to_numpy(float)
    t1 = pd.date_range(idx[0], idx[-1] + pd.Timedelta(minutes=9), freq="1min"); z1 = pvlib.solarposition.get_solarposition(t1, la, lo, altitude=alt).apparent_zenith
    mu1 = np.cos(np.radians(z1)).clip(lower=0); mu_avg = mu1.groupby(t1.floor("10min")).mean().reindex(idx).to_numpy()
    out = {}
    for lab, mu in (("awal t (elevasi kolom DB)", np.sin(np.radians(d.solar_elev_deg.to_numpy(float)))), ("tengah t+5", np.cos(np.radians(pvlib.solarposition.get_solarposition(idx + pd.Timedelta(minutes=5), la, lo, altitude=alt).apparent_zenith.to_numpy()))), ("rata-rata cos Z per menit", mu_avg)):
        Z = np.degrees(np.arccos(np.clip(mu, -1, 1)))
        with np.errstate(all="ignore"):
            r = G / (Dh + Dn * mu); f = (G > 50) & (((Z < 75) & (np.abs(r - 1) > 0.08)) | ((Z >= 75) & (Z < 93) & (np.abs(r - 1) > 0.15)))
        el = 90 - Z; out[lab] = (int(f.sum()), int((f & (el > 15)).sum()), np.round(np.nanmedian(el[f]), 1) if f.any() else np.nan)
    print(s, {k: f"gagal {a} (elevasi>15°: {b}), elevasi median {c}" for k, (a, b, c) in out.items()})
    f = (q.qc_uji.to_numpy() >> 6) & 1 == 1
    print("   gagal (t+5) menurut kode DNI:", pd.Series(q.qc_dni.to_numpy()[f]).value_counts().to_dict(), "| menurut kode GHI:", pd.Series(q.qc_ghi.to_numpy()[f]).value_counts().to_dict())
