# -*- coding: utf-8 -*-
"""Merge hasil target mean 6 situs: tabular (04c) + sequence (04b_seq) -> tabel 8x6 + plot."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import savefig, BASE
import matplotlib.pyplot as plt

OUT=os.path.join(BASE,"04b_arch_6situs_mean"); os.makedirs(OUT,exist_ok=True)
def log(*a): print(*a, flush=True)

tab_cb=pd.read_csv(os.path.join(BASE,"04c_mean_6situs","baseline_mean_6situs.csv"))   # CB, LGB
tab_xm=pd.read_csv(os.path.join(BASE,"04c_mean_6situs","DRAF_Methods_Results_Hourly_6Situs.csv"))  # XGB, MLP
seq=pd.read_csv(os.path.join(OUT,"seq_6situs_mean.csv"))

MODELS=["LightGBM","CatBoost","XGBoost","MLP","LSTM","Transformer","LSTM_hybrid","Transformer_hybrid"]
m=pd.DataFrame({"site":tab_cb.site})
m["LightGBM"]=tab_cb.LGB_R2.values
m["CatBoost"]=tab_cb.CB_R2.values
m["XGBoost"]=tab_xm.XGB_R2.values
m["MLP"]=tab_xm.MLP_R2.values
for mn in ["LSTM","Transformer","LSTM_hybrid","Transformer_hybrid"]:
    m[mn]=seq[seq.model==mn].set_index("site").loc[m.site,"R2"].values
m["SP_R2"]=tab_cb.SP_R2.values
m.to_csv(os.path.join(OUT,"arch_6situs_mean_merged.csv"),index=False)
log("\n== ARSITEKTUR 6 SITUS (R2, target mean) ==\n"+m.round(4).to_string(index=False))

P=m.set_index("site")[MODELS]
x=np.arange(len(P)); w=0.1
fig,ax=plt.subplots(figsize=(12,4.6))
for i,mn in enumerate(MODELS): ax.bar(x+i*w, P[mn], w, label=mn)
ax.axhline(0,color="k",lw=0.6); ax.set_xticks(x+len(MODELS)*w/2); ax.set_xticklabels(P.index, rotation=15)
ax.set_ylabel("R² (test 2025)"); ax.set_title("Arsitektur 6 situs — rata-rata jam (8 model)"); ax.legend(fontsize=7,ncol=4)
savefig(fig,"04b_arch_6situs_bar_mean.png")

spread=P.max(1)-P.min(1)
fig,ax=plt.subplots(figsize=(7,3.6)); ax.bar(P.index,spread,color="teal")
for i,v in enumerate(spread): ax.text(i,v+0.0003,f"{v:.4f}",ha="center",fontsize=8)
ax.set_ylabel("R² max − min (8 model)"); ax.set_title("Spread arsitektur per situs (target mean)"); ax.set_ylim(0,spread.max()*1.3)
savefig(fig,"04b_arch_spread_6situs_mean.png")
log("MERGE SELESAI")
