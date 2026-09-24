# -*- coding: utf-8 -*-
"""
Tahap 4b — Replikasi ARSITEKTUR LENGKAP ke 6 situs (target titik t+1h).
Melengkapi open-item #1: LSTM/Transformer (sequence) kini di semua 6 situs,
bukan hanya Bengkulu. 8 arsitektur per situs:
  tabular : LightGBM, CatBoost, XGBoost, MLP
  sequence: LSTM, Transformer (+ hybrid dengan vektor flat 104 fitur)
Window sequence = 12 langkah x 14 kanal (2 jam sejarah), identik dengan
04_architectures_v2.py agar konsisten dengan angka Bengkulu.
Jalankan: python -u 04b_arch_6situs.py
"""
import os, sys, time, numpy as np, pandas as pd, lightgbm as lgb, xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, savefig, fig_scatter, BASE, SITES
import matplotlib.pyplot as plt

def log(*a): print(*a, flush=True)
t0=time.time(); torch.set_num_threads(max(1,(os.cpu_count() or 4)-1)); torch.manual_seed(42); np.random.seed(42)
OUT=os.path.join(BASE,"04b_arch_6situs"); os.makedirs(OUT, exist_ok=True)

CH=["ghi_wm2","dhi_wm2","dni_wm2","kt","clp_cot","clp_cth_km","clp_ctt_k","clp_cer_um",
    "aws_temp_c","aws_rh_pct","aws_pressure_hpa","aws_wind_speed_ms","aws_rain_mm","solar_elev_deg"]
L=12

def lgbm(**kw):
    return lgb.LGBMRegressor(n_estimators=3000,learning_rate=0.03,num_leaves=63,min_child_samples=50,
                             subsample=0.8,subsample_freq=1,colsample_bytree=0.8,reg_alpha=0.1,
                             reg_lambda=0.1,random_state=42,n_jobs=-1,verbose=-1,**kw)

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
    model.load_state_dict(state); model.eval(); return model, (tr_l,va_l)

rows=[]; curves={}; preds_all={}
# --- resume: muat hasil yang sudah ada (per-situs) ---
DONE_CSV=os.path.join(OUT,"arch_6situs.csv")
if os.path.exists(DONE_CSV):
    done=pd.read_csv(DONE_CSV); rows=done.to_dict("records")
    done_sites=set(done.site.unique())
else:
    done_sites=set()
for site in SITES:
    if site in done_sites:
        log(f"===== {site} SKIP (sudah selesai) ====="); continue
    log(f"\n===== {site} ({time.time()-t0:.0f}s) =====")
    df,feats,yr=prepare(site)
    itr,iva,ite=split_idx(df,yr,"point")
    tr,va,te=df.iloc[itr],df.iloc[iva],df.iloc[ite]
    ytr_r=(tr.y_point-tr.base_point).to_numpy(); yva_r=(va.y_point-va.base_point).to_numpy()
    y=df.y_point.to_numpy(); b=df.base_point.to_numpy()
    yt=y[ite]; bt=b[ite]; rsp=np.sqrt(mean_squared_error(yt,bt))
    # window sequence
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
        log(f"    -> {name:20s} R2={r['R2']:.4f} MAE={r['MAE']:.1f} RMSE={r['RMSE']:.1f}"); return r
    # tabular
    m=lgbm(); m.fit(tr[feats],ytr_r,eval_set=[(va[feats],yva_r)],callbacks=[lgb.early_stopping(100,verbose=False)])
    p=bt+m.predict(te[feats]); site_preds["LightGBM"]=p; rows.append(met(p,"LightGBM"))
    m=CatBoostRegressor(iterations=3000,learning_rate=0.03,depth=6,l2_leaf_reg=3.0,random_seed=42,od_type="Iter",od_wait=100,verbose=False)
    m.fit(tr[feats],ytr_r,eval_set=(va[feats],yva_r),use_best_model=True); p=bt+m.predict(te[feats]); site_preds["CatBoost"]=p; rows.append(met(p,"CatBoost"))
    m=xgb.XGBRegressor(n_estimators=3000,learning_rate=0.03,max_depth=6,subsample=0.8,colsample_bytree=0.8,
                       reg_alpha=0.1,reg_lambda=1.0,random_state=42,n_jobs=-1,early_stopping_rounds=100,eval_metric="rmse")
    m.fit(tr[feats],ytr_r,eval_set=[(va[feats],yva_r)],verbose=False); p=bt+m.predict(te[feats]); site_preds["XGBoost"]=p; rows.append(met(p,"XGBoost"))
    # MLP
    mm,cr=fit(MLP(Ztr.shape[1]),[Ztr],ytr_r,[Zva],yva_r,60,512,1e-3,"MLP")
    with torch.no_grad(): p=bt+mm(torch.tensor(Zte)).numpy()
    site_preds["MLP"]=p; rows.append(met(p,"MLP")); curves[(site,"MLP")]=cr
    # sequence
    for tag,net,flat,key in [("LSTM",LSTMN(len(CH)),False,"LSTM"),("Transformer",TRFN(len(CH)),False,"Transformer"),
                              ("LSTM_hybrid",LSTMH(len(CH),Ztr.shape[1]),True,"LSTM_hybrid"),
                              ("Transformer_hybrid",TRFH(len(CH),Ztr.shape[1]),True,"Transformer_hybrid")]:
        xtr=[Str]+([Ztr] if flat else []); xva=[Sva]+([Zva] if flat else [])
        mm,cr=fit(net,xtr,ytr_r,xva,yva_r,40,256,7e-4,tag)
        ite_in=[torch.tensor(Ste)]+([torch.tensor(Zte)] if flat else [])
        with torch.no_grad(): pr=bt+mm(*ite_in).numpy()
        site_preds[key]=pr; rows.append(met(pr,tag)); curves[(site,key)]=cr
    preds_all[site]=dict(y=yt,b=bt,**site_preds)
    log(f"  {site} selesai ({time.time()-t0:.0f}s)")
    # simpan inkremental per-situs (agar bisa resume bila timeout)
    pd.DataFrame(rows).to_csv(DONE_CSV,index=False)
    np.savez(os.path.join(OUT,"arch_preds_6situs.npz"), **{f"{s}__{k}":v for s,d in preds_all.items() for k,v in d.items()})

