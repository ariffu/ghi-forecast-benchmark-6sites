# -*- coding: utf-8 -*-
"""Tahap 114 a4 — pencarian hiperparameter LightGBM dan LSTM di Bengkulu pada V6.10 (DESAIN_114.md).
Bawaan = protokol baku naskah V6 (Manuskrip_versi6/protokol/01_rerun_jaringan_saraf.py, 02_rerun_pohon.py), diuji reproduksinya.
Ruang dan urutan sampel acak sama dengan tahap 61 (rng 2026; 29 konfigurasi LightGBM lalu 29 LSTM). Dipilih dengan R² validasi 2024.
Hasil per konfigurasi di a4_tuning/preds (dapat dilanjutkan). Ringkasan: a4_tuning/ringkasan_a4.json, search_*.csv."""
import os, sys, time, json, numpy as np, pandas as pd, lightgbm as lgb, torch, torch.nn as nn
from sklearn.metrics import r2_score
_V = r"C:\Users\ariff\Documents\Balai_data_v6_10"
assert os.environ.get("FEATSET") == "P2F"
for _k, _d in (("DATA_DIR", "00_data"), ("CLEARSKY_DIR", "clearsky"), ("CLP_EKSTRA_DIR", "clp_ekstra")): assert os.path.normcase(os.environ.get(_k, "")) == os.path.normcase(os.path.join(_V, _d)), _k
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); ROOT = os.path.dirname(B); sys.path.insert(0, B)
import _common
from _common import prepare, split_idx
from _blockboot import delta_r2
assert len(_common.P2_AKTIF) == 44
PB = os.path.join(ROOT, "Manuskrip_versi6", "protokol", "hasil")
OUT = os.path.join(HERE, "a4_tuning"); PD = os.path.join(OUT, "preds"); os.makedirs(PD, exist_ok=True)
N_CFG, SEEDS = 30, [1, 2, 3, 4]; torch.set_num_threads(3); t0 = time.time()
def log(*a): print(*a, flush=True)
CH = ["ghi_wm2", "dhi_wm2", "dni_wm2", "kt", "clp_cot", "clp_cth_km", "clp_ctt_k", "clp_cer_um",
      "aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_rain_mm", "solar_elev_deg"]; L = 12
PROT = dict(lr=7e-4, batch=256, maks_epoch=100, patience=10, min_delta=1e-5, lr_faktor=0.5, lr_patience=2, lr_min=1e-5, clip=1.0)

# ---------------- data: identik protokol baku (02_rerun_pohon.py, 01_rerun_jaringan_saraf.py) ----------------
df, feats, yr = prepare("bengkulu", l_filter=5); tr, va, te = split_idx(df, yr, tgt="mean")
y = df["y_mean"].to_numpy(); b = df["base_mean"].to_numpy(); X = df[feats]; trd = df.iloc[tr]
med = X.iloc[tr].median().fillna(0.0); Xtr, Xva, Xte = X.iloc[tr].fillna(med), X.iloc[va].fillna(med), X.iloc[te].fillna(med)
rtr, rva = y[tr] - b[tr], y[va] - b[va]; yv, bv, yt, bt = y[va], b[va], y[te], b[te]
day = df["ts_wib"].dt.date.astype(str).to_numpy()[te]
Y = np.load(os.path.join(PB, "nn", "yb_bengkulu.npz"), allow_pickle=True); assert np.allclose(Y["y"], yt) and np.allclose(Y["b"], bt)
Xw = df[CH].to_numpy(float); n = len(df); W = np.full((n, L, len(CH)), np.nan); ar = np.arange(n)
for t in range(L):
    k = L - 1 - t; W[:, t, :] = np.where((ar >= k)[:, None], np.roll(Xw, k, axis=0), np.nan)
medC = trd[CH].median().fillna(0.0); muC = trd[CH].fillna(medC).mean().to_numpy(); sdC = trd[CH].fillna(medC).std().replace(0, 1).fillna(1).to_numpy()
medw = np.nan_to_num(np.nanmedian(W[tr].reshape(-1, len(CH)), axis=0), nan=0.0)
def ps(ind):
    Aw = W[ind].copy(); m = np.isnan(Aw); Aw[m] = np.take(medw, np.where(m)[2]); return torch.tensor(((Aw - muC) / sdC).astype(np.float32))
S = {"tr": ps(tr), "va": ps(va), "te": ps(te)}; del W
mu_r, sd_r = rtr.mean(), rtr.std()
log(f"data siap: latih {len(tr)}, validasi {len(va)}, uji {len(te)}, prediktor {len(feats)} ({time.time()-t0:.0f}s)")

