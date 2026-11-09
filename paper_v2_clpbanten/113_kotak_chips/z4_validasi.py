# -*- coding: utf-8 -*-
"""Tahap 113 Z4: validasi Balai_kotak_v6_10 (hanya membaca).
V1 jejak beku (SHA256, hanya-baca); V2 kausal: lag puncak korelasi |r(k_c(t), f(t+k))|, k = -3..+3, sama dengan clp_cot (sumber dan waktu sama);
V3 fisis: min <= clp_cot <= max, std >= 0, std = 0 bila satu piksel; V4 siklus harian median per jam WIB (siang);
V5 banding data kotak lama (28_clp_spatial/data): korelasi per fitur pada slot yang sama-sama terisi."""
import os, json, hashlib, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE)
V = r"C:\Users\ariff\Documents\Balai_data_v6_10"; K = r"C:\Users\ariff\Documents\Balai_kotak_v6_10"
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
F = ["clps_cot_std", "clps_cot_min", "clps_cot_max", "clps_cth_std", "clps_cloud_frac", "clps_cloud_frac_lag_60m", "clps_cot_std_lag_60m"]
O = {"V1": {}, "V2": [], "V3": [], "V4": [], "V5": []}
sha = dict(l.split("  ")[::-1] for l in open(os.path.join(K, "SHA256.txt")).read().split("\n") if l.strip())
O["V1"] = dict(berkas=len(os.listdir(K)), sha_cocok=all(hashlib.sha256(open(os.path.join(K, n), "rb").read()).hexdigest() == h for n, h in sha.items()), hanya_baca=all(not os.access(os.path.join(K, n), os.W_OK) for n in os.listdir(K)))
for s in S:
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "kt", "clp_cot", "solar_elev_deg"]); k = pd.read_parquet(os.path.join(K, f"{s}_clp_kotak.parquet"))
    assert (d.ts_wib.to_numpy() == k.ts_wib.to_numpy()).all()
    siang = d.solar_elev_deg.to_numpy() > 10; kc = pd.Series(np.where(siang, pd.to_numeric(d.kt).to_numpy(float), np.nan))
    for c in ["clp_cot"] + F:
        x = pd.Series(d[c].to_numpy(float) if c == "clp_cot" else k[c].to_numpy(float))
        r = {kk: kc.corr(x.shift(-kk)) for kk in range(-3, 4)}; kmax = max(r, key=lambda q: abs(r[q]) if np.isfinite(r[q]) else -1)
        O["V2"].append(dict(stasiun=s, fitur=c, lag_puncak_slot=kmax, r_puncak=round(r[kmax], 3), r_k0=round(r[0], 3)))
    cot = d.clp_cot.to_numpy(float); m = np.isfinite(cot)
    O["V3"].append(dict(stasiun=s, min_le_cot=bool((k.clps_cot_min.to_numpy()[m] <= cot[m] + 1e-6).all()), cot_le_max=bool((cot[m] <= k.clps_cot_max.to_numpy()[m] + 1e-6).all()),
                        std_negatif=int((k.clps_cot_std < 0).sum()), std_kosong_saat_awan=int((m & k.clps_cot_std.isna().to_numpy()).sum()), cth_std_maks=round(float(k.clps_cth_std.max()), 2),
                        lag_benar=bool(np.allclose(k.clps_cot_std_lag_60m, k.clps_cot_std.shift(6), equal_nan=True) and np.allclose(k.clps_cloud_frac_lag_60m, k.clps_cloud_frac.shift(6), equal_nan=True))))
    h = d.ts_wib.dt.hour; g = k.assign(h=h)[siang].groupby("h")[["clps_cot_std", "clps_cth_std", "clps_cloud_frac"]].median().round(2)
    for hh, row in g.iterrows(): O["V4"].append(dict(stasiun=s, jam=hh, **row.to_dict()))
    p = os.path.join(B, "28_clp_spatial", "data", f"{s}_clp_spatial.parquet")
    if os.path.exists(p):
        o = pd.read_parquet(p); assert (o.ts_wib.to_numpy() == k.ts_wib.to_numpy()).all()
        for c in F:
            a, b = k[c].to_numpy(float), o[c].to_numpy(float); mm = np.isfinite(a) & np.isfinite(b)
            O["V5"].append(dict(stasiun=s, fitur=c, n_bersama=int(mm.sum()), r=round(float(np.corrcoef(a[mm], b[mm])[0, 1]), 4) if mm.sum() > 100 else np.nan, sama_pct=round(100 * float(np.isclose(a[mm], b[mm], atol=1e-4).mean()), 2) if mm.any() else np.nan))
    print(s, "selesai", flush=True)
print("== V1", O["V1"])
for key in ("V2", "V3", "V4", "V5"):
    T = pd.DataFrame(O[key]); T.to_csv(os.path.join(HERE, f"z4_{key}.csv"), index=False)
    if key == "V2": T = T.pivot(index="fitur", columns="stasiun", values="lag_puncak_slot")
    if key == "V4": T = T.pivot(index="jam", columns="stasiun", values="clps_cth_std")
    if key == "V5": T = T.pivot(index="fitur", columns="stasiun", values="r")
    print("==", key); print(T.to_string())
json.dump(O["V1"], open(os.path.join(HERE, "z4_V1.json"), "w"))
