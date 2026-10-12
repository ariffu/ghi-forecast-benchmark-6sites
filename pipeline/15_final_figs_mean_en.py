# -*- coding: utf-8 -*-
"""15 — FINAL manuscript figures (hourly-mean headline), regenerated from the FINAL CSVs.

Why: (1) Fig. 5b previously used 08_replication_baseline.png, which is the POINT-target
replication (07_replication.py); (2) Fig. S1 used 09_variants_6situs.png and
09_hourly_r2_senja.png from 08_sensitivity.py, also POINT target, while Table S2 is mean;
(3) six-site figures carried the tick labels "kalbar"/"jogja". This script redraws them
from the verified mean CSVs with the manuscript site names. No model is re-fitted
(Fig. S1b re-uses the saved CatBoost mean predictions of 04_arch_mean).
Portable: BASE = folder of this script. Run: python -u 15_final_figs_mean_en.py
"""
import os, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
PLOTS = os.path.join(BASE, "plots")
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
LAB = {"banten": "Banten", "bengkulu": "Bengkulu", "jambi": "Jambi", "jogja": "Yogyakarta",
       "kalbar": "West Kalimantan", "semarang": "Central Java"}
MODELS = ["LightGBM", "CatBoost", "XGBoost", "MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"]
MLAB = {"LSTM_hybrid": "LSTM-hybrid", "Transformer_hybrid": "Transformer-hybrid"}

def rd(*p): return pd.read_csv(os.path.join(BASE, *p))
def savefig(fig, name):
    fig.tight_layout(); fig.savefig(os.path.join(PLOTS, name), dpi=140); plt.close(fig); print("  plot ->", name, flush=True)
def labs(sites): return [LAB[s] for s in sites]

# ---- Fig. 5b: six-site baseline R2, hourly-mean (SP + 4 flat models) ----
B = rd("04c_mean_6situs", "baseline_mean_6situs.csv").merge(
    rd("04c_mean_6situs", "baseline_mean_6situs_xgb_mlp.csv")[["site", "XGB_R2", "MLP_R2"]], on="site")
B = B.set_index("site").loc[SITES]
cols = [("SP_R2", "Smart persistence", "lightgray"), ("LGB_R2", "LightGBM", None), ("CB_R2", "CatBoost", None),
        ("XGB_R2", "XGBoost", None), ("MLP_R2", "MLP", None)]
x = np.arange(len(SITES)); w = 0.16
fig, ax = plt.subplots(figsize=(9, 4))
for i, (c, l, col) in enumerate(cols):
    ax.bar(x + (i - 2) * w, B[c], w, label=l, color=col)
ax.set_xticks(x); ax.set_xticklabels(labs(SITES), rotation=15); ax.set_ylim(0.5, 1.0)
ax.set_ylabel("$R^2$ (test 2025)"); ax.set_title("Six-site replication — baseline, hourly-mean target"); ax.legend(fontsize=8, ncol=5, loc="upper center")
savefig(fig, "08_replication_baseline_mean.png")

# ---- Fig. 5c: incremental dR2 per site (mean) with CLP 95% CI ----
RA = rd("07_replication", "replication_ablation_mean.csv").set_index("site").loc[SITES]
_bb = rd("27_block_bootstrap", "replication_ablation_block.csv"); _bb = _bb[_bb.effect == "dCLP"].set_index("site").loc[SITES]
RA["dCLP_lo"], RA["dCLP_hi"] = _bb.blk_lo.values, _bb.blk_hi.values                                   # CI blok harian (tahap 27)
fig, ax = plt.subplots(figsize=(8, 3.8)); x = np.arange(len(RA))
err = np.vstack([RA["dCLP"] - RA["dCLP_lo"], RA["dCLP_hi"] - RA["dCLP"]])
ax.bar(x - 0.27, RA["dCLP"], 0.27, yerr=err, capsize=3, label="Δ$R^2$ +CLP (95% CI)", color="seagreen")
ax.bar(x, RA["dAWS"], 0.27, label="Δ$R^2$ +AWS", color="gray")
ax.bar(x + 0.27, RA["dSYNOP"], 0.27, label="Δ$R^2$ +SYNOP cloud", color="goldenrod")
ax.axhline(0, color="k", lw=0.8); ax.set_xticks(x); ax.set_xticklabels(labs(RA.index), rotation=15)
ax.set_ylabel("Δ$R^2$ vs T1 core"); ax.set_title("Incremental contribution per site — hourly-mean target"); ax.legend(fontsize=8)
savefig(fig, "08_replication_ablation_mean.png")

