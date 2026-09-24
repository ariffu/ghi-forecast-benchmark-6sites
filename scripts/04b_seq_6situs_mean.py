# -*- coding: utf-8 -*-
"""Tahap 4b-m — SEQUENCE models (LSTM/Transformer/hybrid) untuk target RATA-RATA jam, 6 situs.
Tabular (LightGBM/CatBoost/XGBoost/MLP) target mean sudah dihitung di 04c_*;
skrip ini menambah 4 sequence models lalu menggabungkan menjadi tabel 8x6 target mean.
Resume per-situs (aman bila timeout).
"""
import os, sys, time, numpy as np, pandas as pd, torch, torch.nn as nn
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, savefig, BASE, SITES
import matplotlib.pyplot as plt

def log(*a): print(*a, flush=True)
t0=time.time(); torch.set_num_threads(max(1,(os.cpu_count() or 4)-1)); torch.manual_seed(42); np.random.seed(42)
OUT=os.path.join(BASE,"04b_arch_6situs_mean"); os.makedirs(OUT,exist_ok=True)
DONE_CSV=os.path.join(OUT,"arch_6situs_mean.csv")
CH=["ghi_wm2","dhi_wm2","dni_wm2","kt","clp_cot","clp_cth_km","clp_ctt_k","clp_cer_um",
    "aws_temp_c","aws_rh_pct","aws_pressure_hpa","aws_wind_speed_ms","aws_rain_mm","solar_elev_deg"]
L=12

class PosE(nn.Module):
    def __init__(s,d,L):
        super().__init__(); pe=torch.zeros(L,d); pos=torch.arange(L).unsqueeze(1).float()
        div=torch.exp(torch.arange(0,d,2).float()*(-np.log(10000.0)/d)); pe[:,0::2]=torch.sin(pos*div); pe[:,1::2]=torch.cos(pos*div); s.register_buffer("pe",pe.unsqueeze(0))
    def forward(s,x): return x+s.pe[:,:x.size(1)]
class LSTMN(nn.Module):
    def __init__(s,c,h=96): super().__init__(); s.l=nn.LSTM(c,h,2,batch_first=True,dropout=0.1); s.h=nn.Sequential(nn.Linear(h,64),nn.ReLU(),nn.Linear(64,1))
    def forward(s,x): o,_=s.l(x); return s.h(o[:,-1]).squeeze(-1)
class TRFN(nn.Module):
    def __init__(s,c,d=64): super().__init__(); s.p=nn.Linear(c,d); s.pe=PosE(d,L); s.t=nn.TransformerEncoder(nn.TransformerEncoderLayer(d,4,128,dropout=0.1,batch_first=True),2); s.h=nn.Sequential(nn.Linear(d,64),nn.ReLU(),nn.Linear(64,1))
    def forward(s,x): z=s.t(s.pe(s.p(x))); return s.h(z[:,-1]).squeeze(-1)
class LSTMH(nn.Module):
    def __init__(s,c,d,h=96): super().__init__(); s.l=nn.LSTM(c,h,2,batch_first=True,dropout=0.1); s.h=nn.Sequential(nn.Linear(h+d,128),nn.ReLU(),nn.Dropout(0.2),nn.Linear(128,1))
    def forward(s,x,z): o,_=s.l(x); return s.h(torch.cat([o[:,-1],z],1)).squeeze(-1)
class TRFH(nn.Module):
    def __init__(s,c,d,dd=64): super().__init__(); s.p=nn.Linear(c,dd); s.pe=PosE(dd,L); s.t=nn.TransformerEncoder(nn.TransformerEncoderLayer(dd,4,128,dropout=0.1,batch_first=True),2); s.h=nn.Sequential(nn.Linear(dd+d,128),nn.ReLU(),nn.Dropout(0.2),nn.Linear(128,1))
    def forward(s,x,z): o=s.t(s.pe(s.p(x))); return s.h(torch.cat([o[:,-1],z],1)).squeeze(-1)

def fit(model,xtr,ytr_,xva,yva_,epochs,bs,lr,patience=6):
    opt=torch.optim.Adam(model.parameters(),lr=lr); lf=nn.MSELoss()
    T=[torch.tensor(a) for a in xtr]; Y=torch.tensor(ytr_,dtype=torch.float32)
    V=[torch.tensor(a) for a in xva]; Yv=torch.tensor(yva_,dtype=torch.float32)
    best=np.inf; state=None; bad=0
    for ep in range(1,epochs+1):
        model.train(); perm=torch.randperm(len(Y)); nb=int(np.ceil(len(Y)/bs))
        for i in range(nb):
            j=perm[i*bs:(i+1)*bs]; opt.zero_grad(); l=lf(model(*[T[k][j] for k in range(len(T))]),Y[j]); l.backward(); opt.step()
        model.eval()
        with torch.no_grad(): v=lf(model(*V),Yv).item()
        if v<best-1e-4: best,state,bad=v,{k:t.clone() for k,t in model.state_dict().items()},0
        else:
            bad+=1
            if bad>=patience: break
    model.load_state_dict(state); model.eval(); return model

