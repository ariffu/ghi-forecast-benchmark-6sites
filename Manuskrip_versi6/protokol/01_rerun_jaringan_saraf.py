# Manuskrip V6: salinan dari "rerun protokol baku/01_rerun_jaringan_saraf.py" (sha256 58dfa254f7ef8fc2…); hanya folder keluaran dan pemeriksaan lingkungan yang ditambah.
# -*- coding: utf-8 -*-
"""Rerun 01 — kelima jaringan saraf naskah dilatih ulang dengan SATU PROTOKOL BAKU, 5 seed, enam stasiun (2026-10-18).

Status: DATA DUKUNG untuk pembimbing. TIDAK dipakai mengubah naskah, ESM atau LAPORAN sebelum ada arahan.
Pemicu: audit pelatihan (training mirip, uji 10–10c): MLP kurang terlatih (target mentah W m⁻², batas 40 epoch), Transformer sedikit
kurang optimal (+0,003), kedua hibrid peka inisialisasi (±0,005). Lihat [[Diskusikan dengan pembimbing]] butir 1–2.

PROTOKOL BAKU (ditetapkan sebelum run; sama untuk MLP, LSTM, Transformer, LSTM-hibrid, Transformer-hibrid)
  Data       : identik naskah — _common.prepare(site, l_filter=5), masker siang, split latih 2022–2023 / validasi 2024 / uji 2025.
  Input      : identik naskah — 43 prediktor (median latih → z-score latih); jendela 12 × 14 kanal (median latih → z-score latih).
  Arsitektur : identik Tabel S3 (paper_v2_clpbanten/04b_seq_6situs_mean.py, 04c_mean_6situs_xgb_mlp.py).
  Target     : residual Δ = ȳ − ŷ_SP untuk SEMUA model (MLP sebelumnya langsung ke ȳ), distandarkan (Δ − μ_latih)/σ_latih;
               prakiraan ŷ = ŷ_SP + μ + σ·ẑ.
  Pelatihan  : Adam lr awal 7 × 10⁻⁴, batch 256, MSE; ReduceLROnPlateau (faktor 0,5, patience 2, lr min 10⁻⁵) pada MSE validasi;
               early stopping patience 10 (perbaikan > 10⁻⁵), maks. 100 epoch, bobot terbaik dipulihkan; gradient clipping norma 1,0.
  Seed       : 42, 1, 2, 3, 4 (torch.manual_seed dan np.random.seed tepat sebelum model dibuat).
Keluaran (bisa dilanjutkan bila terputus): hasil/nn/metrik_<situs>.csv (satu baris per model × seed), hasil/nn/pred_<situs>_<model>_s<seed>.npy,
  hasil/nn/yb_<situs>.npz (y, ŷ_SP, tanggal uji). Jalankan: python -u 01_rerun_jaringan_saraf.py --situs banten bengkulu --threads 3
"""
import os, sys, time, argparse, numpy as np, pandas as pd, torch, torch.nn as nn
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))   # Manuskrip V6: dua tingkat di atas protokol/
PAPER = os.path.join(ROOT, "paper_v2_clpbanten"); sys.path.insert(0, PAPER)
import os as _os
_V = r"C:\Users\ariff\Documents\Balai_data_v6_10"
assert _os.environ.get("FEATSET") == "P2F", "Manuskrip V6: FEATSET harus P2F"
assert _os.path.normcase(_os.environ.get("DATA_DIR", "")) == _os.path.normcase(_os.path.join(_V, "00_data")), "DATA_DIR harus Balai_data_v6_10/00_data"
assert _os.path.normcase(_os.environ.get("CLEARSKY_DIR", "")) == _os.path.normcase(_os.path.join(_V, "clearsky")), "CLEARSKY_DIR harus Balai_data_v6_10/clearsky"
assert _os.path.normcase(_os.environ.get("CLP_EKSTRA_DIR", "")) == _os.path.normcase(_os.path.join(_V, "clp_ekstra")), "CLP_EKSTRA_DIR harus Balai_data_v6_10/clp_ekstra"
from _common import prepare, split_idx, SITES
import _common as _c; assert len(_c.P2_AKTIF) == 44
OUT = os.path.join(HERE, "hasil", "nn"); os.makedirs(OUT, exist_ok=True)   # Manuskrip V6: HERE = Manuskrip_versi6/protokol
ap = argparse.ArgumentParser(); ap.add_argument("--situs", nargs="+", default=SITES); ap.add_argument("--seed", nargs="+", type=int, default=[42, 1, 2, 3, 4])
ap.add_argument("--model", nargs="+", default=["MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"]); ap.add_argument("--threads", type=int, default=3)
A = ap.parse_args(); torch.set_num_threads(A.threads); t0 = time.time()
def log(*a): print(*a, flush=True)
CH = ["ghi_wm2", "dhi_wm2", "dni_wm2", "kt", "clp_cot", "clp_cth_km", "clp_ctt_k", "clp_cer_um",
      "aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_rain_mm", "solar_elev_deg"]; L = 12
