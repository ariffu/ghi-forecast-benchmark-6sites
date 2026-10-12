# -*- coding: utf-8 -*-
"""Tahap 4c-bis — XGBoost + MLP untuk target RATA-RATA jam, 6 situs.
Melengkapi Tabel 1 (headline mean) agar tetap 4 model seperti struktur asli
(LightGBM/CatBoost sudah dihitung di 04c_mean_6situs.py).
MLP = flat 104-feature feedforward (2 hidden layer), CPU, per-situs.
"""
import os, sys, gc, numpy as np, pandas as pd, torch, torch.nn as nn
import matplotlib
matplotlib.use("Agg")
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import prepare, split_idx, BASE, SITES

OUT = os.path.join(BASE, "04c_mean_6situs"); os.makedirs(OUT, exist_ok=True)
torch.manual_seed(42); np.random.seed(42)

def log(*a): print(*a, flush=True)

def met(y, p, base):
    rsp = np.sqrt(mean_squared_error(y, base))
    return dict(R2=round(r2_score(y, p), 4),
                MAE=round(mean_absolute_error(y, p), 1),
                RMSE=round(np.sqrt(mean_squared_error(y, p)), 1),
                skill=round(1 - np.sqrt(mean_squared_error(y, p)) / rsp, 4))

class MLP(nn.Module):
    def __init__(s, d):
        super().__init__()
        s.f = nn.Sequential(nn.Linear(d, 256), nn.ReLU(), nn.Dropout(0.2),
                            nn.Linear(256, 128), nn.ReLU(), nn.Dropout(0.2), nn.Linear(128, 1))
    def forward(s, x): return s.f(x).squeeze(-1)

def fit_mlp(Xtr, ytr, Xva, yva, d, epochs=40, bs=1024, lr=1e-3):
    model = MLP(d); opt = torch.optim.Adam(model.parameters(), lr=lr)
    lossf = nn.MSELoss()
    Xt = torch.tensor(Xtr, dtype=torch.float32); yt = torch.tensor(ytr, dtype=torch.float32)
    Xv = torch.tensor(Xva, dtype=torch.float32); yv = torch.tensor(yva, dtype=torch.float32)
    best = 1e18; best_sd = None; patience = 0
    for ep in range(epochs):
        model.train(); perm = torch.randperm(len(Xt))
        for i in range(0, len(Xt), bs):
            idx = perm[i:i+bs]
            opt.zero_grad()
            loss = lossf(model(Xt[idx]), yt[idx])
            loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            pv = model(Xv); vl = lossf(pv, yv).item()
        if vl < best - 1e-5:
            best = vl; best_sd = {k: v.clone() for k, v in model.state_dict().items()}; patience = 0
        else:
            patience += 1
            if patience >= 6: break
    model.load_state_dict(best_sd); model.eval()
    with torch.no_grad(): p = model(torch.tensor(Xva, dtype=torch.float32))
    # return prediksi train (untuk konsistensi) tidak perlu; hanya metrik test di luar
    return model

rows = []
for site in SITES:
    log(f"\n===== {site} =====")
    df, feats, yr = prepare(site, l_filter=5)
    tr, va, te = split_idx(df, yr, tgt="mean")
    y = df["y_mean"].to_numpy(); b = df["base_mean"].to_numpy()
    X = df[feats]
    med = X.iloc[tr].median().fillna(0.0)
    Xtr = X.iloc[tr].fillna(med); Xva = X.iloc[va].fillna(med); Xte = X.iloc[te].fillna(med)
    ytr, yva, yte = y[tr], y[va], y[te]
    bte = b[te]

    # XGBoost
    xgb = XGBRegressor(n_estimators=2500, learning_rate=0.03, max_depth=6,
                       early_stopping_rounds=200, eval_metric="rmse", random_state=42, verbosity=0)
    xgb.fit(Xtr, ytr, eval_set=[(Xva, yva)])
    p_xgb = xgb.predict(Xte)
    m_xgb = met(yte, p_xgb, bte)

    # MLP (normalisasi dari training)
    mu = Xtr.mean(0); sd = Xtr.std(0).replace(0, 1).fillna(1)
    def norm(dfx): return ((dfx - mu) / sd).to_numpy(np.float32)
    model = fit_mlp(norm(Xtr), ytr, norm(Xva), yva, Xtr.shape[1])
    with torch.no_grad():
        p_mlp = model(torch.tensor(norm(Xte), dtype=torch.float32)).numpy()
    m_mlp = met(yte, p_mlp, bte)

    rows.append(dict(site=site, n_test=len(te), SP_R2=round(r2_score(yte, bte), 4),
                     **{f"XGB_{k}": v for k, v in m_xgb.items()},
                     **{f"MLP_{k}": v for k, v in m_mlp.items()}))
    log(f"  XGBoost: R2={m_xgb['R2']} MAE={m_xgb['MAE']} RMSE={m_xgb['RMSE']}")
    log(f"  MLP    : R2={m_mlp['R2']} MAE={m_mlp['MAE']} RMSE={m_mlp['RMSE']}")
    del df, X, Xtr, Xva, Xte, model; gc.collect()

res = pd.DataFrame(rows)
res.to_csv(os.path.join(OUT, "baseline_mean_6situs_xgb_mlp.csv"), index=False)
log("\n===== RESULT =====")
log(res.round(4).to_string())
log("SELESAI")
