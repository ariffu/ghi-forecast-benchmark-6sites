# -*- coding: utf-8 -*-
"""Tahap 114 a5 — R² validasi 2024 LightGBM (konfigurasi ablasi tahap 27) dengan 44 prediktor P2F vs semua kandidat (104 kolom + clp_cloud_frac). Hanya membaca."""
import os, sys, json, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.metrics import r2_score
_V = r"C:\Users\ariff\Documents\Balai_data_v6_10"; assert os.environ.get("FEATSET") == "P2F"
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); sys.path.insert(0, B)
import _common
from _common import prepare, split_idx, SITES, LEADS, SP
DROP = set(["site_id", "ts_wib", "ghi_origin", "has_source_row", "aod_500nm", "angstrom_exp", "smart_persist", "smart_persist_avg", "kt_clearness"]) | set(LEADS) | set(SP)
rows = []
for s in SITES:
    raw = pd.read_parquet(os.path.join(_common.DATA, f"{s}_full.parquet"), columns=None); cand = [c for c in raw.columns if c not in DROP]; assert len(cand) == 104; del raw
    df, feats, yr = prepare(s, l_filter=5); assert len(feats) == 44; semua = cand + ["clp_cloud_frac"]
    itr, iva, ite = split_idx(df, yr, "mean"); tr, va = df.iloc[itr], df.iloc[iva]
    ytr, yva = (tr.y_mean - tr.base_mean).to_numpy(), (va.y_mean - va.base_mean).to_numpy()
    out = {}
    for nama, fs in (("P2F_44", feats), ("semua_105", semua)):
        m = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=63, min_child_samples=50, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1, random_state=42, n_jobs=2, verbose=-1)
        m.fit(tr[fs], ytr, eval_set=[(va[fs], yva)], eval_metric="l2", callbacks=[lgb.early_stopping(80, verbose=False)])
        out[nama] = r2_score(va.y_mean, va.base_mean + m.predict(va[fs]))
    rows.append(dict(site=s, val_R2_44=out["P2F_44"], val_R2_semua=out["semua_105"], selisih=out["P2F_44"] - out["semua_105"])); print(rows[-1], flush=True)
R = pd.DataFrame(rows); R.to_csv(os.path.join(HERE, "a5_seleksi.csv"), index=False); print(R.round(4).to_string(index=False))
json.dump(dict(selisih=[float(R.selisih.min()), float(R.selisih.max())]), open(os.path.join(HERE, "a5_seleksi.json"), "w"))
