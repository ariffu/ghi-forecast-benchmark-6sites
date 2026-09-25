# -*- coding: utf-8 -*-
"""16 — RELEASE figure set (Fig. 3–10 main text), English, no in-image titles, panel letters,
300 dpi, Springer double-column width (174 mm). Output: figures/FigNN.png (+ .pdf, + FigN.eps).

Reason (audit #5, 2026-09-24): several cited figures still carried Indonesian labels/titles
(01_scatter_mean, 03_ablation_delta_mean, 04_arch_bar_mean, 06_*_mean) and raw variable names.
Sources: FINAL CSV/NPZ only (see README_FINAL_ANGKA_MANUSKRIP.md). Fig. 7 re-fits the LightGBM
residual model of 06_strat_mean.py (same seed/params) and asserts it reproduces strat_mean.csv.
Portable: paths resolve to the repository root (results/, figures/, data/). Run: python -u 16_final_figs_release_en.py
"""
import os, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
BASE = os.path.join(REPO, "results"); DATA = os.path.join(REPO, "data"); OUT = os.path.join(REPO, "figures"); os.makedirs(OUT, exist_ok=True)
SUB = OUT; os.makedirs(SUB, exist_ok=True)
plt.rcParams.update({"font.family": "Liberation Sans", "mathtext.fontset": "dejavusans", "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9,
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8, "axes.spines.top": False, "axes.spines.right": False})
W2 = 6.85  # 174 mm
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
LAB = {"banten": "Banten", "bengkulu": "Bengkulu", "jambi": "Jambi", "jogja": "Yogyakarta", "kalbar": "West Kalimantan", "semarang": "Central Java"}
MODELS = ["LightGBM", "CatBoost", "XGBoost", "MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"]
MLAB = {"LSTM_hybrid": "LSTM-hybrid", "Transformer_hybrid": "Transformer-hybrid", "Transf_hybrid": "Transformer-hybrid"}
C_TREE, C_NN, C_SEQ = "#1f5f8b", "#6a8caf", "#b0703c"
def rd(*p): return pd.read_csv(os.path.join(BASE, *p))
def panel(ax, s): ax.text(-0.02, 1.02, s, transform=ax.transAxes, fontweight="bold", fontsize=10, ha="right", va="bottom")
def save(fig, n):
    fig.tight_layout()
    for ext in ("png", "pdf"): fig.savefig(os.path.join(OUT, f"{n}.{ext}"), dpi=600 if ext == "png" else 300)
    k = n.replace("Fig0", "Fig").replace("FigS0", "FigS"); fig.savefig(os.path.join(SUB, f"{k}.eps"), format="eps")
    plt.close(fig); print("  ->", n, flush=True)

# ---------- Bengkulu data (replicates _common.prepare for the local parquet) ----------
import duckdb
df = duckdb.connect().execute("SELECT * FROM read_parquet(?)", [os.path.join(DATA, "bengkulu_full.parquet")]).df()
df = df.sort_values("ts_wib").reset_index(drop=True)
LEADS = [f"ghi_actual_h{i}" for i in range(1, 7)]; SPc = [f"smart_persist_h{i}" for i in range(1, 7)]
DROP = set(["site_id", "ts_wib", "ghi_origin", "has_source_row", "aod_500nm", "angstrom_exp", "smart_persist", "smart_persist_avg"]) | set(LEADS) | set(SPc)
feats = [c for c in df.columns if c not in DROP]
for c in feats:
    if str(df[c].dtype) == "boolean": df[c] = df[c].fillna(False).astype(int)
    df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
ghi = df["ghi_wm2"].to_numpy(float); cs = 1100.0 * np.sin(np.radians(df["solar_elev_deg"].to_numpy(float)))
def fwd(a):
    M = np.full((len(a), 6), np.nan)
    for k in range(1, 7): M[:-k, k - 1] = a[k:]
    return M
G, Cs = fwd(ghi), fwd(cs)
with np.errstate(all="ignore"):
    df["y_mean"] = np.nanmean(G, axis=1); df["base_mean"] = df["kt"].to_numpy() * np.nanmean(Cs, axis=1)
