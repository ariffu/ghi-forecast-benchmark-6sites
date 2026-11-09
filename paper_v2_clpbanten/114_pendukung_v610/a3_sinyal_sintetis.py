# Tahap 114: dibuat oleh a0_siapkan.py dari training mirip\07_sinyal_sintetis.py (sha256 0952509b25cdd65a…); jangan disunting langsung.
# -*- coding: utf-8 -*-
"""Uji 07 — uji sinyal sintetis: apakah pipeline MAMPU memperlihatkan perbedaan antar-model bila perbedaan itu memang ada? (Bengkulu, 2026-10-16)

Latar: delapan model naskah (dan model baru di uji 01) mencapai R² nyaris sama. Keberatan yang wajar: mungkin pipeline
(pembagian data, pelatihan, evaluasi) memang tidak sanggup membedakan model. Uji ini memasang sinyal buatan yang strukturnya
DIKETAHUI pada input asli Bengkulu, lalu melatih model dengan pipeline yang sama.

Target sintetis (input, masker, split, set uji dan smart persistence b identik naskah; semua model RESIDUAL thd b):
    y_syn = b + 80·h + A·g + 60·ε,   ε ~ N(0,1) (seed 11, sama untuk semua skenario), A = 150 W m⁻²
  h  sinyal BERSAMA: fungsi nonlinear kt, RH dan suhu saat origin (ada di 43 fitur DAN di langkah terakhir jendela);
  gA sinyal khusus-TABULAR: nilai acak per sektor arah angin (8 sektor); arah angin ada di 43 fitur, TIDAK ada di jendela;
  gB sinyal khusus-SEKUENS: perubahan DHI, DNI, kecepatan angin dan radius efektif awan antara 110 dan 60 menit sebelum origin;
     hanya terlihat di jendela 2 jam (43 fitur hanya memuat nilai saat origin dan ringkasan riwayat kt/AWS/CLP lain).
  Semua komponen distandarkan (rerata 0, SD 1 di data latih).
Skenario: S_A  A = 150, g = gA (tree pada 43 fitur seharusnya unggul);  S_B  A = 150, g = gB (BiLSTM pada jendela seharusnya unggul);
          S_C  A = 0 (informasi setara: keduanya seharusnya konvergen ke batas atas).
REVISI DESAIN (dicatat terbuka): run pertama memakai A = 100. Ternyata varians target jauh lebih besar dari perkiraan, sehingga sinyal
  khusus hanya 4,8% varians dan celah maksimum yang mungkin (R²_maks − R²_bersama = 0,052) hampir sama dengan ambang T1/T2 (0,05).
  Uji itu salah kalibrasi: bisa gagal karena desain, bukan karena pipeline. Run dihentikan setelah baru LightGBM S_A yang
  selesai (98% sinyal khusus tertangkap), SEBELUM ada hasil BiLSTM atau perbandingan model mana pun. A dinaikkan menjadi 150
  (≈ 10% varians); aturan T1–T4 tidak diubah.
Batas atas diketahui: R²_maks = R²(y_syn, b + 80h + A·g) (oracle tanpa derau); R²_bersama = R²(y_syn, b + 80h) (oracle tanpa sinyal khusus).
Model (konfigurasi uji 01/03/05, satu seed 42): LightGBM pada 43 fitur (= tree naskah); BiLSTM pada jendela 14 kanal × 12 langkah
  (= LSTM naskah); LightGBM pada 43 fitur + jendela diratakan; BiLSTM-hibrid jendela + 43 fitur (= LSTM_hybrid naskah).
Aturan tafsir (ditetapkan sebelum run):
  T1 S_A: R²(LightGBM-43) − R²(BiLSTM-jendela) ≥ 0,05 dan CI bootstrap blok harian > 0  → pipeline mendeteksi keunggulan tabular.
  T2 S_B: R²(BiLSTM-jendela) − R²(LightGBM-43) ≥ 0,05 dan CI > 0                        → pipeline mendeteksi keunggulan sekuens.
  T3 S_C: |R²(LightGBM-43) − R²(BiLSTM-jendela)| ≤ 0,01 dan keduanya ≥ R²_maks − 0,02   → informasi setara ⇒ konvergen dekat batas atas.
  T4 perbedaan mengikuti informasi, bukan arsitektur: celah T1 tertutup ≥ 50% oleh BiLSTM-hibrid (diberi 43 fitur) DAN
     celah T2 tertutup ≥ 50% oleh LightGBM 43 fitur + jendela.
Keluaran: hasil/sinyal_sintetis.csv, hasil/sinyal_sintetis_delta.csv, hasil/sinyal_sintetis.png. Log: hasil/log_07.txt
Jalankan: PYTHONIOENCODING=utf-8 python -u 07_sinyal_sintetis.py > hasil/log_07.txt 2>&1
"""
import os, sys, time, numpy as np, pandas as pd, torch, torch.nn as nn
from sklearn.metrics import r2_score
import lightgbm as lgb
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
import os as _os
_V = r"C:\Users\ariff\Documents\Balai_data_v6_10"
assert _os.environ.get("FEATSET") == "P2F"
for _k, _d in (("DATA_DIR", "00_data"), ("CLEARSKY_DIR", "clearsky"), ("CLP_EKSTRA_DIR", "clp_ekstra")): assert _os.path.normcase(_os.environ.get(_k, "")) == _os.path.normcase(_os.path.join(_V, _d)), _k
PAPER = r"C:\Users\ariff\Documents\Balai Obsidian\Balai\solardata_new_v2\paper_v2_clpbanten"; sys.path.insert(0, PAPER)
import _common
from _common import prepare, split_idx
from _blockboot import delta_r2
assert _common.FEATSET == "P2F"
OUT = os.path.join(HERE, "a3_sintetis"); os.makedirs(OUT, exist_ok=True); t0 = time.time(); torch.set_num_threads(4)
def log(*a): print(*a, flush=True)
M_T43, M_TI3, M_SEQ, M_HYB = "LightGBM, 43 fitur", "LightGBM, 43 fitur + jendela", "BiLSTM, jendela", "BiLSTM-hibrid, jendela + 43 fitur"

