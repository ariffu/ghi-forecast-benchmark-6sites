# -*- coding: utf-8 -*-
"""#2 extended to six sites — skill vs a climatology-persistence-optimal reference.

Reference = convex combination of (hourly) climatology and smart-persistence,
weight tuned on 2024 validation per site (Yang et al. 2020). Model = CatBoost
direct (hourly-mean), whose RMSE per site is taken from the verified
04c_mean_6situs/baseline_mean_6situs.csv.

Run: python -u 13b_reference_skill_6situs.py
"""
import os, sys, numpy as np, pandas as pd
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, savefig
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
LABEL = {"banten": "Banten", "bengkulu": "Bengkulu", "jambi": "Jambi",
         "jogja": "Yogyakarta", "kalbar": "Kalbar", "semarang": "Semarang"}
OUT = os.path.join(BASE, "13_reference_skill_6situs"); os.makedirs(OUT, exist_ok=True)
CB = pd.read_csv(os.path.join(BASE, "04c_mean_6situs", "baseline_mean_6situs.csv")).set_index("site")


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


rows = []
for s in SITES:
    df, feats, yr = prepare(s)
    itr, iva, ite = split_idx(df, yr, "mean")
    tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
    cmap = tr.assign(h=tr["ts_wib"].dt.hour).groupby("h")["y_mean"].mean()
    def clim(f):
        return f["ts_wib"].dt.hour.map(cmap).to_numpy(float)
    y_va, p_va, c_va = va["y_mean"].to_numpy(float), va["base_mean"].to_numpy(float), clim(va)
    fill = np.nanmean(c_va); c_va = np.where(np.isnan(c_va), fill, c_va)
    best_a, best_r = None, np.inf
    for a in np.linspace(0, 1, 101):
        r = rmse(a * c_va + (1 - a) * p_va, y_va)
        if r < best_r:
            best_a, best_r = a, r
    y_te, p_te, c_te = te["y_mean"].to_numpy(float), te["base_mean"].to_numpy(float), clim(te)
    c_te = np.where(np.isnan(c_te), fill, c_te)
    ref_te = best_a * c_te + (1 - best_a) * p_te
    r_clim, r_pers, r_ref = rmse(c_te, y_te), rmse(p_te, y_te), rmse(ref_te, y_te)
    r_mod = float(CB.loc[s, "CB_RMSE"])
    rows.append(dict(site=s, alpha=round(best_a, 2), RMSE_clim=round(r_clim, 1), RMSE_pers=round(r_pers, 1),
                     RMSE_ref=round(r_ref, 1), RMSE_model=round(r_mod, 1),
                     skill_pers=round(1 - r_mod / r_pers, 3), skill_cp=round(1 - r_mod / r_ref, 3)))
    print(f"{s:9s} a*={best_a:.2f} RMSE clim/pers/ref/model = {r_clim:6.1f}/{r_pers:6.1f}/{r_ref:6.1f}/{r_mod:6.1f}  "
          f"skill_sp={1-r_mod/r_pers:.3f} skill_cp={1-r_mod/r_ref:.3f}", flush=True)

R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "reference_skill_6situs.csv"), index=False)
print("\n" + R.to_string(index=False))

x = np.arange(len(R)); w = 0.38
fig, ax = plt.subplots(figsize=(8, 3.8))
ax.bar(x - w / 2, R["skill_pers"], w, label="vs smart-persistence", color="cornflowerblue")
ax.bar(x + w / 2, R["skill_cp"], w, label="vs climatology–persistence-optimal", color="seagreen")
for i, v in enumerate(R["skill_cp"]):
    ax.text(i + w / 2, v + 0.005, f"{v:.3f}", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels([LABEL[s] for s in R["site"]], rotation=15)
ax.set_ylabel("RMSE skill score"); ax.set_ylim(0, 0.45)
ax.set_title("Skill vs references (hourly-mean, CatBoost direct, test 2025)"); ax.legend(fontsize=8)
savefig(fig, "13b_reference_skill_6situs.png")
print("SELESAI")
