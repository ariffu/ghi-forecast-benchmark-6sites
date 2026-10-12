# -*- coding: utf-8 -*-
"""
Tahap 4b (plot) — Visualisasi arsitektur 6 situs untuk manuskrip.
Membaca arch_6situs.csv + arch_preds_6situs.npz (hasil Tahap 4b) dan
menghasilkan semua plot pendukung. Jalankan setelah 04b_arch_6situs.py.
Jalankan: python -u 04b_arch_6situs_plot.py
"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import savefig, fig_scatter, BASE, SITES
import matplotlib.pyplot as plt

OUT=os.path.join(BASE,"04b_arch_6situs")
R=pd.read_csv(os.path.join(OUT,"arch_6situs.csv"))
Z=np.load(os.path.join(OUT,"arch_preds_6situs.npz"),allow_pickle=True)
MODELS=["LightGBM","CatBoost","XGBoost","MLP","LSTM","Transformer","LSTM_hybrid","Transformer_hybrid"]
P=R.pivot_table(index="site",columns="model",values="R2")[MODELS]

# 1) grouped bar per situs (8 model)
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

# 3) scatter terbaik per situs (CatBoost) untuk manuskrip
for site in SITES:
    if f"{site}__y" not in Z.files: 
        print(f"  (skip scatter {site}: prediksi tidak tersedia)"); continue
    y=Z[f"{site}__y"]; p=Z[f"{site}__CatBoost"]
    fig=fig_scatter(y,p,f"{site} — CatBoost titik t+1h R²={P.loc[site,'CatBoost']:.3f}")
    savefig(fig,f"04b_scatter_{site}.png")

# 4) scatter LSTM & Transformer per situs (bukti sequence bekerja)
for site in SITES:
    if f"{site}__y" not in Z.files: continue
    y=Z[f"{site}__y"]
    for key in ["LSTM","Transformer"]:
        p=Z[f"{site}__{key}"]
        fig=fig_scatter(y,p,f"{site} — {key} titik t+1h R²={P.loc[site,key]:.3f}")
        savefig(fig,f"04b_scatter_{key}_{site}.png")

# 5) tabel ringkas R2 (untuk manuskrip) -> csv
P.round(4).to_csv(os.path.join(OUT,"arch_6situs_R2_matrix.csv"))
print("SELESAI plot Tahap 4b")