df.loc[df["kt"].isna(), "base_mean"] = np.nan
df["valid_mean"] = (~np.isnan(G).any(axis=1)) & (~np.isnan(Cs).any(axis=1))
yr = df["ts_wib"].dt.year
m = (df["solar_elev_deg"] > 5) & df["y_mean"].notna() & df["base_mean"].notna() & df["valid_mean"]
idx = np.where(m.to_numpy())[0]; itr, iva, ite = idx[yr[idx] <= 2023], idx[yr[idx] == 2024], idx[yr[idx] == 2025]
te = df.iloc[ite]
d = np.load(os.path.join(BASE, "04_arch_mean", "arch_preds_mean.npz"), allow_pickle=True)
assert len(d["y"]) == len(ite) and np.nanmax(np.abs(d["y"] - te["y_mean"].to_numpy())) < 1e-6
yt, pc, sp = te["y_mean"].to_numpy(), d["CatBoost"], te["base_mean"].to_numpy()
def r2(a, b): return 1 - ((a - b) ** 2).sum() / ((a - a.mean()) ** 2).sum()

# ---------- Fig. 3: scatter (density) + three-day series ----------
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(W2, 2.8), gridspec_kw={"width_ratios": [1, 1.9]})
hb = ax.hexbin(yt, pc, gridsize=45, bins="log", cmap="viridis", mincnt=1, extent=(0, 1150, 0, 1150))
ax.plot([0, 1150], [0, 1150], "r--", lw=0.8); ax.set_xlim(0, 1150); ax.set_ylim(0, 1150); ax.set_aspect("equal")
ax.set_xlabel("Observed GHI (W m$^{-2}$)"); ax.set_ylabel("Predicted GHI (W m$^{-2}$)")
ax.text(0.04, 0.96, f"$R^2$ = {r2(yt, pc):.3f}", transform=ax.transAxes, va="top", fontsize=7.5)
cb = fig.colorbar(hb, ax=ax, fraction=0.046, pad=0.03); cb.set_label("count", fontsize=7); cb.ax.tick_params(labelsize=6.5)
panel(ax, "(a)")
ts = te["ts_wib"].reset_index(drop=True)
sel = ((ts >= "2025-06-10") & (ts < "2025-06-13")).to_numpy()
t = ts[sel].reset_index(drop=True); brk = np.r_[False, (t.diff().dt.total_seconds().to_numpy()[1:] > 600)]
def gap(a):
    a = a.astype(float).copy(); out_t, out_a = [], []
    for i in range(len(a)):
        if brk[i]: out_t.append(t[i] - pd.Timedelta(minutes=5)); out_a.append(np.nan)
        out_t.append(t[i]); out_a.append(a[i])
    return out_t, out_a
for arr, lab, kw in ((yt[sel], "Observed", dict(color="k", lw=1.1)), (pc[sel], "CatBoost", dict(color="#d62750", lw=1.0)),
                     (sp[sel], "Smart persistence", dict(color="gray", lw=0.9, ls="--"))):
    tt, aa = gap(arr); ax2.plot(tt, aa, label=lab, **kw)
ax2.set_ylabel("GHI (W m$^{-2}$)"); ax2.legend(loc="upper right", ncol=3, frameon=False, fontsize=7)
import matplotlib.dates as mdates
ax2.xaxis.set_major_locator(mdates.DayLocator()); ax2.xaxis.set_major_formatter(mdates.DateFormatter("\n%d Jun 2025"))
ax2.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18])); ax2.xaxis.set_minor_formatter(mdates.DateFormatter("%H"))
ax2.tick_params(axis="x", which="minor", labelsize=7); ax2.set_ylim(0, 1000); ax2.set_xlabel("Time (WIB)"); panel(ax2, "(b)")
save(fig, "Fig03")

