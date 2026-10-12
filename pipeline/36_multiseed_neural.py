# -*- coding: utf-8 -*-
"""Tahap 36 — Multi-seed model NEURAL (target rata-rata jam, data rerun B). DESAIN DIKUNCI SEBELUM HASIL (2026-10-05).

Realisasi per model: R0 = run pipeline asli (prediksi dari NPZ pipeline, atau replikasi persis bila NPZ tak ada)
                     R1..R4 = seed 1..4 (torch.manual_seed + np.random.seed tepat sebelum model dibangun).
Kode model, hiperparameter, data, split, normalisasi IDENTIK dengan skrip asli:
  bkl     : Bengkulu standalone, 04_arch_mean.py  — MLP, LSTM, Transformer, LSTM_hybrid, Transf_hybrid (residual)   [threads = cpu−1]
  six_seq : 6 situs, 04b_seq_6situs_mean.py      — LSTM, Transformer, LSTM_hybrid, Transformer_hybrid (residual)   [threads = cpu−1]
  six_tab : 6 situs, 04c_mean_6situs.py — refit LightGBM/CatBoost (deterministik, assert reproduksi CSV) sebagai pembanding
  six_mlp : 6 situs, 04c_mean_6situs_xgb_mlp.py  — MLP direct; R0 direplikasi persis (seed 42 sekali di awal, urut situs) [threads default = 4]
Prediksi uji disimpan per (exp, site, model, realisasi) -> 36_multiseed/preds/*.npy (resume aman; folder baru).
Analisis & aturan tafsir: 37_multiseed_analysis.py.
Jalankan: python -u 36_multiseed_neural.py bkl|six_tab|six_mlp|six_seq  (atau run_36.cmd: berurutan)
"""
import os, sys, time, numpy as np, pandas as pd, torch, torch.nn as nn
from sklearn.metrics import r2_score
B = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, B)
import _common
from _common import prepare, split_idx, SITES
OUT = os.path.join(B, "36_multiseed", "preds"); os.makedirs(OUT, exist_ok=True)
SEEDS = [1, 2, 3, 4]
CH = ["ghi_wm2","dhi_wm2","dni_wm2","kt","clp_cot","clp_cth_km","clp_ctt_k","clp_cer_um",
      "aws_temp_c","aws_rh_pct","aws_pressure_hpa","aws_wind_speed_ms","aws_rain_mm","solar_elev_deg"]
L = 12
t0 = time.time()
def log(*a): print(*a, flush=True)
def fp(exp, site, key): return os.path.join(OUT, f"{exp}__{site}__{key}.npy")

# ---------------- arsitektur (identik 04_arch_mean.py / 04b_seq_6situs_mean.py) ----------------
class MLP(nn.Module):
    def __init__(s,d): super().__init__(); s.f=nn.Sequential(nn.Linear(d,256),nn.ReLU(),nn.Dropout(0.2),nn.Linear(256,128),nn.ReLU(),nn.Dropout(0.2),nn.Linear(128,1))
    def forward(s,x): return s.f(x).squeeze(-1)
class LSTMN(nn.Module):
    def __init__(s,c,h=96): super().__init__(); s.l=nn.LSTM(c,h,2,batch_first=True,dropout=0.1); s.h=nn.Sequential(nn.Linear(h,64),nn.ReLU(),nn.Linear(64,1))
    def forward(s,x): o,_=s.l(x); return s.h(o[:,-1]).squeeze(-1)
class PosE(nn.Module):
    def __init__(s,d,L):
        super().__init__(); pe=torch.zeros(L,d); pos=torch.arange(L).unsqueeze(1).float()
        div=torch.exp(torch.arange(0,d,2).float()*(-np.log(10000.0)/d)); pe[:,0::2]=torch.sin(pos*div); pe[:,1::2]=torch.cos(pos*div); s.register_buffer("pe",pe.unsqueeze(0))
    def forward(s,x): return x+s.pe[:,:x.size(1)]
class TRFN(nn.Module):
    def __init__(s,c,d=64): super().__init__(); s.p=nn.Linear(c,d); s.pe=PosE(d,L); s.t=nn.TransformerEncoder(nn.TransformerEncoderLayer(d,4,128,dropout=0.1,batch_first=True),2); s.h=nn.Sequential(nn.Linear(d,64),nn.ReLU(),nn.Linear(64,1))
    def forward(s,x): z=s.t(s.pe(s.p(x))); return s.h(z[:,-1]).squeeze(-1)
class LSTMH(nn.Module):
    def __init__(s,c,d,h=96): super().__init__(); s.l=nn.LSTM(c,h,2,batch_first=True,dropout=0.1); s.h=nn.Sequential(nn.Linear(h+d,128),nn.ReLU(),nn.Dropout(0.2),nn.Linear(128,1))
    def forward(s,x,z): o,_=s.l(x); return s.h(torch.cat([o[:,-1],z],1)).squeeze(-1)
