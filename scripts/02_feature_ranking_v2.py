# -*- coding: utf-8 -*-
"""Tahap 2 v2 (KOREKSI + visualisasi) — ranking fitur Bengkulu, target titik t+1h (h1)."""
import os, sys, time, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.metrics import r2_score
from sklearn.feature_selection import mutual_info_regression
from sklearn.inspection import permutation_importance
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, savefig, BASE
import matplotlib.pyplot as plt

def log(*a): print(*a, flush=True)
t0 = time.time()
OUT = os.path.join(BASE, "02_feature_ranking_v2"); os.makedirs(OUT, exist_ok=True)
df, feats, yr = prepare()
itr, iva, ite = split_idx(df, yr, "point")
tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
ytr_r = (tr.y_point - tr.base_point).to_numpy()
log(f"[1] target=titik t+1h(h1) train={len(tr)} val={len(va)} test={len(te)} fitur={len(feats)}")

log("[2] R-1 korelasi + MI ...")
pear = tr[feats].corrwith(pd.Series(ytr_r, index=tr.index))
spear = tr[feats].corrwith(pd.Series(ytr_r, index=tr.index), method="spearman")
idx = np.random.default_rng(1).choice(len(tr), size=min(15000, len(tr)), replace=False)
Xf = tr[feats].fillna(tr[feats].median()).fillna(0)
mi = pd.Series(mutual_info_regression(Xf.iloc[idx].to_numpy(float), ytr_r[idx], random_state=42), index=feats)

log("[3] R-2 gain + permutation ...")
m = lgb.LGBMRegressor(n_estimators=1200, learning_rate=0.03, num_leaves=63, min_child_samples=50,
                      subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1,
                      random_state=42, n_jobs=-1, verbose=-1)
m.fit(tr[feats], ytr_r)
gain = pd.Series(m.booster_.feature_importance("gain"), index=feats)
vidx = np.random.default_rng(2).choice(len(va), size=min(8000, len(va)), replace=False)
perm = permutation_importance(m, va[feats].iloc[vidx], (va.y_point-va.base_point).to_numpy()[vidx],
                              scoring="r2", n_repeats=3, random_state=42, n_jobs=1)
perm_s = pd.Series(perm.importances_mean, index=feats)
log(f"    ok ({time.time()-t0:.0f}s)")

rank = pd.DataFrame({"pearson":pear,"spearman":spear,"mi":mi,"gain":gain,"perm":perm_s})
for c in ["pearson","spearman","mi","gain","perm"]: rank["r_"+c] = rank[c].rank(ascending=False)
rank["rank_mean"] = rank[[c for c in rank.columns if c.startswith("r_")]].mean(axis=1)
rank = rank.sort_values("rank_mean"); rank.to_csv(os.path.join(OUT,"feature_ranking_v2.csv"))
log("\n== Top-15 (rank_mean) ==\n"+rank.head(15)[["rank_mean","gain","perm","mi"]].round(3).to_string())

log("[4] R-3 selection sweep ...")
order = rank.index.tolist(); sweep=[]
for K in [5,10,15,20,25,30,40,50,60,80,104]:
    fs = order[:K]
    mm = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=63, min_child_samples=50,
                           subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1,
                           random_state=42, n_jobs=-1, verbose=-1)
    mm.fit(tr[fs], ytr_r, eval_set=[(va[fs],(va.y_point-va.base_point).to_numpy())], eval_metric="l2",
           callbacks=[lgb.early_stopping(80, verbose=False)])
    pv = va.base_point + mm.predict(va[fs]); pt = te.base_point + mm.predict(te[fs])
    sweep.append(dict(K=K, val_R2=round(r2_score(va.y_point,pv),4), test_R2=round(r2_score(te.y_point,pt),4)))
    log(f"    K={K:3d} val={sweep[-1]['val_R2']:.4f} test={sweep[-1]['test_R2']:.4f} ({time.time()-t0:.0f}s)")
