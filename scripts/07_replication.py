# -*- coding: utf-8 -*-
"""
Tahap 8 — Replikasi 6 situs (target titik t+1h).
Per situs: baseline (LGBM/CatBoost/XGBoost/MLP) + ablasi kategori + plot.
Jalankan: python -u 07_replication.py
"""
import os, sys, time, json, numpy as np, pandas as pd, lightgbm as lgb, xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, savefig, fig_scatter, BASE, SITES
import matplotlib.pyplot as plt

def log(*a): print(*a, flush=True)
t0 = time.time(); torch.set_num_threads(max(1,(os.cpu_count() or 4)-1)); torch.manual_seed(42); np.random.seed(42)
OUT = os.path.join(BASE, "07_replication"); os.makedirs(OUT, exist_ok=True)

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
    T1=G["A"]+G["B"]+G["C1"]+G["C2"]; CLP=G["D"]; SYNOP=G["E"]; AWS=G["F"]
    SYNC=[c for c in SYNOP if c in ["synop_cloud_cover_oktas","synop_cl","synop_cm","synop_ch"]]
    return T1, CLP, AWS, SYNC, T4

class MLP(nn.Module):
    def __init__(s,d): super().__init__(); s.f=nn.Sequential(nn.Linear(d,256),nn.ReLU(),nn.Dropout(0.2),nn.Linear(256,128),nn.ReLU(),nn.Dropout(0.2),nn.Linear(128,1))
    def forward(s,x): return s.f(x).squeeze(-1)
def fit_mlp(Xtr,ytr,Xva,yva,epochs=40,bs=512,lr=1e-3,patience=5):
    m=MLP(Xtr.shape[1]); opt=torch.optim.Adam(m.parameters(),lr=lr); lf=nn.MSELoss()
    T=torch.tensor(Xtr); Y=torch.tensor(ytr,dtype=torch.float32); V=torch.tensor(Xva); Yv=torch.tensor(yva,dtype=torch.float32)
    best=np.inf; st=None; bad=0
    for ep in range(epochs):
        m.train(); p=torch.randperm(len(T))
        for i in range(int(np.ceil(len(T)/bs))):
            j=p[i*bs:(i+1)*bs]; opt.zero_grad(); l=lf(m(T[j]),Y[j]); l.backward(); opt.step()
        m.eval()
        with torch.no_grad(): v=lf(m(V),Yv).item()
        if v<best-1e-4: best,st,bad=v,{k:t.clone() for k,t in m.state_dict().items()},0
        else:
            bad+=1
            if bad>=patience: break
    m.load_state_dict(st); m.eval(); return m