class TRFH(nn.Module):
    def __init__(s,c,d,dd=64): super().__init__(); s.p=nn.Linear(c,dd); s.pe=PosE(dd,L); s.t=nn.TransformerEncoder(nn.TransformerEncoderLayer(dd,4,128,dropout=0.1,batch_first=True),2); s.h=nn.Sequential(nn.Linear(dd+d,128),nn.ReLU(),nn.Dropout(0.2),nn.Linear(128,1))
    def forward(s,x,z): o=s.t(s.pe(s.p(x))); return s.h(torch.cat([o[:,-1],z],1)).squeeze(-1)
def fit(model,xtr,ytr_,xva,yva_,epochs,bs,lr,patience=6):          # identik 04_arch_mean / 04b_seq
    opt=torch.optim.Adam(model.parameters(),lr=lr); lf=nn.MSELoss()
    T=[torch.tensor(a) for a in xtr]; Y=torch.tensor(ytr_,dtype=torch.float32)
    V=[torch.tensor(a) for a in xva]; Yv=torch.tensor(yva_,dtype=torch.float32)
    best=np.inf; state=None; bad=0
    for ep in range(1,epochs+1):
        model.train(); perm=torch.randperm(len(Y)); nb=int(np.ceil(len(Y)/bs))
        for i in range(nb):
            j=perm[i*bs:(i+1)*bs]; opt.zero_grad(); l=lf(model(*[T[k][j] for k in range(len(T))]),Y[j]); l.backward(); opt.step()
        model.eval()
        with torch.no_grad(): v=lf(model(*V),Yv).item()
        if v<best-1e-4: best,state,bad=v,{k:t.clone() for k,t in model.state_dict().items()},0
        else:
            bad+=1
            if bad>=patience: break
    model.load_state_dict(state); model.eval(); return model
def fit_mlp_direct(Xtr, ytr, Xva, yva, d, epochs=40, bs=1024, lr=1e-3):   # identik 04c_mean_6situs_xgb_mlp.fit_mlp
    model = MLP(d); opt = torch.optim.Adam(model.parameters(), lr=lr); lossf = nn.MSELoss()
    Xt = torch.tensor(Xtr, dtype=torch.float32); yt = torch.tensor(ytr, dtype=torch.float32)
    Xv = torch.tensor(Xva, dtype=torch.float32); yv = torch.tensor(yva, dtype=torch.float32)
    best = 1e18; best_sd = None; patience = 0
    for ep in range(epochs):
        model.train(); perm = torch.randperm(len(Xt))
        for i in range(0, len(Xt), bs):
            idx = perm[i:i+bs]; opt.zero_grad(); loss = lossf(model(Xt[idx]), yt[idx]); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad(): vl = lossf(model(Xv), yv).item()
        if vl < best - 1e-5: best = vl; best_sd = {k: v.clone() for k, v in model.state_dict().items()}; patience = 0
        else:
            patience += 1
            if patience >= 6: break
    model.load_state_dict(best_sd); model.eval()
    with torch.no_grad(): p = model(torch.tensor(Xva, dtype=torch.float32))
    return model

def seq_inputs(df, feats, itr, iva, ite):                             # identik 04_arch_mean / 04b_seq
    tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
    Xw=df[CH].to_numpy(float); n=len(df); W=np.full((n,L,len(CH)),np.nan); ar=np.arange(n)
    for t in range(L):
        k=L-1-t; W[:,t,:]=np.where((ar>=k)[:,None], np.roll(Xw,k,axis=0), np.nan)
    med=tr[feats].median().fillna(0.0); mu=tr[feats].fillna(med).mean(); sd=tr[feats].fillna(med).std().replace(0,1).fillna(1)
    medC=tr[CH].median().fillna(0.0); muC=tr[CH].fillna(medC).mean().to_numpy(); sdC=tr[CH].fillna(medC).std().replace(0,1).fillna(1).to_numpy()   # statistik kanal sequence per kolom (identik dg sebelumnya bila CH ⊂ feats)
    def pf(X): return (((X.fillna(med)-mu)/sd).astype("float64")).to_numpy(np.float32)
    Ztr,Zva,Zte=pf(tr[feats]),pf(va[feats]),pf(te[feats])
    medw=np.nan_to_num(np.nanmedian(W[itr].reshape(-1,len(CH)),axis=0),nan=0.0)
    def ps(ind):
        A=W[ind].copy(); m=np.isnan(A); A[m]=np.take(medw,np.where(m)[2])
        return ((A-muC)/sdC).astype(np.float32)
    return Ztr, Zva, Zte, ps(itr), ps(iva), ps(ite)

