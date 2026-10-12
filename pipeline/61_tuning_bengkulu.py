# -*- coding: utf-8 -*-
"""Tahap 61 — uji tuning hiperparameter LightGBM dan LSTM di Bengkulu (target rata-rata jam). Desain terkunci: 61_tuning/DESAIN_61.md.

Pencarian acak 30 konfigurasi per model (bawaan + 29 sampel, rng 2026), dipilih dengan R² validasi 2024; data, input, dan prosedur
pelatihan identik dengan 04_arch_mean.py / 36_multiseed_neural.py (bkl). LSTM terpilih dilatih ulang dengan seed 1–4.
Uji reproduksi (wajib): LightGBM bawaan = 04_arch_mean; LSTM bawaan seed 1 = 36_multiseed bkl LSTM s1.
Hasil per konfigurasi disimpan di 61_tuning/preds/ (dapat dilanjutkan). Ringkasan: 61_tuning/ringkasan_61.json, search_*.csv.
Jalankan: FEATSET=P2 CLEARSKY=IP PYTHONIOENCODING=utf-8 python -u 61_tuning_bengkulu.py > logs/61_tuning_bengkulu.log 2>&1
"""
import os, sys, time, json, numpy as np, pandas as pd, lightgbm as lgb, torch, torch.nn as nn
from sklearn.metrics import r2_score
B = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, B)
import _common
from _common import prepare, split_idx
from _blockboot import delta_r2
assert _common.FEATSET == "P2" and _common.CLEARSKY == "IP", "tahap 61: 43 prediktor dan Ineichen–Perez"
OUT = os.path.join(B, "61_tuning"); PD = os.path.join(OUT, "preds"); os.makedirs(PD, exist_ok=True)
PR36 = os.path.join(B, "36_multiseed", "preds")
N_CFG, SEEDS = 30, [1, 2, 3, 4]
CH = ["ghi_wm2","dhi_wm2","dni_wm2","kt","clp_cot","clp_cth_km","clp_ctt_k","clp_cer_um",
      "aws_temp_c","aws_rh_pct","aws_pressure_hpa","aws_wind_speed_ms","aws_rain_mm","solar_elev_deg"]
L = 12; t0 = time.time()
def log(*a): print(*a, flush=True)
torch.set_num_threads(max(1, (os.cpu_count() or 4) - 1))

# ---------------- data (identik 04_arch_mean / 36 bkl) ----------------
df, feats, yr = prepare("bengkulu"); itr, iva, ite = split_idx(df, yr, "mean")
tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
ytr_r = (tr.y_mean - tr.base_mean).to_numpy(); yva_r = (va.y_mean - va.base_mean).to_numpy()
yv, bv = va.y_mean.to_numpy(), va.base_mean.to_numpy(); yt, bt = te.y_mean.to_numpy(), te.base_mean.to_numpy()
day = te.ts_wib.dt.date.astype(str).to_numpy()
assert np.allclose(yt, np.load(os.path.join(PR36, "bkl__bengkulu__y.npy")))
Xw = df[CH].to_numpy(float); n = len(df); W = np.full((n, L, len(CH)), np.nan); ar = np.arange(n)
for t in range(L):
    k = L - 1 - t; W[:, t, :] = np.where((ar >= k)[:, None], np.roll(Xw, k, axis=0), np.nan)
medC = tr[CH].median().fillna(0.0); muC = tr[CH].fillna(medC).mean().to_numpy(); sdC = tr[CH].fillna(medC).std().replace(0, 1).fillna(1).to_numpy()
medw = np.nan_to_num(np.nanmedian(W[itr].reshape(-1, len(CH)), axis=0), nan=0.0)
def ps(ind):
    A = W[ind].copy(); m = np.isnan(A); A[m] = np.take(medw, np.where(m)[2]); return ((A - muC) / sdC).astype(np.float32)
