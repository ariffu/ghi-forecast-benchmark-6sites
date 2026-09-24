# -*- coding: utf-8 -*-
"""
Tahap 10 — Multi-horizon h1..h6 (target titik t+k jam).
Protokol: filter solar_elev_deg>5 (origin) DAN solar_elev_hk>5 (target siang).
Model: LightGBM residual (semua situs) + CatBoost & MLP (Bengkulu, uji konvergensi).
Jalankan: python -u 10_multihorizon.py
"""
import os, sys, time, numpy as np, pandas as pd, lightgbm as lgb
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, savefig, BASE, SITES
import matplotlib.pyplot as plt

def log(*a): print(*a, flush=True)
t0=time.time(); torch.set_num_threads(max(1,(os.cpu_count() or 4)-1)); torch.manual_seed(42); np.random.seed(42)
OUT=os.path.join(BASE,"10_multihorizon"); os.makedirs(OUT,exist_ok=True)
H=[1,2,3,4,5,6]

class MLP(nn.Module):
    def __init__(s,d): super().__init__(); s.f=nn.Sequential(nn.Linear(d,256),nn.ReLU(),nn.Dropout(0.2),nn.Linear(256,128),nn.ReLU(),nn.Dropout(0.2),nn.Linear(128,1))
    def forward(s,x): return s.f(x).squeeze(-1)
def fit_mlp(Xtr,ytr,Xva,yva,epochs=35,bs=512,lr=1e-3,patience=5):
    m=MLP(Xtr.shape[1]); opt=torch.optim.Adam(m.parameters(),lr=lr); lf=nn.MSELoss()
    T=torch.tensor(Xtr);Y=torch.tensor(ytr,dtype=torch.float32);V=torch.tensor(Xva);Yv=torch.tensor(yva,dtype=torch.float32)
    best=np.inf;st=None;bad=0
    for _ in range(epochs):
        m.train();p=torch.randperm(len(T))
        for i in range(int(np.ceil(len(T)/bs))):
            j=p[i*bs:(i+1)*bs];opt.zero_grad();l=lf(m(T[j]),Y[j]);l.backward();opt.step()
        m.eval()
        with torch.no_grad():v=lf(m(V),Yv).item()
        if v<best-1e-4:best,st,bad=v,{k:t.clone() for k,t in m.state_dict().items()},0
        else:
            bad+=1
            if bad>=patience:break
    m.load_state_dict(st);m.eval();return m

rows=[]; bkl_rows=[]
for site in SITES:
    df,feats,yr=prepare(site)
    def run_k(k, model="lgb"):
        yc=f"ghi_actual_h{k}"; bc=f"smart_persist_h{k}"
        m=(df.solar_elev_deg>5)&(df[f"solar_elev_h{k}"]>5)&df[yc].notna()&df[bc].notna()
        idx=np.where(m.to_numpy())[0]
        itr,iva,ite=idx[yr[idx]<=2023],idx[yr[idx]==2024],idx[yr[idx]==2025]
        if len(ite)<200: return None
        tr,va,te=df.iloc[itr],df.iloc[iva],df.iloc[ite]
        yt,bt=te[yc].to_numpy(),te[bc].to_numpy()
        rsp=np.sqrt(mean_squared_error(yt,bt))
        out=dict(site=site,h=k,n_test=len(ite),SP_R2=round(r2_score(yt,bt),4))
        if model in ("lgb","cb"):
            if model=="lgb":
                mm=lgb.LGBMRegressor(n_estimators=3000,learning_rate=0.03,num_leaves=63,min_child_samples=50,subsample=0.8,
                                     subsample_freq=1,colsample_bytree=0.8,reg_alpha=0.1,reg_lambda=0.1,random_state=42,n_jobs=-1,verbose=-1)
                mm.fit(tr[feats],(tr[yc]-tr[bc]).to_numpy(),eval_set=[(va[feats],(va[yc]-va[bc]).to_numpy())],callbacks=[lgb.early_stopping(100,verbose=False)])
                p=bt+mm.predict(te[feats])
            else:
                mm=CatBoostRegressor(iterations=3000,learning_rate=0.03,depth=6,l2_leaf_reg=3.0,random_seed=42,od_type="Iter",od_wait=100,verbose=False)
                mm.fit(tr[feats],(tr[yc]-tr[bc]).to_numpy(),eval_set=(va[feats],(va[yc]-va[bc]).to_numpy()),use_best_model=True)
                p=bt+mm.predict(te[feats])
            out[f"{model}_R2"]=round(r2_score(yt,p),4); out[f"{model}_MAE"]=round(mean_absolute_error(yt,p),1)
            out[f"{model}_RMSE"]=round(np.sqrt(mean_squared_error(yt,p)),1); out[f"{model}_skill"]=round(1-np.sqrt(mean_squared_error(yt,p))/rsp,4)
        elif model=="mlp":
            med=tr[feats].median().fillna(0.0);mu=tr[feats].fillna(med).mean();sd=tr[feats].fillna(med).std().replace(0,1).fillna(1)
            sc=lambda X:(((X.fillna(med)-mu)/sd).astype("float64")).to_numpy(np.float32)
            mm=fit_mlp(sc(tr[feats]),(tr[yc]-tr[bc]).to_numpy(),sc(va[feats]),(va[yc]-va[bc]).to_numpy())
            with torch.no_grad(): p=bt+mm(torch.tensor(sc(te[feats]))).numpy()
            out["mlp_R2"]=round(r2_score(yt,p),4); out["mlp_MAE"]=round(mean_absolute_error(yt,p),1)
            out["mlp_RMSE"]=round(np.sqrt(mean_squared_error(yt,p)),1); out["mlp_skill"]=round(1-np.sqrt(mean_squared_error(yt,p))/rsp,4)
        return out
    for k in H:
        r=run_k(k,"lgb")
        if r: rows.append(r)
    log(f"  {site}: LGBM R2 per h = "+", ".join(f"h{r['h']}={r['lgb_R2']}" for r in rows if r['site']==site)+f" ({time.time()-t0:.0f}s)")
    if site=="bengkulu":
        for k in H:
            for mo in ("cb","mlp"):
                r=run_k(k,mo)
                if r: bkl_rows.append(r)
        log("  bengkulu cb/mlp selesai")

