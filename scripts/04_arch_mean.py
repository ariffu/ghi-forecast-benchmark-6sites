# -*- coding: utf-8 -*-
"""Tahap 4m — head-to-head arsitektur, target RATA-RATA jam (headline), Bengkulu.
Tabular: LightGBM/CatBoost/XGBoost/MLP. Sequential: LSTM/Transformer (+hybrid).
Jalankan: python -u 04_arch_mean.py
"""
import os, sys, time, numpy as np, pandas as pd, lightgbm as lgb, xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, savefig, BASE
import matplotlib.pyplot as plt

def log(*a): print(*a, flush=True)
t0=time.time(); torch.set_num_threads(max(1,(os.cpu_count() or 4)-1)); torch.manual_seed(42); np.random.seed(42)
OUT=os.path.join(BASE,"04_arch_mean"); os.makedirs(OUT, exist_ok=True)
df, feats, yr = prepare()
itr,iva,ite = split_idx(df, yr, "mean")
tr,va,te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
ytr_r=(tr.y_mean-tr.base_mean).to_numpy(); yva_r=(va.y_mean-va.base_mean).to_numpy()
y=df.y_mean.to_numpy(); b=df.base_mean.to_numpy()
CH=["ghi_wm2","dhi_wm2","dni_wm2","kt","clp_cot","clp_cth_km","clp_ctt_k","clp_cer_um",
    "aws_temp_c","aws_rh_pct","aws_pressure_hpa","aws_wind_speed_ms","aws_rain_mm","solar_elev_deg"]
L=12; Xw=df[CH].to_numpy(float); n=len(df); W=np.full((n,L,len(CH)),np.nan); ar=np.arange(n)
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
log(f"prep ok ({time.time()-t0:.0f}s)")

preds={}; res=[]; curves={}
def met(p,name):
    r=dict(model=name,R2=round(r2_score(y[ite],p),4),MAE=round(mean_absolute_error(y[ite],p),2),
           RMSE=round(np.sqrt(mean_squared_error(y[ite],p)),2),
           skill=round(1-np.sqrt(mean_squared_error(y[ite],p))/np.sqrt(mean_squared_error(y[ite],b[ite])),4))
    log(f"    -> {name:20s} R2={r['R2']:.4f} MAE={r['MAE']:.1f} RMSE={r['RMSE']:.1f}"); return r
for nm in ["LightGBM","CatBoost","XGBoost"]:
    if nm=="LightGBM":
        m=lgb.LGBMRegressor(n_estimators=3000,learning_rate=0.03,num_leaves=63,min_child_samples=50,subsample=0.8,
                            subsample_freq=1,colsample_bytree=0.8,reg_alpha=0.1,reg_lambda=0.1,random_state=42,n_jobs=-1,verbose=-1)
        m.fit(tr[feats],ytr_r,eval_set=[(va[feats],yva_r)],callbacks=[lgb.early_stopping(100,verbose=False)])
        p=b[ite]+m.predict(te[feats])
    elif nm=="CatBoost":
        m=CatBoostRegressor(iterations=3000,learning_rate=0.03,depth=6,l2_leaf_reg=3.0,random_seed=42,od_type="Iter",od_wait=100,verbose=False)
        m.fit(tr[feats],ytr_r,eval_set=(va[feats],yva_r),use_best_model=True); p=b[ite]+m.predict(te[feats])
    else:
        m=xgb.XGBRegressor(n_estimators=3000,learning_rate=0.03,max_depth=6,subsample=0.8,colsample_bytree=0.8,
                           reg_alpha=0.1,reg_lambda=1.0,random_state=42,n_jobs=-1,early_stopping_rounds=100,eval_metric="rmse")
        m.fit(tr[feats],ytr_r,eval_set=[(va[feats],yva_r)],verbose=False)
        p=b[ite]+m.predict(te[feats])
    preds[nm]=p; res.append(met(p,nm)); log(f"    ({time.time()-t0:.0f}s)")

