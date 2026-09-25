# -*- coding: utf-8 -*-
"""18b — SYNOP temporal-alignment check at all six sites (hourly-mean target).
Same design as 18_synop_asof_test_bengkulu.py (original :00-only alignment vs 'as-of' alignment,
latest report carried forward max 50 min = ffill limit 5 slots; no look-ahead), same LightGBM params as
03_ablation_mean.py / 07b_replication_ablation_mean.py. Data: std.model_base_10min_full (solar_new.duckdb),
Bengkulu from data/bengkulu_full.parquet (as in _common.prepare).
Usage: python 18b_synop_asof_6situs.py run <site> [max_seconds]   (resumable; skips configs already saved)
       python 18b_synop_asof_6situs.py summary"""
import os, sys, time, numpy as np, pandas as pd, duckdb
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
BASE = os.path.join(REPO, "results"); DATA = os.path.join(REPO, "data")
OUT = os.path.join(BASE, "18_synop_asof", "6situs"); os.makedirs(OUT, exist_ok=True)
DB = os.environ.get("GHI_DB", "")  # path to solar_new.duckdb (read-only std.* layer)
PARQ = os.path.join(DATA, "bengkulu_full.parquet")
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
LEADS = [f"ghi_actual_h{i}" for i in range(1, 7)]; SPc = [f"smart_persist_h{i}" for i in range(1, 7)]
DROP = set(["site_id", "ts_wib", "ghi_origin", "has_source_row", "aod_500nm", "angstrom_exp", "smart_persist", "smart_persist_avg"]) | set(LEADS) | set(SPc)
SC = ["synop_cloud_cover_oktas", "synop_cl", "synop_cm", "synop_ch"]

def load(site):
    if site == "bengkulu" and os.path.exists(PARQ):
        df = duckdb.connect().execute("SELECT * FROM read_parquet(?)", [PARQ]).df()
    else:
        if not DB: raise SystemExit("Set env var GHI_DB to the path of solar_new.duckdb (read-only std.* layer).")
        df = duckdb.connect(DB, read_only=True).execute("SELECT * FROM std.model_base_10min_full WHERE site_id = ?", [site]).df()
    df = df.sort_values("ts_wib").reset_index(drop=True)
    feats = [c for c in df.columns if c not in DROP]
    X = {}
    for c in feats:
        s = df[c]
        if str(s.dtype) == "boolean": s = s.fillna(False).astype(int)
        X[c] = pd.to_numeric(s, errors="coerce").astype("float64")
    X = pd.DataFrame(X)
    SYN = [c for c in feats if c.startswith("synop_")]
    for c in SYN: X[c + "_asof"] = X[c].ffill(limit=5)
    ghi = X["ghi_wm2"].to_numpy(float); cs = 1100.0 * np.sin(np.radians(X["solar_elev_deg"].to_numpy(float)))
    def fwd(a):
        M = np.full((len(a), 6), np.nan)
        for k in range(1, 7): M[:-k, k - 1] = a[k:]
        return M
    G, C = fwd(ghi), fwd(cs)
    with np.errstate(all="ignore"): y = np.nanmean(G, 1); b = X["kt"].to_numpy(float) * np.nanmean(C, 1)
    b[np.isnan(X["kt"].to_numpy(float))] = np.nan
    valid = (~np.isnan(G).any(1)) & (~np.isnan(C).any(1)); yr = df.ts_wib.dt.year.to_numpy()
    m = (X.solar_elev_deg.to_numpy() > 5) & ~np.isnan(y) & ~np.isnan(b) & valid
    idx = np.where(m)[0]
    return X, feats, SYN, y, b, idx[yr[idx] <= 2023], idx[yr[idx] == 2024], idx[yr[idx] == 2025]

