# -*- coding: utf-8 -*-
"""Tahap 27 — (A) Semua uji signifikansi naskah diulang dengan BLOCK BOOTSTRAP HARIAN (_blockboot.py).

Prediksi yang belum tersimpan di-refit dengan konfigurasi IDENTIK skrip asli dan WAJIB mereproduksi CSV asli
(assert |ΔR²| < 1e-4) sebelum dipakai:
  1. §3.3 ablasi Bengkulu          = 03_ablation_mean.py           -> 5 pasangan
  2. §3.4 arsitektur Bengkulu       = 04_arch_mean/arch_preds_mean.npz (tanpa refit) -> 7 pasangan vs LightGBM
  3. §3.7 ablasi 6 situs           = 07b_replication_ablation_mean.py (+ T1+CLP+AWS, T1+CLP+SYNcloud)
  4. Table S5/S8 isian CLP          = 19_sens_clp_fill.py (00_data vs 00_data_rawfill)
Seed bootstrap 11, 2000 resampel, blok = tanggal WIB origin. Output: 27_block_bootstrap/*.csv, prediksi *.npz.
Jalankan: python -u 27_block_bootstrap.py
"""
import os, sys, time, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.metrics import r2_score
B = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, B)
import _common
from _common import split_idx, SITES
from _blockboot import delta_r2
OUT = os.path.join(B, "27_block_bootstrap"); os.makedirs(OUT, exist_ok=True)
t0 = time.time()
def log(*a): print(*a, flush=True)
def lgbm():
    return lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=63, min_child_samples=50, subsample=0.8, subsample_freq=1,
                             colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1, random_state=42, n_jobs=-1, verbose=-1)
def groups(feats):                                   # identik 03_ablation_mean.py / 07b
    def grp(f):
        if f.startswith("clp_"): return "D"
        if f.startswith("synop_"): return "E"
        if f.startswith("aws_"): return "F"
        if f.startswith(("clear_sky","solar_elev","decl_","eot_","is_day","elev_sin")): return "B"
        if f.startswith(("kt_lag","kt_delta","kt_roll","kt_std","kt_cooper")) or f=="kt": return "C2"
        if f.startswith(("ghi_lag","ghi_delta")): return "C1"
        if f.startswith(("ghi_wm2","dhi_","dni_","nett_","reflected","sunshine")): return "A"
        return "B"
    T4 = ([f for f in feats if f.startswith("accel_") or "_std_" in f] if os.environ.get("FEATSET", "P2") == "P0" else [])   # P2: kelompok eksperimental dilebur ke inti
    G = {g: [] for g in ["A","B","C1","C2","D","E","F"]}
    for f in feats:
        if f in T4: continue
        G[grp(f)].append(f)
    T1 = G["A"]+G["B"]+G["C1"]+G["C2"]; SYNC = [c for c in G["E"] if c in ["synop_cloud_cover_oktas","synop_cl","synop_cm","synop_ch"]]
    return T1, G["D"], G["E"], G["F"], SYNC, T4
def setup(site, folder="00_data"):
    _common.DATA = os.path.join(B, folder); df, feats, yr = _common.prepare(site)
    itr, iva, ite = split_idx(df, yr, "mean")
    tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
    S = dict(tr=tr, va=va, te=te, ytr=(tr.y_mean-tr.base_mean).to_numpy(), yva=(va.y_mean-va.base_mean).to_numpy(),
             y=te.y_mean.to_numpy(), b=te.base_mean.to_numpy(), day=te.ts_wib.dt.date.to_numpy())
    return S, feats
def run(S, fs):
    m = lgbm(); m.fit(S["tr"][fs], S["ytr"], eval_set=[(S["va"][fs], S["yva"])], eval_metric="l2", callbacks=[lgb.early_stopping(80, verbose=False)])
    return S["b"] + m.predict(S["te"][fs])
def check(name, got, ref):
    ok = abs(round(got, 4) - ref) < 1e-4 + 1e-9
    log(f"    reproduksi {name:28s} refit={got:.4f} csv={ref:.4f} {'OK' if ok else 'BEDA'}"); assert ok, name
def rec(rows, **kw):
    r = delta_r2(kw.pop("y"), kw.pop("pa"), kw.pop("pb"), kw.pop("day")); r.update(kw); rows.append(r); return r

# ---------------- 1. ablasi Bengkulu (03) ----------------
log("== 1. Ablasi Bengkulu (03_ablation_mean) ==")
S, feats = setup("bengkulu"); T1, CLP, SYN, AWS, SYNC, T4 = groups(feats)
ref03 = pd.read_csv(os.path.join(B, "03_ablation_mean", "ablation_mean.csv")).set_index("config")
cfg = {"T1 core": T1, "T1+CLP": T1+CLP, "T1+AWS_meteo": T1+AWS, "T1+CLP+AWS_meteo": T1+CLP+AWS, "T1+SYNOP_cloud": T1+SYNC,
       "T1+CLP+SYNOP_cloud": T1+CLP+SYNC, "FULL": T1+CLP+SYN+AWS+T4}