# ---------------- model ----------------
class LSTMC(nn.Module):        # bawaan (96, 2, 0,1, 64) = LSTMN protokol baku; urutan pembuatan modul sama
    def __init__(s, c, h=96, nl=2, dr=0.1, hw=64):
        super().__init__(); s.l = nn.LSTM(c, h, nl, batch_first=True, dropout=dr if nl > 1 else 0.0); s.h = nn.Sequential(nn.Linear(h, hw), nn.ReLU(), nn.Linear(hw, 1))
    def forward(s, x): o, _ = s.l(x); return s.h(o[:, -1]).squeeze(-1)
def prediksi(net, xs):
    with torch.no_grad(): return np.concatenate([net(*[a[i:i + 4096] for a in xs]).numpy() for i in range(0, len(xs[0]), 4096)])
def latih(net, xtr, ytr_, xva, yva_, lr, batch):          # identik protokol baku, kecuali lr dan batch dari konfigurasi
    P = PROT; opt = torch.optim.Adam(net.parameters(), lr=lr); lf = nn.MSELoss()
    sch = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=P["lr_faktor"], patience=P["lr_patience"], min_lr=P["lr_min"])
    Yt = torch.tensor(ytr_, dtype=torch.float32); best, state, bad, eb, ep = np.inf, None, 0, 0, 0
    for ep in range(1, P["maks_epoch"] + 1):
        net.train(); perm = torch.randperm(len(Yt))
        for i in range(0, len(Yt), batch):
            j = perm[i:i + batch]; opt.zero_grad(); lf(net(*[a[j] for a in xtr]), Yt[j]).backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), P["clip"]); opt.step()
        net.eval(); v = float(np.mean((prediksi(net, xva) - yva_) ** 2)); sch.step(v)
        if v < best - P["min_delta"]: best, state, bad, eb = v, {k: t.clone() for k, t in net.state_dict().items()}, 0, ep
        else:
            bad += 1
            if bad >= P["patience"]: break
    net.load_state_dict(state); net.eval(); return net, eb
def run_lstm(cfg, seed):
    torch.manual_seed(seed); np.random.seed(seed)
    net = LSTMC(len(CH), cfg["hidden"], cfg["layers"], cfg["dropout"], cfg["head"])
    net, eb = latih(net, [S["tr"]], ((rtr - mu_r) / sd_r).astype(np.float32), [S["va"]], ((rva - mu_r) / sd_r).astype(np.float32), cfg["lr"], cfg["batch"])
    return bv + mu_r + sd_r * prediksi(net, [S["va"]]), bt + mu_r + sd_r * prediksi(net, [S["te"]]), eb
def run_lgb(cfg):
    p = {k: v for k, v in cfg.items() if k != "n_estimators"}
    extra = dict(subsample_freq=1) if "subsample" in p else {}
    m = lgb.LGBMRegressor(n_estimators=cfg["n_estimators"], verbose=-1, random_state=42, n_jobs=2, **extra, **p)   # n_jobs 2 = run protokol baku pohon
    m.fit(Xtr, rtr, eval_set=[(Xva, rva)], callbacks=[lgb.early_stopping(200, verbose=False)])
    return bv + m.predict(Xva), bt + m.predict(Xte), int(m.best_iteration_)

# ---------------- konfigurasi: bawaan protokol baku + 29 acak (rng 2026, urutan tahap 61) ----------------
rng = np.random.default_rng(2026); lu = lambda a, c: float(np.exp(rng.uniform(np.log(a), np.log(c))))
LGB = [dict(learning_rate=0.03, num_leaves=63, n_estimators=2500)]
for _ in range(N_CFG - 1):
    LGB.append(dict(learning_rate=lu(0.01, 0.1), num_leaves=int(rng.choice([15, 31, 63, 127, 255])), min_child_samples=int(rng.choice([10, 20, 50, 100, 200])),
                    subsample=float(rng.uniform(0.5, 1.0)), colsample_bytree=float(rng.uniform(0.5, 1.0)), reg_alpha=lu(1e-3, 10), reg_lambda=lu(1e-3, 10), n_estimators=5000))
LST = [dict(hidden=96, layers=2, dropout=0.1, head=64, lr=7e-4, batch=256)]
for _ in range(N_CFG - 1):
    LST.append(dict(hidden=int(rng.choice([32, 64, 96, 128, 192])), layers=int(rng.choice([1, 2, 3])), dropout=float(rng.uniform(0, 0.4)),
                    head=int(rng.choice([32, 64, 128])), lr=lu(2e-4, 3e-3), batch=int(rng.choice([128, 256, 512]))))
json.dump(dict(LightGBM=LGB, LSTM=LST), open(os.path.join(OUT, "konfigurasi_a4.json"), "w", encoding="utf-8"), indent=1)