baseline_rows=[]; abl_rows=[]
for site in SITES:
    log(f"\n===== {site} ({time.time()-t0:.0f}s) =====")
    try:
        df, feats, yr = prepare(site)
        itr,iva,ite = split_idx(df, yr, "point")
        tr,va,te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
        ytr_r=(tr.y_point-tr.base_point).to_numpy(); yva_r=(va.y_point-va.base_point).to_numpy()
        yt=te.y_point.to_numpy(); bt=te.base_point.to_numpy()
        rsp=np.sqrt(mean_squared_error(yt,bt))
        est_frac=float((te["ghi_origin"].to_numpy()!="measured").mean())
        baseline_rows.append(dict(site=site, n_test=len(te), est_frac=round(est_frac,4),
                                  SP_R2=round(r2_score(yt,bt),4)))
        def rec(model,r2,mae,rmse): baseline_rows[-1].update({f"{model}_R2":round(r2,4),f"{model}_MAE":round(mae,1),f"{model}_skill":round(1-rmse/rsp,4)})
        # trees
        m=lgb.LGBMRegressor(n_estimators=3000,learning_rate=0.03,num_leaves=63,min_child_samples=50,subsample=0.8,
                            subsample_freq=1,colsample_bytree=0.8,reg_alpha=0.1,reg_lambda=0.1,random_state=42,n_jobs=-1,verbose=-1)
        m.fit(tr[feats],ytr_r,eval_set=[(va[feats],yva_r)],callbacks=[lgb.early_stopping(100,verbose=False)])
        p=bt+m.predict(te[feats]); rec("LGBM",r2_score(yt,p),mean_absolute_error(yt,p),np.sqrt(mean_squared_error(yt,p)))
        m=xgb.XGBRegressor(n_estimators=3000,learning_rate=0.03,max_depth=6,subsample=0.8,colsample_bytree=0.8,
                           reg_alpha=0.1,reg_lambda=1.0,random_state=42,n_jobs=-1,early_stopping_rounds=100,eval_metric="rmse")
        m.fit(tr[feats],ytr_r,eval_set=[(va[feats],yva_r)],verbose=False)
        p=bt+m.predict(te[feats]); rec("XGB",r2_score(yt,p),mean_absolute_error(yt,p),np.sqrt(mean_squared_error(yt,p)))
        m=CatBoostRegressor(iterations=3000,learning_rate=0.03,depth=6,l2_leaf_reg=3.0,random_seed=42,od_type="Iter",od_wait=100,verbose=False)
        m.fit(tr[feats],ytr_r,eval_set=(va[feats],yva_r),use_best_model=True)
        p=bt+m.predict(te[feats]); rec("CatBoost",r2_score(yt,p),mean_absolute_error(yt,p),np.sqrt(mean_squared_error(yt,p)))
        # MLP
        med=tr[feats].median().fillna(0.0); mu=tr[feats].fillna(med).mean(); sd=tr[feats].fillna(med).std().replace(0,1).fillna(1)
        sc=lambda X: (((X.fillna(med)-mu)/sd).astype("float64")).to_numpy(np.float32)
        mm=fit_mlp(sc(tr[feats]),ytr_r,sc(va[feats]),yva_r)
        with torch.no_grad(): p=bt+mm(torch.tensor(sc(te[feats]))).numpy()
        rec("MLP",r2_score(yt,p),mean_absolute_error(yt,p),np.sqrt(mean_squared_error(yt,p)))
        log(f"  {site}: LGBM={baseline_rows[-1]['LGBM_R2']} XGB={baseline_rows[-1]['XGB_R2']} CB={baseline_rows[-1]['CatBoost_R2']} MLP={baseline_rows[-1]['MLP_R2']} SP={baseline_rows[-1]['SP_R2']}")

        # ablasi
        T1,CLP,AWS,SYNC,T4=tiers(feats)
        def abl(name,fs):
            mm=lgb.LGBMRegressor(n_estimators=2000,learning_rate=0.03,num_leaves=63,min_child_samples=50,subsample=0.8,
                                 subsample_freq=1,colsample_bytree=0.8,reg_alpha=0.1,reg_lambda=0.1,random_state=42,n_jobs=-1,verbose=-1)
            mm.fit(tr[fs],ytr_r,eval_set=[(va[fs],yva_r)],eval_metric="l2",callbacks=[lgb.early_stopping(80,verbose=False)])
            return r2_score(yt, bt+mm.predict(te[fs]))
        r_t1=abl("T1",T1); r_clp=abl("T1+CLP",T1+CLP); r_aws=abl("T1+AWS",T1+AWS); r_syn=abl("T1+SYNC",T1+SYNC)
        abl_rows.append(dict(site=site, T1=round(r_t1,4), T1_CLP=round(r_clp,4), T1_AWS=round(r_aws,4),
                             T1_SYNOPcloud=round(r_syn,4), dCLP=round(r_clp-r_t1,4), dAWS=round(r_aws-r_t1,4),
                             dSYNOP=round(r_syn-r_t1,4)))
        log(f"  ablasi: ΔCLP={abl_rows[-1]['dCLP']:+.4f} ΔAWS={abl_rows[-1]['dAWS']:+.4f} ΔSYNOP={abl_rows[-1]['dSYNOP']:+.4f}")
    except Exception as e:
        log(f"  GAGAL {site}: {e}")

B=pd.DataFrame(baseline_rows); A=pd.DataFrame(abl_rows)
B.to_csv(os.path.join(OUT,"replication_baseline.csv"),index=False)
A.to_csv(os.path.join(OUT,"replication_ablation.csv"),index=False)
log("\n== BASELINE 6 SITUS ==\n"+B.to_string(index=False))
log("\n== ABLASI 6 SITUS ==\n"+A.to_string(index=False))

# ---------- PLOT ----------
if len(B):
    mdl=["LGBM","XGB","CatBoost","MLP"]; x=np.arange(len(B)); w=0.2
    fig,ax=plt.subplots(figsize=(9,4))
    for i,mn in enumerate(mdl): ax.bar(x+i*w, B[f"{mn}_R2"], w, label=mn)
    ax.axhline(0,color="k",lw=0.6); ax.set_xticks(x+1.5*w); ax.set_xticklabels(B.site, rotation=15)
    ax.set_ylabel("R² (test 2025)"); ax.set_title("Replikasi 6 situs — baseline titik t+1h"); ax.legend(fontsize=8)
    savefig(fig,"08_replication_baseline.png")
if len(A):
    x=np.arange(len(A)); fig,ax=plt.subplots(figsize=(8,3.8))
    ax.bar(x-0.2, A.dCLP, 0.4, label="ΔR² +CLP", color="seagreen")
    ax.bar(x+0.2, A.dAWS, 0.4, label="ΔR² +AWS", color="gray")
    ax.axhline(0,color="k",lw=0.8); ax.set_xticks(x); ax.set_xticklabels(A.site, rotation=15)
    ax.set_ylabel("ΔR² vs T1 core"); ax.set_title("Kontribusi inkremental per situs"); ax.legend(fontsize=8)
    savefig(fig,"08_replication_ablation.png")
log(f"SELESAI Tahap 8 dalam {time.time()-t0:.0f}s")