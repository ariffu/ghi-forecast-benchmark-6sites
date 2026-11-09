# -*- coding: utf-8 -*-
"""Tahap 94 A3–A6: kalibrasi/drift, horizon/bayangan, homogenitas satelit, metadata. Hanya membaca; data tidak diubah."""
import os, math, json, duckdb, numpy as np, pandas as pd, pvlib
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50); pd.set_option("display.max_rows", 200)
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); V6 = r"C:\Users\ariff\Documents\Balai_data_v6"; V61 = r"C:\Users\ariff\Documents\Balai_data_v6_1"
META = dict(banten=(-6.26147, 106.7509, 27), bengkulu=(-3.8607, 102.3381, 9), jambi=(-1.60111, 103.4944, 24), jogja=(-7.731064, 110.353578, 182), kalbar=(0.07489, 109.1905, 2), semarang=(-6.9847, 110.3812, 6))
A3, A4, A5 = [], [], []
for s, (la, lo, alt) in META.items():
    d = pd.read_parquet(os.path.join(V6, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "ghi_wm2", "dni_wm2", "solar_elev_deg", "clp_cot", "clp_cth_km"]); idx = pd.DatetimeIndex(d.ts_wib)
    cs = pd.read_parquet(os.path.join(V61, "clearsky", f"{s}_ineichen.parquet")); q = pd.read_parquet(os.path.join(V61, "qc", f"{s}_qc.parquet"))
    el = d.solar_elev_deg.to_numpy(float)
    with np.errstate(all="ignore"): kc = np.where(cs.ghi_cs > 50, d.ghi_wm2 / cs.ghi_cs, np.nan); kb = np.where(cs.dni_cs > 100, d.dni_wm2 / cs.dni_cs, np.nan)
    # A3: persentil 95 bulanan pada elevasi > 30°, hanya GHI/DNI terukur (kode 0–1)
    mg = (el > 30) & (q.qc_ghi.to_numpy() <= 1); mb = (el > 30) & (q.qc_dni.to_numpy() <= 1)
    pg = pd.Series(kc[mg], index=idx[mg]).groupby(idx[mg].to_period("M")).quantile(0.95); pb = pd.Series(kb[mb], index=idx[mb]).groupby(idx[mb].to_period("M")).quantile(0.95)
    for lab, p in (("GHI", pg), ("DNI", pb)):
        if len(p) < 6: continue
        x = np.arange(len(p)) / 12.0; tr = np.polyfit(x, p.to_numpy(), 1)[0] / np.median(p) * 100; jmp = p.pct_change().abs()
        A3.append(dict(stasiun=s, kanal=lab, bulan=len(p), median_k95=round(float(p.median()), 3), min_k95=round(float(p.min()), 3), bulan_min=str(p.idxmin()), maks_k95=round(float(p.max()), 3), tren_pct_per_tahun=round(float(tr), 2),
                       lompatan_maks_pct=round(float(jmp.max() * 100), 1), bulan_lompatan=str(jmp.idxmax()), bulan_lompat_gt5=int((jmp > 0.05).sum()), per_tahun={str(k): round(float(v), 3) for k, v in p.groupby(p.index.year).median().items()}))
    # A4: horizon — setengah hari cerah (k_c elevasi 20–40° median > 0,9, simpangan < 0,05), lalu k_c elevasi 2–15° per sektor azimut
    az = pvlib.solarposition.get_solarposition(idx.tz_localize("Etc/GMT-7") + pd.Timedelta(minutes=5), la, lo, altitude=alt).azimuth.to_numpy()
    with np.errstate(all="ignore"): kc_lo = np.where(cs.ghi_cs > 5, d.ghi_wm2 / cs.ghi_cs, np.nan)
    half = pd.Series(idx.date).astype(str).to_numpy() + np.where(idx.hour < 12, "am", "pm")
    ref = pd.DataFrame({"h": half, "k": kc, "m": (el > 20) & (el <= 40)}); g = ref[ref.m].groupby("h").k.agg(["median", "std", "count"]); cl = set(g[(g["median"] > 0.9) & (g["std"] < 0.05) & (g["count"] >= 6)].index)
    m = np.isin(half, list(cl)) & (el > 2) & (el <= 15) & np.isfinite(kc_lo); sec = (az[m] // 10 * 10).astype(int)
    T = pd.DataFrame({"sektor": sec, "k": kc_lo[m], "th": idx.year[m]})
    for sct, gg in T.groupby("sektor"):
        A4.append(dict(stasiun=s, azimut=f"{sct}–{sct + 10}", n=len(gg), median_kc=round(float(gg.k.median()), 3), tahun_lt08=int((gg.groupby("th").k.median() < 0.8).sum())))
    # A5: homogenitas satelit — hubungan COT/fraksi awan dengan k_c per periode satelit
    C = pd.read_parquet(os.path.join(B, "93_versi6", f"_csv_baru_dibalik_{s}.parquet"), columns=["timestamp", "source_file"]); C["t"] = pd.to_datetime(C.timestamp) + pd.Timedelta(minutes=10)
    sat = C.set_index("t").source_file.str.extract(r"NC_(H0\d)_")[0].reindex(idx).to_numpy()
    W = {"H08 13 Nov–12 Des 2022": ("2022-11-13", "2022-12-12"), "H09 13 Des 2022–11 Jan 2023": ("2022-12-13", "2023-01-11"),
         "H09 12 Okt–26 Nov 2024": ("2024-10-12", "2024-11-26"), "H08 12 Okt–26 Nov 2025": ("2025-10-12", "2025-11-26"), "H08 12 Okt–26 Nov 2022": ("2022-10-12", "2022-11-26"), "H09 27 Nov–31 Des 2025": ("2025-11-27", "2025-12-31")}
    for lab, (a, b) in W.items():
        w = (idx >= a) & (idx <= b + " 23:59") & (el > 20) & np.isfinite(kc)
        r = dict(stasiun=s, periode=lab, satelit=",".join(sorted(set(x for x in sat[w] if isinstance(x, str)))), n=int(w.sum()))
        for lo_, hi_ in ((0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)):
            mm = w & (kc > lo_) & (kc <= hi_); r[f"COT|kc{lo_}-{hi_}"] = round(float(np.nanmedian(d.clp_cot.to_numpy(float)[mm])), 2) if mm.sum() > 20 else np.nan
        r["frac_COT>=1|kc0.8-1"] = round(float(np.nanmean(d.clp_cot.to_numpy(float)[w & (kc > 0.8) & (kc <= 1.0)] >= 1)), 3); r["CTH_median"] = round(float(np.nanmedian(d.clp_cth_km.to_numpy(float)[w])), 2); A5.append(r)
    print(s, "selesai", flush=True)
a3 = pd.DataFrame(A3); a3.to_csv(os.path.join(HERE, "d3_A3_kalibrasi.csv"), index=False); print("== A3 kalibrasi/drift"); print(a3.to_string(index=False))
a4 = pd.DataFrame(A4); a4.to_csv(os.path.join(HERE, "d3_A4_horizon.csv"), index=False); print("== A4 sektor horizon dengan median k_c < 0,8 (n ≥ 20)"); print(a4[(a4.median_kc < 0.8) & (a4.n >= 20)].to_string(index=False)); print("ringkas per stasiun:", a4.groupby("stasiun").apply(lambda g: f"{len(g)} sektor, n {g.n.sum()}, median {g.median_kc.median():.3f}").to_dict())
a5 = pd.DataFrame(A5); a5.to_csv(os.path.join(HERE, "d3_A5_satelit.csv"), index=False); print("== A5 homogenitas satelit"); print(a5.to_string(index=False))
# A6 metadata
con = duckdb.connect(os.path.join(os.path.dirname(B), "solar_harmonised_clpbanten_v2.duckdb"), read_only=True); dim = con.execute("select site_id, latitude, longitude from std.dim_site").df().set_index("site_id")
reg = con.execute("select site_id, table_name, role, latitude, longitude from std.station_coordinate_registry where role ilike '%asrs%' or role ilike '%logger%' or role ilike '%aws_station%'").df()
T1 = dict(banten=(-6.261, 106.751, 27), bengkulu=(-3.861, 102.338, 9), jambi=(-1.583, 103.667, 24), jogja=(-7.731, 110.354, 182), kalbar=(0.075, 109.191, 2), semarang=(-6.985, 110.381, 6))
CLPC = dict(banten=(-6.2615, 106.7508), bengkulu=(-3.86, 102.31), jambi=(-1.602, 103.485), jogja=(-7.731, 110.354), kalbar=(0.075, 109.19), semarang=(-6.9847, 110.3806))
def km(a, b): la_ = math.radians((a[0] + b[0]) / 2); return round(111.2 * math.hypot(a[0] - b[0], (a[1] - b[1]) * math.cos(la_)), 2)
rows = []
for s in META:
    t1 = T1[s]; r = dict(stasiun=s, tabel1=f"{t1[0]}, {t1[1]}, {t1[2]} m", dim_site=f"{dim.loc[s, 'latitude']:.5f}, {dim.loc[s, 'longitude']:.5f}", pusat_CLP=f"{CLPC[s][0]}, {CLPC[s][1]}", CLP_ke_tabel1_km=km(CLPC[s], t1[:2]),
                         ketinggian_pvlib=round(max(0.0, float(pvlib.location.lookup_altitude(t1[0], t1[1]))), 0))
    rr = reg[reg.site_id == s]; r["koordinat_alat_di_DB"] = "; ".join(f"{x.role}: {x.latitude:.5f}, {x.longitude:.5f} ({km((x.latitude, x.longitude), t1[:2])} km)" for _, x in rr.drop_duplicates(["latitude", "longitude"]).iterrows()) or "tidak ada"
    rows.append(r)
a6 = pd.DataFrame(rows); a6.to_csv(os.path.join(HERE, "d3_A6_metadata.csv"), index=False); print("== A6 metadata"); print(a6.to_string(index=False))
