# -*- coding: utf-8 -*-
"""Tahap 37 — Analisis multi-seed model neural (aturan terkunci: 36_multiseed/DESAIN_TERKUNCI.md).

Masukan : 36_multiseed/preds/*.npy (dari 36_multiseed_neural.py), CSV pipeline (tabular deterministik).
Keluaran: 36_multiseed/{r2_per_realisasi,r2_ringkas,spread_6situs,bkl_block,six_block,klaim_naskah}.csv,
          ringkasan_aturan.json, RINGKASAN_37.md, plots/36_multiseed_*.png.
Realisasi: pipe (R0, seed 42 pipeline) + s1..s4. Ansambel-seed = rata-rata prediksi 5 realisasi (diagnostik saja).
Klaim naskah yang diuji (CLEAN v2 §3.4, §3.6, §4.1):
  K1 spread 8 model 6 situs 0.007–0.013 (R1) · K2 Bengkulu: 4 terbaik dalam 0.0028, spread 0.0099
  K3 MLP tak beda dari LightGBM (blok) · K4 Transformer/LSTM/LSTM_hybrid/Transf_hybrid signifikan lebih rendah (R2)
  K5 MLP dalam 0.009 dari model terbaik di tiap situs · K6 LSTM terendah di 4/6 situs, dalam 0.013 dari terbaik · R3 derau seed
Jalankan: python -u 37_multiseed_analysis.py   (boleh parsial: model/realisasi yang belum ada dilewati & dilaporkan)
"""
import os, sys, json, glob, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
B = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, B)
from _blockboot import delta_r2, r2
from _common import SITES, savefig
D = os.path.join(B, "36_multiseed"); P = os.path.join(D, "preds")
REAL = ["pipe", "s1", "s2", "s3", "s4"]
TAB = ["LightGBM", "CatBoost", "XGBoost"]
NN6 = ["MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"]
NNB = ["MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transf_hybrid"]
LBL = {"LSTM_hybrid": "LSTM-hyb", "Transformer_hybrid": "Transf-hyb", "Transf_hybrid": "Transf-hyb"}
def ld(exp, site, key):
    f = os.path.join(P, f"{exp}__{site}__{key}.npy")
    if not os.path.exists(f) and key == "y": f = os.path.join(P, f"{exp}__{site}__y_mlp.npy")   # 6 situs: target dari six_mlp bila six_seq belum
    return np.load(f, allow_pickle=True) if os.path.exists(f) else None
for _s in SITES:                                                     # konsistensi target antar-mode
    _a, _b = (os.path.join(P, f"six__{_s}__{k}.npy") for k in ("y", "y_mlp"))
    if os.path.exists(_a) and os.path.exists(_b): assert np.allclose(np.load(_a), np.load(_b)), _s
def log(*a): print(*a, flush=True)

# ---------------- 1. R² per realisasi ----------------
rows = []; preds = {}
for exp, sites, models in [("bkl", ["bengkulu"], NNB), ("six", SITES, NN6)]:
    for site in sites:
        y = ld(exp, site, "y")
        if y is None: continue
        for m in models + (["LightGBM", "CatBoost", "XGBoost"] if exp == "bkl" else ["LightGBM", "CatBoost"]):
            for rl in (REAL if m in models else ["pipe"]):
                p = ld(exp, site, f"{m}__{rl}")
                if p is None: continue
                preds[(exp, site, m, rl)] = p; rows.append(dict(exp=exp, site=site, model=m, real=rl, R2=r2(y, p)))
R = pd.DataFrame(rows); R.to_csv(os.path.join(D, "r2_per_realisasi.csv"), index=False)
mlp_ok = {s: bool(ld("six", s, "MLP__pipe_ok")[0]) for s in SITES if ld("six", s, "MLP__pipe_ok") is not None}

# ringkasan per model: R0, mean, SD, min, max, ansambel
S = []
for (exp, site, m), g in R.groupby(["exp", "site", "model"]):
    rl = [r for r in REAL if (exp, site, m, r) in preds]
    ens = r2(ld(exp, site, "y"), np.mean([preds[(exp, site, m, r)] for r in rl], 0)) if len(rl) > 1 else np.nan
    v = g.set_index("real").R2
    S.append(dict(exp=exp, site=site, model=m, n_real=len(rl), R2_pipe=v.get("pipe", np.nan), R2_mean=v.mean(),
                  R2_sd=v.std(ddof=1) if len(v) > 1 else np.nan, R2_min=v.min(), R2_max=v.max(), R2_ens=ens))
S = pd.DataFrame(S); S.to_csv(os.path.join(D, "r2_ringkas.csv"), index=False)
log(S.round(4).to_string(index=False))