# ---------- Fig. 4: SHAP top-15 + selection curve ----------
NAME = {"kt": "$k_t$", "clp_cot": "COT", "dhi_wm2": "DHI", "kt_cooper": "$k_t$ (Cooper)", "clp_cot_delta_60m": "ΔCOT (60 min)",
        "solar_elev_h2": "Solar elevation (t+2 h)", "decl_noaa_deg": "Solar declination", "clear_sky_ghi_h1": "Clear-sky GHI (t+1 h)",
        "solar_elev_cooper_deg": "Solar elevation (Cooper)", "clear_sky_ghi_h2": "Clear-sky GHI (t+2 h)", "ghi_delta_60m": "ΔGHI (60 min)",
        "aws_wind_speed_ms": "Wind speed (AWS)", "clp_cth_km": "CTH", "solar_elev_deg": "Solar elevation", "dni_wm2": "DNI"}
def tier(f): return "T2 satellite cloud (CLP)" if f.startswith("clp_") else ("T4 surface meteorology (AWS)" if f.startswith("aws_") and f != "aws_ghi_wm2" else "T1 core")
TC = {"T1 core": "#8c8c8c", "T2 satellite cloud (CLP)": "#2e8b57", "T4 surface meteorology (AWS)": "#d98c1f"}
S = rd("02_feature_ranking_mean", "shap_global_mean.csv"); S.columns = ["f", "v"]; S = S.head(15)[::-1]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(W2, 3.2), gridspec_kw={"width_ratios": [1.15, 1]})
a1.barh([NAME.get(f, f) for f in S.f], S.v, color=[TC[tier(f)] for f in S.f])
a1.set_xlabel("mean |SHAP| (W m$^{-2}$)")
from matplotlib.patches import Patch
a1.legend(handles=[Patch(color=v, label=k) for k, v in TC.items()], loc="lower right", frameon=False, fontsize=6.8); panel(a1, "(a)")
SS = rd("02_feature_ranking_mean", "selection_sweep_mean.csv").dropna()
a2.plot(SS.K, SS.val_R2, "o-", ms=3.5, label="validation 2024"); a2.plot(SS.K, SS.test_R2, "s--", ms=3.5, label="test 2025")
a2.set_xlabel("Number of predictors (K)"); a2.set_ylabel("$R^2$"); a2.legend(frameon=False, loc="lower right"); panel(a2, "(b)")
save(fig, "Fig04")

# ---------- Fig. 5: ablation (Bengkulu, bootstrap 95% CI) ----------
AB = rd("03_ablation_mean", "ablation_bootstrap_mean.csv")
lab = ["+CLP\nvs T1", "+AWS\nvs T1+CLP", "+SYNOP cloud\nvs T1+CLP", "T1+CLP\nvs T1+AWS", "FULL\nvs T1+CLP"]
col = ["#2e8b57", "#d98c1f", "#6a5acd", "#2e8b57", "#8c8c8c"]
fig, ax = plt.subplots(figsize=(W2 * 0.8, 2.8)); x = np.arange(len(AB))
ax.bar(x, AB.dR2, color=col, yerr=[AB.dR2 - AB.CI_lo, AB.CI_hi - AB.dR2], capsize=3)
ax.axhline(0, color="k", lw=0.7); ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=7.2); ax.set_ylabel("Δ$R^2$ (test 2025)")
save(fig, "Fig05")

# ---------- Fig. 6: 8-model R2, Bengkulu standalone run ----------
A = rd("04_arch_mean", "arch_mean.csv")
cmap = {"CatBoost": C_TREE, "XGBoost": C_TREE, "LightGBM": C_TREE, "MLP": C_NN}
fig, ax = plt.subplots(figsize=(W2 * 0.75, 2.8))
ax.bar([MLAB.get(mm, mm) for mm in A.model], A.R2, color=[cmap.get(mm, C_SEQ) for mm in A.model])
for i, v in enumerate(A.R2): ax.text(i, v + 0.0003, f"{v:.4f}", ha="center", fontsize=6.8)
ax.set_ylim(0.900, 0.916); ax.set_ylabel("$R^2$ (test 2025)"); plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
ax.legend(handles=[Patch(color=C_TREE, label="tree ensembles"), Patch(color=C_NN, label="MLP"), Patch(color=C_SEQ, label="sequence models")],
          frameon=False, fontsize=7, loc="upper right")
