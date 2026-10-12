# -*- coding: utf-8 -*-
"""Tahap 4c — Baseline target RATA-RATA jam (headline) untuk 6 situs.
Melatih CatBoost direct (dan LightGBM) pada target rata-rata jam y_mean,
menghitung metrik R2/MAE/RMSE/skill vs smart-persistence, menyimpan prediksi,
dan membuat scatter 6-panel target rata-rata.
Diproses per-situs untuk menghemat RAM (free RAM kecil).
"""
import os, sys, gc, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, BASE, PLOTS, SITES

OUT = os.path.join(BASE, "04c_mean_6situs"); os.makedirs(OUT, exist_ok=True)
os.makedirs(PLOTS, exist_ok=True)

def log(*a): print(*a, flush=True)

def met(y, p, base):
    rsp = np.sqrt(mean_squared_error(y, base))
    return dict(R2=round(r2_score(y, p), 4),
                MAE=round(mean_absolute_error(y, p), 1),
                RMSE=round(np.sqrt(mean_squared_error(y, p)), 1),
                skill=round(1 - np.sqrt(mean_squared_error(y, p)) / rsp, 4),
                RMSE_SP=round(rsp, 1))

rows = []
pred_store = {}

for site in SITES:
    log(f"\n===== {site} =====")
    df, feats, yr = prepare(site, l_filter=5)
    tr, va, te = split_idx(df, yr, tgt="mean")
    log(f"  n_train={len(tr)} n_val={len(va)} n_test={len(te)}")
    y = df["y_mean"].to_numpy(); b = df["base_mean"].to_numpy()
    X = df[feats]
    ytr, btr = y[tr], b[tr]
    yte, bte = y[te], b[te]
    Xtr, Xte = X.iloc[tr], X.iloc[te]
    med = Xtr.median().fillna(0.0)

    # CatBoost direct (headline)
    cb = CatBoostRegressor(iterations=2500, learning_rate=0.03, depth=6,
                           loss_function="RMSE", verbose=0, random_seed=42)
    cb.fit(Xtr.fillna(med), ytr, eval_set=(X.iloc[va].fillna(med), y[va]),
           early_stopping_rounds=200, use_best_model=True)
    p_cb = cb.predict(Xte.fillna(med))
    m_cb = met(yte, p_cb, bte)

    # LightGBM residual (target rata-rata) sebagai pembanding
    lgb = LGBMRegressor(n_estimators=2500, learning_rate=0.03, num_leaves=63,
                        verbose=-1, random_state=42)
    lgb.fit(Xtr.fillna(med), ytr - btr, eval_set=[(X.iloc[va].fillna(med), y[va] - b[va])],
            callbacks=[__import__("lightgbm").early_stopping(200, verbose=False)])
    p_lgb = lgb.predict(Xte.fillna(med)) + bte
    m_lgb = met(yte, p_lgb, bte)

    rows.append(dict(site=site, n_test=len(te),
                     SP_R2=round(r2_score(yte, bte), 4),
                     **{f"CB_{k}": v for k, v in m_cb.items()},
                     **{f"LGB_{k}": v for k, v in m_lgb.items()}))
    pred_store[site] = (yte, p_cb, bte)
    log(f"  CatBoost: R2={m_cb['R2']} MAE={m_cb['MAE']} RMSE={m_cb['RMSE']} skill={m_cb['skill']}")
    log(f"  LightGBM: R2={m_lgb['R2']} MAE={m_lgb['MAE']} RMSE={m_lgb['RMSE']} skill={m_lgb['skill']}")
    # hemat memori: simpan prediksi, lepas dataframe
    del df, X, Xtr, Xte; gc.collect()

res = pd.DataFrame(rows)
res.to_csv(os.path.join(OUT, "baseline_mean_6situs.csv"), index=False)
log("\n===== RESULT =====")
log(res.round(4).to_string())

# ---- Scatter 6-panel target rata-rata (CatBoost) ----
fig, axes = plt.subplots(2, 3, figsize=(13, 8.5))
titles = {"banten": "Banten", "bengkulu": "Bengkulu", "jambi": "Jambi",
          "jogja": "Yogyakarta", "kalbar": "Kalbar", "semarang": "Semarang"}
r2map = dict(zip(res.site, res.CB_R2))
for ax, site in zip(axes.flat, SITES):
    yte, p_cb, _ = pred_store[site]
    ax.scatter(yte, p_cb, s=4, alpha=0.22, color="steelblue")
    lim = [0, max(yte.max(), p_cb.max()) * 1.02]
    ax.plot(lim, lim, "r--", lw=1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("Observed GHI (W/m2)")
    ax.set_ylabel("Predicted GHI (W/m2)")
    ax.set_title(f"{titles[site]}  (R2={r2map[site]:.3f})")
fig.suptitle("Hour-mean target (h+1) — CatBoost, test 2025, 6 sites", fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.97])
p = os.path.join(PLOTS, "01_scatter_mean_6situs.png")
fig.savefig(p, dpi=140); plt.close(fig)
log(f"\nplot -> {p}")
log("SELESAI")
