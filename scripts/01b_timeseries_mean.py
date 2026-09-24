# -*- coding: utf-8 -*-
"""Regenerate 01_timeseries_mean.png (Bengkulu, hourly-mean headline target).

Reuses saved mean-target test predictions (04_arch_mean/arch_preds_mean.npz)
-- NO model re-fitting -- and writes the same 3-day example as the point
version so the manuscript's Fig. 2 (b) panel matches the headline target.

Run: python -u 01b_timeseries_mean.py
"""
import os, sys, numpy as np
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, savefig
import matplotlib.pyplot as plt


def log(*a):
    print(*a, flush=True)


df, feats, yr = prepare()
_, _, ite = split_idx(df, yr, "mean")
te = df.iloc[ite]

d = np.load(os.path.join(BASE, "04_arch_mean", "arch_preds_mean.npz"), allow_pickle=True)
y, b, pc = d["y"], d["b"], d["CatBoost"]        # obs, smart-persistence, CatBoost (mean)

assert len(te) == len(y), (len(te), len(y))
diff = np.nanmax(np.abs(te["y_mean"].to_numpy(float) - y))
log(f"n_test={len(te)}  max|te.y_mean - npz.y|={diff:.3e}")
assert diff < 1e-6, "prediction/row misalignment"

ts = te["ts_wib"].to_numpy()
m = (ts >= np.datetime64("2025-06-10")) & (ts <= np.datetime64("2025-06-12T23:59:59"))
log(f"window rows = {int(m.sum())}")

fig, ax = plt.subplots(figsize=(11, 3.6))
ax.plot(ts[m], y[m],  "-",  color="black",  lw=1.1, label="Observation")
ax.plot(ts[m], pc[m], "-",  color="crimson", lw=1.0, alpha=0.85, label="CatBoost")
ax.plot(ts[m], b[m],  "--", color="gray",   lw=0.9, alpha=0.8, label="smart-persistence")
ax.set_ylabel("GHI (W/m$^2$)")
ax.set_title("Test 2025 — hourly-mean forecast (3-day example)")
ax.legend(fontsize=8)
savefig(fig, "01_timeseries_mean.png")
log("SELESAI — 01_timeseries_mean.png")
