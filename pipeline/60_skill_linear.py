# -*- coding: utf-8 -*-
"""Tahap 60 — skill terhadap smart persistence dan pembanding linear untuk perbandingan arsitektur (rekomendasi 1 audit, LAPORAN §24).

Desain terkunci sebelum hasil: 60_skill_linear/DESAIN_60.md.
- Skill = 1 − RMSE/RMSE_SP; R² residual = 1 − SSE/Σ(r − r̄)², r = y − SP (uji 2025, protokol A, target rata-rata jam).
- Ridge pada 43 prediktor, target residual y − SP (NaN -> median latih, standardisasi latih), α dari {1e-2 … 1e5} dipilih pada validasi 2024.
- Bootstrap blok harian berpasangan CatBoost − linear dan LightGBM − linear.
Keluaran: 60_skill_linear/{skill_6situs.csv, linear_ridge.csv, boot_vs_linear.csv, preds_linear.npz}.
Jalankan: FEATSET=P2 CLEARSKY=IP PYTHONIOENCODING=utf-8 python -u 60_skill_linear.py
"""
import os, sys, time, json, numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
B = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, B)
import _common
from _common import split_idx, SITES
from _blockboot import delta_r2
assert _common.FEATSET == "P2" and _common.CLEARSKY == "IP", "tahap 60: 43 prediktor dan Ineichen–Perez"
OUT = os.path.join(B, "60_skill_linear"); PR = os.path.join(B, "36_multiseed", "preds"); t0 = time.time()
M8 = ["LightGBM", "CatBoost", "XGBoost", "MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"]
ALPHAS = [10.0 ** k for k in range(-2, 6)]
def log(*a): print(*a, flush=True)
def rmse(y, p): return float(np.sqrt(np.mean((y - p) ** 2)))
rd = lambda *p: pd.read_csv(os.path.join(B, *p))
c4 = rd("04c_mean_6situs", "baseline_mean_6situs.csv").set_index("site")
xm = rd("04c_mean_6situs", "baseline_mean_6situs_xgb_mlp.csv").set_index("site")
sq = rd("04b_arch_6situs_mean", "seq_6situs_mean.csv").set_index(["site", "model"])
mm = rd("04b_arch_6situs_mean", "arch_6situs_mean_merged.csv").set_index("site")
def csv_metrics(s, m):                                   # R², RMSE, MAE, skill dari CSV pipeline
    if m == "CatBoost": q = c4.loc[s]; return q.CB_R2, q.CB_RMSE, q.CB_MAE, q.CB_skill
    if m == "LightGBM": q = c4.loc[s]; return q.LGB_R2, q.LGB_RMSE, q.LGB_MAE, q.LGB_skill
    if m in ("XGBoost", "MLP"): k = "XGB" if m == "XGBoost" else "MLP"; q = xm.loc[s]; return q[f"{k}_R2"], q[f"{k}_RMSE"], q[f"{k}_MAE"], q[f"{k}_skill"]
    q = sq.loc[(s, m)]; return q.R2, q.RMSE, q.MAE, q.skill