# (tabular dihitung terpisah di 04c_*; merge di 04b_merge_mean.py)
rows=[]; preds_all={}
for site in SITES:
    log(f"\n===== {site} ({time.time()-t0:.0f}s) =====")
    df,feats,yr=prepare(site)
    itr,iva,ite=split_idx(df,yr,"mean")
    tr,va,te=df.iloc[itr],df.iloc[iva],df.iloc[ite]
    ytr_r=(tr.y_mean-tr.base_mean).to_numpy(); yva_r=(va.y_mean-va.base_mean).to_numpy()
    y=df.y_mean.to_numpy(); b=df.base_mean.to_numpy()
    yt=y[ite]; bt=b[ite]; rsp=np.sqrt(mean_squared_error(yt,bt))
    Xw=df[CH].to_numpy(float); n=len(df); W=np.full((n,L,len(CH)),np.nan); ar=np.arange(n)
    for t in range(L):
        k=L-1-t; W[:,t,:]=np.where((ar>=k)[:,None], np.roll(Xw,k,axis=0), np.nan)
    med=tr[feats].median().fillna(0.0); mu=tr[feats].fillna(med).mean(); sd=tr[feats].fillna(med).std().replace(0,1).fillna(1)
    def pf(X): return (((X.fillna(med)-mu)/sd).astype("float64")).to_numpy(np.float32)
    Ztr,Zva,Zte=pf(tr[feats]),pf(va[feats]),pf(te[feats])
    medw=np.nan_to_num(np.nanmedian(W[itr].reshape(-1,len(CH)),axis=0),nan=0.0)
    def ps(ind):
        A=W[ind].copy(); m=np.isnan(A); A[m]=np.take(medw,np.where(m)[2])
        return ((A-mu[CH].to_numpy())/sd[CH].to_numpy()).astype(np.float32)
    Str,Sva,Ste=ps(itr),ps(iva),ps(ite)
    site_preds={}
    def met(p,name):
        r=dict(site=site,model=name,R2=round(r2_score(yt,p),4),MAE=round(mean_absolute_error(yt,p),2),
               RMSE=round(np.sqrt(mean_squared_error(yt,p)),2),skill=round(1-np.sqrt(mean_squared_error(yt,p))/rsp,4))
        log(f"    -> {name:20s} R2={r['R2']:.4f}"); return r
    for tag,net,flat,key in [("LSTM",LSTMN(len(CH)),False,"LSTM"),("Transformer",TRFN(len(CH)),False,"Transformer"),
                              ("LSTM_hybrid",LSTMH(len(CH),Ztr.shape[1]),True,"LSTM_hybrid"),
                              ("Transformer_hybrid",TRFH(len(CH),Ztr.shape[1]),True,"Transformer_hybrid")]:
        log(f"[nn] {tag} ...")
        xtr=[Str]+([Ztr] if flat else []); xva=[Sva]+([Zva] if flat else [])
        mm=fit(net,xtr,ytr_r,xva,yva_r,40,256,7e-4)
        ite_in=[torch.tensor(Ste)]+([torch.tensor(Zte)] if flat else [])
        with torch.no_grad(): pr=bt+mm(*ite_in).numpy()
        site_preds[key]=pr; rows.append(met(pr,tag))
    preds_all[site]=dict(y=yt,b=bt,**site_preds)
    pd.DataFrame(rows).to_csv(DONE_CSV,index=False)
    np.savez(os.path.join(OUT,"arch_preds_6situs_mean.npz"), **{f"{s}__{k}":v for s,d in preds_all.items() for k,v in d.items()})
    log(f"  {site} selesai ({time.time()-t0:.0f}s)")

seq=pd.DataFrame(rows)
seq.to_csv(os.path.join(OUT,"seq_6situs_mean.csv"),index=False)
log("\n== SEQUENCE 6 SITUS (R2, target mean) ==\n"+seq.to_string(index=False))
log(f"SELESAI Tahap 4b-seq dalam {time.time()-t0:.0f}s — lanjut merge via 04b_merge_mean.py")
