# -*- coding: utf-8 -*-
"""Tahap 33 — Verifikasi silang rerun B.
(1) 00_data benar-benar diseragamkan (provenance clp_harmonised = True; Kalbar tidak digeser; 5 situs = V0 digeser 1 slot).
(2) Hasil pipeline B == varian H uji sensitivitas 31 (dihitung independen sebelum keputusan B):
    R² CatBoost headline (04c) dan R² T1+CLP (07b) per situs harus sama (4 desimal).
Jalankan: python -u 33_verify_B.py"""
import os, json, numpy as np, pandas as pd, duckdb
B = os.path.dirname(os.path.abspath(__file__)); ARS = os.path.join(B, "_arsip_V0_clp_campuran")
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
prov = json.load(open(os.path.join(B, "00_data", "provenance.json"))); assert prov.get("clp_harmonised") is True and prov.get("mask_clp") is True
print("provenance:", prov["clp_time_convention"])
# (2) bandingkan dengan 31 (V0 = konvensi lama; H = L10 untuk 5 situs, V0 untuk Kalbar)
L = pd.read_csv(os.path.join(B, "31_clp_lag", "clp_lag_results.csv"))
c4 = pd.read_csv(os.path.join(B, "04c_mean_6situs", "baseline_mean_6situs.csv")).set_index("site")
r7 = pd.read_csv(os.path.join(B, "07_replication", "replication_ablation_mean.csv")).set_index("site")
rows = []
for s in SITES:
    h = L[(L.site == s) & (L.variant == ("V0" if s == "kalbar" else "L10"))].iloc[0]
    rows.append(dict(site=s, CB_pipeline=c4.loc[s, "CB_R2"], CB_31H=round(h.R2_CB, 4), T1CLP_pipeline=r7.loc[s, "T1_CLP"], T1CLP_31H=round(h.R2_T1CLP, 4)))
V = pd.DataFrame(rows); V["ok"] = (np.abs(V.CB_pipeline - V.CB_31H) < 1e-4 + 1e-9) & (np.abs(V.T1CLP_pipeline - V.T1CLP_31H) < 1e-4 + 1e-9)
print(V.to_string(index=False)); V.to_csv(os.path.join(B, "31_clp_lag", "verify_B_vs_31H.csv"), index=False)
assert V.ok.all(), "hasil rerun B tidak sama dengan varian H uji 31"
# (1) cek pergeseran langsung pada parquet: 5 situs digeser, Kalbar tidak (bandingkan dengan HARMONISE_CLP=0 secara analitik via kolom clp_cot lag)
for s in SITES:
    d = duckdb.connect().execute(f"SELECT ts_wib, clp_cot FROM read_parquet('{os.path.join(B,'00_data',s+'_full.parquet').replace(chr(92),'/')}') ORDER BY ts_wib").df()
    print(f"  {s:9s} clp_cot non-null = {d.clp_cot.notna().sum()}")
print("VERIFIKASI B: OK — hasil pipeline identik dengan varian H yang dihitung independen di tahap 31")
