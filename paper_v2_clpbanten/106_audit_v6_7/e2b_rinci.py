# -*- coding: utf-8 -*-
"""Tahap 106 (salinan untuk V6.7) (salinan uji tahap 98 untuk V6.4) (salinan uji tahap 95 untuk V6.2) rincian R: k_c > 1,3; k_d < 0,1 Bengkulu; definisi nett; penyinaran Kalbar; GHI 2022 Banten/Yogyakarta."""
import os, numpy as np, pandas as pd, pvlib
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_7"
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; R = []
for s in S:
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "ghi_wm2", "dhi_wm2", "dni_wm2", "reflected_wm2", "nett_wm2", "sunshine_slot_min", "solar_elev_deg"])
    q = pd.read_parquet(os.path.join(V, "qc", f"{s}_qc.parquet")); cs = pd.read_parquet(os.path.join(V, "clearsky", f"{s}_ineichen.parquet")).ghi_cs.to_numpy()
    p = pd.read_parquet(os.path.join(V, "provenance", f"{s}_provenance.parquet"), columns=["ghi_sumber"]).ghi_sumber.astype(str).to_numpy()
    ts = pd.DatetimeIndex(d.ts_wib); G, Dh, Rf, Rn = d.ghi_wm2.to_numpy(float), d.dhi_wm2.to_numpy(float), d.reflected_wm2.to_numpy(float), d.nett_wm2.to_numpy(float); el = d.solar_elev_deg.to_numpy(float)
    with np.errstate(all="ignore"): kc = np.where((el > 5) & (cs > 50), G / cs, np.nan)
    h = np.isfinite(kc) & (kc > 1.3); hh = pd.Series(ts[h].hour).value_counts().sort_index()
    nb = pd.Series(kc).shift(1).to_numpy(); na = pd.Series(kc).shift(-1).to_numpy()
    tung = h & ~((nb > 1.15) | (na > 1.15))   # lonjakan tunggal
    hari = pd.Series(ts[h].date).value_counts()
    r = dict(stasiun=s, n_kc13=int(h.sum()), jam_terbanyak=str(hh.sort_values(ascending=False).head(4).to_dict()), pagi_lt9=round(float((ts[h].hour < 9).mean()), 3), sore_ge15=round(float((ts[h].hour >= 15).mean()), 3),
             G_median=round(float(np.median(G[h])), 0), cs_median=round(float(np.median(cs[h])), 0), tunggal=round(float(tung.sum() / max(h.sum(), 1)), 3), hari_terbanyak=str(hari.head(3).to_dict()),
             sumber=str(pd.Series(p[h]).value_counts().head(4).to_dict()))
    w = (el > 30) & np.isfinite(Dh) & np.isfinite(G) & (G > 300) & (q.qc_dhi.to_numpy() == 0)
    kd = Dh / np.where(G > 0, G, np.nan); r["kd_lt0.1_%"] = round(float((kd[w] < 0.1).mean()) * 100, 2)
    if (w & (kd < 0.1)).sum() > 50:
        y = pd.Series((kd < 0.1)[w]).groupby(ts[w].year).mean().round(3).to_dict(); r["kd_lt0.1_per_tahun"] = str(y); r["kd_p1_el>30"] = round(float(np.percentile(kd[w], 1)), 3)
    f = np.isfinite(Rn) & np.isfinite(G) & np.isfinite(Rf); r["nett=G−refl_%"] = round(float(np.isclose(Rn[f], G[f] - Rf[f], atol=0.6).mean()) * 100, 2)
    for y in (2022, 2023, 2024, 2025):
        m = (ts.year == y) & np.isfinite(kc) & (el > 30)
        r[f"kc_median_{y}"] = round(float(np.median(kc[m])), 3)
    R.append(r); print(s, flush=True)
T = pd.DataFrame(R); T.to_csv(os.path.join(HERE, "R_rinci.csv"), index=False); print(T.T.to_string())
# penyinaran Kalbar: per tahun dan geseran waktu
d = pd.read_parquet(os.path.join(V, "00_data", "kalbar_full.parquet"), columns=["ts_wib", "dni_wm2", "sunshine_slot_min", "solar_elev_deg"]); ts = pd.DatetimeIndex(d.ts_wib)
ss, dn = d.sunshine_slot_min, d.dni_wm2; m = (d.solar_elev_deg > 5) & ss.notna() & dn.notna()
print("Kalbar penyinaran per tahun (n, cocok dengan DNI>120):", {y: (int((m & (ts.year == y)).sum()), round(float(((ss > 5) == (dn > 120))[m & (ts.year == y)].mean()), 3)) for y in range(2022, 2026)})
print("Kalbar geseran:", {k * 10: round(float(((ss.shift(-k) > 5) == (dn > 120))[m].mean()), 3) for k in range(-6, 7)})