save(fig, "Fig06")

# ---------- Fig. 7: stratification (LightGBM residual re-fit, verified vs strat_mean.csv) ----------
import lightgbm as lgb
tr, va = df.iloc[itr], df.iloc[iva]
mdl = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=63, min_child_samples=50, subsample=0.8, subsample_freq=1,
                        colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1, random_state=42, n_jobs=-1, verbose=-1)
mdl.fit(tr[feats], (tr.y_mean - tr.base_mean).to_numpy(), eval_set=[(va[feats], (va.y_mean - va.base_mean).to_numpy())],
        callbacks=[lgb.early_stopping(80, verbose=False)])
pl = te.base_mean.to_numpy() + mdl.predict(te[feats]); kt = te.kt.to_numpy(); hr = te.ts_wib.dt.hour.to_numpy()
ST = rd("06_strat_mean", "strat_mean.csv").set_index("regime")["R2"]
chk = {"clear": r2(yt[kt > 0.65], pl[kt > 0.65]), "midday(10-14)": r2(yt[(hr >= 10) & (hr < 14)], pl[(hr >= 10) & (hr < 14)])}
for k, v in chk.items(): print(f"  check {k}: refit={v:.4f} csv={ST[k]:.4f}"); assert abs(v - ST[k]) < 2e-3, "refit does not reproduce strat_mean.csv"
fig, (a1, a2) = plt.subplots(1, 2, figsize=(W2, 2.7), gridspec_kw={"width_ratios": [1, 2]})
reg = ["clear", "partly", "overcast"]; a1.bar(["Clear\n($k_t$>0.65)", "Partly cloudy\n(0.30–0.65)", "Overcast\n($k_t$≤0.30)"], [ST[r] for r in reg], color="#2e8b57")
for i, r in enumerate(reg): a1.text(i, ST[r] + 0.01, f"{ST[r]:.3f}", ha="center", fontsize=7)
a1.set_ylim(0, 1); a1.set_ylabel("$R^2$ (test 2025)"); a1.tick_params(axis="x", labelsize=7); panel(a1, "(a)")
hh = [(h, r2(yt[hr == h], pl[hr == h]), (hr == h).sum()) for h in range(6, 19) if (hr == h).sum() >= 50]
H = pd.DataFrame(hh, columns=["hour", "R2", "n"]); H.to_csv(os.path.join(BASE, "06_strat_mean", "r2_by_hour_mean.csv"), index=False)
Hp = H[H.R2 > -1]
a2.bar(Hp.hour, Hp.R2, color=["#b0703c" if 10 <= h < 14 else "#1f5f8b" for h in Hp.hour])
a2.set_ylim(0, 1); a2.set_xlabel("Hour at forecast origin (WIB)"); a2.set_ylabel("$R^2$ (test 2025)"); a2.set_xticks(range(6, 19)); panel(a2, "(b)")
for _, r in H[H.R2 <= -1].iterrows(): a2.text(r.hour, 0.03, f"{r.R2:.0f}\n(n={int(r.n)})", ha="center", fontsize=6.5)
save(fig, "Fig07")

# ---------- Fig. 8: six-site convergence ----------
P = rd("04b_arch_6situs_mean", "arch_6situs_mean_merged.csv").set_index("site").loc[SITES]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(W2, 3.0), gridspec_kw={"width_ratios": [2.2, 1]})
x = np.arange(len(SITES)); w = 0.1; cols = plt.cm.tab10(np.arange(8))
for i, mn in enumerate(MODELS): a1.bar(x + (i - 3.5) * w, P[mn], w, label=MLAB.get(mn, mn), color=cols[i])
a1.set_xticks(x); a1.set_xticklabels([LAB[s] for s in SITES], rotation=30, ha="right"); a1.set_ylim(0.80, 0.96); a1.set_yticks(np.arange(0.80, 0.921, 0.02))
a1.set_ylabel("$R^2$ (test 2025)"); a1.legend(ncol=4, fontsize=6.0, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.0)); panel(a1, "(a)")
spread = P[MODELS].max(axis=1) - P[MODELS].min(axis=1)
yy = np.arange(len(SITES))[::-1]; a2.barh(yy, spread.values, color="teal"); a2.set_yticks(yy); a2.set_yticklabels([LAB[s] for s in SITES])
for i, v in zip(yy, spread.values): a2.text(v + 0.0002, i, f"{v:.4f}", va="center", fontsize=6.5)
a2.set_xlabel("$R^2$ spread (max − min)"); a2.set_xlim(0, 0.016); panel(a2, "(b)")
save(fig, "Fig08")

