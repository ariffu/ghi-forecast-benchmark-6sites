# -*- coding: utf-8 -*-
"""Tahap 3m — ablasi kategori, target RATA-RATA jam (headline), Bengkulu."""
import os, sys, time, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, savefig, BASE
import matplotlib.pyplot as plt

def log(*a): print(*a, flush=True)
t0 = time.time()
OUT = os.path.join(BASE, "03_ablation_mean"); os.makedirs(OUT, exist_ok=True)
df, feats, yr = prepare()
itr, iva, ite = split_idx(df, yr, "mean")
tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
ytr_r = (tr.y_mean - tr.base_mean).to_numpy()

def grp(f):
    if f.startswith("clp_"): return "D"
    if f.startswith("synop_"): return "E"
    if f.startswith("aws_"): return "F"
    if f.startswith(("clear_sky","solar_elev","decl_","eot_","is_day","elev_sin")): return "B"
    if f.startswith(("kt_lag","kt_delta","kt_roll","kt_std","kt_cooper")) or f=="kt": return "C2"
    if f.startswith(("ghi_lag","ghi_delta")): return "C1"
    if f.startswith(("ghi_wm2","dhi_","dni_","nett_","reflected","sunshine")): return "A"
    return "B"
T4 = [f for f in feats if f.startswith("accel_") or "_std_" in f]
G = {g: [] for g in ["A","B","C1","C2","D","E","F"]}
for f in feats:
    if f in T4: continue
    G[grp(f)].append(f)
T1 = G["A"]+G["B"]+G["C1"]+G["C2"]; CLP=G["D"]; SYNOP=G["E"]; AWS=G["F"]
SYN_CLOUD=[c for c in SYNOP if c in ["synop_cloud_cover_oktas","synop_cl","synop_cm","synop_ch"]]
log(f"T1={len(T1)} CLP={len(CLP)} SYNOP={len(SYNOP)} AWS={len(AWS)} T4={len(T4)}")

def run(name, fs):
    mm = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=63, min_child_samples=50,
                           subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1,
                           random_state=42, n_jobs=-1, verbose=-1)
    mm.fit(tr[fs], ytr_r, eval_set=[(va[fs],(va.y_mean-va.base_mean).to_numpy())], eval_metric="l2",
           callbacks=[lgb.early_stopping(80, verbose=False)])
    pt = te.base_mean + mm.predict(te[fs]); pv = va.base_mean + mm.predict(va[fs])
    rmse_sp = np.sqrt(mean_squared_error(te.y_mean, te.base_mean))
    r = dict(config=name, n=len(fs), val_R2=round(r2_score(va.y_mean,pv),4),
             test_R2=round(r2_score(te.y_mean,pt),4), MAE=round(mean_absolute_error(te.y_mean,pt),1),
             RMSE=round(np.sqrt(mean_squared_error(te.y_mean,pt)),1),
             skill=round(1-np.sqrt(mean_squared_error(te.y_mean,pt))/rmse_sp,4))
    log(f"    {name:30s} n={len(fs):3d} val={r['val_R2']:.4f} test={r['test_R2']:.4f} ({time.time()-t0:.0f}s)")
    return r, pt

cfgs = [("T1 core", T1), ("T1+CLP", T1+CLP), ("T1+AWS_meteo", T1+AWS),
        ("T1+CLP+AWS_meteo", T1+CLP+AWS), ("T1+SYNOP_cloud", T1+SYN_CLOUD),
        ("T1+CLP+SYNOP_cloud", T1+CLP+SYN_CLOUD), ("FULL", T1+CLP+SYNOP+AWS+T4)]
rows=[]; preds={}
for n, fs in cfgs:
    r, p = run(n, fs); rows.append(r); preds[n]=p
rmse_sp=np.sqrt(mean_squared_error(te.y_mean, te.base_mean))
rows.insert(0, dict(config="smart-persistence", n=0, val_R2=round(r2_score(va.y_mean,va.base_mean),4),
                    test_R2=round(r2_score(te.y_mean,te.base_mean),4),
                    MAE=round(mean_absolute_error(te.y_mean,te.base_mean),1),
                    RMSE=round(rmse_sp,1), skill=0.0))
R=pd.DataFrame(rows); R.to_csv(os.path.join(OUT,"ablation_mean.csv"), index=False)
log("\n"+R.to_string(index=False))

# bootstrap
y=te.y_mean.to_numpy(); nb=2000; rng=np.random.default_rng(11); bi=rng.integers(0,len(y),size=(nb,len(y)))
def br(p):
    p = np.asarray(p, dtype=float)
    e=(y-p)**2; ee=e[bi]; mu=y[bi].mean(1); return 1-ee.mean(1)/((y[bi]-mu[:,None])**2).mean(1)
pairs=[("T1+CLP","T1 core","efek CLP"),("T1+CLP+AWS_meteo","T1+CLP","efek AWS meteo"),
       ("T1+CLP+SYNOP_cloud","T1+CLP","efek SYNOP cloud"),("T1+CLP","T1+AWS_meteo","CLP vs AWS"),
       ("FULL","T1+CLP","sisa fitur")]
bs=[]
for a,b_,lab in pairs:
    dr=br(preds[a])-br(preds[b_]); lo,hi=np.percentile(dr,[2.5,97.5])
    bs.append(dict(pair=f"{a} - {b_}", label=lab, dR2=round(dr.mean(),4), CI_lo=round(lo,4),
                   CI_hi=round(hi,4), signif=("YA" if lo>0 or hi<0 else "tidak")))
B=pd.DataFrame(bs); B.to_csv(os.path.join(OUT,"ablation_bootstrap_mean.csv"), index=False)
log("\n"+B.to_string(index=False))

Rp=R[R.config!="smart-persistence"].copy()
fig, ax = plt.subplots(figsize=(8,3.8))
ax.barh(Rp.config[::-1], Rp.test_R2[::-1], color="cornflowerblue")
ax.axvline(R.test_R2[0], color="gray", ls="--", lw=1, label=f"smart-persistence={R.test_R2[0]:.3f}")
ax.set_xlabel("R² (test 2025)"); ax.set_title("Ablasi kategori fitur — rata-rata jam (headline)"); ax.legend(fontsize=8)
savefig(fig, "03_ablation_bar_mean.png")

fig, ax = plt.subplots(figsize=(7,3.6)); x=np.arange(len(B))
ax.bar(x, B.dR2, yerr=[B.dR2-B.CI_lo, B.CI_hi-B.dR2], capsize=4, color=["seagreen" if s=="YA" else "lightgray" for s in B.signif])
ax.axhline(0, color="k", lw=0.8); ax.set_xticks(x); ax.set_xticklabels(B.label, rotation=20, ha="right", fontsize=8)
ax.set_ylabel("ΔR²"); ax.set_title("Kontribusi inkremental (bootstrap 95% CI) — target mean")
savefig(fig, "03_ablation_delta_mean.png")
log(f"SELESAI Tahap 3m dalam {time.time()-t0:.0f}s")
