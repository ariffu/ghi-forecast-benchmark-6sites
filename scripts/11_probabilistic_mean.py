# -*- coding: utf-8 -*-
"""
Tahap 11m — Lapisan probabilistik (target RATA-RATA jam, headline).
Dua pendekatan:
  (I)  Quantile LightGBM (tau = 9 level)  -> interval & CRPS
  (II) Residual-per-hour Gaussian (ala Sansine) dari validasi
Metrik: PICP (50/80/90/95%), PINAW, CRPS (approx), PIT (kalibrasi).
Protokol: filter origin elev>5 (A) untuk konsistensi headline.
Jalankan: python -u 11_probabilistic_mean.py
"""
import os, sys, time, numpy as np, pandas as pd, lightgbm as lgb
from scipy.stats import norm
from sklearn.metrics import r2_score, mean_squared_error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, savefig, BASE, SITES
import matplotlib.pyplot as plt

def log(*a): print(*a, flush=True)
t0=time.time(); OUT=os.path.join(BASE,"11_probabilistic_mean"); os.makedirs(OUT,exist_ok=True)
TAU=[0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975]
CENT={0.50:(0.25,0.75),0.80:(0.10,0.90),0.90:(0.05,0.95),0.95:(0.025,0.975)}
ZL={0.50:0.6745,0.80:1.2816,0.90:1.6449,0.95:1.9600}

def lgbm(**kw):
    return lgb.LGBMRegressor(n_estimators=3000,learning_rate=0.03,num_leaves=63,min_child_samples=50,
                             subsample=0.8,subsample_freq=1,colsample_bytree=0.8,reg_alpha=0.1,
                             reg_lambda=0.1,random_state=42,n_jobs=-1,verbose=-1,**kw)

def pinball(y,q,tau):
    d=y-q; return np.mean(np.maximum(tau*d,(tau-1)*d))

rows=[]; detail_bkl=None
for site in SITES:
    df,feats,yr=prepare(site)
    m=(df.solar_elev_deg>5)&df.y_mean.notna()&df.base_mean.notna()&df.valid_mean
    idx=np.where(m.to_numpy())[0]
    itr,iva,ite=idx[yr[idx]<=2023],idx[yr[idx]==2024],idx[yr[idx]==2025]
    tr,va,te=df.iloc[itr],df.iloc[iva],df.iloc[ite]
    yt=te.y_mean.to_numpy(); bt=te.base_mean.to_numpy()
    ytr=(tr.y_mean-tr.base_mean).to_numpy(); yva=(va.y_mean-va.base_mean).to_numpy()
    # point model
    mp=lgbm(); mp.fit(tr[feats],ytr,eval_set=[(va[feats],yva)],callbacks=[lgb.early_stopping(100,verbose=False)])
    pt=bt+mp.predict(te[feats])
    # val residual per jam
    pv=va.base_mean.to_numpy()+mp.predict(va[feats]); rv=va.y_mean.to_numpy()-pv
    hr=va.ts_wib.dt.hour.to_numpy(); sig={h:(np.std(rv[hr==h]) if (hr==h).sum()>50 else np.nan) for h in range(24)}
    sig_all=np.nanstd(rv)
    # quantile models
    Q=np.zeros((len(te),len(TAU)))
    for i,tau in enumerate(TAU):
        mq=lgbm(objective="quantile",alpha=tau)
        mq.fit(tr[feats],ytr,eval_set=[(va[feats],yva)],callbacks=[lgb.early_stopping(100,verbose=False)])
        Q[:,i]=bt+mq.predict(te[feats])
    hte=te.ts_wib.dt.hour.to_numpy()
    sg=np.array([sig.get(h,np.nan) for h in hte]); sg=np.where(np.isnan(sg),sig_all,sg)
    def picp(lo,hi): return float(np.mean((yt>=lo)&(yt<=hi)))
    def pinaw(lo,hi): return float(np.mean(hi-lo)/(np.percentile(yt,99)-np.percentile(yt,1)))
    out=dict(site=site,n_test=len(te),R2_point=round(r2_score(yt,pt),4))
    for c,(a,b) in CENT.items():
        ia,ib=TAU.index(a),TAU.index(b)
        out[f"q_PICP_{int(c*100)}"]=round(picp(Q[:,ia],Q[:,ib]),3)
        out[f"q_PINAW_{int(c*100)}"]=round(pinaw(Q[:,ia],Q[:,ib]),3)
    out["q_CRPS"]=round(2*np.mean([pinball(yt,Q[:,i],t) for i,t in enumerate(TAU)]),2)
    for c in CENT:
        z=ZL[c]; out[f"g_PICP_{int(c*100)}"]=round(picp(pt-z*sg,pt+z*sg),3)
    out["g_CRPS"]=round(np.mean(sg)*(1/np.sqrt(np.pi)),2)
    rows.append(out)
    log(f"  {site:10s} pointR2={out['R2_point']} | q_PICP90={out['q_PICP_90']} g_PICP90={out['g_PICP_90']} "
        f"| q_CRPS={out['q_CRPS']} ({time.time()-t0:.0f}s)")
    if site=="bengkulu":
        def pit_q():
            P=np.zeros(len(yt))
            for k in range(len(yt)):
                P[k]=np.interp(yt[k],Q[k,:],TAU,left=0.0,right=1.0)
            return P
        Pq=pit_q(); Pg=norm.cdf((yt-pt)/sg)
        detail_bkl=dict(yt=yt,qt=Q,pt=pt,sg=sg,Pq=Pq,Pg=Pg,hr=hte,ts=te.ts_wib.to_numpy())