def gambar(R):                               # hanya dari hasil/sinyal_sintetis.csv; ulang gambar tanpa melatih: python 07_sinyal_sintetis.py --gambar
    fig, ax = plt.subplots(figsize=(8.2, 4.6)); w = 0.19; SC = list(dict.fromkeys(R.skenario))
    MOD = [(M_T43, "#2b8cbe"), (M_TI3, "#08519c"), (M_SEQ, "#41ab5d"), (M_HYB, "#006d2c")]
    for gi, sc in enumerate(SC):
        Rs = R[R.skenario == sc]; mx, sh = Rs.R2_maks.iloc[0], Rs.R2_bersama.iloc[0]
        for mi, (m, c) in enumerate(MOD):
            x = gi + (mi - 1.5) * w; v = Rs[Rs.model == m].R2.iloc[0]; ax.bar(x, v, w * 0.92, color=c, label=m if gi == 0 else None)
            ax.text(x, v - 0.004, f"{v:.3f}", ha="center", va="top", fontsize=7, rotation=90, color="white", fontweight="bold")
        ax.hlines(mx, gi - 2 * w, gi + 2 * w, colors="k", linestyles="--", lw=1.1, label="batas atas (oracle)" if gi == 0 else None)
        if sh < mx - 1e-6: ax.hlines(sh, gi - 2 * w, gi + 2 * w, colors="#d62728", linestyles=":", lw=1.4, label="batas atas tanpa sinyal khusus" if gi == 0 else None)
    ax.set_xticks(range(len(SC))); ax.set_xticklabels(["S_A: sinyal khusus hanya di 43 fitur\n(arah angin)", "S_B: sinyal khusus hanya di jendela\n(riwayat 1–2 jam)", "S_C: informasi setara"][:len(SC)], fontsize=8)
    ax.set_ylim(min(R.R2.min(), R.R2_bersama.min()) - 0.03, 0.99)
    ax.set_ylabel("R² uji 2025 (target sintetis, Bengkulu)"); ax.grid(axis="y", lw=0.4, alpha=0.6)
    ax.legend(fontsize=7.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.17), frameon=False)
    ax.set_title("Uji sinyal sintetis: pipeline yang sama, struktur sinyal diketahui", fontsize=9.5)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "sinyal_sintetis.png"), dpi=200)
if "--gambar" in sys.argv: gambar(pd.read_csv(os.path.join(OUT, "sinyal_sintetis.csv"))); sys.exit()

