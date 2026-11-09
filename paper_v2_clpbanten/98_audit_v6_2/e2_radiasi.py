# -*- coding: utf-8 -*-
"""Tahap 98 (salinan uji tahap 95 untuk V6.2) R1–R9: uji fisis radiasi pada Balai_data_v6_2 (hanya membaca)."""
import os, numpy as np, pandas as pd, pvlib
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 60); pd.set_option("display.max_rows", 200)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_2"
META = dict(banten=(-6.26147, 106.7509, 27), bengkulu=(-3.86493, 102.311998, 9), jambi=(-1.60111, 103.4944, 24), jogja=(-7.731064, 110.353578, 182), kalbar=(0.07489, 109.1905, 2), semarang=(-6.9847, 110.3812, 6))
O = {k: [] for k in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9")}
for s, (la, lo, alt) in META.items():
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "ghi_wm2", "dhi_wm2", "dni_wm2", "reflected_wm2", "nett_wm2", "sunshine_slot_min", "synop_sunshine_h", "solar_elev_deg"])
    q = pd.read_parquet(os.path.join(V, "qc", f"{s}_qc.parquet")); cs = pd.read_parquet(os.path.join(V, "clearsky", f"{s}_ineichen.parquet"))
    ts = pd.DatetimeIndex(d.ts_wib); idx = ts.tz_localize("Etc/GMT-7"); sp = pvlib.solarposition.get_solarposition(idx + pd.Timedelta(minutes=5), la, lo, altitude=alt)
    Z = sp.apparent_zenith.to_numpy(); el = 90 - Z; mu = np.cos(np.radians(Z)); E0 = pvlib.irradiance.get_extra_radiation(idx).to_numpy()
    G, Dh, Dn, Rf, Rn, SS = (d[c].to_numpy(float) for c in ("ghi_wm2", "dhi_wm2", "dni_wm2", "reflected_wm2", "nett_wm2", "sunshine_slot_min"))
    Gc, Dnc = cs.ghi_cs.to_numpy(), cs.dni_cs.to_numpy(); yr = ts.year.to_numpy(); hr = ts.hour.to_numpy(); u = q.qc_uji.to_numpy(); qg = q.qc_ghi.to_numpy(); qd = q.qc_dhi.to_numpy(); qn = q.qc_dni.to_numpy()
    day = el > 5
    with np.errstate(all="ignore"):
        kc = np.where(day & (Gc > 50), G / Gc, np.nan); kt = np.where(day, G / (E0 * mu), np.nan); kd = np.where(day & (G > 20), Dh / G, np.nan)
    # R1 bit uji per tahun dan kode asal GHI
    for y in range(2022, 2026):
        for code in (0, 1, 3):
            m = day & (yr == y) & (qg == code) & np.isfinite(G)
            if m.sum() < 200: continue
            O["R1"].append(dict(stasiun=s, tahun=y, kode_ghi=code, n=int(m.sum()), **{f"b{b}": round(float(((u[m] >> b) & 1).mean()) * 100, 3) for b in range(8)}))
    # R2 malam
    n_ = el < -2
    for c, x in (("ghi", G), ("dhi", Dh), ("dni", Dn), ("refl", Rf)):
        xm = x[n_]; f = np.isfinite(xm)
        O["R2"].append(dict(stasiun=s, var=c, n_malam=int(n_.sum()), isi=round(float(f.mean()), 4), nol_persis=round(float((xm[f] == 0).mean()), 4) if f.any() else np.nan, negatif=round(float((xm[f] < 0).mean()), 4) if f.any() else np.nan,
                            p01=round(float(np.percentile(xm[f], 1)), 2) if f.any() else np.nan, p99=round(float(np.percentile(xm[f], 99)), 2) if f.any() else np.nan))
    # R3 peningkatan awan
    k = kc[np.isfinite(kc)]; e = el[np.isfinite(kc)]
    r3 = dict(stasiun=s, n=len(k), **{f"kc_gt_{t}": round(float((k > t).mean()) * 100, 3) for t in (1.0, 1.1, 1.2, 1.3, 1.5)}, kc_maks=round(float(k.max()), 3), kc_p999=round(float(np.percentile(k, 99.9)), 3))
    for lo_, hi_ in ((5, 15), (15, 30), (30, 90)):
        mm = (e > lo_) & (e <= hi_); r3[f"kc_gt1.3_el{lo_}-{hi_}"] = int((k[mm] > 1.3).sum())
    hi13 = np.isfinite(kc) & (kc > 1.3); r3["kc_gt1.3_kode"] = str(pd.Series(qg[hi13]).value_counts().to_dict()); O["R3"].append(r3)
    # R4 kecocokan clear-sky: periode cerah dari DHI/GHI ukur dan variabilitas, tidak bergantung pada model clear-sky
    sd = pd.Series(G / np.where(mu > 0.05, E0 * mu, np.nan)).rolling(6, center=True, min_periods=6).std().to_numpy()
    cl = day & (el > 15) & (qd == 0) & (qg == 0) & np.isfinite(kd) & (kd < 0.3) & (sd < 0.015)
    r4 = dict(stasiun=s, slot_cerah=int(cl.sum()), hari_cerah=int(pd.Series(ts[cl].date).nunique()))
    for lo_, hi_ in ((15, 30), (30, 50), (50, 90)):
        mm = cl & (el > lo_) & (el <= hi_); r4[f"kc_med_el{lo_}-{hi_}"] = round(float(np.nanmedian(kc[mm])), 3) if mm.sum() > 50 else np.nan
    r4["kb_med_cerah_el>30"] = round(float(np.nanmedian((Dn / Dnc)[cl & (el > 30) & (qn == 0)])), 3) if (cl & (el > 30) & (qn == 0)).sum() > 50 else np.nan
    # Linke yang membuat GHI cerah = Ineichen (titik tengah), per bulan; dibanding Remund
    if cl.sum() > 200:
        am = pvlib.atmosphere.get_relative_airmass(Z[cl]); ama = pvlib.atmosphere.get_absolute_airmass(am, pvlib.atmosphere.alt2pres(alt))
        TLg = np.arange(1.5, 8.01, 0.05); best = np.empty(cl.sum())
        Gm = np.stack([pvlib.clearsky.ineichen(Z[cl], ama, tl, altitude=alt, dni_extra=E0[cl])["ghi"] for tl in TLg])
        best = TLg[np.nanargmin(np.abs(Gm - G[cl]), axis=0)]
        rem = pvlib.clearsky.lookup_linke_turbidity(idx[cl], la, lo, interp_turbidity=True).to_numpy()
        r4["TL_cocok_median"] = round(float(np.median(best)), 2); r4["TL_remund_median"] = round(float(np.median(rem)), 2); r4["TL_cocok_minus_remund"] = round(float(np.median(best - rem)), 2)
        mo = ts[cl].month; r4["TL_selisih_per_bulan"] = str({int(a): round(float(b), 2) for a, b in pd.Series(best - rem).groupby(mo).median().items()})
    O["R4"].append(r4)
    # R5 lama penyinaran WMO: DNI > 120 W m-2
    m5 = day & np.isfinite(SS) & np.isfinite(Dn) & (qn <= 1)
    if m5.sum() > 1000:
        O["R5"].append(dict(stasiun=s, n=int(m5.sum()), ss_maks=float(np.nanmax(SS)), ss_unik=int(len(np.unique(SS[m5]))), r=round(float(np.corrcoef(SS[m5], Dn[m5])[0, 1]), 3),
                            ss_saat_dni_gt300=round(float(np.mean(SS[m5 & (Dn > 300)])), 2), ss_saat_dni_lt50=round(float(np.mean(SS[m5 & (Dn < 50)])), 2),
                            frac_ss0_dni_gt300=round(float(np.mean(SS[m5 & (Dn > 300)] == 0)), 4), frac_ss10_dni_lt50=round(float(np.mean(SS[m5 & (Dn < 50)] >= 9.5)), 4),
                            ambang_dni_terbaik=int(min(range(40, 400, 10), key=lambda a: np.mean((SS[m5] > 5) != (Dn[m5] > a))))))
    else: O["R5"].append(dict(stasiun=s, n=int(m5.sum())))
    # R6 albedo siang cerah
    m6 = day & (el > 30) & np.isfinite(Rf) & np.isfinite(kc) & (kc > 0.9) & (kc < 1.1) & (q.qc_refl.to_numpy() <= 1)
    a6 = pd.Series(Rf[m6] / G[m6]).groupby(yr[m6]).median().round(3).to_dict(); O["R6"].append(dict(stasiun=s, n=int(m6.sum()), **{f"albedo_{y}": v for y, v in a6.items()}, lebih_1=int((Rf[day] > G[day] + 5).sum())))
    # R7 selubung k_d–k_t
    w = np.isfinite(kt) & np.isfinite(kd) & (el > 10)
    for code in (0, 1, 3):
        mm = w & (qd == code)
        if mm.sum() < 500: continue
        O["R7"].append({"stasiun": s, "kode_dhi": code, "n": int(mm.sum()), "kt>0.75&kd>0.6_%": round(float(((kt > 0.75) & (kd > 0.6))[mm].mean()) * 100, 3), "kt<0.2&kd<0.8_%": round(float(((kt < 0.2) & (kd < 0.8))[mm].mean()) * 100, 3),
                        "kd<0.1_%": round(float((kd < 0.1)[mm].mean()) * 100, 3), "kd>1.05_%": round(float((kd > 1.05)[mm].mean()) * 100, 3)})
    # R8 total harian (hari dengan GHI lengkap di semua slot elevasi > 0)
    df = pd.DataFrame({"t": ts, "G": np.where(el > 0, G, 0.0), "lengkap": np.where(el > 0, np.isfinite(G), True)}); g = df.groupby(df.t.dt.date).agg(G=("G", "sum"), ok=("lengkap", "all"))
    g = g[g.ok]; g.index = pd.to_datetime(g.index); kwh = g.G / 6 / 1000
    O["R8"].append(dict(stasiun=s, **{f"kWh_{y}": round(float(v), 2) for y, v in kwh.groupby(kwh.index.year).mean().items()}, **{f"hari_{y}": int(v) for y, v in kwh.groupby(kwh.index.year).size().items()}, min_hari=round(float(kwh.min()), 2), maks_hari=round(float(kwh.max()), 2)))
    # R9 radiasi neto
    f9 = np.isfinite(Rn)
    O["R9"].append(dict(stasiun=s, isi=round(float(f9.mean()), 3), malam_median=round(float(np.nanmedian(Rn[n_])), 1) if (f9 & n_).any() else np.nan, malam_positif=round(float(np.nanmean(Rn[n_ & f9] > 5)), 4) if (f9 & n_).any() else np.nan,
                        siang_rasio_RnG_median=round(float(np.nanmedian((Rn / G)[day & (el > 40) & f9 & (G > 300)])), 3) if (f9 & day).any() else np.nan, Rn_gt_G=int((f9 & day & (Rn > G + 10)).sum())))
    print(s, "selesai", flush=True)
for k, L in O.items():
    T = pd.DataFrame(L); T.to_csv(os.path.join(HERE, f"{k}.csv"), index=False); print("==", k); print(T.to_string(index=False))
