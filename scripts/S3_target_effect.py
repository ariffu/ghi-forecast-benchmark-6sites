# -*- coding: utf-8 -*-
"""Fig. S3 — target effect: point vs hourly-mean R² per site (CatBoost direct).

Reads saved CSVs only (no re-fitting). Writes plots/S3_target_effect_6situs.png
Run: python -u S3_target_effect.py
"""
import os, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
PLOTS = os.path.join(BASE, "plots")

SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
LABELS = ["Banten", "Bengkulu", "Jambi", "Yogyakarta", "Kalbar", "Semarang"]

point = pd.read_csv(os.path.join(BASE, "04b_arch_6situs", "arch_6situs_R2_matrix.csv")).set_index("site")
mean = pd.read_csv(os.path.join(BASE, "04b_arch_6situs_mean", "arch_6situs_mean_merged.csv")).set_index("site")

p = point.loc[SITES, "CatBoost"].to_numpy(float)
m = mean.loc[SITES, "CatBoost"].to_numpy(float)

x = np.arange(len(SITES)); w = 0.38
fig, ax = plt.subplots(figsize=(8, 3.8))
ax.bar(x - w / 2, p, w, label="point t+1 h (companion)", color="cornflowerblue")
ax.bar(x + w / 2, m, w, label="hourly mean (headline)", color="seagreen")
for i, (pi, mi) in enumerate(zip(p, m)):
    ax.text(i, max(pi, mi) + 0.012, f"+{mi - pi:.2f}", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(LABELS, rotation=15)
ax.set_ylabel("$R^2$ (test 2025)"); ax.set_ylim(0, 1.0)
ax.set_title("Target effect: point vs hourly-mean $R^2$ (CatBoost direct)")
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(PLOTS, "S3_target_effect_6situs.png"), dpi=140)
plt.close(fig)
print("plot -> S3_target_effect_6situs.png")
print("point:", np.round(p, 4).tolist())
print("mean :", np.round(m, 4).tolist())
print("delta:", np.round(m - p, 4).tolist())
