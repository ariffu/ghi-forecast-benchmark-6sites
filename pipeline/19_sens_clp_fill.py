# -*- coding: utf-8 -*-
"""Tahap 19 (baru, rerun v2) — sensitivitas perlakuan slot CLP tanpa retrieval.

DB v2 mengisi slot no_retrieval dengan COT=0/CTH=0 di 5 situs (Banten v2 = NULL).
Pipeline utama memakai 00_data (CLP dimask oleh clp_retrieval_ok). Skrip ini
membandingkan dengan 00_data_rawfill (isian dipakai apa adanya) memakai protokol
ablasi 07b (LightGBM residual, target mean, protokol A): T1, T1+CLP, FULL, + bootstrap dCLP.
Jalankan: python -u 19_sens_clp_fill.py
"""
import os, sys, time, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.metrics import r2_score
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common
from _common import split_idx, savefig, BASE, SITES
import matplotlib.pyplot as plt

def log(*a): print(*a, flush=True)
t0 = time.time(); OUT = os.path.join(BASE, "19_sens_clp_fill"); os.makedirs(OUT, exist_ok=True)

def tiers(feats):
    def grp(f):
        if f.startswith("clp_"): return "D"
        if f.startswith("synop_"): return "E"
        if f.startswith("aws_"): return "F"
        if f.startswith(("clear_sky","solar_elev","decl_","eot_","is_day","elev_sin")): return "B"
        if f.startswith(("kt_lag","kt_delta","kt_roll","kt_std","kt_cooper")) or f=="kt": return "C2"
        if f.startswith(("ghi_lag","ghi_delta")): return "C1"
        if f.startswith(("ghi_wm2","dhi_","dni_","nett_","reflected","sunshine")): return "A"
        return "B"
    T4=([f for f in feats if f.startswith("accel_") or "_std_" in f] if os.environ.get("FEATSET", "P2") == "P0" else [])   # P2: kelompok eksperimental dilebur ke inti
    G={g:[] for g in ["A","B","C1","C2","D","E","F"]}
    for f in feats:
        if f in T4: continue
        G[grp(f)].append(f)
    return G["A"]+G["B"]+G["C1"]+G["C2"], G["D"]

rows=[]
for variant, folder in [("masked (utama)", "00_data"), ("raw fill (COT=0)", "00_data_rawfill")]:
    _common.DATA = os.path.join(BASE, folder)
    for site in SITES:
        df, feats, yr = _common.prepare(site)
        itr,iva,ite = split_idx(df, yr, "mean")
        tr,va,te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
        ytr_r=(tr.y_mean-tr.base_mean).to_numpy(); yva_r=(va.y_mean-va.base_mean).to_numpy()
        yt=te.y_mean.to_numpy(); bt=te.base_mean.to_numpy()
        T1, CLP = tiers(feats)
        def run(fs):
            m=lgb.LGBMRegressor(n_estimators=2000,learning_rate=0.03,num_leaves=63,min_child_samples=50,subsample=0.8,
                                subsample_freq=1,colsample_bytree=0.8,reg_alpha=0.1,reg_lambda=0.1,random_state=42,n_jobs=-1,verbose=-1)
            m.fit(tr[fs],ytr_r,eval_set=[(va[fs],yva_r)],eval_metric="l2",callbacks=[lgb.early_stopping(80,verbose=False)])
            return bt+m.predict(te[fs])
        p1, pc, pf = run(T1), run(T1+CLP), run(feats)
        n=len(yt); bi=np.random.default_rng(11).integers(0,n,size=(2000,n))
        def br(p):
            e=(yt-p)**2; ee=e[bi]; mu=yt[bi].mean(1); return 1-ee.mean(1)/((yt[bi]-mu[:,None])**2).mean(1)
        dr=br(pc)-br(p1); lo,hi=np.percentile(dr,[2.5,97.5])
        clp_day = te["clp_cot"].notna().mean()
        rows.append(dict(variant=variant, site=site, n_test=n, clp_cot_avail_test=round(float(clp_day),4),
                         T1=round(r2_score(yt,p1),4), T1_CLP=round(r2_score(yt,pc),4), FULL=round(r2_score(yt,pf),4),
                         dCLP=round(r2_score(yt,pc)-r2_score(yt,p1),4), dCLP_lo=round(lo,4), dCLP_hi=round(hi,4)))
        log(f"  {variant:18s} {site:9s} avail={clp_day:.3f} T1={rows[-1]['T1']:.4f} +CLP={rows[-1]['T1_CLP']:.4f} "
            f"FULL={rows[-1]['FULL']:.4f} dCLP={rows[-1]['dCLP']:+.4f} [{lo:+.4f},{hi:+.4f}] ({time.time()-t0:.0f}s)")
R=pd.DataFrame(rows); R.to_csv(os.path.join(OUT,"sens_clp_fill.csv"),index=False)
log("\n"+R.to_string(index=False))

P=R.pivot(index="site",columns="variant",values="dCLP").loc[SITES]
x=np.arange(len(P)); fig,ax=plt.subplots(figsize=(8,3.6))
for i,c in enumerate(P.columns): ax.bar(x+(i-0.5)*0.38, P[c], 0.38, label=c)
ax.axhline(0,color="k",lw=0.7); ax.set_xticks(x); ax.set_xticklabels(P.index, rotation=15)
ax.set_ylabel("ΔR² (+CLP vs T1)"); ax.set_title("Sensitivity to no-retrieval CLP treatment (hourly mean, test 2025)"); ax.legend(fontsize=8)
savefig(fig,"19_sens_clp_fill.png")
log(f"SELESAI Tahap 19 dalam {time.time()-t0:.0f}s")