PROTOKOL = dict(lr=7e-4, batch=256, maks_epoch=100, patience=10, min_delta=1e-5, lr_faktor=0.5, lr_patience=2, lr_min=1e-5, clip=1.0)

# ---------------- arsitektur: identik naskah (04b, 04c) ----------------
class PosE(nn.Module):
    def __init__(s, d, L):
        super().__init__(); pe = torch.zeros(L, d); pos = torch.arange(L).unsqueeze(1).float()
        div = torch.exp(torch.arange(0, d, 2).float() * (-np.log(10000.0) / d)); pe[:, 0::2] = torch.sin(pos * div); pe[:, 1::2] = torch.cos(pos * div); s.register_buffer("pe", pe.unsqueeze(0))
    def forward(s, x): return x + s.pe[:, :x.size(1)]
class MLP(nn.Module):
    def __init__(s, d):
        super().__init__(); s.f = nn.Sequential(nn.Linear(d, 256), nn.ReLU(), nn.Dropout(0.2), nn.Linear(256, 128), nn.ReLU(), nn.Dropout(0.2), nn.Linear(128, 1))
    def forward(s, z): return s.f(z).squeeze(-1)
class LSTMN(nn.Module):
    def __init__(s, c, h=96): super().__init__(); s.l = nn.LSTM(c, h, 2, batch_first=True, dropout=0.1); s.h = nn.Sequential(nn.Linear(h, 64), nn.ReLU(), nn.Linear(64, 1))
    def forward(s, x): o, _ = s.l(x); return s.h(o[:, -1]).squeeze(-1)
class TRFN(nn.Module):
    def __init__(s, c, d=64): super().__init__(); s.p = nn.Linear(c, d); s.pe = PosE(d, L); s.t = nn.TransformerEncoder(nn.TransformerEncoderLayer(d, 4, 128, dropout=0.1, batch_first=True), 2); s.h = nn.Sequential(nn.Linear(d, 64), nn.ReLU(), nn.Linear(64, 1))
    def forward(s, x): z = s.t(s.pe(s.p(x))); return s.h(z[:, -1]).squeeze(-1)
class LSTMH(nn.Module):
    def __init__(s, c, d, h=96): super().__init__(); s.l = nn.LSTM(c, h, 2, batch_first=True, dropout=0.1); s.h = nn.Sequential(nn.Linear(h + d, 128), nn.ReLU(), nn.Dropout(0.2), nn.Linear(128, 1))
    def forward(s, x, z): o, _ = s.l(x); return s.h(torch.cat([o[:, -1], z], 1)).squeeze(-1)
class TRFH(nn.Module):
    def __init__(s, c, d, dd=64): super().__init__(); s.p = nn.Linear(c, dd); s.pe = PosE(dd, L); s.t = nn.TransformerEncoder(nn.TransformerEncoderLayer(dd, 4, 128, dropout=0.1, batch_first=True), 2); s.h = nn.Sequential(nn.Linear(dd + d, 128), nn.ReLU(), nn.Dropout(0.2), nn.Linear(128, 1))
    def forward(s, x, z): o = s.t(s.pe(s.p(x))); return s.h(torch.cat([o[:, -1], z], 1)).squeeze(-1)
def buat(nama, d):
    return {"MLP": lambda: MLP(d), "LSTM": lambda: LSTMN(len(CH)), "Transformer": lambda: TRFN(len(CH)),
            "LSTM_hybrid": lambda: LSTMH(len(CH), d), "Transformer_hybrid": lambda: TRFH(len(CH), d)}[nama]()
INPUT = {"MLP": ("Z",), "LSTM": ("S",), "Transformer": ("S",), "LSTM_hybrid": ("S", "Z"), "Transformer_hybrid": ("S", "Z")}

def prediksi(net, xs):
    with torch.no_grad(): return np.concatenate([net(*[a[i:i + 4096] for a in xs]).numpy() for i in range(0, len(xs[0]), 4096)])
def latih(net, xtr, ytr, xva, yva):
    P = PROTOKOL; opt = torch.optim.Adam(net.parameters(), lr=P["lr"]); lf = nn.MSELoss()
    sch = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=P["lr_faktor"], patience=P["lr_patience"], min_lr=P["lr_min"])
    Y = torch.tensor(ytr, dtype=torch.float32); best, state, bad, eb, ep = np.inf, None, 0, 0, 0
    for ep in range(1, P["maks_epoch"] + 1):
        net.train(); perm = torch.randperm(len(Y))
        for i in range(0, len(Y), P["batch"]):
            j = perm[i:i + P["batch"]]; opt.zero_grad(); lf(net(*[a[j] for a in xtr]), Y[j]).backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), P["clip"]); opt.step()
        net.eval(); v = float(np.mean((prediksi(net, xva) - yva) ** 2)); sch.step(v)
        if v < best - P["min_delta"]: best, state, bad, eb = v, {k: t.clone() for k, t in net.state_dict().items()}, 0, ep
        else:
            bad += 1
            if bad >= P["patience"]: break
    net.load_state_dict(state); net.eval(); return net, eb, ep