R=pd.DataFrame(rows); R.to_csv(os.path.join(OUT,"multihorizon_lgbm.csv"),index=False)
log("\n== LGBM 6 SITUS x h1..h6 (R2) ==\n"+R.pivot(index="site",columns="h",values="lgb_R2").to_string())
log("\n== n_test ==\n"+R.pivot(index="site",columns="h",values="n_test").to_string())
if bkl_rows:
    Bl=pd.DataFrame(bkl_rows).sort_values("h")
    # gabungkan kolom model pada baris bengkulu
    B=Bl.groupby("h",as_index=False).first()[["h","n_test","SP_R2"]].copy()
    for mo in ("lgb","cb","mlp"):
        sub=Bl[Bl[mo+"_R2"].notna()][["h",mo+"_R2"]] if (mo+"_R2") in Bl.columns else None
        if sub is not None: B=B.merge(sub,on="h",how="left")
    B.to_csv(os.path.join(OUT,"multihorizon_bengkulu_families.csv"),index=False)
    log("\n== BENGKULU per horizon (SP/LGBM/CatBoost/MLP) ==\n"+B.to_string(index=False))

# ---------- PLOT ----------
fig,ax=plt.subplots(figsize=(7,4))
for site in SITES:
    sub=R[R.site==site].sort_values("h")
    if len(sub): ax.plot(sub.h, sub.lgb_R2, "o-", label=site)
ax.set_xticks(H); ax.set_xlabel("Horizon (jam ke depan)"); ax.set_ylabel("R² (test 2025)")
ax.set_title("Degradasi akurasi per horizon — 6 situs (LightGBM)")
ax.legend(fontsize=8); savefig(fig,"10_degradation_r2.png")

fig,ax=plt.subplots(figsize=(7,4))
for site in SITES:
    sub=R[R.site==site].sort_values("h")
    if len(sub): ax.plot(sub.h, sub.lgb_skill, "o-", label=site)
ax.axhline(0,color="k",lw=0.8); ax.set_xticks(H); ax.set_xlabel("Horizon (jam)")
ax.set_ylabel("Skill vs smart-persistence"); ax.set_title("Skill vs horizon — 6 situs")
ax.legend(fontsize=8); savefig(fig,"10_degradation_skill.png")

if bkl_rows:
    fig,ax=plt.subplots(figsize=(7,4))
    for lbl,col in [("smart-persistence","SP_R2"),("LightGBM","lgb_R2"),("CatBoost","cb_R2"),("MLP","mlp_R2")]:
        if col in B.columns: ax.plot(B.h,B[col],"o-",label=lbl)
    ax.set_xticks(H); ax.set_xlabel("Horizon (jam)"); ax.set_ylabel("R² (test 2025)")
    ax.set_title("Konvergensi keluarga model per horizon — Bengkulu"); ax.legend(fontsize=8)
    savefig(fig,"10_bengkulu_families.png")
log(f"SELESAI Tahap 10 dalam {time.time()-t0:.0f}s")