df, feats, yr = prepare("bengkulu")
itr, iva, ite = split_idx(df, yr, "mean")
b = df["base_mean"].to_numpy(float); day = df["ts_wib"].dt.date.to_numpy()[ite]
assert len(feats) == 44; print('uji', len(ite), flush=True)
# 43 fitur: mentah untuk LightGBM (NaN dibiarkan), terimputasi + terstandar untuk cabang dense hibrid (sama dengan uji 01)
X = df[feats]; med = X.iloc[itr].median().fillna(0.0); Xf = X.fillna(med)
mu, sd = Xf.iloc[itr].mean(), Xf.iloc[itr].std().replace(0, 1).fillna(1)
Z = ((Xf - mu) / sd).to_numpy(np.float32)
# jendela 14 kanal × 12 langkah (sama dengan uji 05); langkah terakhir = origin
CH = ["ghi_wm2", "dhi_wm2", "dni_wm2", "kt", "clp_cot", "clp_cth_km", "clp_ctt_k", "clp_cer_um",
      "aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_rain_mm", "solar_elev_deg"]; L = 12
Xc = df[CH].to_numpy(np.float32); n = len(df)
k_ = np.arange(L - 1, -1, -1); j_ = np.arange(n)[:, None] - k_[None, :]
Wraw = Xc[np.clip(j_, 0, None)]; Wraw[j_ < 0] = np.nan
mc = np.nanmedian(Wraw[itr].reshape(-1, 14), axis=0); mc = np.where(np.isfinite(mc), mc, 0.0)
Wf = Wraw.copy(); mk = np.isnan(Wf); Wf[mk] = np.take(mc, np.where(mk)[2]); del mk
muW, sdW = Wf[itr].reshape(-1, 14).mean(0), Wf[itr].reshape(-1, 14).std(0); sdW[sdW == 0] = 1
S = ((Wf - muW) / sdW).astype(np.float32); del Wf                                   # input BiLSTM
cols = [f"w_{c}_lag{L - 1 - t}" for t in range(L) for c in CH]
I3 = pd.concat([X, pd.DataFrame(Wraw.reshape(n, -1), columns=cols, index=df.index)], axis=1); del Wraw

# ---------------- komponen sinyal ----------------
def zs(v):
    v = np.asarray(v, float); return (v - v[itr].mean()) / v[itr].std()
cz = lambda name: zs(Xf[name].to_numpy(float))
h = zs(np.tanh(1.5 * cz("kt")) * (1 + 0.5 * cz("aws_rh_pct")) + 0.5 * np.sin(2 * cz("aws_temp_c")))
th = np.arctan2(X["aws_wind_dir_sin"].to_numpy(float), X["aws_wind_dir_cos"].to_numpy(float))
sek = np.floor((th + np.pi) / (2 * np.pi / 8))                                        # sektor 0–7; NaN bila arah angin hilang
val = np.random.default_rng(7).normal(size=9)
gA = zs(np.where(np.isnan(sek), 0.0, val[np.nan_to_num(sek, nan=0.0).astype(int).clip(0, 8)]))
ci = {c: CH.index(c) for c in CH}
dd = lambda c: S[:, L - 1 - 6, ci[c]].astype(float) - S[:, L - 1 - 11, ci[c]].astype(float)   # nilai t−60 menit dikurangi t−110 menit
gB = zs(dd("dhi_wm2") - dd("dni_wm2") + dd("aws_wind_speed_ms") * dd("clp_cer_um"))
eps = np.random.default_rng(11).normal(size=n)
AH, AG, SIG = 80.0, 150.0, 60.0
log(f"Bengkulu: latih {len(itr)}, validasi {len(iva)}, uji {len(ite)}; korelasi (latih) h–gA {np.corrcoef(h[itr], gA[itr])[0, 1]:+.3f}, "
    f"h–gB {np.corrcoef(h[itr], gB[itr])[0, 1]:+.3f}, gA–gB {np.corrcoef(gA[itr], gB[itr])[0, 1]:+.3f}")
SCEN = {"S_A tabular": ("sinyal khusus tabular (arah angin)", AG * gA), "S_B sekuens": ("sinyal khusus sekuens (riwayat 1–2 jam)", AG * gB),
        "S_C setara": ("informasi setara (tanpa sinyal khusus)", 0.0 * gA)}