def run_seq_family(exp, site, df, feats, itr, iva, ite, models, include_mlp):
    tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
    ytr_r=(tr.y_mean-tr.base_mean).to_numpy(); yva_r=(va.y_mean-va.base_mean).to_numpy(); bt=te.base_mean.to_numpy()
    Ztr,Zva,Zte,Str,Sva,Ste = seq_inputs(df, feats, itr, iva, ite)
    for seed in SEEDS:
        if include_mlp and not os.path.exists(fp(exp, site, f"MLP__s{seed}")):
            torch.manual_seed(seed); np.random.seed(seed)
            m=fit(MLP(Ztr.shape[1]),[Ztr],ytr_r,[Zva],yva_r,60,512,1e-3)
            with torch.no_grad(): np.save(fp(exp, site, f"MLP__s{seed}"), bt+m(torch.tensor(Zte)).numpy())
            log(f"   {exp} {site} MLP s{seed} R2={r2_score(te.y_mean, np.load(fp(exp, site, f'MLP__s{seed}'))):.4f} ({time.time()-t0:.0f}s)")
        for key in models:
            if os.path.exists(fp(exp, site, f"{key}__s{seed}")): continue
            torch.manual_seed(seed); np.random.seed(seed)
            net = {"LSTM": lambda: LSTMN(len(CH)), "Transformer": lambda: TRFN(len(CH)), "LSTM_hybrid": lambda: LSTMH(len(CH), Ztr.shape[1]),
                   "Transformer_hybrid": lambda: TRFH(len(CH), Ztr.shape[1]), "Transf_hybrid": lambda: TRFH(len(CH), Ztr.shape[1])}[key]()
            flat = "hybrid" in key
            m=fit(net,[Str]+([Ztr] if flat else []),ytr_r,[Sva]+([Zva] if flat else []),yva_r,40,256,7e-4)
            with torch.no_grad(): pr=bt+m(*([torch.tensor(Ste)]+([torch.tensor(Zte)] if flat else []))).numpy()
            np.save(fp(exp, site, f"{key}__s{seed}"), pr)
            log(f"   {exp} {site} {key} s{seed} R2={r2_score(te.y_mean, pr):.4f} ({time.time()-t0:.0f}s)")

part = sys.argv[1]
if part == "bkl":
    torch.set_num_threads(max(1, (os.cpu_count() or 4) - 1))
    df, feats, yr = prepare("bengkulu"); itr, iva, ite = split_idx(df, yr, "mean"); te = df.iloc[ite]
    Zp = np.load(os.path.join(B, "04_arch_mean", "arch_preds_mean.npz")); assert np.allclose(Zp["y"], te.y_mean.to_numpy())
    np.save(fp("bkl", "bengkulu", "y"), te.y_mean.to_numpy()); np.save(fp("bkl", "bengkulu", "day"), te.ts_wib.dt.date.astype(str).to_numpy())
    for k in ["LightGBM", "CatBoost", "XGBoost", "MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transf_hybrid"]: np.save(fp("bkl", "bengkulu", f"{k}__pipe"), Zp[k])
    run_seq_family("bkl", "bengkulu", df, feats, itr, iva, ite, ["LSTM", "Transformer", "LSTM_hybrid", "Transf_hybrid"], include_mlp=True)
elif part == "six_seq":
    torch.set_num_threads(max(1, (os.cpu_count() or 4) - 1))
    Zp = np.load(os.path.join(B, "04b_arch_6situs_mean", "arch_preds_6situs_mean.npz"))
    for site in SITES:
        log(f"== six_seq {site} ({time.time()-t0:.0f}s)")
        df, feats, yr = prepare(site); itr, iva, ite = split_idx(df, yr, "mean"); te = df.iloc[ite]
        assert np.allclose(Zp[f"{site}__y"], te.y_mean.to_numpy())
        np.save(fp("six", site, "y"), te.y_mean.to_numpy()); np.save(fp("six", site, "day"), te.ts_wib.dt.date.astype(str).to_numpy())
        for k in ["LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"]: np.save(fp("six", site, f"{k}__pipe"), Zp[f"{site}__{k}"])
        run_seq_family("six", site, df, feats, itr, iva, ite, ["LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"], include_mlp=False)
