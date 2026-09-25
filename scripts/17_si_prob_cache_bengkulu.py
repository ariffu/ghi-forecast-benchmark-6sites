# -*- coding: utf-8 -*-
"""17a — (step mode: python 17_si_prob_cache_bengkulu.py point|0..8|assemble) Re-fit Bengkulu probabilistic layer of 11_probabilistic_mean.py (same params/seed) and cache
test-year predictions for the release SI figure (Fig. S2). Asserts reproduction of probabilistic_6situs_mean.csv.
Portable. Run: python -u 17_si_prob_cache_bengkulu.py  (output: 11_probabilistic_mean/bengkulu_prob_cache.npz)"""
import os, numpy as np, pandas as pd, lightgbm as lgb, duckdb
from scipy.stats import norm
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
BASE = os.path.join(REPO, "results"); DATA = os.path.join(REPO, "data")
TAU = [0.025, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.975]
df = duckdb.connect().execute("SELECT * FROM read_parquet(?)", [os.path.join(DATA, "bengkulu_full.parquet")]).df().sort_values("ts_wib").reset_index(drop=True)
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
G, C = fwd(ghi), fwd(cs)
with np.errstate(all="ignore"):
    df["y_mean"] = np.nanmean(G, axis=1); df["base_mean"] = df["kt"].to_numpy() * np.nanmean(C, axis=1)
df.loc[df["kt"].isna(), "base_mean"] = np.nan
df["valid_mean"] = (~np.isnan(G).any(axis=1)) & (~np.isnan(C).any(axis=1)); yr = df["ts_wib"].dt.year
m = (df.solar_elev_deg > 5) & df.y_mean.notna() & df.base_mean.notna() & df.valid_mean
idx = np.where(m.to_numpy())[0]; itr, iva, ite = idx[yr[idx] <= 2023], idx[yr[idx] == 2024], idx[yr[idx] == 2025]
tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
yt, bt = te.y_mean.to_numpy(), te.base_mean.to_numpy(); ytr = (tr.y_mean - tr.base_mean).to_numpy(); yva = (va.y_mean - va.base_mean).to_numpy()
def lgbm(**kw):
    return lgb.LGBMRegressor(n_estimators=3000, learning_rate=0.03, num_leaves=63, min_child_samples=50, subsample=0.8, subsample_freq=1,
                             colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1, random_state=42, n_jobs=-1, verbose=-1, **kw)
import sys
CACHE=os.path.join(BASE, "11_probabilistic_mean", "_parts"); os.makedirs(CACHE, exist_ok=True)
job=sys.argv[1]
if job=="point":
    mp = lgbm(); mp.fit(tr[feats], ytr, eval_set=[(va[feats], yva)], callbacks=[lgb.early_stopping(100, verbose=False)])
    np.savez(os.path.join(CACHE,"point.npz"), pt=bt + mp.predict(te[feats]), pv=va.base_mean.to_numpy() + mp.predict(va[feats]))
elif job=="assemble":
    P=np.load(os.path.join(CACHE,"point.npz")); pt=P["pt"]; pv=P["pv"]
    rv = va.y_mean.to_numpy() - pv; hv = va.ts_wib.dt.hour.to_numpy()
    sig = {h: (np.std(rv[hv == h]) if (hv == h).sum() > 50 else np.nan) for h in range(24)}; sall = np.nanstd(rv)
    Q=np.column_stack([np.load(os.path.join(CACHE,f"q{i}.npz"))["q"] for i in range(len(TAU))])
    hte = te.ts_wib.dt.hour.to_numpy(); sg = np.array([sig.get(h, np.nan) for h in hte]); sg = np.where(np.isnan(sg), sall, sg)
    q90 = float(np.mean((yt >= Q[:, 1]) & (yt <= Q[:, 7]))); ref = pd.read_csv(os.path.join(BASE, "11_probabilistic_mean", "probabilistic_6situs_mean.csv")).set_index("site").loc["bengkulu", "q_PICP_90"]
    print(f"check q_PICP_90 refit={q90:.3f} csv={ref:.3f}"); assert abs(q90 - ref) < 0.003
    Pq = np.array([np.interp(yt[k], Q[k, :], TAU, left=0.0, right=1.0) for k in range(len(yt))]); Pg = norm.cdf((yt - pt) / sg)
    np.savez(os.path.join(BASE, "11_probabilistic_mean", "bengkulu_prob_cache.npz"), yt=yt, Q=Q, pt=pt, sg=sg, Pq=Pq, Pg=Pg, hr=hte, ts=te.ts_wib.astype("int64").to_numpy())
    print("CACHED")
else:
    i=int(job); mq = lgbm(objective="quantile", alpha=TAU[i]); mq.fit(tr[feats], ytr, eval_set=[(va[feats], yva)], callbacks=[lgb.early_stopping(100, verbose=False)])
    np.savez(os.path.join(CACHE,f"q{i}.npz"), q=bt + mq.predict(te[feats])); print("done", job, mq.best_iteration_)