for site in A.situs:
    fm = os.path.join(OUT, f"metrik_{site}.csv"); done = set()
    if os.path.exists(fm): M0 = pd.read_csv(fm); done = set(zip(M0.model, M0.seed))
    todo = [(s, m) for s in A.seed for m in A.model if (m, s) not in done]
    if not todo: log(f"{site}: semua sudah selesai"); continue
    df, feats, yr = prepare(site, l_filter=5); tr, va, te = split_idx(df, yr, tgt="mean")
    y = df["y_mean"].to_numpy(); b = df["base_mean"].to_numpy(); trd = df.iloc[tr]
    np.savez(os.path.join(OUT, f"yb_{site}.npz"), y=y[te], b=b[te], day=df["ts_wib"].dt.date.astype(str).to_numpy()[te])
    fmed = trd[feats].median().fillna(0.0); fmu = trd[feats].fillna(fmed).mean(); fsd = trd[feats].fillna(fmed).std().replace(0, 1).fillna(1)
    pf = lambda D_: torch.tensor((((D_.fillna(fmed) - fmu) / fsd).astype("float64")).to_numpy(np.float32))
    Z = {"tr": pf(df.iloc[tr][feats]), "va": pf(df.iloc[va][feats]), "te": pf(df.iloc[te][feats])}
    Xw = df[CH].to_numpy(float); n = len(df); W = np.full((n, L, len(CH)), np.nan); ar = np.arange(n)
    for t in range(L):
        k = L - 1 - t; W[:, t, :] = np.where((ar >= k)[:, None], np.roll(Xw, k, axis=0), np.nan)
    medC = trd[CH].median().fillna(0.0); muC = trd[CH].fillna(medC).mean().to_numpy(); sdC = trd[CH].fillna(medC).std().replace(0, 1).fillna(1).to_numpy()
    medw = np.nan_to_num(np.nanmedian(W[tr].reshape(-1, len(CH)), axis=0), nan=0.0)
    def ps(ind):
        Aw = W[ind].copy(); m = np.isnan(Aw); Aw[m] = np.take(medw, np.where(m)[2]); return torch.tensor(((Aw - muC) / sdC).astype(np.float32))
    S = {"tr": ps(tr), "va": ps(va), "te": ps(te)}; del W
    D = {"S": S, "Z": Z}
    r_tr, r_va = y[tr] - b[tr], y[va] - b[va]; mu_r, sd_r = r_tr.mean(), r_tr.std()
    yt, bt = y[te], b[te]; rsp = np.sqrt(mean_squared_error(yt, bt))
    log(f"\n===== {site}: latih {len(tr)}, validasi {len(va)}, uji {len(te)}; Δ latih μ {mu_r:.2f}, σ {sd_r:.2f}; {len(todo)} pelatihan  ({time.time() - t0:.0f}s)")
    for seed, nama in todo:
        t1 = time.time(); torch.manual_seed(seed); np.random.seed(seed)
        net = buat(nama, len(feats)); xs = lambda part: [D[k][part] for k in INPUT[nama]]
        net, eb, el = latih(net, xs("tr"), ((r_tr - mu_r) / sd_r).astype(np.float32), xs("va"), ((r_va - mu_r) / sd_r).astype(np.float32))
        p = bt + mu_r + sd_r * prediksi(net, xs("te"))
        np.save(os.path.join(OUT, f"pred_{site}_{nama}_s{seed}.npy"), p.astype(np.float32))
        row = dict(site=site, model=nama, seed=seed, R2=r2_score(yt, p), RMSE=np.sqrt(mean_squared_error(yt, p)), MAE=mean_absolute_error(yt, p),
                   bias=float(np.mean(p - yt)), skill=1 - np.sqrt(mean_squared_error(yt, p)) / rsp, epoch_terbaik=eb, epoch_berhenti=el,
                   n_parameter=int(sum(q.numel() for q in net.parameters())), detik=round(time.time() - t1, 1))
        pd.DataFrame([row]).to_csv(fm, mode="a", header=not os.path.exists(fm), index=False)
        log(f"  {site:9s} {nama:18s} seed {seed:2d}  R² {row['R2']:.4f}  epoch terbaik {eb}/{el}  ({row['detik']:.0f}s; total {time.time() - t0:.0f}s)")
log(f"SELESAI {time.time() - t0:.0f}s")