R=pd.DataFrame(rows); R.to_csv(DONE_CSV,index=False)
np.savez(os.path.join(OUT,"arch_preds_6situs.npz"), **{f"{s}__{k}":v for s,d in preds_all.items() for k,v in d.items()})
log("\n== ARSITEKTUR 6 SITUS (R2) ==\n"+R.pivot_table(index="site",columns="model",values="R2").to_string())

# ---------- PLOT ----------
MODELS=["LightGBM","CatBoost","XGBoost","MLP","LSTM","Transformer","LSTM_hybrid","Transformer_hybrid"]
# 1) grouped bar per situs
P=R.pivot_table(index="site",columns="model",values="R2")[MODELS]
x=np.arange(len(P)); w=0.1
fig,ax=plt.subplots(figsize=(12,4.6))
for i,mn in enumerate(MODELS): ax.bar(x+i*w, P[mn], w, label=mn)
ax.axhline(0,color="k",lw=0.6); ax.set_xticks(x+len(MODELS)*w/2); ax.set_xticklabels(P.index, rotation=15)
ax.set_ylabel("R² (test 2025)"); ax.set_title("Arsitektur 6 situs — titik t+1h (8 model)"); ax.legend(fontsize=7,ncol=4)
savefig(fig,"04b_arch_6situs_bar.png")
# 2) spread per situs (konvergensi)
spread=P.max(1)-P.min(1)
fig,ax=plt.subplots(figsize=(7,3.6)); ax.bar(P.index,spread,color="teal")
for i,v in enumerate(spread): ax.text(i,v+0.0003,f"{v:.4f}",ha="center",fontsize=8)
ax.set_ylabel("R² max − min (8 model)"); ax.set_title("Spread arsitektur per situs — konvergensi"); ax.set_ylim(0,spread.max()*1.25)
savefig(fig,"04b_arch_spread_6situs.png")
# 3) kurva belajar LSTM & Transformer per situs (contoh Bengkulu + satu lagi)
for site in ["bengkulu","kalbar"]:
    for key in ["LSTM","Transformer"]:
        if (site,key) in curves:
            tr_l,va_l=curves[(site,key)]; fig,ax=plt.subplots(figsize=(5.6,3.2))
            ax.plot(range(1,len(tr_l)+1),tr_l,label="train"); ax.plot(range(1,len(va_l)+1),va_l,label="val")
            ax.set_xlabel("Epoch"); ax.set_ylabel("MSE"); ax.set_title(f"Kurva belajar {key} — {site}"); ax.legend()
            savefig(fig,f"04b_learning_{key}_{site}.png")
# 4) scatter terbaik per situs (CatBoost) untuk manuskrip
for site in SITES:
    d=preds_all[site]; fig=fig_scatter(d["y"],d["CatBoost"],f"{site} — CatBoost titik t+1h R²={P.loc[site,'CatBoost']:.3f}")
    savefig(fig,f"04b_scatter_{site}.png")
log(f"SELESAI Tahap 4b dalam {time.time()-t0:.0f}s")