sw = pd.DataFrame(sweep); sw.to_csv(os.path.join(OUT,"selection_sweep_v2.csv"), index=False)
bestK = int(sw.loc[sw.val_R2.idxmax(),"K"]); log(f"    K terbaik(val)={bestK}")

log("[5] R-4 SHAP ...")
fs = order[:bestK]
best = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=63, min_child_samples=50,
                         subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1,
                         random_state=42, n_jobs=-1, verbose=-1)
best.fit(tr[fs], ytr_r, eval_set=[(va[fs],(va.y_point-va.base_point).to_numpy())],
         callbacks=[lgb.early_stopping(80, verbose=False)])
contrib = best.predict(va[fs], pred_contrib=True)
shap = pd.DataFrame(contrib[:, :len(fs)], columns=fs, index=va.index)
glob = shap.abs().mean().sort_values(ascending=False); glob.to_csv(os.path.join(OUT,"shap_global_v2.csv"))
kt_va = va["kt"].to_numpy()
reg = np.where(kt_va>0.65,"clear",np.where(kt_va>0.3,"partly","overcast"))
byreg = shap.groupby(reg).apply(lambda g: g.abs().mean()).T
byreg.columns=[f"shap_{c}" for c in byreg.columns]; byreg=byreg.reindex(glob.index); byreg["overall"]=glob
byreg.to_csv(os.path.join(OUT,"shap_by_regime_v2.csv"))
log("Top-10 SHAP:\n"+glob.head(10).round(2).to_string())

# ---------- PLOT ----------
top = rank.head(20).iloc[::-1]
fig, ax = plt.subplots(figsize=(7,6)); ax.barh(top.index, top["gain"], color="slateblue")
ax.set_xlabel("LightGBM gain"); ax.set_title("Top-20 fitur — LightGBM gain (titik t+1h)")
savefig(fig, "02_top20_gain.png")

fig, ax = plt.subplots(figsize=(7,6)); ax.barh(top.index, top["perm"], color="darkorange")
ax.set_xlabel("Permutation importance (ΔR²)"); ax.set_title("Top-20 fitur — permutation importance")
savefig(fig, "02_top20_perm.png")

fig, ax = plt.subplots(figsize=(6,3.4)); ax.plot(sw.K, sw.val_R2, "o-", label="val 2024")
ax.plot(sw.K, sw.test_R2, "s--", label="test 2025")
ax.axvline(bestK, color="gray", ls=":", lw=1); ax.set_xlabel("Jumlah fitur (K)"); ax.set_ylabel("R²")
ax.set_title("Kurva seleksi fitur"); ax.legend()
savefig(fig, "02_selection_curve.png")

fig, ax = plt.subplots(figsize=(7,5)); g10 = glob.head(15).iloc[::-1]
ax.barh(g10.index, g10.values, color="seagreen"); ax.set_xlabel("mean|SHAP|")
ax.set_title("Top-15 SHAP global (titik t+1h)")
savefig(fig, "02_shap_top15.png")

key = ["kt","clp_cot","clp_cth_km","aws_rh_pct","aws_temp_c","clear_sky_ghi","solar_elev_deg","synop_cloud_cover_oktas"]
key = [c for c in key if c in feats]
cm = tr[key].corr(method="spearman")
fig, ax = plt.subplots(figsize=(6.2,5.4)); im = ax.imshow(cm, cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(key))); ax.set_xticklabels(key, rotation=45, ha="right", fontsize=8)
ax.set_yticks(range(len(key))); ax.set_yticklabels(key, fontsize=8)
for i in range(len(key)):
    for j in range(len(key)):
        ax.text(j, i, f"{cm.iloc[i,j]:.2f}", ha="center", va="center", fontsize=7)
ax.set_title("Korelasi Spearman fitur kunci"); fig.colorbar(im, fraction=0.046)
savefig(fig, "02_corr_heatmap.png")
log(f"SELESAI Tahap 2 v2 dalam {time.time()-t0:.0f}s")