# ---------------- 2. Spread 8 model 6 situs (K1/R1, K5, K6) ----------------
rep = pd.read_csv(os.path.join(B, "04b_arch_6situs_mean", "arch_6situs_mean_merged.csv")).set_index("site")
xgb6 = pd.read_csv(os.path.join(B, "04c_mean_6situs", "baseline_mean_6situs_xgb_mlp.csv")).set_index("site")["XGB_R2"]
ALL8 = TAB + NN6
def tab_r2(site, m):
    if m == "XGBoost": return xgb6[site]
    g = S[(S.exp == "six") & (S.site == site) & (S.model == m)]
    return float(g.R2_pipe.iloc[0]) if len(g) else rep.loc[site, m]
sp = []; k56 = []
for site in SITES:
    nn_full = all(len(R[(R.exp == "six") & (R.site == site) & (R.model == m)]) == 5 for m in NN6)
    vals_rep = rep.loc[site, ALL8].astype(float)
    def spread_of(nnv):
        v = {m: tab_r2(site, m) for m in TAB}; v.update(nnv); v = pd.Series(v); return v.max() - v.min(), v
    g6 = S[(S.exp == "six") & (S.site == site)].set_index("model")
    s_mean, v_mean = spread_of({m: g6.loc[m, "R2_mean"] for m in NN6}) if nn_full else (np.nan, None)   # hanya bila 5 model neural × 5 realisasi lengkap
    per_real = []
    for rl in REAL:
        nnv = {m: float(R[(R.exp == "six") & (R.site == site) & (R.model == m) & (R.real == rl)].R2.iloc[0])
               for m in NN6 if len(R[(R.exp == "six") & (R.site == site) & (R.model == m) & (R.real == rl)])}
        if len(nnv) < len(NN6): continue
        s_r, v_r = spread_of(nnv); per_real.append(s_r)
        best = v_r.max()
        k56.append(dict(site=site, real=rl, MLP_gap=best - v_r["MLP"], LSTM_lowest=bool(v_r.idxmin() == "LSTM"),
                        LSTM_gap=best - v_r["LSTM"], best_neural=v_r[NN6].idxmax(), best_model=v_r.idxmax(),
                        neural_beats_tab=bool(v_r[NN6].max() > v_r[TAB].max())))
    sp.append(dict(site=site, spread_reported=vals_rep.max() - vals_rep.min(), spread_seedmean=s_mean,
                   spread_real_min=min(per_real) if per_real else np.nan, spread_real_max=max(per_real) if per_real else np.nan,
                   n_real_complete=len(per_real), nn_complete=nn_full, MLP_R0_reproduced=mlp_ok.get(site)))
SP = pd.DataFrame(sp); SP.to_csv(os.path.join(D, "spread_6situs.csv"), index=False)
K56 = pd.DataFrame(k56); K56.to_csv(os.path.join(D, "k5_k6_per_realisasi.csv"), index=False)
log("\n" + SP.round(4).to_string(index=False))

# ---------------- 3. Bengkulu standalone: ΔR² vs LightGBM, blok harian (K3/K4/R2) ----------------
orig = pd.read_csv(os.path.join(B, "27_block_bootstrap", "arch_bengkulu_block.csv")).set_index("model")
bk = []
yb = ld("bkl", "bengkulu", "y"); dayb = ld("bkl", "bengkulu", "day")
if yb is not None:
    ref = preds[("bkl", "bengkulu", "LightGBM", "pipe")]
    for m in NNB:
        rl = [r for r in REAL if ("bkl", "bengkulu", m, r) in preds]
        for r in rl + (["ens"] if len(rl) == 5 else []):
            p = np.mean([preds[("bkl", "bengkulu", m, q)] for q in rl], 0) if r == "ens" else preds[("bkl", "bengkulu", m, r)]
            o = delta_r2(yb, p, ref, dayb, record=False); o.update(model=m, real=r); bk.append(o)
BK = pd.DataFrame(bk); BK.to_csv(os.path.join(D, "bkl_block.csv"), index=False)

# 6 situs: ΔR² vs LightGBM (refit 04c) per realisasi + ansambel (deskriptif)
sx = []
for site in SITES:
    y = ld("six", site, "y"); day = ld("six", site, "day")
    if y is None or ("six", site, "LightGBM", "pipe") not in preds: continue
    ref = preds[("six", site, "LightGBM", "pipe")]
    for m in NN6:
        rl = [r for r in REAL if ("six", site, m, r) in preds]
        for r in rl + (["ens"] if len(rl) == 5 else []):
            p = np.mean([preds[("six", site, m, q)] for q in rl], 0) if r == "ens" else preds[("six", site, m, r)]
            o = delta_r2(y, p, ref, day, record=False); o.update(site=site, model=m, real=r); sx.append(o)
SX = pd.DataFrame(sx); SX.to_csv(os.path.join(D, "six_block.csv"), index=False)

