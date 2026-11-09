# -*- coding: utf-8 -*-
"""Tahap 94: dampak clear-sky interval pada smart persistence (target rata-rata 1 jam, uji 2025, origin elevasi > 5°), V6 + clear-sky lama lawan V6.1. Tanpa model."""
import os, sys, numpy as np, pandas as pd
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, B)
os.environ["DATA_DIR"] = r"C:\Users\ariff\Documents\Balai_data_v6_1\00_data"
import _common
from sklearn.metrics import r2_score, mean_squared_error
R = []
for lab, d in (("clear-sky lama (titik t)", os.path.join(B, "00_clearsky")), ("clear-sky V6.1 (interval)", r"C:\Users\ariff\Documents\Balai_data_v6_1\clearsky")):
    _common.CS_DIR = d
    for s in _common.SITES:
        df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean"); x = df.iloc[te]; y, b = x.y_mean.to_numpy(), x.base_mean.to_numpy(); h = x.ts_wib.dt.hour.to_numpy()
        e = lambda m: float(np.sqrt(np.mean((y[m] - b[m]) ** 2)))
        R.append(dict(clear_sky=lab, stasiun=s, n=len(te), R2_SP=round(r2_score(y, b), 4), RMSE_SP=round(e(np.ones(len(y), bool)), 1), RMSE_pagi_lt9=round(e(h < 9), 1), RMSE_sore_ge15=round(e(h >= 15), 1), bias_pagi=round(float(np.mean((b - y)[h < 9])), 1), bias_sore=round(float(np.mean((b - y)[h >= 15])), 1)))
T = pd.DataFrame(R); T.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "d4_persistence.csv"), index=False)
pd.set_option("display.width", 250); print(T.pivot(index="stasiun", columns="clear_sky", values=["R2_SP", "RMSE_SP", "bias_pagi", "bias_sore"]).to_string())
