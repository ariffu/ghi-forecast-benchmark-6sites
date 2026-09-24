# -*- coding: utf-8 -*-
"""Yang-2020-style reference skill (mean target, Bengkulu).

Reference = convex combination of climatology and persistence, weight tuned on
2024 validation (Yang et al. 2020 recommend RMSE skill score against this
climatology-persistence-optimal reference as the cross-scenario measure).
Uses the parquet + saved mean predictions; no re-fitting of the DL/tree models.
Run: python -u 13_reference_skill.py
"""
import os, sys, numpy as np, pandas as pd
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx

df, feats, yr = prepare()
itr, iva, ite = split_idx(df, yr, "mean")
tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]

# climatology = mean y_mean by ORIGIN hour, computed on TRAIN only
clim_map = tr.assign(h=tr["ts_wib"].dt.hour).groupby("h")["y_mean"].mean()

def clim(frame):
    return frame["ts_wib"].dt.hour.map(clim_map).to_numpy(float)

def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))

y_va, p_va, c_va = va["y_mean"].to_numpy(float), va["base_mean"].to_numpy(float), clim(va)
y_te, p_te, c_te = te["y_mean"].to_numpy(float), te["base_mean"].to_numpy(float), clim(te)

best_a, best_r = None, np.inf
for a in np.linspace(0, 1, 101):
    r = rmse(a * c_va + (1 - a) * p_va, y_va)
    if r < best_r:
        best_a, best_r = a, r
ref_te = best_a * c_te + (1 - best_a) * p_te

d = np.load(os.path.join(BASE, "04_arch_mean", "arch_preds_mean.npz"), allow_pickle=True)
pred, y_npz = d["CatBoost"], d["y"]
assert len(pred) == len(y_te), (len(pred), len(y_te))
assert np.nanmax(np.abs(y_npz - y_te)) < 1e-6, "row misalignment"

r_clim, r_pers, r_ref, r_mod = rmse(c_te, y_te), rmse(p_te, y_te), rmse(ref_te, y_te), rmse(pred, y_te)
print(f"n_test={len(y_te)}  alpha*={best_a:.2f}")
print(f"RMSE climatology          = {r_clim:7.2f} W/m2")
print(f"RMSE persistence (smart)  = {r_pers:7.2f} W/m2")
print(f"RMSE reference (CP-opt)   = {r_ref:7.2f} W/m2")
print(f"RMSE model (CatBoost mean)= {r_mod:7.2f} W/m2")
print(f"skill vs smart-persistence = {1 - r_mod / r_pers:.4f}")
print(f"skill vs CP-optimal        = {1 - r_mod / r_ref:.4f}")