# ---- Fig. 6b/6c: 8-model R2 and spread per site (mean) ----
P = rd("04b_arch_6situs_mean", "arch_6situs_mean_merged.csv").set_index("site").loc[SITES, MODELS]
x = np.arange(len(P)); w = 0.1
fig, ax = plt.subplots(figsize=(12, 4.6))
for i, mn in enumerate(MODELS):
    ax.bar(x + i * w, P[mn], w, label=MLAB.get(mn, mn))
ax.set_xticks(x + (len(MODELS) - 1) * w / 2); ax.set_xticklabels(labs(P.index), rotation=15); ax.set_ylim(min(0.8, P.values.min() - 0.02), P.values.max() + 0.015)
ax.set_ylabel("$R^2$ (test 2025)"); ax.set_title("Architecture — six sites, hourly-mean target (8 models)"); ax.legend(fontsize=7, ncol=4)
savefig(fig, "04b_arch_6situs_bar_mean.png")
spread = P.max(axis=1) - P.min(axis=1)
fig, ax = plt.subplots(figsize=(7, 3.6)); ax.bar(labs(P.index), spread.values, color="teal")
for i, v in enumerate(spread.values): ax.text(i, v + 0.0003, f"{v:.4f}", ha="center", fontsize=8)
ax.set_ylabel("$R^2$ max − min (8 models)"); ax.set_title("Architecture spread per site — hourly-mean target")
ax.set_ylim(0, spread.values.max() * 1.25); plt.setp(ax.get_xticklabels(), rotation=15)
savefig(fig, "04b_arch_spread_6situs_mean.png")

# ---- Fig. 8: PICP before/after split-conformal (mean) ----
C = rd("12b_conformal_split_mean", "conformal_6situs_split_mean.csv").set_index("site")
fig, axs = plt.subplots(2, 3, figsize=(12, 6.4)); nom = [50, 80, 90, 95]
for ax, s in zip(axs.ravel(), SITES):
    r = C.loc[s]
    ax.plot(nom, [r[f"PICP_{c}_before"] * 100 for c in nom], "o-", label="before")
    ax.plot(nom, [r[f"PICP_{c}_after"] * 100 for c in nom], "s-", label="conformal (split)")
    ax.plot([50, 95], [50, 95], "k:", lw=1)
    ax.set_title(LAB[s], fontsize=9); ax.set_xlabel("nominal (%)"); ax.set_ylabel("PICP (%)"); ax.set_ylim(40, 100); ax.legend(fontsize=7)
savefig(fig, "12b_picp_conformal_6situs_split_mean.png")

# ---- Fig. S1a: protocol sensitivity A/B/C (mean) ----
V = rd("09_sensitivity_mean", "sensitivity_variants_mean.csv").set_index("site").loc[SITES]
fig, ax = plt.subplots(figsize=(9, 3.8)); x = np.arange(len(V)); w = 0.27
ax.bar(x - w, V["A_r2"], w, label="A: origin > 5°", color="indianred")
ax.bar(x, V["B_r2"], w, label="B: target > 5°", color="cornflowerblue")
ax.bar(x + w, V["C_r2"], w, label="C: measured-only", color="seagreen")
ax.set_xticks(x); ax.set_xticklabels(labs(V.index), rotation=15); ax.set_ylim(min(0.75, V[['A_r2','B_r2','C_r2']].values.min() - 0.03), 0.95); ax.set_ylabel("$R^2$ (test 2025)")
ax.set_title("Sensitivity of the evaluation protocol — six sites, hourly-mean target"); ax.legend(fontsize=8, ncol=3)
savefig(fig, "09_variants_6situs_mean.png")

# ---- Fig. S1b: per-hour R2 at Bengkulu (mean), protocol A vs B ----
import duckdb
df = duckdb.connect().execute("SELECT * FROM read_parquet(?)", [os.path.join(BASE, "00_data", "bengkulu_full.parquet")]).df()
df = df.sort_values("ts_wib").reset_index(drop=True)
import sys; sys.path.insert(0, BASE); import _common                     # definisi langit cerah aktif (CLEARSKY)
for _c in ["kt", "ghi_wm2"]: df[_c] = pd.to_numeric(df[_c], errors="coerce").astype("float64")
df = _common.apply_clearsky(df, "bengkulu")
ghi = df["ghi_wm2"].to_numpy(float); cs = _common.cs_for_baseline(df)
def fwd(a):
    M = np.full((len(a), 6), np.nan)
    for k in range(1, 7): M[:-k, k - 1] = a[k:]
    return M