# ---------------- uji reproduksi bawaan ----------------
ref_lgb = np.load(os.path.join(PB, "pohon", "pred_bengkulu_LightGBM_s42.npy")).astype(float)
ref_lstm = np.load(os.path.join(PB, "nn", "pred_bengkulu_LSTM_s42.npy")).astype(float)
def search(name, cfgs, runner):
    rows = []
    for c, cfg in enumerate(cfgs):
        f = os.path.join(PD, f"{name}__c{c:02d}.npz")
        if not os.path.exists(f):
            t1 = time.time(); pv_, pt_, k_ = runner(cfg); np.savez(f, val=pv_, test=pt_, it=k_, sec=time.time() - t1)
        z = np.load(f); rows.append(dict(model=name, config=c, **cfg, val_R2=r2_score(yv, z["val"]), test_R2=r2_score(yt, z["test"]), iters_or_epochs=int(z["it"]), seconds=float(z["sec"])))
        log(f"  {name} c{c:02d}: val R² {rows[-1]['val_R2']:.4f} uji R² {rows[-1]['test_R2']:.4f} ({rows[-1]['iters_or_epochs']}) ({time.time()-t0:.0f}s)")
        if c == 0:
            ref = ref_lgb if name == "LightGBM" else ref_lstm; d = float(np.abs(z["test"] - ref).max())
            ok = d < (1e-3 if name == "LightGBM" else 0.05); log(f"  reproduksi {name} bawaan vs protokol baku: maks |Δp| {d:.2e} W m⁻² {'OK' if ok else 'BEDA'}")
            assert ok, f"{name} bawaan tidak mereproduksi protokol baku — pencarian dihentikan"
    Sx = pd.DataFrame(rows); Sx.to_csv(os.path.join(OUT, f"search_{name}.csv"), index=False); return Sx
SL = search("LightGBM", LGB, run_lgb)
SN = search("LSTM", LST, lambda cfg: run_lstm(cfg, 42))
bl, bn = int(SL.val_R2.idxmax()), int(SN.val_R2.idxmax()); log(f"terpilih: LightGBM c{bl:02d}, LSTM c{bn:02d}")
tuned_lstm = [np.load(os.path.join(PD, f"LSTM__c{bn:02d}.npz"))["test"]]
for sd in SEEDS:
    f = os.path.join(PD, f"LSTM__c{bn:02d}__s{sd}.npz")
    if not os.path.exists(f):
        pv_, pt_, ep_ = run_lstm(LST[bn], sd); np.savez(f, val=pv_, test=pt_, it=ep_)
    tuned_lstm.append(np.load(f)["test"]); log(f"  LSTM c{bn:02d} seed {sd}: uji R² {r2_score(yt, tuned_lstm[-1]):.4f} ({time.time()-t0:.0f}s)")
def_lstm = [np.load(os.path.join(PB, "nn", f"pred_bengkulu_LSTM_s{sd}.npy")).astype(float) for sd in [42] + SEEDS]
lgb_def, lgb_tun = ref_lgb, np.load(os.path.join(PD, f"LightGBM__c{bl:02d}.npz"))["test"]
r2 = lambda p: float(r2_score(yt, p))
R_ld, R_lt = r2(lgb_def), r2(lgb_tun); R_nd, R_nt = [r2(p) for p in def_lstm], [r2(p) for p in tuned_lstm]
bl_ci = delta_r2(yt, lgb_tun, lgb_def, day, record=False); bn_ci = delta_r2(yt, np.mean(tuned_lstm, 0), np.mean(def_lstm, 0), day, record=False)
J = dict(n_cfg=N_CFG, selected=dict(LightGBM=dict(config=bl, **LGB[bl]), LSTM=dict(config=bn, **LST[bn])),
         n_better_val=dict(LightGBM=int((SL.val_R2 > SL.val_R2.iloc[0]).sum()), LSTM=int((SN.val_R2 > SN.val_R2.iloc[0]).sum())),
         val_R2=dict(LightGBM_default=float(SL.val_R2.iloc[0]), LightGBM_tuned=float(SL.val_R2.iloc[bl]), LSTM_default=float(SN.val_R2.iloc[0]), LSTM_tuned=float(SN.val_R2.iloc[bn])),
         test_R2=dict(LightGBM_default=R_ld, LightGBM_tuned=R_lt, LSTM_default_runs=R_nd, LSTM_tuned_runs=R_nt, LSTM_default_mean=float(np.mean(R_nd)), LSTM_tuned_mean=float(np.mean(R_nt))),
         d_LightGBM=dict(dR2=R_lt - R_ld, blk_lo=bl_ci["blk_lo"], blk_hi=bl_ci["blk_hi"], sig=bl_ci["sig_block"]),
         d_LSTM=dict(dR2_mean=float(np.mean(R_nt) - np.mean(R_nd)), ens_dR2=bn_ci["dR2"], blk_lo=bn_ci["blk_lo"], blk_hi=bn_ci["blk_hi"], sig=bn_ci["sig_block"]),
         seconds=round(time.time() - t0))
json.dump(J, open(os.path.join(OUT, "ringkasan_a4.json"), "w", encoding="utf-8"), indent=1, default=float); log("\n" + json.dumps(J, indent=1, default=float)); log(f"SELESAI a4 {time.time()-t0:.0f}s")