elif part == "six_tab":                                                 # pembanding deterministik 6 situs (04c_mean_6situs.py), wajib reproduksi CSV
    import lightgbm
    from lightgbm import LGBMRegressor
    from catboost import CatBoostRegressor
    ref = pd.read_csv(os.path.join(B, "04c_mean_6situs", "baseline_mean_6situs.csv")).set_index("site")
    for site in SITES:
        df, feats, yr = prepare(site, l_filter=5); tr, va, te = split_idx(df, yr, tgt="mean")
        y = df["y_mean"].to_numpy(); b = df["base_mean"].to_numpy(); X = df[feats]
        Xtr, Xte = X.iloc[tr], X.iloc[te]; med = Xtr.median().fillna(0.0)
        np.save(fp("six", site, "day"), df.ts_wib.iloc[te].dt.date.astype(str).to_numpy())
        lg = LGBMRegressor(n_estimators=2500, learning_rate=0.03, num_leaves=63, verbose=-1, random_state=42)
        lg.fit(Xtr.fillna(med), y[tr] - b[tr], eval_set=[(X.iloc[va].fillna(med), y[va] - b[va])],
               callbacks=[lightgbm.early_stopping(200, verbose=False)])
        p_lgb = lg.predict(Xte.fillna(med)) + b[te]
        cb = CatBoostRegressor(iterations=2500, learning_rate=0.03, depth=6, loss_function="RMSE", verbose=0, random_seed=42)
        cb.fit(Xtr.fillna(med), y[tr], eval_set=(X.iloc[va].fillna(med), y[va]), early_stopping_rounds=200, use_best_model=True)
        p_cb = cb.predict(Xte.fillna(med))
        for k, p, col in [("LightGBM", p_lgb, "LGB_R2"), ("CatBoost", p_cb, "CB_R2")]:
            r2 = r2_score(y[te], p); ok = abs(round(r2, 4) - ref.loc[site, col]) < 1e-4 + 1e-9
            log(f"   six {site} {k} refit R2={r2:.4f} csv={ref.loc[site, col]:.4f} {'OK' if ok else 'BEDA'} ({time.time()-t0:.0f}s)")
            if k == "LightGBM": assert ok, f"{site} LightGBM tidak tereproduksi"
            np.save(fp("six", site, f"{k}__pipe"), p); np.save(fp("six", site, f"{k}__pipe_ok"), np.array([ok]))
elif part == "six_mlp":
    torch.set_num_threads(4)                                            # = default saat 04c_mean_6situs_xgb_mlp dijalankan
    ref = pd.read_csv(os.path.join(B, "04c_mean_6situs", "baseline_mean_6situs_xgb_mlp.csv")).set_index("site")
    data = {}
    for site in SITES:
        df, feats, yr = prepare(site, l_filter=5); tr, va, te = split_idx(df, yr, tgt="mean")
        y = df["y_mean"].to_numpy(); X = df[feats]; med = X.iloc[tr].median().fillna(0.0)
        Xtr = X.iloc[tr].fillna(med); Xva = X.iloc[va].fillna(med); Xte = X.iloc[te].fillna(med)
        mu = Xtr.mean(0); sd = Xtr.std(0).replace(0, 1).fillna(1)
        nz = lambda d_: ((d_ - mu) / sd).to_numpy(np.float32)
        data[site] = (nz(Xtr), y[tr], nz(Xva), y[va], nz(Xte), y[te], Xtr.shape[1], df.ts_wib.iloc[te].dt.date.astype(str).to_numpy())
    # R0: replikasi persis pipeline (seed 42 SEKALI di awal, urut situs)
    torch.manual_seed(42); np.random.seed(42)
    for site in SITES:
        Xtr_, ytr_, Xva_, yva_, Xte_, yte_, d_, day_ = data[site]
        m = fit_mlp_direct(Xtr_, ytr_, Xva_, yva_, d_)
        with torch.no_grad(): p = m(torch.tensor(Xte_, dtype=torch.float32)).numpy()
        r2 = r2_score(yte_, p); ok = abs(round(r2, 4) - ref.loc[site, "MLP_R2"]) < 1e-4 + 1e-9
        log(f"   six {site} MLP pipe R2={r2:.4f} csv={ref.loc[site,'MLP_R2']:.4f} {'OK' if ok else 'BEDA (dicatat; tetap dipakai sebagai realisasi)'}")
        np.save(fp("six", site, "MLP__pipe"), p); np.save(fp("six", site, "MLP__pipe_ok"), np.array([ok]))
        np.save(fp("six", site, "y_mlp"), yte_)
    for seed in SEEDS:
        for site in SITES:
            if os.path.exists(fp("six", site, f"MLP__s{seed}")): continue
            Xtr_, ytr_, Xva_, yva_, Xte_, yte_, d_, day_ = data[site]
            torch.manual_seed(seed); np.random.seed(seed)
            m = fit_mlp_direct(Xtr_, ytr_, Xva_, yva_, d_)
            with torch.no_grad(): p = m(torch.tensor(Xte_, dtype=torch.float32)).numpy()
            np.save(fp("six", site, f"MLP__s{seed}"), p); log(f"   six {site} MLP s{seed} R2={r2_score(yte_, p):.4f} ({time.time()-t0:.0f}s)")
log(f"SELESAI {part} dalam {time.time()-t0:.0f}s")