# ---------------- 4. Aturan R1–R3 dan klaim K1–K6 ----------------
out = {"realisasi": REAL, "MLP6_R0_reproduksi": mlp_ok}
c = SP.dropna(subset=["spread_seedmean"])
if len(c) == 6 and c.nn_complete.all():
    dev = (c.spread_seedmean - c.spread_reported).abs()
    out["R1"] = dict(spread_reported=[round(c.spread_reported.min(), 4), round(c.spread_reported.max(), 4)],
                     spread_seedmean=[round(c.spread_seedmean.min(), 4), round(c.spread_seedmean.max(), 4)],
                     spread_any_realisation=[round(c.spread_real_min.min(), 4), round(c.spread_real_max.max(), 4)],
                     max_abs_dev=round(dev.max(), 4), robust=bool((dev <= 0.003).all() and c.spread_seedmean.max() <= 0.016))
if len(K56) and len(K56.real.unique()) == 5 and K56.site.nunique() == 6:
    out["K5_MLP_within_0.009"] = dict(realisasi_lolos=int(K56.groupby("real").MLP_gap.max().le(0.009).sum()), dari=5,
                                       max_gap=round(K56.MLP_gap.max(), 4))
    out["K6_LSTM_lowest"] = dict(per_realisasi={r: int(g.LSTM_lowest.sum()) for r, g in K56.groupby("real")},
                                  max_gap=round(K56.LSTM_gap.max(), 4), within_0013_all=bool(K56.LSTM_gap.max() <= 0.013))
    out["neural_beats_tabular_count"] = int(K56.neural_beats_tab.sum()); out["n_site_real"] = len(K56)
    out["best_neural_freq"] = K56.best_neural.value_counts().to_dict()
if len(BK):
    r2r = {}
    for m in NNB:
        g = BK[BK.model == m]; per = g[g.real != "ens"]; ens = g[g.real == "ens"]
        if len(per) < 5 or not len(ens): continue
        o_sig = orig.loc[m, "sig_block"] == "yes"; o_dir = np.sign(orig.loc[m, "dR2"])
        n_sig_same = int(((per.sig_block == "yes") & (np.sign(per.dR2) == o_dir)).sum()); n_sig = int((per.sig_block == "yes").sum())
        e = ens.iloc[0]; ens_sig = e.sig_block == "yes" and np.sign(e.dR2) == o_dir
        robust = (ens_sig and n_sig_same >= 4) if o_sig else (n_sig <= 1)
        r2r[m] = dict(klaim=("signifikan " + ("lebih rendah" if o_dir < 0 else "lebih tinggi")) if o_sig else "tidak beda",
                      dR2_pipe=round(orig.loc[m, "dR2"], 4), dR2_mean=round(per.dR2.mean(), 4), dR2_min=round(per.dR2.min(), 4),
                      dR2_max=round(per.dR2.max(), 4), dR2_ens=round(e.dR2, 4), ens_CI=[round(e.blk_lo, 4), round(e.blk_hi, 4)],
                      n_sig=n_sig, n_sig_arah_klaim=n_sig_same, robust=bool(robust))
    out["R2_bengkulu"] = r2r
    g = S[(S.exp == "bkl")].set_index("model")
    if all(m in g.index and g.loc[m, "n_real"] == 5 for m in NNB):
        v = pd.Series({m: (g.loc[m, "R2_mean"] if m in NNB else g.loc[m, "R2_pipe"]) for m in TAB + NNB})
        top4 = v.sort_values(ascending=False).iloc[:4]
        out["K2_bengkulu"] = dict(spread_seedmean=round(v.max() - v.min(), 4), spread_reported=0.0099, top4=list(top4.index),
                                  top4_range=round(top4.max() - top4.min(), 4), top4_reported=0.0028)
sd6 = S[(S.exp == "six") & S.model.isin(NN6) & (S.n_real == 5)].R2_sd
if len(sd6) == 30 and len(c) == 6:
    out["R3"] = dict(median_seed_sd=round(sd6.median(), 4), max_seed_sd=round(sd6.max(), 4),
                     median_arch_spread=round(c.spread_reported.median(), 4), kecil=bool(sd6.median() < 0.5 * c.spread_reported.median()))
