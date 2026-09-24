# -*- coding: utf-8 -*-
"""Tahap 1b-m — Walk-forward 5-fold (LightGBM residual, target RATA-RATA jam), Bengkulu."""
import os, sys, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, BASE

df, feats, yr = prepare("bengkulu")
m = (df["solar_elev_deg"] > 5) & df["y_mean"].notna() & df["base_mean"].notna() & df["valid_mean"]
d = df[m].reset_index(drop=True)
d["blk"] = pd.qcut(np.arange(len(d)), 6, labels=False)

folds = []
for k in range(1, 6):
    tr, te = d[d.blk < k], d[d.blk == k]
    model = lgb.LGBMRegressor(n_estimators=3000, learning_rate=0.03, num_leaves=63,
                              min_child_samples=50, subsample=0.8, subsample_freq=1,
                              colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1,
                              random_state=42, n_jobs=-1, verbose=-1)
    model.fit(tr[feats], tr.y_mean - tr.base_mean)
    p = te.base_mean.to_numpy() + model.predict(te[feats])
    folds.append(dict(fold=k, n_train=len(tr), n_test=len(te),
                      R2=round(r2_score(te.y_mean, p), 4),
                      MAE=round(mean_absolute_error(te.y_mean, p), 1),
                      RMSE=round(np.sqrt(mean_squared_error(te.y_mean, p)), 1)))
    print(f"fold {k}: n_train={len(tr)} n_test={len(te)} R2={folds[-1]['R2']}", flush=True)

r = pd.DataFrame(folds)
print(r.to_string(index=False))
print(f"\nWalk-forward R2 (target rata-rata jam) = {r.R2.mean():.4f} +/- {r.R2.std(ddof=1):.4f}")
out = os.path.join(BASE, "01_baseline", "bengkulu_walkforward_mean.csv")
r.to_csv(out, index=False)
print("tersimpan ->", out)
