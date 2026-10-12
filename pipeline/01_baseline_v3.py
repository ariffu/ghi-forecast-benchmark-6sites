# -*- coding: utf-8 -*-
"""Tahap 1 v3 (KOREKSI + visualisasi) — baseline Bengkulu target t+1h & rata-rata jam.
Jalankan: python -u 01_baseline_v3.py
"""
import os, sys, numpy as np, pandas as pd, lightgbm as lgb
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, savefig, fig_scatter, BASE
import matplotlib.pyplot as plt

def log(*a): print(*a, flush=True)
df, feats, yr = prepare()
OUT = os.path.join(BASE, "01_baseline"); os.makedirs(OUT, exist_ok=True)
results = []; store = {}

for tgt in ["point", "mean"]:
    yc, bc = f"y_{tgt}", f"base_{tgt}"
    itr, iva, ite = split_idx(df, yr, tgt)
    tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
    yt, bt = te[yc].to_numpy(), te[bc].to_numpy()
    r_sp = np.sqrt(mean_squared_error(yt, bt))
    results.append(dict(model="smart-persistence", target=tgt, R2=round(r2_score(yt, bt),4),
                        MAE=round(mean_absolute_error(yt,bt),1), RMSE=round(r_sp,1), skill=0.0))
    m1 = lgb.LGBMRegressor(n_estimators=3000, learning_rate=0.03, num_leaves=63, min_child_samples=50,
                           subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_alpha=0.1,
                           reg_lambda=0.1, random_state=42, n_jobs=-1, verbose=-1)
    m1.fit(tr[feats], (tr[yc]-tr[bc]).to_numpy(), eval_set=[(va[feats],(va[yc]-va[bc]).to_numpy())],
           callbacks=[lgb.early_stopping(100, verbose=False)])
    p1 = bt + m1.predict(te[feats])
    results.append(dict(model="LightGBM residual", target=tgt, R2=round(r2_score(yt,p1),4),
                        MAE=round(mean_absolute_error(yt,p1),1),
                        RMSE=round(np.sqrt(mean_squared_error(yt,p1)),1),
                        skill=round(1-np.sqrt(mean_squared_error(yt,p1))/r_sp,4)))
    m2 = CatBoostRegressor(iterations=3000, learning_rate=0.03, depth=6, l2_leaf_reg=3.0, random_seed=42,
                           od_type="Iter", od_wait=100, verbose=False)
    m2.fit(tr[feats], tr[yc].to_numpy(), eval_set=(va[feats], va[yc].to_numpy()), use_best_model=True)
    p2 = m2.predict(te[feats])
    results.append(dict(model="CatBoost direct", target=tgt, R2=round(r2_score(yt,p2),4),
                        MAE=round(mean_absolute_error(yt,p2),1),
                        RMSE=round(np.sqrt(mean_squared_error(yt,p2)),1),
                        skill=round(1-np.sqrt(mean_squared_error(yt,p2))/r_sp,4)))
    store[tgt] = dict(te=te, yt=yt, bt=bt, p1=p1, p2=p2, ev=m1.evals_result_ if hasattr(m1,"evals_result_") else None)
    log(f"[{tgt}] n_test={len(te)} LGBM R2={results[-2]['R2']} | CB R2={results[-1]['R2']}")

R = pd.DataFrame(results)[["model","target","R2","MAE","RMSE","skill"]]
print("\n==== BASELINE v3 (target benar) ===="); print(R.to_string(index=False))
R.to_csv(os.path.join(OUT, "baseline_v3.csv"), index=False)
pd.DataFrame({"ts": store["point"]["te"]["ts_wib"].to_numpy(),
              "y": store["point"]["yt"], "base": store["point"]["bt"],
              "lgbm": store["point"]["p1"], "catboost": store["point"]["p2"],
              "hour": store["point"]["te"]["ts_wib"].dt.hour.to_numpy()}).to_csv(os.path.join(OUT,"pred_point.csv"), index=False)

# ---- PLOT 1: scatter titik & rata-rata ----
savefig(fig_scatter(store["point"]["yt"], store["point"]["p2"],
        f"Titik t+1h — CatBoost direct (R²={R['R2'][2]:.3f})"), "01_scatter_point.png")
savefig(fig_scatter(store["mean"]["yt"], store["mean"]["p2"],
        f"Rata-rata jam — CatBoost direct (R²={R['R2'][5]:.3f})"), "01_scatter_mean.png")

# ---- PLOT 2: time series 3 hari (titik) ----
s = store["point"]; t = s["te"]; m = (t["ts_wib"] >= "2025-06-10") & (t["ts_wib"] <= "2025-06-12 23:59")
fig, ax = plt.subplots(figsize=(11, 3.6))
ax.plot(t["ts_wib"][m], s["yt"][m], "-", color="black", lw=1.1, label="Observasi")
ax.plot(t["ts_wib"][m], s["p2"][m], "-", color="crimson", lw=1.0, alpha=0.85, label="CatBoost")
ax.plot(t["ts_wib"][m], s["bt"][m], "--", color="gray", lw=0.9, alpha=0.8, label="smart-persistence")
ax.set_ylabel("GHI (W/m²)"); ax.set_title("Uji 2025 — prediksi titik t+1h (contoh 3 hari)"); ax.legend(fontsize=8)
savefig(fig, "01_timeseries_point.png")

# ---- PLOT 3: histogram residual ----
fig, ax = plt.subplots(figsize=(5.2, 3.4))
ax.hist(s["yt"]-s["p2"], bins=60, color="teal", alpha=0.8)
ax.axvline(0, color="k", lw=0.8); ax.set_xlabel("Residual (Obs − Pred), W/m²"); ax.set_ylabel("Frekuensi")
ax.set_title("Distribusi residual — titik t+1h")
savefig(fig, "01_residual_hist.png")

# ---- PLOT 4: R² per jam ----
rows = []
for hh in range(6, 19):
    mm = s["te"]["ts_wib"].dt.hour.to_numpy() == hh
    if mm.sum() > 30: rows.append((hh, r2_score(s["yt"][mm], s["p2"][mm]), mm.sum()))
H = pd.DataFrame(rows, columns=["hour","R2","n"])
fig, ax = plt.subplots(figsize=(6.5, 3.2))
ax.bar(H["hour"], H["R2"], color="cornflowerblue")
ax.set_xlabel("Jam (WIB)"); ax.set_ylabel("R²"); ax.set_ylim(0, 1)
ax.set_title("R² per jam lokasi — titik t+1h (CatBoost)")
savefig(fig, "01_r2_by_hour.png")
H.to_csv(os.path.join(OUT, "r2_by_hour_point.csv"), index=False)

# ---- PLOT 5: learning curve LightGBM (val MSE per iterasi) ----
ev = store["point"]["ev"]
if ev and "valid_0" in ev:
    v = ev["valid_0"]["l2"]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.plot(range(1, len(v)+1), v, color="darkgreen")
    ax.set_xlabel("Iterasi boosting"); ax.set_ylabel("MSE validasi"); ax.set_title("Kurva belajar LightGBM (titik t+1h)")
    savefig(fig, "01_learning_lgbm.png")
log("SELESAI Tahap 1 v3.")