rows, lin, boot, P = [], [], [], {}
for s in SITES:
    df, feats, yr = _common.prepare(s); itr, iva, ite = split_idx(df, yr, "mean"); assert len(feats) == 43
    tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
    y, b = te.y_mean.to_numpy(float), te.base_mean.to_numpy(float); day = te.ts_wib.dt.date.astype(str).to_numpy()
    assert np.allclose(y, np.load(os.path.join(PR, f"six__{s}__y.npy"))) and (day == np.load(os.path.join(PR, f"six__{s}__day.npy"), allow_pickle=True)).all()
    n = len(y); rmse_sp = rmse(y, b); r = y - b; sst_r = float(np.sum((r - r.mean()) ** 2))
    assert abs(round(rmse_sp, 1) - c4.loc[s, "CB_RMSE_SP"]) < 0.05 + 1e-9 and abs(round(r2_score(y, b), 4) - c4.loc[s, "SP_R2"]) < 1e-4 + 1e-9
    # ---- ridge pada residual
    X = lambda d: d[feats].astype("float64")
    med = X(tr).median().fillna(0.0); mu = X(tr).fillna(med).mean(); sd = X(tr).fillna(med).std().replace(0, 1).fillna(1)
    Z = lambda d: ((X(d).fillna(med) - mu) / sd).to_numpy()
    Ztr, Zva, Zte = Z(tr), Z(va), Z(te); rtr = (tr.y_mean - tr.base_mean).to_numpy(float)
    vb = va.base_mean.to_numpy(float); vy = va.y_mean.to_numpy(float); best = None
    for a in ALPHAS:
        m = Ridge(alpha=a).fit(Ztr, rtr); v = r2_score(vy, vb + m.predict(Zva))
        lin.append(dict(site=s, alpha=a, val_R2=v))
        if best is None or v > best[0]: best = (v, a, m)
    p_lin = b + best[2].predict(Zte); P[f"{s}__linear"] = p_lin; P[f"{s}__y"] = y; P[f"{s}__b"] = b
    log(f"{s}: α terpilih {best[1]:g} (val R² {best[0]:.4f}{', DI TEPI GRID' if best[1] in (ALPHAS[0], ALPHAS[-1]) else ''}); uji R² linear {r2_score(y, p_lin):.4f}")
    def add(model, p=None, csv=None):
        if p is not None:
            R2, RM, MA = r2_score(y, p), rmse(y, p), float(np.mean(np.abs(y - p))); sk = 1 - RM / rmse_sp; r2r = 1 - float(np.sum((y - p) ** 2)) / sst_r
        else:
            R2, RM, MA, sk = csv; r2r = 1 - n * ((1 - sk) * rmse_sp) ** 2 / sst_r
        rows.append(dict(site=s, model=model, n=n, R2=R2, RMSE=RM, MAE=MA, skill=sk, R2_residual=r2r, source="prediksi" if p is not None else "CSV"))
    add("SmartPersistence", b); add("Linear", p_lin)
    for m in M8:
        cm = csv_metrics(s, m); f = os.path.join(PR, f"six__{s}__{m}__pipe.npy")
        if os.path.exists(f):
            p = np.load(f); yy = np.load(os.path.join(PR, f"six__{s}__y_mlp.npy")) if m == "MLP" else y
            assert np.allclose(yy, y), f"{s} {m}: urutan y berbeda"
            add(m, p); q = rows[-1]
            ok = abs(q["R2"] - cm[0]) < 1e-4 + 1e-9 and abs(q["skill"] - cm[3]) < 1e-4 + 1e-9
            log(f"  reproduksi {m:18s} R² {q['R2']:.4f} vs CSV {cm[0]:.4f}; skill {q['skill']:.4f} vs {cm[3]:.4f} {'OK' if ok else 'BEDA'}"); assert ok
            P[f"{s}__{m}"] = p
        else:
            add(m, csv=cm)
        assert abs(rows[-1]["R2"] - float(mm.loc[s, m])) < 1e-4 + 1e-9, f"{s} {m}: R² beda dengan tabel 8×6"
    for m in ["CatBoost", "LightGBM"]:
        q = delta_r2(y, P[f"{s}__{m}"], p_lin, day, record=False)
        boot.append(dict(site=s, model=m, vs="Linear", dR2=q["dR2"], blk_lo=q["blk_lo"], blk_hi=q["blk_hi"], sig_block=q["sig_block"]))
        log(f"  {m} − linear: ΔR² {q['dR2']:+.4f} [{q['blk_lo']:+.4f}, {q['blk_hi']:+.4f}] sig={q['sig_block']}")
    del df, tr, va, te

S = pd.DataFrame(rows); S.to_csv(os.path.join(OUT, "skill_6situs.csv"), index=False)
pd.DataFrame(lin).to_csv(os.path.join(OUT, "linear_ridge.csv"), index=False)
BT = pd.DataFrame(boot); BT.to_csv(os.path.join(OUT, "boot_vs_linear.csv"), index=False)
np.savez(os.path.join(OUT, "preds_linear.npz"), **P)
au = rd("54_audit", "C_pembanding.csv").set_index("site")
w = S.pivot(index="site", columns="model", values="skill").loc[SITES]; r2w = S.pivot(index="site", columns="model", values="R2").loc[SITES]
log("\nperbandingan dengan audit 54 (ridge, grid α audit):", ", ".join(f"{s} {r2w.loc[s, 'Linear']:.4f}/{au.loc[s, 'R2_ridge43']:.4f}" for s in SITES))
log("spread R² 8 arsitektur:", (r2w[M8].max(1) - r2w[M8].min(1)).round(4).to_dict())
log("spread skill 8 arsitektur:", (w[M8].max(1) - w[M8].min(1)).round(4).to_dict())
log(f"SELESAI tahap 60 dalam {time.time() - t0:.0f}s")
