# -*- coding: utf-8 -*-
"""Tahap 9m — sensitivitas protokol filter A/B/C pada target RATA-RATA jam, 6 situs (CatBoost)."""
import os, sys, numpy as np, pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, BASE, SITES

OUT=os.path.join(BASE,"09_sensitivity_mean"); os.makedirs(OUT,exist_ok=True)
def log(*a): print(*a, flush=True)
rows=[]
for site in SITES:
    df,feats,yr=prepare(site)
    y=df.y_mean.to_numpy(); b=df.base_mean.to_numpy(); X=df[feats]
    tr_idx=yr<=2023
    # train pada protokol A (origin elev>5, valid_mean)
    mA=(df.solar_elev_deg>5)&df.y_mean.notna()&df.base_mean.notna()&df.valid_mean
    itr=np.where((mA.to_numpy())&(yr<=2023))[0]; iva=np.where((mA.to_numpy())&(yr==2024))[0]
    med=X.iloc[itr].median().fillna(0.0)
    cb=CatBoostRegressor(iterations=2500,learning_rate=0.03,depth=6,loss_function="RMSE",verbose=0,random_seed=42)
    cb.fit(X.iloc[itr].fillna(med), y[itr]-b[itr], eval_set=(X.iloc[iva].fillna(med), y[iva]-b[iva]),
           early_stopping_rounds=200, use_best_model=True)
    def ev(mask,label):
        te=np.where((mask.to_numpy())&(yr==2025))[0]
        p=b[te]+cb.predict(X.iloc[te].fillna(med))
        return label,len(te),round(r2_score(y[te],p),4)
    a=ev(mA,"A")
    mB=(df.solar_elev_deg>5)&(df.solar_elev_h1>5)&df.y_mean.notna()&df.base_mean.notna()&df.valid_mean
    be=ev(mB,"B")
    mC=(mA)&(df.ghi_origin=="measured")
    c=ev(mC,"C")
    rows.append(dict(site=site,A_n=a[1],A_r2=a[2],B_n=be[1],B_r2=be[2],C_n=c[1],C_r2=c[2]))
    log(f"  {site:10s} A={a[0]} n={a[1]} r2={a[2]:.4f} | B={be[0]} n={be[1]} r2={be[2]:.4f} | C={c[0]} n={c[1]} r2={c[2]:.4f}")
R=pd.DataFrame(rows); R.to_csv(os.path.join(OUT,"sensitivity_variants_mean.csv"),index=False)
print(R.to_string(index=False))
