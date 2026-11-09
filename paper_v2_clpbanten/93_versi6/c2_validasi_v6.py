# -*- coding: utf-8 -*-
"""Tahap 93: validasi Balai_data_v6 (sebelum P5) dengan uji tahap 91: segaris AWS, isi CLP menurut elevasi, CER, struktur, fisis. Hanya membaca."""
import os, json, numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
V5 = r"C:\Users\ariff\Documents\Balai_data_v5_final87\00_data"; V6 = r"C:\Users\ariff\Documents\Balai_data_v6\00_data"; HERE = os.path.dirname(os.path.abspath(__file__))
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; R = []
def seg(a, idx, tol=0.006):
    h0 = idx.minute == 0; s = pd.Series(a); pv = s.where(h0).ffill().to_numpy(); nx = s.where(h0).bfill().to_numpy(); fr = idx.minute.to_numpy() / 60
    return (~h0) & np.isfinite(a) & (np.abs(a - (pv + (nx - pv) * fr)) < tol) & (np.abs(nx - pv) > tol)
for s in S:
    a, b = pd.read_parquet(os.path.join(V5, f"{s}_full.parquet")), pd.read_parquet(os.path.join(V6, f"{s}_full.parquet")); idx = pd.DatetimeIndex(b.ts_wib); day = (b.solar_elev_deg > 5).to_numpy(); nh = day & (idx.minute != 0)
    r = dict(stasiun=s, struktur_sama=bool(list(a.columns) == list(b.columns) and (a.dtypes == b.dtypes).all() and len(a) == len(b) and a.ts_wib.equals(b.ts_wib)))
    for c in ("aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms"):
        x5, x6 = a[c].to_numpy(float), b[c].to_numpy(float); xx = x5[np.isfinite(x5)][:200000]; res = next((q for q in (1.0, 0.1, 0.01) if np.mean(np.abs(xx / q - np.round(xx / q)) < 1e-6) > 0.95), 0.0); tl = max(0.006, res / 2 + 0.001)
        s5 = seg(x5, idx, tl); s6 = seg(x6, idx, tl); r[f"segaris_{c}_V5"] = round(float(s5[nh].mean()), 4); r[f"bocor_sisa_{c}_V6"] = round(float((s6 & np.isclose(x5, x6))[nh].mean()), 4)
    e = b.solar_elev_deg; bins = pd.cut(e, [5, 7.5, 10, 15, 90])
    for lab, d in (("V5", a), ("V6", b)):
        g = d.clp_cot.notna().groupby(bins.to_numpy(), observed=True).mean(); r.update({f"clp_isi_{lab}_{k}": round(v, 3) for k, v in g.items()})
    r["cer_nol_V6"] = int((b.clp_cer_um == 0).sum()); r["cer_min_V6"] = round(float(b.clp_cer_um.min()), 3)
    r["rh_luar_0_100"] = int(((b.aws_rh_pct < 0) | (b.aws_rh_pct > 100)).sum()); r["suhu_min_max"] = (round(float(b.aws_temp_c.min()), 2), round(float(b.aws_temp_c.max()), 2)); r["tekanan_min_max"] = (round(float(b.aws_pressure_hpa.min()), 1), round(float(b.aws_pressure_hpa.max()), 1))
    r["arah_sin2cos2_dev"] = round(float(((b.aws_wind_dir_sin ** 2 + b.aws_wind_dir_cos ** 2) - 1).abs().max()), 6) if b.aws_wind_dir_sin.notna().any() else None
    for c in ("aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "clp_cot"):
        r[f"kosong_{c}_V5_V6"] = (round(float(a[c][day].isna().mean()), 4), round(float(b[c][day].isna().mean()), 4))
    q = day & b.clp_cot.notna().to_numpy(); r["flag_cocok_siang"] = round(float(((b.clp_cot[q] >= 1).astype(int) == b.clp_cloud_present_int[q]).mean()), 4)
    r["radiasi_identik"] = all(a[c].equals(b[c]) for c in ("ghi_wm2", "dhi_wm2", "dni_wm2", "reflected_wm2", "kt", "clear_sky_ghi"))
    R.append(r)
T = pd.DataFrame(R).set_index("stasiun").T; print(T.to_string()); T.to_csv(os.path.join(HERE, "c2_validasi.csv"))