Str, Sva, Ste = ps(itr), ps(iva), ps(ite)
log(f"data siap: latih {len(itr)}, validasi {len(iva)}, uji {len(ite)} ({time.time()-t0:.0f}s)")

# ---------------- model ----------------
class LSTMC(nn.Module):                     # bawaan (h=96, nl=2, dr=0.1, hw=64) = LSTMN di 04/36, urutan inisialisasi sama
    def __init__(s, c, h=96, nl=2, dr=0.1, hw=64):
        super().__init__(); s.l = nn.LSTM(c, h, nl, batch_first=True, dropout=dr if nl > 1 else 0.0); s.h = nn.Sequential(nn.Linear(h, hw), nn.ReLU(), nn.Linear(hw, 1))
    def forward(s, x): o, _ = s.l(x); return s.h(o[:, -1]).squeeze(-1)
def fit(model, xtr, ytr_, xva, yva_, epochs, bs, lr, patience=6):          # identik 36_multiseed_neural.fit
    opt = torch.optim.Adam(model.parameters(), lr=lr); lf = nn.MSELoss()
    T = [torch.tensor(a) for a in xtr]; Y = torch.tensor(ytr_, dtype=torch.float32)
    V = [torch.tensor(a) for a in xva]; Yv = torch.tensor(yva_, dtype=torch.float32)
    best = np.inf; state = None; bad = 0; ep_run = 0
    for ep in range(1, epochs + 1):
        ep_run = ep; model.train(); perm = torch.randperm(len(Y)); nb = int(np.ceil(len(Y) / bs))
        for i in range(nb):
            j = perm[i*bs:(i+1)*bs]; opt.zero_grad(); l = lf(model(*[T[k][j] for k in range(len(T))]), Y[j]); l.backward(); opt.step()
        model.eval()
        with torch.no_grad(): v = lf(model(*V), Yv).item()
        if v < best - 1e-4: best, state, bad = v, {k: t.clone() for k, t in model.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= patience: break
    model.load_state_dict(state); model.eval(); return model, ep_run
def run_lstm(cfg, seed):
    torch.manual_seed(seed); np.random.seed(seed)
    m, ep = fit(LSTMC(len(CH), cfg["hidden"], cfg["layers"], cfg["dropout"], cfg["head"]), [Str], ytr_r, [Sva], yva_r, 40, cfg["batch"], cfg["lr"])
    with torch.no_grad(): return bv + m(torch.tensor(Sva)).numpy(), bt + m(torch.tensor(Ste)).numpy(), ep
def run_lgb(cfg):
    p = {k: v for k, v in cfg.items() if k != "n_estimators"}
    m = lgb.LGBMRegressor(n_estimators=cfg["n_estimators"], subsample_freq=1, random_state=42, n_jobs=-1, verbose=-1, **p)
    m.fit(tr[feats], ytr_r, eval_set=[(va[feats], yva_r)], callbacks=[lgb.early_stopping(100, verbose=False)])
    return bv + m.predict(va[feats]), bt + m.predict(te[feats]), int(m.best_iteration_)

# ---------------- konfigurasi (bawaan + 29 acak, rng 2026; LightGBM dulu lalu LSTM) ----------------
rng = np.random.default_rng(2026); lu = lambda a, b: float(np.exp(rng.uniform(np.log(a), np.log(b))))
LGB = [dict(learning_rate=0.03, num_leaves=63, min_child_samples=50, subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1, n_estimators=3000)]
for _ in range(N_CFG - 1):
    LGB.append(dict(learning_rate=lu(0.01, 0.1), num_leaves=int(rng.choice([15, 31, 63, 127, 255])), min_child_samples=int(rng.choice([10, 20, 50, 100, 200])),
                    subsample=float(rng.uniform(0.5, 1.0)), colsample_bytree=float(rng.uniform(0.5, 1.0)), reg_alpha=lu(1e-3, 10), reg_lambda=lu(1e-3, 10), n_estimators=5000))
LST = [dict(hidden=96, layers=2, dropout=0.1, head=64, lr=7e-4, batch=256)]
for _ in range(N_CFG - 1):
    LST.append(dict(hidden=int(rng.choice([32, 64, 96, 128, 192])), layers=int(rng.choice([1, 2, 3])), dropout=float(rng.uniform(0, 0.4)),
                    head=int(rng.choice([32, 64, 128])), lr=lu(2e-4, 3e-3), batch=int(rng.choice([128, 256, 512]))))
json.dump(dict(LightGBM=LGB, LSTM=LST), open(os.path.join(OUT, "konfigurasi_61.json"), "w", encoding="utf-8"), indent=1)

# ---------------- uji reproduksi ----------------
pv, pt, it = run_lgb(LGB[0]); ref = np.load(os.path.join(PR36, "bkl__bengkulu__LightGBM__pipe.npy"))
ok = np.allclose(pt, ref, atol=1e-6) and round(r2_score(yt, pt), 4) == 0.9093
log(f"reproduksi LightGBM bawaan: R² {r2_score(yt, pt):.4f} vs 04_arch_mean 0.9093, prediksi sama={np.allclose(pt, ref, atol=1e-6)} {'OK' if ok else 'BEDA'}"); assert ok
np.savez(os.path.join(PD, "LightGBM__c00.npz"), val=pv, test=pt, it=it)
f_rep = os.path.join(PD, "LSTM__default__s1_reproduksi.npz")
if not os.path.exists(f_rep):
    pv1, pt1, ep1 = run_lstm(LST[0], 1); np.savez(f_rep, val=pv1, test=pt1, ep=ep1)
z = np.load(f_rep); ref = np.load(os.path.join(PR36, "bkl__bengkulu__LSTM__s1.npy"))
ok = np.allclose(z["test"], ref, atol=1e-4) and round(r2_score(yt, z["test"]), 4) == round(r2_score(yt, ref), 4)
log(f"reproduksi LSTM bawaan seed 1: R² {r2_score(yt, z['test']):.4f} vs tahap 36 {r2_score(yt, ref):.4f}, maks |Δp| {np.abs(z['test'] - ref).max():.2e} {'OK' if ok else 'BEDA'} ({time.time()-t0:.0f}s)")
assert ok, "LSTM bawaan tidak tereproduksi — pencarian dihentikan"

# ---------------- pencarian ----------------
def search(name, cfgs, runner):
    rows = []
    for c, cfg in enumerate(cfgs):
        f = os.path.join(PD, f"{name}__c{c:02d}.npz")
        if not os.path.exists(f):
            t1 = time.time(); pv_, pt_, k_ = runner(cfg); np.savez(f, val=pv_, test=pt_, it=k_, sec=time.time() - t1)
        z = np.load(f); rows.append(dict(model=name, config=c, **cfg, val_R2=r2_score(yv, z["val"]), test_R2=r2_score(yt, z["test"]), iters_or_epochs=int(z["it"]),
                                         seconds=float(z["sec"]) if "sec" in z.files else np.nan))
        log(f"  {name} c{c:02d}: val R² {rows[-1]['val_R2']:.4f} uji R² {rows[-1]['test_R2']:.4f} ({rows[-1]['iters_or_epochs']}) ({time.time()-t0:.0f}s)")
    S = pd.DataFrame(rows); S.to_csv(os.path.join(OUT, f"search_{name}.csv"), index=False); return S
SL = search("LightGBM", LGB, run_lgb)
SN = search("LSTM", LST, lambda cfg: run_lstm(cfg, 42))
bl, bn = int(SL.val_R2.idxmax()), int(SN.val_R2.idxmax())
log(f"terpilih: LightGBM c{bl:02d}, LSTM c{bn:02d}")
# LSTM terpilih: seed 1–4
tuned_lstm = [np.load(os.path.join(PD, f"LSTM__c{bn:02d}.npz"))["test"]]
for s in SEEDS:
    f = os.path.join(PD, f"LSTM__c{bn:02d}__s{s}.npz")
    if not os.path.exists(f):
        pv_, pt_, ep_ = run_lstm(LST[bn], s); np.savez(f, val=pv_, test=pt_, it=ep_)
    tuned_lstm.append(np.load(f)["test"]); log(f"  LSTM c{bn:02d} seed {s}: uji R² {r2_score(yt, tuned_lstm[-1]):.4f} ({time.time()-t0:.0f}s)")
def_lstm = [np.load(os.path.join(PR36, f"bkl__bengkulu__LSTM__{k}.npy")) for k in ["pipe", "s1", "s2", "s3", "s4"]]
lgb_def = np.load(os.path.join(PR36, "bkl__bengkulu__LightGBM__pipe.npy")); lgb_tun = np.load(os.path.join(PD, f"LightGBM__c{bl:02d}.npz"))["test"]

# ---------------- ringkasan ----------------
r2 = lambda p: float(r2_score(yt, p))
R_ld, R_lt = r2(lgb_def), r2(lgb_tun); R_nd, R_nt = [r2(p) for p in def_lstm], [r2(p) for p in tuned_lstm]
d_lgb = R_lt - R_ld; d_lstm = float(np.mean(R_nt) - np.mean(R_nd))
bl_ci = delta_r2(yt, lgb_tun, lgb_def, day, record=False); bn_ci = delta_r2(yt, np.mean(tuned_lstm, 0), np.mean(def_lstm, 0), day, record=False)
am = pd.read_csv(os.path.join(B, "04_arch_mean", "arch_mean.csv")); spread8 = float(am.R2.max() - am.R2.min())
mx = max(abs(d_lgb), abs(d_lstm)); rule = "U1" if (abs(d_lgb) < 0.005 and abs(d_lstm) < 0.005) else ("U3" if mx > 0.01 else "U2")
J = dict(n_cfg=N_CFG, selected=dict(LightGBM=dict(config=bl, **LGB[bl]), LSTM=dict(config=bn, **LST[bn])),
         n_better_val=dict(LightGBM=int((SL.val_R2 > SL.val_R2.iloc[0]).sum()), LSTM=int((SN.val_R2 > SN.val_R2.iloc[0]).sum())),
         val_R2=dict(LightGBM_default=float(SL.val_R2.iloc[0]), LightGBM_tuned=float(SL.val_R2.iloc[bl]), LSTM_default=float(SN.val_R2.iloc[0]), LSTM_tuned=float(SN.val_R2.iloc[bn])),
         test_R2=dict(LightGBM_default=R_ld, LightGBM_tuned=R_lt, LSTM_default_runs=R_nd, LSTM_tuned_runs=R_nt,
                      LSTM_default_mean=float(np.mean(R_nd)), LSTM_tuned_mean=float(np.mean(R_nt)), LSTM_default_sd=float(np.std(R_nd, ddof=1)), LSTM_tuned_sd=float(np.std(R_nt, ddof=1))),
         d_LightGBM=dict(dR2=d_lgb, blk_lo=bl_ci["blk_lo"], blk_hi=bl_ci["blk_hi"], sig=bl_ci["sig_block"]),
         d_LSTM=dict(dR2=d_lstm, ens_dR2=bn_ci["dR2"], blk_lo=bn_ci["blk_lo"], blk_hi=bn_ci["blk_hi"], sig=bn_ci["sig_block"]),
         gap_LGB_minus_LSTM=dict(default=R_ld - float(np.mean(R_nd)), tuned=R_lt - float(np.mean(R_nt))), spread8_bengkulu=spread8,
         order_reversed=bool(np.mean(R_nt) > R_lt), rule=rule, seconds=round(time.time() - t0))
json.dump(J, open(os.path.join(OUT, "ringkasan_61.json"), "w", encoding="utf-8"), indent=1)
log("\n" + json.dumps(J, indent=1)); log(f"SELESAI tahap 61 dalam {time.time()-t0:.0f}s")