class MLP(nn.Module):
    def __init__(s,d): super().__init__(); s.f=nn.Sequential(nn.Linear(d,256),nn.ReLU(),nn.Dropout(0.2),nn.Linear(256,128),nn.ReLU(),nn.Dropout(0.2),nn.Linear(128,1))
    def forward(s,x): return s.f(x).squeeze(-1)
class LSTMN(nn.Module):
    def __init__(s,c,h=96): super().__init__(); s.l=nn.LSTM(c,h,2,batch_first=True,dropout=0.1); s.h=nn.Sequential(nn.Linear(h,64),nn.ReLU(),nn.Linear(64,1))
    def forward(s,x): o,_=s.l(x); return s.h(o[:,-1]).squeeze(-1)
class PosE(nn.Module):
    def __init__(s,d,L):
        super().__init__(); pe=torch.zeros(L,d); pos=torch.arange(L).unsqueeze(1).float()
        div=torch.exp(torch.arange(0,d,2).float()*(-np.log(10000.0)/d)); pe[:,0::2]=torch.sin(pos*div); pe[:,1::2]=torch.cos(pos*div); s.register_buffer("pe",pe.unsqueeze(0))
    def forward(s,x): return x+s.pe[:,:x.size(1)]
class TRFN(nn.Module):
    def __init__(s,c,d=64): super().__init__(); s.p=nn.Linear(c,d); s.pe=PosE(d,L); s.t=nn.TransformerEncoder(nn.TransformerEncoderLayer(d,4,128,dropout=0.1,batch_first=True),2); s.h=nn.Sequential(nn.Linear(d,64),nn.ReLU(),nn.Linear(64,1))
    def forward(s,x): z=s.t(s.pe(s.p(x))); return s.h(z[:,-1]).squeeze(-1)
class LSTMH(nn.Module):
    def __init__(s,c,d,h=96): super().__init__(); s.l=nn.LSTM(c,h,2,batch_first=True,dropout=0.1); s.h=nn.Sequential(nn.Linear(h+d,128),nn.ReLU(),nn.Dropout(0.2),nn.Linear(128,1))
    def forward(s,x,z): o,_=s.l(x); return s.h(torch.cat([o[:,-1],z],1)).squeeze(-1)
class TRFH(nn.Module):
    def __init__(s,c,d,dd=64): super().__init__(); s.p=nn.Linear(c,dd); s.pe=PosE(dd,L); s.t=nn.TransformerEncoder(nn.TransformerEncoderLayer(dd,4,128,dropout=0.1,batch_first=True),2); s.h=nn.Sequential(nn.Linear(dd+d,128),nn.ReLU(),nn.Dropout(0.2),nn.Linear(128,1))
    def forward(s,x,z): o=s.t(s.pe(s.p(x))); return s.h(torch.cat([o[:,-1],z],1)).squeeze(-1)

def fit(model,xtr,ytr_,xva,yva_,epochs,bs,lr,tag,patience=6):
    opt=torch.optim.Adam(model.parameters(),lr=lr); lf=nn.MSELoss()
    T=[torch.tensor(a) for a in xtr]; Y=torch.tensor(ytr_,dtype=torch.float32)
    V=[torch.tensor(a) for a in xva]; Yv=torch.tensor(yva_,dtype=torch.float32)
    best=np.inf; state=None; bad=0; tr_l=[]; va_l=[]
    for ep in range(1,epochs+1):
        model.train(); perm=torch.randperm(len(Y)); tot=0.0; nb=int(np.ceil(len(Y)/bs))
        for i in range(nb):
            j=perm[i*bs:(i+1)*bs]; opt.zero_grad(); l=lf(model(*[T[k][j] for k in range(len(T))]),Y[j]); l.backward(); opt.step(); tot+=l.item()*len(j)
        model.eval()
        with torch.no_grad(): v=lf(model(*V),Yv).item()
        tr_l.append(tot/len(Y)); va_l.append(v)
        if v<best-1e-4: best,state,bad=v,{k:t.clone() for k,t in model.state_dict().items()},0
        else:
            bad+=1
            if bad>=patience: break
    model.load_state_dict(state); model.eval(); curves[tag]=(tr_l,va_l); return model