sdb = S[(S.exp == "bkl") & S.model.isin(NNB) & (S.n_real == 5)]
if len(sdb): out["bkl_seed_sd"] = {r.model: round(r.R2_sd, 4) for r in sdb.itertuples()}
json.dump(out, open(os.path.join(D, "ringkasan_aturan.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=float)
log("\n" + json.dumps(out, indent=1, ensure_ascii=False, default=float))

# ---------------- 5. Gambar ----------------
def strip(ax, exp, site, models, tab):
    g = R[(R.exp == exp) & (R.site == site)]
    allm = tab + models
    for i, m in enumerate(allm):
        v = g[g.model == m]
        if not len(v): continue
        if m in tab:
            val = v.R2.iloc[0] if len(v) else (xgb6[site] if m == "XGBoost" else np.nan)
            ax.plot(i, val, "s", color="0.25", ms=5)
        else:
            vv = v[v.real != "pipe"].R2; v0 = v[v.real == "pipe"].R2
            ax.plot(np.full(len(vv), i) + np.linspace(-0.12, 0.12, max(len(vv), 1))[:len(vv)], vv, "o", color="tab:blue", ms=3.5, alpha=.8)
            if len(v0): ax.plot(i, v0.iloc[0], "D", color="tab:red", ms=4.5, mfc="none")
            ax.hlines(v.R2.mean(), i - .25, i + .25, color="tab:blue", lw=1.5)
    if exp == "six" and "XGBoost" in tab: ax.plot(tab.index("XGBoost"), xgb6[site], "s", color="0.25", ms=5)
    ax.set_xticks(range(len(allm))); ax.set_xticklabels([LBL.get(m, m) for m in allm], rotation=45, ha="right", fontsize=7)
    ax.grid(axis="y", alpha=.3); ax.tick_params(axis="y", labelsize=7)
fig, axs = plt.subplots(2, 4, figsize=(12, 6.2))
panels = [("bkl", "bengkulu", NNB, TAB, "Bengkulu (standalone)")] + [("six", s, NN6, TAB, s.capitalize()) for s in SITES]
for ax, (exp, site, mods, tab, ttl) in zip(axs.flat, panels):
    strip(ax, exp, site, mods, tab); ax.set_title(ttl, fontsize=9)
ax = axs.flat[-1]; ax.axis("off")
ax.plot([], [], "s", color="0.25", label="tabular (deterministic)"); ax.plot([], [], "D", color="tab:red", mfc="none", label="neural R0 (pipeline, seed 42)")
ax.plot([], [], "o", color="tab:blue", label="neural seeds 1–4"); ax.plot([], [], "-", color="tab:blue", label="mean of 5 realisations")
ax.legend(loc="center", fontsize=8, frameon=False)
fig.supylabel("R² (test 2025, hourly mean)", fontsize=9)
savefig(fig, "36_multiseed_r2.png")
if len(BK):
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for i, m in enumerate(NNB):
        g = BK[BK.model == m]
        for j, r in enumerate(REAL + ["ens"]):
            gg = g[g.real == r]
            if not len(gg): continue
            x = i + (j - 2.5) * 0.12; e = gg.iloc[0]
            ax.errorbar(x, e.dR2, yerr=[[e.dR2 - e.blk_lo], [e.blk_hi - e.dR2]], fmt="D" if r == "ens" else ("s" if r == "pipe" else "o"),
                        color="k" if r == "ens" else ("tab:red" if r == "pipe" else "tab:blue"), ms=4, capsize=2, lw=1)
    ax.axhline(0, color="0.4", lw=.8); ax.axhspan(-0.002, 0.002, color="0.85", zorder=0)
    ax.set_xticks(range(len(NNB))); ax.set_xticklabels([LBL.get(m, m) for m in NNB], fontsize=8)
    ax.set_ylabel("ΔR² vs LightGBM (daily-block 95% CI)", fontsize=8)
    ax.set_title("Bengkulu: R0 (red), seeds 1–4 (blue), seed ensemble (black); grey band = |ΔR²|<0.002", fontsize=8)
    savefig(fig, "36_multiseed_bkl_delta.png")

# ---------------- 6. Ringkasan markdown ----------------
L = ["---", "tags: [disertasi, prediksi-radiasi, eksperimen, multi-seed, clpbanten-v2]", "created: 2026-10-05", "modified: 2026-10-05", "---", "",
     "# Ringkasan multi-seed model neural (tahap 37)", "", "Desain & aturan: [[DESAIN_TERKUNCI]]. Angka mentah: `r2_ringkas.csv`, `bkl_block.csv`, `six_block.csv`, `spread_6situs.csv`.", "",
     "## R² per model (rata-rata ± SD 5 realisasi; R0 = pipeline)", "", "| Eksperimen | Situs | Model | R0 | rata-rata | SD | min–maks | ansambel |", "|---|---|---|---|---|---|---|---|"]
for r in S[S.model.isin(NN6 + NNB)].itertuples():
    L.append(f"| {r.exp} | {r.site} | {r.model} | {r.R2_pipe:.4f} | {r.R2_mean:.4f} | {r.R2_sd:.4f} | {r.R2_min:.4f}–{r.R2_max:.4f} | {r.R2_ens:.4f} |")
L += ["", "## Aturan & klaim", "", "```json", json.dumps(out, indent=1, ensure_ascii=False, default=float), "```"]
open(os.path.join(D, "RINGKASAN_37.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
log("SELESAI 37")
