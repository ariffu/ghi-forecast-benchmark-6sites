# -*- coding: utf-8 -*-
"""Tahap 6m — stratifikasi target RATA-RATA jam, Bengkulu (LightGBM residual)."""
import os, sys, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.metrics import r2_score
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, savefig, BASE
import matplotlib.pyplot as plt

OUT=os.path.join(BASE,"06_strat_mean"); os.makedirs(OUT,exist_ok=True)
df,feats,yr=prepare()
itr,iva,ite=split_idx(df,yr,"mean")
tr,va,te=df.iloc[itr],df.iloc[iva],df.iloc[ite]
ytr_r=(tr.y_mean-tr.base_mean).to_numpy(); yva_r=(va.y_mean-va.base_mean).to_numpy()
m=lgb.LGBMRegressor(n_estimators=2000,learning_rate=0.03,num_leaves=63,min_child_samples=50,subsample=0.8,
                    subsample_freq=1,colsample_bytree=0.8,reg_alpha=0.1,reg_lambda=0.1,random_state=42,n_jobs=-1,verbose=-1)
m.fit(tr[feats],ytr_r,eval_set=[(va[feats],yva_r)],callbacks=[lgb.early_stopping(80,verbose=False)])
p=te.base_mean+m.predict(te[feats]); yt=te.y_mean.to_numpy()
kt=te.kt.to_numpy(); hr=te.ts_wib.dt.hour.to_numpy(); mon=te.ts_wib.dt.month.to_numpy()

def r2sub(mask): 
    if mask.sum()<50: return np.nan
    return r2_score(yt[mask],p[mask])
# kondisi langit
rows=[]
rows.append(("clear",r2sub(kt>0.65))); rows.append(("partly",r2sub((kt>0.30)&(kt<=0.65)))); rows.append(("overcast",r2sub(kt<=0.30)))
# musim
rows.append(("DJF",r2sub((mon==12)|(mon<=2)))); rows.append(("MAM",r2sub(np.isin(mon,[3,4,5]))))
rows.append(("JJA",r2sub(np.isin(mon,[6,7,8])))); rows.append(("SON",r2sub(np.isin(mon,[9,10,11]))))
# waktu
rows.append(("morning(6-10)",r2sub((hr>=6)&(hr<10)))); rows.append(("midday(10-14)",r2sub((hr>=10)&(hr<14))))
rows.append(("afternoon(14-18)",r2sub((hr>=14)&(hr<18))))
R=pd.DataFrame(rows,columns=["regime","R2"])
R.to_csv(os.path.join(OUT,"strat_mean.csv"),index=False)
print(R.to_string(index=False))