# ---------- Fig. 9: six-site baseline + ablation ----------
B = rd("04c_mean_6situs", "baseline_mean_6situs.csv").merge(rd("04c_mean_6situs", "baseline_mean_6situs_xgb_mlp.csv")[["site", "XGB_R2", "MLP_R2"]], on="site").set_index("site").loc[SITES]
RA = rd("07_replication", "replication_ablation_mean.csv").set_index("site").loc[SITES]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(W2, 3.0))
for i, (c, l, colr) in enumerate([("SP_R2", "Smart persistence", "#bdbdbd"), ("LGB_R2", "LightGBM", cols[0]), ("CB_R2", "CatBoost", cols[1]), ("XGB_R2", "XGBoost", cols[2]), ("MLP_R2", "MLP", cols[3])]):
    a1.bar(x + (i - 2) * 0.16, B[c], 0.16, label=l, color=colr)
a1.set_xticks(x); a1.set_xticklabels([LAB[s] for s in SITES], rotation=30, ha="right"); a1.set_ylim(0.5, 1.05); a1.set_yticks(np.arange(0.5, 1.01, 0.1)); a1.set_ylabel("$R^2$ (test 2025)")
a1.legend(ncol=3, fontsize=6.3, frameon=False, loc="upper left"); panel(a1, "(a)")
err = np.vstack([RA.dCLP - RA.dCLP_lo, RA.dCLP_hi - RA.dCLP])
a2.bar(x - 0.27, RA.dCLP, 0.27, yerr=err, capsize=2, color="#2e8b57", label="+CLP (95% CI)")
a2.bar(x, RA.dAWS, 0.27, color="#d98c1f", label="+AWS meteo."); a2.bar(x + 0.27, RA.dSYNOP, 0.27, color="#6a5acd", label="+SYNOP cloud")
a2.axhline(0, color="k", lw=0.7); a2.set_xticks(x); a2.set_xticklabels([LAB[s] for s in SITES], rotation=30, ha="right")
a2.set_ylabel("Δ$R^2$ vs T1 core"); a2.legend(fontsize=6.5, frameon=False); panel(a2, "(b)")
save(fig, "Fig09")

# ---------- Fig. 10: CQR PICP before/after ----------
C = rd("12b_conformal_split_mean", "conformal_6situs_split_mean.csv").set_index("site"); nom = [50, 80, 90, 95]
fig, axs = plt.subplots(2, 3, figsize=(W2, 4.3), sharex=True, sharey=True)
for k, (ax, s) in enumerate(zip(axs.ravel(), SITES)):
    r = C.loc[s]
    ax.plot(nom, [r[f"PICP_{c}_before"] * 100 for c in nom], "o-", ms=3, label="quantile (before)")
    ax.plot(nom, [r[f"PICP_{c}_after"] * 100 for c in nom], "s-", ms=3, label="after split-conformal")
    ax.plot([50, 95], [50, 95], "k:", lw=0.8, label="ideal"); ax.set_ylim(35, 100)
    ax.text(0.04, 0.93, f"({'abcdef'[k]}) {LAB[s]}", transform=ax.transAxes, fontsize=8, va="top")
    if k >= 3: ax.set_xlabel("Nominal coverage (%)")
    if k % 3 == 0: ax.set_ylabel("PICP (%)")