# ---------------- model ----------------
def fit_lgb(Xdf, r):
    m = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=63, min_child_samples=50, subsample=0.8, subsample_freq=1,
                          colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1, random_state=42, n_jobs=-1, verbose=-1)
    m.fit(Xdf.iloc[itr], r[itr], eval_set=[(Xdf.iloc[iva], r[iva])], callbacks=[lgb.early_stopping(80, verbose=False)])
    return m.predict(Xdf.iloc[ite]), f"iterasi {m.best_iteration_}"
class BiLSTM(nn.Module):                     # jendela saja (arsitektur uji 01/05)
    def __init__(s, c, h=64): super().__init__(); s.l = nn.LSTM(c, h, 2, batch_first=True, dropout=0.1, bidirectional=True); s.o = nn.Sequential(nn.Linear(2 * h, 64), nn.ReLU(), nn.Linear(64, 1))
    def forward(s, x): o, _ = s.l(x); return s.o(o.mean(1)).squeeze(-1)
class Hyb(nn.Module):                        # enkoder BiLSTM jendela + vektor 43 prediktor (arsitektur uji 01)
    def __init__(s, c, d, h=64):
        super().__init__(); s.e = nn.LSTM(c, h, 2, batch_first=True, dropout=0.1, bidirectional=True)
        s.o = nn.Sequential(nn.Linear(2 * h + d, 128), nn.ReLU(), nn.Dropout(0.2), nn.Linear(128, 1))
    def forward(s, x, z): o, _ = s.e(x); return s.o(torch.cat([o.mean(1), z], 1)).squeeze(-1)
def fit(model, xtr, ytr_, xva, yva_, epochs=40, bs=256, lr=7e-4, patience=6):
    opt = torch.optim.Adam(model.parameters(), lr=lr); lf = nn.MSELoss()
    T = [torch.tensor(a) for a in xtr]; Y = torch.tensor(ytr_, dtype=torch.float32); V = [torch.tensor(a) for a in xva]; Yv = torch.tensor(yva_, dtype=torch.float32)
    best, state, bad, ep_best = np.inf, None, 0, 0
    for ep in range(1, epochs + 1):
        model.train(); perm = torch.randperm(len(Y))
        for i in range(int(np.ceil(len(Y) / bs))):
            j = perm[i * bs:(i + 1) * bs]; opt.zero_grad(); l = lf(model(*[t[j] for t in T]), Y[j]); l.backward(); opt.step()
        model.eval()
        with torch.no_grad(): v = sum(((model(*[t[i:i + 4096] for t in V]) - Yv[i:i + 4096]) ** 2).sum().item() for i in range(0, len(Yv), 4096)) / len(Yv)
        if v < best - 1e-5: best, state, bad, ep_best = v, {k: t.clone() for k, t in model.state_dict().items()}, 0, ep
        else:
            bad += 1
            if bad >= patience: break
    model.load_state_dict(state); model.eval(); return model, ep_best
def pred(model, xs):
    with torch.no_grad(): return np.concatenate([model(*[torch.tensor(a[i:i + 4096]) for a in xs]).numpy() for i in range(0, len(xs[0]), 4096)])

rows, P, YT, LIM = [], {}, {}, {}
def add(sc, model, p, extra):
    r2 = r2_score(YT[sc], p); r2max, r2sh = LIM[sc]; P[(sc, model)] = p
    por = (r2 - r2sh) / (r2max - r2sh) if r2max - r2sh > 1e-6 else np.nan
    rows.append(dict(skenario=sc, model=model, R2=r2, R2_maks=r2max, R2_bersama=r2sh, jarak_ke_maks=r2max - r2,
                     porsi_sinyal_khusus=por, catatan=extra))
    log(f"  {model:34s} R² {r2:.4f}  (jarak ke batas atas {r2max - r2:.4f}; porsi sinyal khusus tertangkap "
        f"{'—' if np.isnan(por) else f'{100 * por:.0f}%'})  {extra}  ({time.time() - t0:.0f}s)")

