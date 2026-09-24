# -*- coding: utf-8 -*-
"""Tahap 8b-m — ablasi kategori per situs (target RATA-RATA jam, headline) + bootstrap dCLP."""
import os, sys, time, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.metrics import r2_score, mean_squared_error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, savefig, BASE, SITES
import matplotlib.pyplot as plt

def log(*a): print(*a, flush=True)
t0=time.time(); OUT=os.path.join(BASE,"07_replication"); os.makedirs(OUT,exist_ok=True)

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
    T4=[f for f in feats if f.startswith("accel_") or "_std_" in f]
    G={g:[] for g in ["A","B","C1","C2","D","E","F"]}
    for f in feats:
        if f in T4: continue
        G[grp(f)].append(f)
    T1=G["A"]+G["B"]+G["C1"]+G["C2"]
    SYNC=[c for c in G["E"] if c in ["synop_cloud_cover_oktas","synop_cl","synop_cm","synop_ch"]]
    return T1, G["D"], G["F"], SYNC

rows=[]
for site in SITES:
    df, feats, yr = prepare(site)
    itr,iva,ite = split_idx(df, yr, "mean")
    tr,va,te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
    ytr_r=(tr.y_mean-tr.base_mean).to_numpy(); yva_r=(va.y_mean-va.base_mean).to_numpy()
    yt=te.y_mean.to_numpy(); bt=te.base_mean.to_numpy()
    T1,CLP,AWS,SYNC=tiers(feats)
    def run(fs):
        m=lgb.LGBMRegressor(n_estimators=2000,learning_rate=0.03,num_leaves=63,min_child_samples=50,subsample=0.8,
                            subsample_freq=1,colsample_bytree=0.8,reg_alpha=0.1,reg_lambda=0.1,random_state=42,n_jobs=-1,verbose=-1)
        m.fit(tr[fs],ytr_r,eval_set=[(va[fs],yva_r)],eval_metric="l2",callbacks=[lgb.early_stopping(80,verbose=False)])
        return bt+m.predict(te[fs])
    p1=run(T1); pc=run(T1+CLP); pa=run(T1+AWS); ps=run(T1+SYNC)
    r1,rc,ra,rs=[r2_score(yt,p) for p in (p1,pc,pa,ps)]
    n=len(yt); nb=2000; rng=np.random.default_rng(11); bi=rng.integers(0,n,size=(nb,n))
    def br(p):
        e=(yt-p)**2; ee=e[bi]; mu=yt[bi].mean(1); return 1-ee.mean(1)/((yt[bi]-mu[:,None])**2).mean(1)
    dr=br(pc)-br(p1); lo,hi=np.percentile(dr,[2.5,97.5])
    rows.append(dict(site=site, T1=round(r1,4), T1_CLP=round(rc,4), T1_AWS=round(ra,4), T1_SYNOPcloud=round(rs,4),
                     dCLP=round(rc-r1,4), dCLP_lo=round(lo,4), dCLP_hi=round(hi,4),
                     CLP_sig=("YA" if lo>0 else "tidak"), dAWS=round(ra-r1,4), dSYNOP=round(rs-r1,4)))
    log(f"  {site:10s} T1={r1:.4f} +CLP={rc:.4f} +AWS={ra:.4f} +SYNOPcloud={rs:.4f} | dCLP={rc-r1:+.4f} [{lo:+.4f},{hi:+.4f}] dAWS={ra-r1:+.4f} ({time.time()-t0:.0f}s)")
A=pd.DataFrame(rows); A.to_csv(os.path.join(OUT,"replication_ablation_mean.csv"),index=False)
log("\n== ABLASI 6 SITUS (target mean) ==\n"+A.to_string(index=False))

x=np.arange(len(A))
fig,ax=plt.subplots(figsize=(8.5,3.8))
ax.bar(x-0.2, A.dCLP, 0.4, label="dR2 +CLP", color="seagreen", yerr=[A.dCLP-A.dCLP_lo, A.dCLP_hi-A.dCLP])
ax.bar(x+0.2, A.dAWS, 0.4, label="dR2 +AWS", color="gray")
ax.axhline(0,color="k",lw=0.8); ax.set_xticks(x); ax.set_xticklabels(A.site, rotation=15)
ax.set_ylabel("delta R2 vs T1 core"); ax.set_title("Kontribusi inkremental per situs (target mean)"); ax.legend(fontsize=8)
savefig(fig,"08_replication_ablation_mean.png")
log(f"SELESAI Tahap 8b-m dalam {time.time()-t0:.0f}s")