axs[0, 0].legend(fontsize=6.5, frameon=False, loc="lower right")
save(fig, "Fig10")

# =================== SUPPLEMENTARY (ESM) FIGURES ===================
# ---------- Fig. S1: protocol sensitivity (a) + per-hour R2 A vs B at Bengkulu (b) ----------
V = rd("09_sensitivity_mean", "sensitivity_variants_mean.csv").set_index("site").loc[SITES]
Hh = rd("09_sensitivity_mean", "hourly_metrics_bengkulu_mean.csv")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(W2, 3.0))
for i, (c, l, colr) in enumerate([("A_r2", "A: origin > 5°", "#b2182b"), ("B_r2", "B: target > 5°", "#2166ac"), ("C_r2", "C: measured only", "#2e8b57")]):
    a1.bar(x + (i - 1) * 0.27, V[c], 0.27, label=l, color=colr)
a1.set_xticks(x); a1.set_xticklabels([LAB[s] for s in SITES], rotation=30, ha="right"); a1.set_ylim(0.75, 0.97); a1.set_yticks(np.arange(0.75, 0.951, 0.05))
a1.set_ylabel("$R^2$ (test 2025)"); a1.legend(ncol=3, fontsize=6.3, frameon=False, loc="upper center"); panel(a1, "(a)")
xx = np.arange(len(Hh)); a2.bar(xx - 0.2, Hh["R2_A"].clip(lower=-1).fillna(0), 0.4, color="#b2182b", label="A: origin > 5°")
a2.bar(xx + 0.2, Hh["R2_B"].clip(lower=-1).fillna(0), 0.4, color="#2166ac", label="B: target > 5°")
for i, v in enumerate(Hh["R2_A"]):
    if pd.notna(v) and v < -1: a2.text(i - 0.2, 0.05, f"{v:.1f}", ha="center", fontsize=6.5, rotation=90)
a2.axhline(0, color="k", lw=0.7); a2.set_xticks(xx); a2.set_xticklabels(Hh["hour"]); a2.set_ylim(-1, 1)
a2.set_xlabel("Hour at forecast origin (WIB)"); a2.set_ylabel("$R^2$"); a2.legend(fontsize=6.5, frameon=False, loc="lower left"); panel(a2, "(b)")
save(fig, "FigS01")

# ---------- Fig. S3: probabilistic diagnostics at Bengkulu ----------
PC = np.load(os.path.join(BASE, "11_probabilistic_mean", "bengkulu_prob_cache.npz")); TAU = [0.025, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.975]
Qm, ytq, hq = PC["Q"], PC["yt"], PC["hr"]; _t = PC["ts"]; tsq = pd.to_datetime(_t, unit=("us" if _t.max() < 1e17 else "ns"))
fig = plt.figure(figsize=(W2, 5.0)); gs = fig.add_gridspec(2, 2, height_ratios=[1, 1])
a1 = fig.add_subplot(gs[0, :]); selq = np.where((tsq >= "2025-06-10") & (tsq < "2025-06-13"))[0]
tq = pd.Series(tsq[selq]); brk2 = np.r_[False, tq.diff().dt.total_seconds().to_numpy()[1:] > 600]
seg = np.split(np.arange(len(selq)), np.where(brk2)[0])
for k, sg_ in enumerate(seg):
    ii = selq[sg_]; tt = tsq[ii]
    a1.fill_between(tt, Qm[ii, 0], Qm[ii, 8], color="#c6dbef", lw=0, label="95%" if k == 0 else None)
    a1.fill_between(tt, Qm[ii, 2], Qm[ii, 6], color="#9ecae1", lw=0, label="80%" if k == 0 else None)
    a1.fill_between(tt, Qm[ii, 3], Qm[ii, 5], color="#6baed6", lw=0, label="50%" if k == 0 else None)
    a1.plot(tt, Qm[ii, 4], color="#08306b", lw=0.9, label="median" if k == 0 else None)
    a1.plot(tt, ytq[ii], "k.", ms=2.2, label="observed" if k == 0 else None)
