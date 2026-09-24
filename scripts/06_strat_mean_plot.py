# -*- coding: utf-8 -*-
"""Tahap 6m-plot — plot stratifikasi target RATA-RATA jam Bengkulu (R2 per jam + skill regime)."""
import os, sys, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.metrics import r2_score
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, savefig, BASE
import matplotlib.pyplot as plt

df,feats,yr=prepare()
itr,iva,ite=split_idx(df,yr,"mean")
tr,va,te=df.iloc[itr],df.iloc[iva],df.iloc[ite]
ytr_r=(tr.y_mean-tr.base_mean).to_numpy(); yva_r=(va.y_mean-va.base_mean).to_numpy()
m=lgb.LGBMRegressor(n_estimators=2000,learning_rate=0.03,num_leaves=63,min_child_samples=50,subsample=0.8,
                    subsample_freq=1,colsample_bytree=0.8,reg_alpha=0.1,reg_lambda=0.1,random_state=42,n_jobs=-1,verbose=-1)
m.fit(tr[feats],ytr_r,eval_set=[(va[feats],yva_r)],callbacks=[lgb.early_stopping(80,verbose=False)])
p=te.base_mean+m.predict(te[feats]); yt=te.y_mean.to_numpy()
kt=te.kt.to_numpy(); hr=te.ts_wib.dt.hour.to_numpy()

def r2sub(mask):
    if mask.sum()<50: return np.nan
    return r2_score(yt[mask],p[mask])

# R2 per jam
hh=[]; 
for h in range(6,19):
    s=hr==h
    if s.sum()<50: continue
    hh.append((h,r2_score(yt[s],p[s])))
H=pd.DataFrame(hh,columns=["hour","R2"])
fig,ax=plt.subplots(figsize=(6.5,3.2)); ax.bar(H.hour,H.R2,color="teal")
ax.set_ylim(0,1); ax.set_xlabel("Jam (WIB)"); ax.set_ylabel("R² (test 2025)")
ax.set_title("R² per jam — Bengkulu (target rata-rata jam)")
savefig(fig,"06_r2_by_hour_mean.png")

# skill regime (clear/partly/overcast)
regs=[("clear",kt>0.65),("partly",(kt>0.30)&(kt<=0.65)),("overcast",kt<=0.30)]
names=[r[0] for r in regs]; vals=[r2sub(r[1]) for r in regs]
fig,ax=plt.subplots(figsize=(5.5,3.4)); ax.bar(names,vals,color="seagreen")
ax.set_ylim(0,1); ax.set_ylabel("R² (test 2025)"); ax.set_title("Skill per kondisi langit — Bengkulu (mean)")
savefig(fig,"06_skill_regime_mean.png")
print("plot strat mean selesai")