P = {}
for k, fs in cfg.items(): P[k] = run(S, fs); check(k, r2_score(S["y"], P[k]), ref03.loc[k, "test_R2"])
np.savez(os.path.join(OUT, "preds_ablation_bengkulu.npz"), y=S["y"], day=S["day"].astype(str), **P)
rows = []
for a, b_, lab in [("T1+CLP","T1 core","CLP effect"), ("T1+CLP+AWS_meteo","T1+CLP","AWS meteo | CLP"), ("T1+CLP+SYNOP_cloud","T1+CLP","SYNOP cloud | CLP"),
                   ("T1+CLP","T1+AWS_meteo","CLP vs AWS"), ("FULL","T1+CLP","remaining predictors"), ("T1+AWS_meteo","T1 core","AWS meteo (no CLP)"),
                   ("T1+SYNOP_cloud","T1 core","SYNOP cloud (no CLP)")]:
    rec(rows, y=S["y"], pa=P[a], pb=P[b_], day=S["day"], pair=f"{a} − {b_}", label=lab)
A1 = pd.DataFrame(rows); A1.to_csv(os.path.join(OUT, "ablation_bengkulu_block.csv"), index=False); log(A1.round(4).to_string(index=False))

# ---------------- 2. arsitektur Bengkulu (04_arch_mean, tanpa refit) ----------------
log("\n== 2. Arsitektur Bengkulu (04_arch_mean npz) ==")
Z = np.load(os.path.join(B, "04_arch_mean", "arch_preds_mean.npz")); assert np.allclose(Z["y"], S["y"])
rows = []
for m in ["CatBoost","XGBoost","MLP","Transformer","LSTM","LSTM_hybrid","Transf_hybrid"]:
    rec(rows, y=S["y"], pa=Z[m], pb=Z["LightGBM"], day=S["day"], model=m)
A2 = pd.DataFrame(rows); A2.to_csv(os.path.join(OUT, "arch_bengkulu_block.csv"), index=False); log(A2.round(4).to_string(index=False))

# ---------------- 3. ablasi 6 situs (07b) + 4. isian CLP (19) ----------------
log("\n== 3–4. Ablasi 6 situs (07b) + isian CLP (19) ==")
ref07 = pd.read_csv(os.path.join(B, "07_replication", "replication_ablation_mean.csv")).set_index("site")
ref19 = pd.read_csv(os.path.join(B, "19_sens_clp_fill", "sens_clp_fill.csv")); ref19r = ref19[ref19.variant.str.startswith("raw")].set_index("site")
rows3, rows4 = [], []
for s in SITES:
    log(f"  -- {s} ({time.time()-t0:.0f}s)")
    S, feats = setup(s); T1, CLP, SYN, AWS, SYNC, T4 = groups(feats)
    P = {k: run(S, fs) for k, fs in {"T1": T1, "T1+CLP": T1+CLP, "T1+AWS": T1+AWS, "T1+SYNcloud": T1+SYNC,
                                     "T1+CLP+AWS": T1+CLP+AWS, "T1+CLP+SYNcloud": T1+CLP+SYNC}.items()}
    for k, col in [("T1","T1"), ("T1+CLP","T1_CLP"), ("T1+AWS","T1_AWS"), ("T1+SYNcloud","T1_SYNOPcloud")]: check(f"{s} {k}", r2_score(S["y"], P[k]), ref07.loc[s, col])
    np.savez(os.path.join(OUT, f"preds_replication_{s}.npz"), y=S["y"], day=S["day"].astype(str), **P)
    for a, b_, lab in [("T1+CLP","T1","dCLP"), ("T1+AWS","T1","dAWS"), ("T1+SYNcloud","T1","dSYNOP"),
                       ("T1+CLP+AWS","T1+CLP","dAWS|CLP"), ("T1+CLP+SYNcloud","T1+CLP","dSYNOP|CLP")]:
        rec(rows3, y=S["y"], pa=P[a], pb=P[b_], day=S["day"], site=s, effect=lab)
    # 4. isian CLP mentah
    Sr, featsr = setup(s, "00_data_rawfill"); T1r, CLPr, *_ = groups(featsr)
    p1r, pcr = run(Sr, T1r), run(Sr, T1r + CLPr)
    check(f"{s} rawfill T1+CLP", r2_score(Sr["y"], pcr), ref19r.loc[s, "T1_CLP"]); assert np.allclose(Sr["y"], S["y"])
    rm = rec(rows4, y=S["y"], pa=P["T1+CLP"], pb=P["T1"], day=S["day"], site=s, variant="masked")
    rf = rec(rows4, y=S["y"], pa=pcr, pb=p1r, day=S["day"], site=s, variant="fill as-is")
A3 = pd.DataFrame(rows3); A3.to_csv(os.path.join(OUT, "replication_ablation_block.csv"), index=False)
A4 = pd.DataFrame(rows4); A4.to_csv(os.path.join(OUT, "clp_fill_block.csv"), index=False)
log(A3.round(4).to_string(index=False)); log(A4.round(4).to_string(index=False))
log(f"SELESAI tahap 27 dalam {time.time()-t0:.0f}s")