G, Cs = fwd(ghi), fwd(cs)
y = np.nanmean(G, axis=1); b = df["kt"].to_numpy(float) * np.nanmean(Cs, axis=1)
valid = (~np.isnan(G).any(axis=1)) & (~np.isnan(Cs).any(axis=1))
mA = (df["solar_elev_deg"].to_numpy() > 5) & ~np.isnan(y) & ~np.isnan(b) & valid
ite = np.where(mA & (df["ts_wib"].dt.year.to_numpy() == 2025))[0]
d = np.load(os.path.join(BASE, "04_arch_mean", "arch_preds_mean.npz"), allow_pickle=True)
assert len(d["y"]) == len(ite) and np.nanmax(np.abs(d["y"] - y[ite])) < 1e-6, "row misalignment"
p = d["CatBoost"]; yt = y[ite]; hr = df["ts_wib"].dt.hour.to_numpy()[ite]; inB = df["solar_elev_h1"].to_numpy()[ite] > 5
def met(a, q):
    return 1 - ((a - q) ** 2).sum() / ((a - a.mean()) ** 2).sum(), np.abs(a - q).mean(), np.sqrt(((a - q) ** 2).mean())
rec = []
for h in range(6, 19):
    r = dict(hour=h)
    for tag, m in (("A", hr == h), ("B", (hr == h) & inB)):
        r[f"n_{tag}"] = int(m.sum())
        if m.sum() >= 30: r[f"R2_{tag}"], r[f"MAE_{tag}"], r[f"RMSE_{tag}"] = [round(v, 4 if i == 0 else 1) for i, v in enumerate(met(yt[m], p[m]))]
    rec.append(r)
H = pd.DataFrame(rec); H.to_csv(os.path.join(BASE, "09_sensitivity_mean", "hourly_metrics_bengkulu_mean.csv"), index=False)
print(H.to_string(index=False))
fig, ax = plt.subplots(figsize=(8, 3.8)); x = np.arange(len(H)); w = 0.4
ax.bar(x - w / 2, H["R2_A"].fillna(0), w, label="A: origin > 5°", color="indianred")
ax.bar(x + w / 2, H.get("R2_B", pd.Series(np.nan, index=H.index)).fillna(0), w, label="B: target > 5°", color="cornflowerblue")
ax.axhline(0, color="k", lw=0.8); ax.set_xticks(x); ax.set_xticklabels(H["hour"]); ax.set_ylim(-1, 1)
for i, v in enumerate(H["R2_A"]):
    if pd.notna(v) and v < -1: ax.text(i - w / 2, -0.95, f"{v:.1f}\n(clipped)", ha="center", va="bottom", fontsize=7)
ax.set_xlabel("Hour at origin (WIB)"); ax.set_ylabel("$R^2$")
ax.set_title("Per-hour $R^2$ at Bengkulu — hourly-mean target (CatBoost)"); ax.legend(fontsize=8)
savefig(fig, "09_hourly_r2_senja_mean.png")

# ---- Fig. S3: target effect ----
pt = rd("04b_arch_6situs", "arch_6situs_R2_matrix.csv").set_index("site").loc[SITES, "CatBoost"].to_numpy(float)
mn = rd("04b_arch_6situs_mean", "arch_6situs_mean_merged.csv").set_index("site").loc[SITES, "CatBoost"].to_numpy(float)
x = np.arange(len(SITES)); w = 0.38
fig, ax = plt.subplots(figsize=(8, 3.8))
ax.bar(x - w / 2, pt, w, label="point t+1 h (companion)", color="cornflowerblue")
ax.bar(x + w / 2, mn, w, label="hourly mean (headline)", color="seagreen")
for i, (a, c) in enumerate(zip(pt, mn)): ax.text(i, max(a, c) + 0.012, f"+{c - a:.3f}", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(labs(SITES), rotation=15); ax.set_ylabel("$R^2$ (test 2025)"); ax.set_ylim(0, 1.0)
ax.set_title("Target effect: point vs hourly-mean $R^2$ (CatBoost direct)"); ax.legend(fontsize=8)
savefig(fig, "S3_target_effect_6situs.png")

# ---- Fig. S4: skill vs references ----
R = rd("13_reference_skill_6situs", "reference_skill_6situs.csv").set_index("site").loc[SITES]
x = np.arange(len(R)); w = 0.38
fig, ax = plt.subplots(figsize=(8, 3.8))
ax.bar(x - w / 2, R["skill_pers"], w, label="vs smart-persistence", color="cornflowerblue")
ax.bar(x + w / 2, R["skill_cp"], w, label="vs climatology–persistence-optimal", color="seagreen")
for i, v in enumerate(R["skill_cp"]): ax.text(i + w / 2, v + 0.005, f"{v:.3f}", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(labs(R.index), rotation=15); ax.set_ylabel("RMSE skill score"); ax.set_ylim(0, 0.45)
ax.set_title("Skill vs references (hourly-mean, CatBoost direct, test 2025)"); ax.legend(fontsize=8)
savefig(fig, "13b_reference_skill_6situs.png")
print("DONE")
