# -*- coding: utf-8 -*-
"""
Tahap 12b — Kalibrasi conformal (CQR) dengan SET KALIBRASI DIPISAHKAN.
Perbaikan open-item #4: set kalibrasi conformal TIDAK lagi sama dengan set
early-stopping. Validasi 2024 dipotong dua secara kronologis:
  - paruh pertama 2024  -> early-stopping quantile LightGBM
  - paruh kedua 2024    -> kalibrasi conformal (hitung E & dq)
Evaluasi tetap test 2025.
Jalankan: python -u 12b_conformal_split.py
"""
import os, sys, time, math, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.metrics import r2_score
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, savefig, BASE, SITES
import matplotlib.pyplot as plt

def log(*a): print(*a, flush=True)
t0=time.time(); OUT=os.path.join(BASE,"12b_conformal_split"); os.makedirs(OUT,exist_ok=True)
LEVELS=[0.50,0.80,0.90,0.95]
TAU_NEED=sorted(set([0.5]+[round((1-l)/2,4) for l in LEVELS]+[round((1+l)/2,4) for l in LEVELS]))
def lgbm(**kw):
    return lgb.LGBMRegressor(n_estimators=3000,learning_rate=0.03,num_leaves=63,min_child_samples=50,
                             subsample=0.8,subsample_freq=1,colsample_bytree=0.8,reg_alpha=0.1,
                             reg_lambda=0.1,random_state=42,n_jobs=-1,verbose=-1,**kw)
def pinball(y,q,tau):
    d=y-q; return np.mean(np.maximum(tau*d,(tau-1)*d))
def qlevel(n,cov): return min(1.0, math.ceil((n+1)*cov)/n)

rows=[]; bkl=None
for site in SITES:
    df,feats,yr=prepare(site)
    m=(df.solar_elev_deg>5)&(df.solar_elev_h1>5)&df.y_point.notna()&df.base_point.notna()
    idx=np.where(m.to_numpy())[0]
    itr,iva,ite=idx[yr[idx]<=2023],idx[yr[idx]==2024],idx[yr[idx]==2025]
    # --- PISAH 2024 jadi dua (kronologis): paruh awal = early-stopping, paruh akhir = kalibrasi ---
    half=len(iva)//2
    iva_es, iva_cal = iva[:half], iva[half:]
    tr,va_es,va_cal,te=df.iloc[itr],df.iloc[iva_es],df.iloc[iva_cal],df.iloc[ite]
    ytr=(tr.y_point-tr.base_point).to_numpy()
    yva_es=(va_es.y_point-va_es.base_point).to_numpy()
    ycal, yte = va_cal.y_point.to_numpy(), te.y_point.to_numpy()
    bcal, bte = va_cal.base_point.to_numpy(), te.base_point.to_numpy()
    Qc={}; Qt={}
    for tau in TAU_NEED:
        mq=lgbm(objective="quantile",alpha=tau)
        mq.fit(tr[feats],ytr,eval_set=[(va_es[feats],yva_es)],callbacks=[lgb.early_stopping(100,verbose=False)])
        Qc[tau]=bcal+mq.predict(va_cal[feats]); Qt[tau]=bte+mq.predict(te[feats])
    out=dict(site=site,n_es=len(va_es),n_cal=len(va_cal),n_test=len(te),R2_point=round(r2_score(yte, Qt[0.5]),4))
    for L in LEVELS:
        lo_t,hi_t=round((1-L)/2,4),round((1+L)/2,4)
        # sebelum (tanpa conformal)
        picp_b=float(np.mean((yte>=Qt[lo_t])&(yte<=Qt[hi_t])))
        pin_b=float(np.mean(Qt[hi_t]-Qt[lo_t])/(np.percentile(yte,99)-np.percentile(yte,1)))
        # conformal (kalibrasi pada paruh kedua 2024)
        E=np.maximum(Qc[lo_t]-ycal, ycal-Qc[hi_t])
        dq=np.quantile(E, qlevel(len(E),L), method="higher")
        lo_cc,hi_cc=Qt[lo_t]-dq, Qt[hi_t]+dq
        picp_a=float(np.mean((yte>=lo_cc)&(yte<=hi_cc)))
        pin_a=float(np.mean(hi_cc-lo_cc)/(np.percentile(yte,99)-np.percentile(yte,1)))
        out[f"PICP_{int(L*100)}_before"]=round(picp_b,3); out[f"PICP_{int(L*100)}_after"]=round(picp_a,3)
        out[f"PINAW_{int(L*100)}_before"]=round(pin_b,3); out[f"PINAW_{int(L*100)}_after"]=round(pin_a,3)
        out[f"dq_{int(L*100)}"]=round(float(dq),1)
        if site=="bengkulu" and L==0.90:
            bkl=dict(yte=yte,lo=lo_cc,hi=hi_cc,med=Qt[0.5],ts=te.ts_wib.to_numpy(),
                     hr=te.ts_wib.dt.hour.to_numpy())
    rows.append(out)
    log(f"  {site:10s} PICP90 {out['PICP_90_before']}->{out['PICP_90_after']} | PICP80 {out['PICP_80_before']}->{out['PICP_80_after']} "
        f"| dq90={out['dq_90']} ({time.time()-t0:.0f}s)")