for sc, (desc, G) in SCEN.items():
    ys = b + AH * h + G + SIG * eps; r = ys - b; YT[sc] = ys[ite]
    LIM[sc] = (r2_score(ys[ite], b[ite] + AH * h[ite] + G[ite]), r2_score(ys[ite], b[ite] + AH * h[ite]))
    log(f"\n== {sc}: {desc} ==\n  batas atas R²_maks {LIM[sc][0]:.4f}; tanpa sinyal khusus R²_bersama {LIM[sc][1]:.4f}; "
        f"porsi varians sinyal khusus (uji) {np.var(G[ite]) / np.var(ys[ite]):.3f}")
    p, ex = fit_lgb(X, r); add(sc, M_T43, b[ite] + p, ex)
    p, ex = fit_lgb(I3, r); add(sc, M_TI3, b[ite] + p, ex)
    rs = r[itr].std(); ytr_, yva_ = (r[itr] / rs).astype(np.float32), (r[iva] / rs).astype(np.float32)
    torch.manual_seed(42); np.random.seed(42)
    net, ep = fit(BiLSTM(14), [S[itr]], ytr_, [S[iva]], yva_); add(sc, M_SEQ, b[ite] + rs * pred(net, [S[ite]]), f"epoch terbaik {ep}")
    torch.manual_seed(42); np.random.seed(42)
    net, ep = fit(Hyb(14, Z.shape[1]), [S[itr], Z[itr]], ytr_, [S[iva], Z[iva]], yva_); add(sc, M_HYB, b[ite] + rs * pred(net, [S[ite], Z[ite]]), f"epoch terbaik {ep}")

R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "sinyal_sintetis.csv"), index=False)
dl = []
for sc in SCEN:
    for lab, a, c in [("tree-43 − BiLSTM", M_T43, M_SEQ), ("BiLSTM-hibrid − BiLSTM", M_HYB, M_SEQ), ("tree-43+jendela − tree-43", M_TI3, M_T43)]:
        d = delta_r2(YT[sc], P[(sc, a)], P[(sc, c)], day, record=False)
        dl.append(dict(skenario=sc, uji=lab, dR2=d["dR2"], blk_lo=d["blk_lo"], blk_hi=d["blk_hi"],
                       signifikan="ya" if (d["blk_lo"] > 0 or d["blk_hi"] < 0) else "tidak"))
D = pd.DataFrame(dl); D.to_csv(os.path.join(OUT, "sinyal_sintetis_delta.csv"), index=False)
log("\n" + R.drop(columns="catatan").round(4).to_string(index=False)); log("\n" + D.round(4).to_string(index=False))

r2 = lambda sc, m: R[(R.skenario == sc) & (R.model == m)].R2.iloc[0]
dget = lambda sc, lab: D[(D.skenario == sc) & (D.uji == lab)].iloc[0]
gapA = r2("S_A tabular", M_T43) - r2("S_A tabular", M_SEQ); dA = dget("S_A tabular", "tree-43 − BiLSTM")
gapB = r2("S_B sekuens", M_SEQ) - r2("S_B sekuens", M_T43); dB = dget("S_B sekuens", "tree-43 − BiLSTM")
gapC = r2("S_C setara", M_T43) - r2("S_C setara", M_SEQ); mxC = LIM["S_C setara"][0]
t1 = gapA >= 0.05 and dA.blk_lo > 0
t2 = gapB >= 0.05 and dB.blk_hi < 0
t3 = abs(gapC) <= 0.01 and min(r2("S_C setara", M_T43), r2("S_C setara", M_SEQ)) >= mxC - 0.02
tutupA = (r2("S_A tabular", M_HYB) - r2("S_A tabular", M_SEQ)) / gapA if gapA > 0 else np.nan
tutupB = (r2("S_B sekuens", M_TI3) - r2("S_B sekuens", M_T43)) / gapB if gapB > 0 else np.nan
t4 = bool(tutupA >= 0.5 and tutupB >= 0.5)
log(f"\nATURAN TAFSIR\n T1 S_A tree-43 unggul ≥ 0,05 & signifikan: {t1}  [Δ {gapA:+.4f}; CI {dA.blk_lo:+.4f}..{dA.blk_hi:+.4f}]"
    f"\n T2 S_B BiLSTM unggul ≥ 0,05 & signifikan: {t2}  [Δ {gapB:+.4f}; CI (tree−BiLSTM) {dB.blk_lo:+.4f}..{dB.blk_hi:+.4f}]"
    f"\n T3 S_C konvergen (|Δ| ≤ 0,01, keduanya ≥ R²_maks − 0,02 = {mxC - 0.02:.4f}): {t3}  [Δ {gapC:+.4f}]"
    f"\n T4 celah tertutup bila informasi diberikan (≥ 50%): {t4}  [hibrid menutup {100 * tutupA:.0f}% celah S_A; tree+jendela menutup {100 * tutupB:.0f}% celah S_B]")

gambar(R)
log(f"SELESAI dalam {time.time() - t0:.0f}s")