R=pd.DataFrame(rows); R.to_csv(os.path.join(OUT,"probabilistic_6situs_mean.csv"),index=False)
log("\n== PROBABILISTIK 6 SITUS (mean) ==\n"+R.to_string(index=False))

if detail_bkl:
    d=detail_bkl
    fig,ax=plt.subplots(figsize=(6.4,3.4))
    ax.hist(d["Pq"],bins=20,range=(0,1),alpha=0.6,label="Quantile LGBM",density=True)
    ax.hist(d["Pg"],bins=20,range=(0,1),alpha=0.5,label="Gaussian residual/h",density=True)
    ax.axhline(1,color="k",lw=1,ls="--",label="ideal")
    ax.set_xlabel("PIT"); ax.set_ylabel("kepadatan"); ax.set_title("Kalibrasi PIT — Bengkulu (mean)"); ax.legend(fontsize=8)
    savefig(fig,"11_pit_bengkulu_mean.png")
    nom=[50,80,90,95]
    fig,ax=plt.subplots(figsize=(5,4))
    ax.plot(nom,[R.loc[R.site=='bengkulu',f'q_PICP_{c}'].values[0] for c in nom],"o-",label="Quantile")
    ax.plot(nom,[R.loc[R.site=='bengkulu',f'g_PICP_{c}'].values[0] for c in nom],"s--",label="Gaussian")
    ax.plot([50,95],[50,95],color="k",lw=1,ls=":",label="ideal")
    ax.set_xlabel("Nominal coverage (%)"); ax.set_ylabel("Empirical PICP (%)")
    ax.set_title("PICP vs nominal — Bengkulu (mean)"); ax.legend(fontsize=8)
    savefig(fig,"11_picp_bengkulu_mean.png")
    mk=(d["hr"]>=9)&(d["hr"]<=16)
    sel=np.where(mk)[0][:400]
    fig,ax=plt.subplots(figsize=(11,3.6))
    x=np.arange(len(sel))
    ax.fill_between(x,d["qt"][sel,TAU.index(0.025)],d["qt"][sel,TAU.index(0.975)],alpha=0.2,color="steelblue",label="95%")
    ax.fill_between(x,d["qt"][sel,TAU.index(0.10)],d["qt"][sel,TAU.index(0.90)],alpha=0.3,color="steelblue",label="80%")
    ax.fill_between(x,d["qt"][sel,TAU.index(0.25)],d["qt"][sel,TAU.index(0.75)],alpha=0.4,color="steelblue",label="50%")
    ax.plot(x,d["qt"][sel,TAU.index(0.50)],color="navy",lw=1,label="median")
    ax.plot(x,d["yt"][sel],"o",ms=2,color="black",label="observasi")
    ax.set_xlabel("sampel (jam siang, Bengkulu)"); ax.set_ylabel("GHI (W/m²)")
    ax.set_title("Interval prediksi bertingkat — Bengkulu (mean)"); ax.legend(fontsize=8)
    savefig(fig,"11_interval_fan_mean.png")
    hh=d["hr"]; rec=[]
    for h in range(6,19):
        s=hh==h
        if s.sum()<100: continue
        rec.append((h,float(np.mean((d["yt"][s]>=d["qt"][s,TAU.index(0.05)])&(d["yt"][s]<=d["qt"][s,TAU.index(0.95)])))))
    H=pd.DataFrame(rec,columns=["hour","PICP90"]); H.to_csv(os.path.join(OUT,"picp_by_hour_bengkulu_mean.csv"),index=False)
    fig,ax=plt.subplots(figsize=(6.5,3.2)); ax.bar(H.hour,H.PICP90,color="teal"); ax.axhline(0.9,color="r",ls="--")
    ax.set_ylim(0,1); ax.set_xlabel("Jam (WIB)"); ax.set_ylabel("PICP 90%"); ax.set_title("Coverage 90% per jam — Bengkulu (mean)")
    savefig(fig,"11_picp_by_hour_mean.png")
log(f"SELESAI Tahap 11m dalam {time.time()-t0:.0f}s")