R=pd.DataFrame(rows); R.to_csv(os.path.join(OUT,"conformal_6situs_split.csv"),index=False)
log("\n== KALIBRASI CONFORMAL SPLIT (before -> after) ==\n"+R[["site","n_es","n_cal","R2_point","PICP_50_before","PICP_50_after","PICP_80_before","PICP_80_after","PICP_90_before","PICP_90_after","PICP_95_before","PICP_95_after"]].to_string(index=False))

# PLOT 1: PICP vs nominal before/after (per situs)
fig,axs=plt.subplots(2,3,figsize=(12,6.4))
for ax,site in zip(axs.ravel(),SITES):
    r=R[R.site==site].iloc[0]
    nom=[50,80,90,95]
    ax.plot(nom,[r[f"PICP_{c}_before"]*100 for c in nom],"o-",label="sebelum")
    ax.plot(nom,[r[f"PICP_{c}_after"]*100 for c in nom],"s-",label="conformal (split)")
    ax.plot([50,95],[50,95],"k:",lw=1)
    ax.set_title(site,fontsize=9); ax.set_xlabel("nominal (%)"); ax.set_ylabel("PICP (%)"); ax.set_ylim(40,100); ax.legend(fontsize=7)
savefig(fig,"12b_picp_conformal_6situs_split.png")

# PLOT 2: contoh interval terkalibrasi (Bengkulu)
if bkl:
    sel=np.where((bkl["hr"]>=9)&(bkl["hr"]<=16))[0][:400]; x=np.arange(len(sel))
    fig,ax=plt.subplots(figsize=(11,3.6))
    ax.fill_between(x,bkl["lo"][sel],bkl["hi"][sel],alpha=0.25,color="seagreen",label="90% conformal")
    ax.plot(x,bkl["med"][sel],color="darkgreen",lw=1,label="median")
    ax.plot(x,bkl["yte"][sel],"o",ms=2,color="black",label="observasi")
    ax.set_title("Interval 90% setelah kalibrasi conformal (split) — Bengkulu"); ax.set_ylabel("GHI (W/m²)"); ax.legend(fontsize=8)
    savefig(fig,"12b_interval_conformal_bengkulu_split.png")
    # PICP90 per jam setelah conformal
    hr=bkl["hr"]; rec=[]
    for h in range(6,19):
        s=hr==h
        if s.sum()<100: continue
        rec.append((h,float(np.mean((bkl["yte"][s]>=bkl["lo"][s])&(bkl["yte"][s]<=bkl["hi"][s])))))
    Hh=pd.DataFrame(rec,columns=["hour","PICP90_after"]); Hh.to_csv(os.path.join(OUT,"picp90_by_hour_after_split.csv"),index=False)
    fig,ax=plt.subplots(figsize=(6.5,3.2)); ax.bar(Hh.hour,Hh.PICP90_after*100,color="seagreen"); ax.axhline(90,color="r",ls="--")
    ax.set_ylim(60,100); ax.set_xlabel("Jam (WIB)"); ax.set_ylabel("PICP90 (%)"); ax.set_title("Coverage 90% per jam (setelah conformal split) — Bengkulu")
    savefig(fig,"12b_picp90_by_hour_after_split.png")
log(f"SELESAI Tahap 12b dalam {time.time()-t0:.0f}s")
