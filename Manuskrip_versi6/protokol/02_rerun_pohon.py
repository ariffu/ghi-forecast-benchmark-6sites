# Manuskrip V6: salinan dari "rerun protokol baku/02_rerun_pohon.py" (sha256 d8392f6d58276a82…); hanya folder keluaran dan pemeriksaan lingkungan yang ditambah.
# -*- coding: utf-8 -*-
"""Rerun 02 — ketiga model pohon dengan FORMULASI TARGET SERAGAM (residual) pada run enam stasiun, 5 seed (2026-10-18).

Status: DATA DUKUNG untuk pembimbing. TIDAK dipakai mengubah naskah, ESM atau LAPORAN sebelum ada arahan.
Pada Tabel 3, LightGBM memakai residual, sedangkan CatBoost dan XGBoost langsung ke ȳ. Di sini ketiganya memakai residual
Δ = ȳ − ŷ_SP (prakiraan ŷ = ŷ_SP + Δ̂), sama dengan kelima jaringan saraf pada rerun 01. Hiperparameter identik run enam stasiun
(Tabel S3; paper_v2_clpbanten/04c_mean_6situs.py, 04c_mean_6situs_xgb_mlp.py): input 43 prediktor diisi median latih.
  LightGBM: 2500 pohon, lr 0,03, 63 daun, bawaan lain, early stopping 200   (tanpa subsampel → hasil sama untuk semua seed)
  XGBoost : 2500 pohon, lr 0,03, kedalaman 6, bawaan lain, early stopping 200 (tanpa subsampel → hasil sama untuk semua seed)
  CatBoost: 2500 iterasi, lr 0,03, kedalaman 6, RMSE, early stopping 200, use_best_model (MVS 0,8 → bergantung seed)
Seed 42, 1, 2, 3, 4. Keluaran: hasil/pohon/metrik_pohon.csv, hasil/pohon/pred_<situs>_<model>_s<seed>.npy.
Jalankan: python -u 02_rerun_pohon.py --threads 2
"""
import os, sys, time, argparse, numpy as np, pandas as pd
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))   # Manuskrip V6: dua tingkat di atas protokol/
PAPER = os.path.join(ROOT, "paper_v2_clpbanten"); sys.path.insert(0, PAPER)
import os as _os
_V = r"C:\Users\ariff\Documents\Balai_data_v6_10"
assert _os.environ.get("FEATSET") == "P2F", "Manuskrip V6: FEATSET harus P2F"
assert _os.path.normcase(_os.environ.get("DATA_DIR", "")) == _os.path.normcase(_os.path.join(_V, "00_data")), "DATA_DIR harus Balai_data_v6_10/00_data"
assert _os.path.normcase(_os.environ.get("CLEARSKY_DIR", "")) == _os.path.normcase(_os.path.join(_V, "clearsky")), "CLEARSKY_DIR harus Balai_data_v6_10/clearsky"
assert _os.path.normcase(_os.environ.get("CLP_EKSTRA_DIR", "")) == _os.path.normcase(_os.path.join(_V, "clp_ekstra")), "CLP_EKSTRA_DIR harus Balai_data_v6_10/clp_ekstra"
from _common import prepare, split_idx, SITES
import _common as _c; assert len(_c.P2_AKTIF) == 44
OUT = os.path.join(HERE, "hasil", "pohon"); os.makedirs(OUT, exist_ok=True)   # Manuskrip V6: HERE = Manuskrip_versi6/protokol
ap = argparse.ArgumentParser(); ap.add_argument("--situs", nargs="+", default=SITES); ap.add_argument("--seed", nargs="+", type=int, default=[42, 1, 2, 3, 4])
ap.add_argument("--threads", type=int, default=2); A = ap.parse_args(); t0 = time.time()
def log(*a): print(*a, flush=True)
import lightgbm as lgbm, xgboost as xgb
from catboost import CatBoostRegressor
fm = os.path.join(OUT, "metrik_pohon.csv"); done = set()
if os.path.exists(fm): M0 = pd.read_csv(fm); done = set(zip(M0.site, M0.model, M0.seed))
for site in A.situs:
    todo = [(s, m) for s in A.seed for m in ("LightGBM", "XGBoost", "CatBoost") if (site, m, s) not in done]
    if not todo: log(f"{site}: semua sudah selesai"); continue
    df, feats, yr = prepare(site, l_filter=5); tr, va, te = split_idx(df, yr, tgt="mean")
    y = df["y_mean"].to_numpy(); b = df["base_mean"].to_numpy(); X = df[feats]
    med = X.iloc[tr].median().fillna(0.0); Xtr, Xva, Xte = X.iloc[tr].fillna(med), X.iloc[va].fillna(med), X.iloc[te].fillna(med)
    rtr, rva = y[tr] - b[tr], y[va] - b[va]; yt, bt = y[te], b[te]; rsp = np.sqrt(mean_squared_error(yt, bt))
    log(f"\n===== {site} ({time.time() - t0:.0f}s)")
    for seed, nama in todo:
        t1 = time.time()
        if nama == "LightGBM":
            m = lgbm.LGBMRegressor(n_estimators=2500, learning_rate=0.03, num_leaves=63, verbose=-1, random_state=seed, n_jobs=A.threads)
            m.fit(Xtr, rtr, eval_set=[(Xva, rva)], callbacks=[lgbm.early_stopping(200, verbose=False)]); n_it = int(m.best_iteration_)
        elif nama == "XGBoost":
            m = xgb.XGBRegressor(n_estimators=2500, learning_rate=0.03, max_depth=6, early_stopping_rounds=200, eval_metric="rmse",
                                 random_state=seed, verbosity=0, n_jobs=A.threads)
            m.fit(Xtr, rtr, eval_set=[(Xva, rva)], verbose=False); n_it = int(m.best_iteration) + 1
        else:
            m = CatBoostRegressor(iterations=2500, learning_rate=0.03, depth=6, loss_function="RMSE", verbose=0, random_seed=seed,
                                  thread_count=A.threads, allow_writing_files=False)
            m.fit(Xtr, rtr, eval_set=(Xva, rva), early_stopping_rounds=200, use_best_model=True); n_it = int(m.tree_count_)
        p = bt + m.predict(Xte); np.save(os.path.join(OUT, f"pred_{site}_{nama}_s{seed}.npy"), p.astype(np.float32))
        row = dict(site=site, model=nama, seed=seed, target="residual", R2=r2_score(yt, p), RMSE=np.sqrt(mean_squared_error(yt, p)),
                   MAE=mean_absolute_error(yt, p), bias=float(np.mean(p - yt)), skill=1 - np.sqrt(mean_squared_error(yt, p)) / rsp,
                   n_pohon=n_it, detik=round(time.time() - t1, 1))
        pd.DataFrame([row]).to_csv(fm, mode="a", header=not os.path.exists(fm), index=False)
        log(f"  {site:9s} {nama:9s} seed {seed:2d}  R² {row['R2']:.4f}  pohon {n_it}  ({row['detik']:.0f}s)")
log(f"SELESAI {time.time() - t0:.0f}s")