def configs(feats, SYN):
    def g(f):
        if f.startswith("clp_"): return "D"
        if f.startswith("synop_"): return "E"
        if f.startswith("aws_"): return "F"
        return "T1"
    T5 = [f for f in feats if f.startswith("accel_") or "_std_" in f]
    T1 = [f for f in feats if g(f) == "T1" and f not in T5]; CLP = [f for f in feats if g(f) == "D"]
    sc = [c for c in SC if c in feats]
    return {"T1": T1, "T1+CLP": T1 + CLP,
            "T1+SYNcloud_orig": T1 + sc, "T1+SYNcloud_asof": T1 + [c + "_asof" for c in sc],
            "T1+SYNall_orig": T1 + SYN, "T1+SYNall_asof": T1 + [c + "_asof" for c in SYN],
            "T1+CLP+SYNcloud_orig": T1 + CLP + sc, "T1+CLP+SYNcloud_asof": T1 + CLP + [c + "_asof" for c in sc],
            "T1+CLP+SYNall_orig": T1 + CLP + SYN, "T1+CLP+SYNall_asof": T1 + CLP + [c + "_asof" for c in SYN]}

def r2(a, q): return 1 - ((a - q) ** 2).sum() / ((a - a.mean()) ** 2).sum()

if sys.argv[1] == "run":
    import lightgbm as lgb
    site = sys.argv[2]; tmax = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9; t0 = time.time()
    X, feats, SYN, y, b, itr, iva, ite = load(site); CFG = configs(feats, SYN)
    od = os.path.join(OUT, site); os.makedirs(od, exist_ok=True); np.save(os.path.join(od, "y_test.npy"), y[ite])
    d = X.solar_elev_deg.to_numpy() > 5
    with open(os.path.join(od, "availability.txt"), "w") as f:
        f.write(f"{np.mean(~np.isnan(X.synop_temp_c.to_numpy()[d])):.4f} {np.mean(~np.isnan(X.synop_temp_c_asof.to_numpy()[d])):.4f}\n")
    for k, fs in CFG.items():
        fp = os.path.join(od, k + ".npy")
        if os.path.exists(fp) and not os.environ.get("FORCE"): continue
        if time.time() - t0 > tmax: print("time budget reached"); break
        mm = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=63, min_child_samples=50, subsample=0.8, subsample_freq=1,
                               colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1, random_state=42, n_jobs=-1, verbose=-1)
        mm.fit(X.iloc[itr][fs], y[itr] - b[itr], eval_set=[(X.iloc[iva][fs], y[iva] - b[iva])], callbacks=[lgb.early_stopping(80, verbose=False)])
        p = b[ite] + mm.predict(X.iloc[ite][fs]); np.save(fp, p)
        print(site, k, len(fs), round(r2(y[ite], p), 4), f"{time.time()-t0:.0f}s", flush=True)
else:
    pairs = [("T1+SYNcloud_orig", "T1"), ("T1+SYNcloud_asof", "T1"), ("T1+SYNall_orig", "T1"), ("T1+SYNall_asof", "T1"),
             ("T1+CLP+SYNcloud_orig", "T1+CLP"), ("T1+CLP+SYNcloud_asof", "T1+CLP"),
             ("T1+CLP+SYNall_orig", "T1+CLP"), ("T1+CLP+SYNall_asof", "T1+CLP"), ("T1+CLP", "T1")]
    rows = []
    for site in SITES:
        od = os.path.join(OUT, site)
        if not os.path.exists(os.path.join(od, "y_test.npy")): continue
        yt = np.load(os.path.join(od, "y_test.npy")); n = len(yt)
        av = open(os.path.join(od, "availability.txt")).read().split()
        bi = np.random.default_rng(0).integers(0, n, size=(2000, n))
        def br(p):
            e = (yt[bi] - p[bi]) ** 2; mu = yt[bi].mean(1); return 1 - e.mean(1) / ((yt[bi] - mu[:, None]) ** 2).mean(1)
        for a, c in pairs:
            fa, fc = os.path.join(od, a + ".npy"), os.path.join(od, c + ".npy")
            if not (os.path.exists(fa) and os.path.exists(fc)): continue
            pa, pc = np.load(fa), np.load(fc); dd = br(pa) - br(pc)
            rows.append(dict(site=site, config=a, vs=c, dR2=round(r2(yt, pa) - r2(yt, pc), 4),
                             CI_lo=round(np.percentile(dd, 2.5), 4), CI_hi=round(np.percentile(dd, 97.5), 4),
                             avail_orig=float(av[0]), avail_asof=float(av[1])))
    R = pd.DataFrame(rows); print(R.to_string(index=False)); R.to_csv(os.path.join(OUT, "synop_asof_6situs.csv"), index=False)
