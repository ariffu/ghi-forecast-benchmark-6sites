# -*- coding: utf-8 -*-
"""Tahap 93: pratinjau CatBoost lima seed di enam stasiun pada Balai_data_v6 (tanpa P5). Pembanding: CatBoost V5 tersimpan (protokol baku).
Bukan angka naskah. Hasil ditulis per run (bisa dilanjutkan)."""
import os, sys, time, warnings, numpy as np, pandas as pd
warnings.simplefilter("ignore")
from sklearn.metrics import r2_score, mean_squared_error
from catboost import CatBoostRegressor
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); sys.path.insert(0, B)
import _common
from _common import split_idx
assert _common.FEATSET in ("P2", "P2F") and _common.CLEARSKY == "IP"
_common.DATA = r"C:\Users\ariff\Documents\Balai_data_v6\00_data"
F = os.path.join(HERE, "pratinjau_catboost_v6.csv"); done = set(map(tuple, pd.read_csv(F)[["site", "seed"]].astype(str).values)) if os.path.exists(F) else set(); t0 = time.time()
for s in _common.SITES:
    df, feats, yr = _common.prepare(s, l_filter=5); tr, va, te = split_idx(df, yr, tgt="mean"); y = df.y_mean.to_numpy(); b_ = df.base_mean.to_numpy(); X = df[feats]; med = X.iloc[tr].median().fillna(0.0)
    for seed in (42, 1, 2, 3, 4):
        if (s, str(seed)) in done: continue
        m = CatBoostRegressor(iterations=2500, learning_rate=0.03, depth=6, loss_function="RMSE", verbose=0, random_seed=seed, thread_count=3, allow_writing_files=False)
        m.fit(X.iloc[tr].fillna(med), y[tr] - b_[tr], eval_set=(X.iloc[va].fillna(med), y[va] - b_[va]), early_stopping_rounds=200, use_best_model=True)
        p = b_[te] + m.predict(X.iloc[te].fillna(med))
        pd.DataFrame([dict(site=s, seed=seed, R2=r2_score(y[te], p), RMSE=float(np.sqrt(mean_squared_error(y[te], p))), n_te=len(te))]).to_csv(F, mode="a", header=not os.path.exists(F), index=False)
        print(f"[{time.time() - t0:5.0f}s] {s} seed {seed} R² {r2_score(y[te], p):.4f} n_te {len(te)}", flush=True)
R = pd.read_csv(F); V = pd.read_csv(r"C:\Users\ariff\Documents\Balai Obsidian\Balai\solardata_new_v2\Manuskrip_versi5\protokol\hasil\pohon\metrik_pohon.csv").query("model == 'CatBoost'")[["site", "seed", "R2"]].rename(columns={"R2": "R2_V5"})
J = R.merge(V, on=["site", "seed"]); J["selisih"] = J.R2 - J.R2_V5
print(J.groupby("site").agg(R2_V5=("R2_V5", "mean"), R2_V6=("R2", "mean"), selisih=("selisih", "mean"), sel_min=("selisih", "min"), sel_max=("selisih", "max")).round(4).to_string())
