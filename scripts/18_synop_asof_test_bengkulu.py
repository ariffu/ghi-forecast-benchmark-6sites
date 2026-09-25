# -*- coding: utf-8 -*-
"""18 — SYNOP temporal-alignment check (Bengkulu, hourly-mean target).
Finding: SYNOP is hourly and sits only on the :00 slot of the 10-min grid (NaN at :10-:50), so only ~16% of
daytime forecast origins see a SYNOP report. This test compares the original alignment with an 'as-of'
alignment (latest report at or before the origin, max age 50 min = ffill limit 5 slots; no look-ahead).
Model/params identical to 03_ablation_mean.py. Usage: python 18_synop_asof_test_bengkulu.py <config>|summary"""
import os, sys, numpy as np, pandas as pd, duckdb, lightgbm as lgb
from sklearn.metrics import r2_score
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
BASE = os.path.join(REPO, "results"); DATA = os.path.join(REPO, "data"); OUT = os.environ.get("SYN_OUT", os.path.join(BASE, "18_synop_asof")); os.makedirs(OUT, exist_ok=True)
df = duckdb.connect().execute("SELECT * FROM read_parquet(?)", [os.path.join(DATA, "bengkulu_full.parquet")]).df().sort_values("ts_wib").reset_index(drop=True)
LEADS = [f"ghi_actual_h{i}" for i in range(1, 7)]; SPc = [f"smart_persist_h{i}" for i in range(1, 7)]
DROP = set(["site_id", "ts_wib", "ghi_origin", "has_source_row", "aod_500nm", "angstrom_exp", "smart_persist", "smart_persist_avg"]) | set(LEADS) | set(SPc)
feats = [c for c in df.columns if c not in DROP]
X = {}
for c in feats:
    s = df[c]
    if str(s.dtype) == "boolean": s = s.fillna(False).astype(int)
    X[c] = pd.to_numeric(s, errors="coerce").astype("float64")
X = pd.DataFrame(X)
SYN = [c for c in feats if c.startswith("synop_")]
for c in SYN: X[c + "_asof"] = X[c].ffill(limit=5)
ghi = X["ghi_wm2"].to_numpy(); cs = 1100.0 * np.sin(np.radians(X["solar_elev_deg"].to_numpy()))
def fwd(a):
    M = np.full((len(a), 6), np.nan)
    for k in range(1, 7): M[:-k, k - 1] = a[k:]
    return M
G, C = fwd(ghi), fwd(cs)
with np.errstate(all="ignore"): y = np.nanmean(G, 1); b = X["kt"].to_numpy() * np.nanmean(C, 1)
b[np.isnan(X["kt"].to_numpy())] = np.nan
valid = (~np.isnan(G).any(1)) & (~np.isnan(C).any(1)); yr = df.ts_wib.dt.year.to_numpy()
m = (X.solar_elev_deg.to_numpy() > 5) & ~np.isnan(y) & ~np.isnan(b) & valid
idx = np.where(m)[0]; itr, iva, ite = idx[yr[idx] <= 2023], idx[yr[idx] == 2024], idx[yr[idx] == 2025]
def g(f):
    if f.startswith("clp_"): return "D"
    if f.startswith("synop_"): return "E"
    if f.startswith("aws_"): return "F"
    return "T1"
T5 = [f for f in feats if f.startswith("accel_") or "_std_" in f]
T1 = [f for f in feats if g(f) == "T1" and f not in T5]; CLP = [f for f in feats if g(f) == "D"]
SC = ["synop_cloud_cover_oktas", "synop_cl", "synop_cm", "synop_ch"]
CFG = {"T1": T1, "T1+CLP": T1 + CLP,
       "T1+SYNcloud_orig": T1 + SC, "T1+SYNcloud_asof": T1 + [c + "_asof" for c in SC],
       "T1+SYNall_orig": T1 + SYN, "T1+SYNall_asof": T1 + [c + "_asof" for c in SYN],
       "T1+CLP+SYNcloud_orig": T1 + CLP + SC, "T1+CLP+SYNcloud_asof": T1 + CLP + [c + "_asof" for c in SC],
       "T1+CLP+SYNall_asof": T1 + CLP + [c + "_asof" for c in SYN]}
job = sys.argv[1]
if job != "summary":
    fs = CFG[job]
    mm = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=63, min_child_samples=50, subsample=0.8, subsample_freq=1,
                           colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1, random_state=42, n_jobs=-1, verbose=-1)
    mm.fit(X.iloc[itr][fs], y[itr] - b[itr], eval_set=[(X.iloc[iva][fs], y[iva] - b[iva])], callbacks=[lgb.early_stopping(80, verbose=False)])
    p = b[ite] + mm.predict(X.iloc[ite][fs]); np.save(os.path.join(OUT, job + ".npy"), p)
    print(job, len(fs), round(r2_score(y[ite], p), 4))
else:
    yt = y[ite]; P = {k: np.load(os.path.join(OUT, k + ".npy")) for k in CFG if os.path.exists(os.path.join(OUT, k + ".npy"))}
    rng = np.random.default_rng(0); n = len(yt); B = 2000
    def r2(a, q): return 1 - ((a - q) ** 2).sum() / ((a - a.mean()) ** 2).sum()
    def boot(k1, k0):
        d = []
        for _ in range(B):
            i = rng.integers(0, n, n); d.append(r2(yt[i], P[k1][i]) - r2(yt[i], P[k0][i]))
        d = np.array(d); return round(r2(yt, P[k1]) - r2(yt, P[k0]), 4), round(np.percentile(d, 2.5), 4), round(np.percentile(d, 97.5), 4)
    rows = [(k, round(r2(yt, v), 4)) for k, v in P.items()]
    print(pd.DataFrame(rows, columns=["config", "test_R2"]).to_string(index=False))
    pairs = [("T1+SYNcloud_orig", "T1"), ("T1+SYNcloud_asof", "T1"), ("T1+SYNall_orig", "T1"), ("T1+SYNall_asof", "T1"),
             ("T1+CLP+SYNcloud_orig", "T1+CLP"), ("T1+CLP+SYNcloud_asof", "T1+CLP"), ("T1+CLP+SYNall_asof", "T1+CLP"), ("T1+CLP", "T1")]
    out = [(a, b_) + boot(a, b_) for a, b_ in pairs if a in P and b_ in P]
    R = pd.DataFrame(out, columns=["config", "vs", "dR2", "CI_lo", "CI_hi"]); print(R.to_string(index=False))
    R.to_csv(os.path.join(OUT, "synop_asof_bengkulu.csv"), index=False)
    d = (X.solar_elev_deg.to_numpy() > 5)
    print("daytime rows with SYNOP: orig", round(np.mean(~np.isnan(X.synop_temp_c.to_numpy()[d])), 3), " asof", round(np.mean(~np.isnan(X.synop_temp_c_asof.to_numpy()[d])), 3))