a1.xaxis.set_major_locator(mdates.DayLocator()); a1.xaxis.set_major_formatter(mdates.DateFormatter("\n%d Jun 2025"))
a1.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18])); a1.xaxis.set_minor_formatter(mdates.DateFormatter("%H"))
a1.tick_params(axis="x", which="minor", labelsize=7); a1.set_ylabel("GHI (W m$^{-2}$)"); a1.set_ylim(0, 1050)
a1.legend(ncol=5, fontsize=6.5, frameon=False, loc="upper center"); panel(a1, "(a)")
a2 = fig.add_subplot(gs[1, 0]); HB = rd("11_probabilistic_mean", "picp_by_hour_bengkulu_mean.csv")
a2.bar(HB["hour"], HB["PICP90"], color="#2b8cbe"); a2.axhline(0.9, color="#b2182b", ls="--", lw=0.9, label="nominal 90%")
a2.set_ylim(0.5, 1.0); a2.set_xlabel("Hour at forecast origin (WIB)"); a2.set_ylabel("PICP90 (before calibration)"); a2.legend(fontsize=6.5, frameon=False, loc="lower right"); panel(a2, "(b)")
a3 = fig.add_subplot(gs[1, 1])
a3.hist(PC["Pq"], bins=20, range=(0, 1), density=True, histtype="step", lw=1.3, color="#2b8cbe", label="quantile model")
a3.hist(PC["Pg"], bins=20, range=(0, 1), density=True, histtype="step", lw=1.3, color="#d98c1f", label="per-hour Gaussian")
a3.axhline(1, color="k", ls=":", lw=0.9, label="uniform"); a3.set_xlabel("PIT"); a3.set_ylabel("Density"); a3.legend(fontsize=6.5, frameon=False); panel(a3, "(c)")
save(fig, "FigS03")

# ---------- Fig. S4: target effect ----------
pt3 = rd("04b_arch_6situs", "arch_6situs_R2_matrix.csv").set_index("site").loc[SITES, "CatBoost"].to_numpy(float)
mn3 = rd("04b_arch_6situs_mean", "arch_6situs_mean_merged.csv").set_index("site").loc[SITES, "CatBoost"].to_numpy(float)
fig, ax = plt.subplots(figsize=(W2 * 0.8, 2.9))
ax.bar(x - 0.19, pt3, 0.38, label="point, t + 1 h", color="#6a8caf"); ax.bar(x + 0.19, mn3, 0.38, label="hourly mean", color="#2e8b57")
for i, (a, c) in enumerate(zip(pt3, mn3)): ax.text(i, c + 0.012, f"+{c - a:.3f}", ha="center", fontsize=6.8)
ax.set_xticks(x); ax.set_xticklabels([LAB[s] for s in SITES], rotation=30, ha="right"); ax.set_ylim(0, 1.15); ax.set_yticks(np.arange(0, 1.01, 0.2)); ax.set_ylabel("$R^2$ (test 2025)")
ax.legend(fontsize=7, frameon=False, loc="upper center", ncol=2); save(fig, "FigS04")

# ---------- Fig. S2: skill vs references ----------
RS = rd("13_reference_skill_6situs", "reference_skill_6situs.csv").set_index("site").loc[SITES]
fig, ax = plt.subplots(figsize=(W2 * 0.8, 2.9))
ax.bar(x - 0.19, RS["skill_pers"], 0.38, label="vs smart persistence", color="#6a8caf"); ax.bar(x + 0.19, RS["skill_cp"], 0.38, label="vs climatology–persistence optimum", color="#2e8b57")
for i, v in enumerate(RS["skill_cp"]): ax.text(i + 0.19, v + 0.006, f"{v:.3f}", ha="center", fontsize=6.8)
ax.set_xticks(x); ax.set_xticklabels([LAB[s] for s in SITES], rotation=30, ha="right"); ax.set_ylim(0, 0.45); ax.set_ylabel("RMSE skill score")
ax.legend(fontsize=7, frameon=False, loc="upper left"); save(fig, "FigS02")
print("SI DONE")

print("DONE")