log("[nn] MLP ...")
m=fit(MLP(Ztr.shape[1]),[Ztr],ytr_r,[Zva],yva_r,60,512,1e-3,"MLP")
with torch.no_grad(): p=b[ite]+m(torch.tensor(Zte)).numpy()
preds["MLP"]=p; res.append(met(p,"MLP"))
for tag,net,flat,key in [("LSTM",LSTMN(len(CH)),False,"LSTM"),("Transformer",TRFN(len(CH)),False,"Transformer"),
                          ("LSTM_hybrid",LSTMH(len(CH),Ztr.shape[1]),True,"LSTM_hybrid"),
                          ("Transformer_hybrid",TRFH(len(CH),Ztr.shape[1]),True,"Transf_hybrid")]:
    log(f"[nn] {tag} ...")
    xtr=[Str]+([Ztr] if flat else []); xva=[Sva]+([Zva] if flat else [])
    m=fit(net,xtr,ytr_r,xva,yva_r,40,256,7e-4,tag)
    ite_in=[torch.tensor(Ste)]+([torch.tensor(Zte)] if flat else [])
    with torch.no_grad(): pr=b[ite]+m(*ite_in).numpy()
    preds[key]=pr; res.append(met(pr,tag))
R=pd.DataFrame(res).sort_values("R2",ascending=False); R.to_csv(os.path.join(OUT,"arch_mean.csv"),index=False)
np.savez(os.path.join(OUT,"arch_preds_mean.npz"), y=y[ite], b=b[ite], **preds)
log("\n"+R.to_string(index=False))

yy=y[ite]; nb=3000; rng=np.random.default_rng(11); bi=rng.integers(0,len(yy),size=(nb,len(yy)))
def br(p):
    p=np.asarray(p,float); e=(yy-p)**2; ee=e[bi]; m=yy[bi].mean(1); return 1-ee.mean(1)/((yy[bi]-m[:,None])**2).mean(1)
base=br(preds["LightGBM"]); bs=[]
for k,v in preds.items():
    if k=="LightGBM": continue
    dr=br(v)-base; lo,hi=np.percentile(dr,[2.5,97.5])
    bs.append(dict(model=k,dR2=round(dr.mean(),4),CI_lo=round(lo,4),CI_hi=round(hi,4),signif=("YA" if lo>0 or hi<0 else "tidak")))
B=pd.DataFrame(bs).sort_values("dR2",ascending=False); B.to_csv(os.path.join(OUT,"arch_bootstrap_mean.csv"),index=False)
log("\n"+B.to_string(index=False))

fig,ax=plt.subplots(figsize=(7,4)); ax.bar(R.model,R.R2,color="teal"); ax.set_ylim(R.R2.min()-0.02, R.R2.max()+0.005)
for i,v in enumerate(R.R2): ax.text(i,v+0.0005,f"{v:.4f}",ha="center",fontsize=8)
ax.set_ylabel("R² (test 2025)"); ax.set_title("Konvergensi arsitektur — rata-rata jam (headline)"); plt.setp(ax.get_xticklabels(),rotation=20,ha="right",fontsize=8)
savefig(fig,"04_arch_bar_mean.png")
for tag,key in [("MLP","MLP"),("LSTM","LSTM"),("Transformer","Transformer"),("LSTM_hybrid","LSTM_hybrid"),("Transformer_hybrid","Transf_hybrid")]:
    if tag in curves and isinstance(curves[tag],tuple):
        tr_l,va_l=curves[tag]; fig,ax=plt.subplots(figsize=(5.6,3.2))
        ax.plot(range(1,len(tr_l)+1),tr_l,label="train"); ax.plot(range(1,len(va_l)+1),va_l,label="val")
        ax.set_xlabel("Epoch"); ax.set_ylabel("MSE"); ax.set_title(f"Kurva belajar {tag} (mean)"); ax.legend()
        savefig(fig,f"04_learning_{key}_mean.png")
log(f"SELESAI Tahap 4m dalam {time.time()-t0:.0f}s")
