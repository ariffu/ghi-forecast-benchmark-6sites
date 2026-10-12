# -*- coding: utf-8 -*-
"""Tahap 62 — Sebaran observasi–prediksi CatBoost di enam situs (target rata-rata jam, uji 2025) untuk Online Resource 1.

04c membuat plot diagnostik plots/01_scatter_mean_6situs.png tetapi tidak menyimpan prediksinya. Tahap ini melatih ulang
CatBoost direct dengan pengaturan yang sama persis dengan 04c (iterations 2500, lr 0.03, depth 6, seed 42, early stopping 200
pada 2024, imputasi median latih), memeriksa bahwa R² sama dengan 04c_mean_6situs/baseline_mean_6situs.csv (CB_R2), lalu:
  62_scatter_6situs/preds_cb_6situs.npz         prediksi uji per situs (y, p, b)
  62_scatter_6situs/scatter_6situs.csv          R², RMSE, MAE, bias per situs
  plots/final/FigS05.{png,pdf} + eps_submission/FigS5.eps   gambar rilis (hexbin, 2 × 3 panel)
Keluaran 04c tidak disentuh. Jalankan: python -u 62_scatter_6situs.py  (tambahkan --plot-only untuk menggambar dari npz)
"""
import os, sys, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common
from _common import BASE, SITES
assert _common.FEATSET == "P2", "Online Resource v3 = 43 prediktor (FEATSET=P2)"

B = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(B, "62_scatter_6situs"); os.makedirs(OUT, exist_ok=True)
NPZ = os.path.join(OUT, "preds_cb_6situs.npz")
FIN = os.path.join(B, "plots", "final"); SUB = os.path.join(FIN, "eps_submission")
LAB = {"banten": "Banten", "bengkulu": "Bengkulu", "jambi": "Jambi", "jogja": "Yogyakarta", "kalbar": "West Kalimantan", "semarang": "Central Java"}
REF = pd.read_csv(os.path.join(BASE, "04c_mean_6situs", "baseline_mean_6situs.csv")).set_index("site")

def r2(y, p): return 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()

if "--plot-only" not in sys.argv:
    from catboost import CatBoostRegressor
    from _common import prepare, split_idx
    store = {}
    for site in SITES:
        df, feats, yr = prepare(site, l_filter=5)
        tr, va, te = split_idx(df, yr, tgt="mean")
        y = df["y_mean"].to_numpy(); b = df["base_mean"].to_numpy(); X = df[feats]
        med = X.iloc[tr].median().fillna(0.0)
        cb = CatBoostRegressor(iterations=2500, learning_rate=0.03, depth=6, loss_function="RMSE", verbose=0, random_seed=42)
        cb.fit(X.iloc[tr].fillna(med), y[tr], eval_set=(X.iloc[va].fillna(med), y[va]), early_stopping_rounds=200, use_best_model=True)
        p = cb.predict(X.iloc[te].fillna(med))
        store[f"{site}__y"], store[f"{site}__p"], store[f"{site}__b"] = y[te], p, b[te]
        d = r2(y[te], p) - REF.loc[site, "CB_R2"]
        print(f"{site}: R2={r2(y[te], p):.4f} (04c {REF.loc[site, 'CB_R2']:.4f}, selisih {d:+.4f})", flush=True)
        assert abs(d) < 5e-4, f"{site}: CatBoost tidak mereproduksi 04c"
        del df, X; import gc; gc.collect()
    np.savez(NPZ, **store)

Z = np.load(NPZ)
rows = []
for s in SITES:
    y, p = Z[f"{s}__y"], Z[f"{s}__p"]
    rows.append(dict(site=s, n=len(y), R2=round(r2(y, p), 4), RMSE=round(float(np.sqrt(((y - p) ** 2).mean())), 1),
                     MAE=round(float(np.abs(y - p).mean()), 1), bias=round(float((p - y).mean()), 1)))
T = pd.DataFrame(rows); T.to_csv(os.path.join(OUT, "scatter_6situs.csv"), index=False); print(T.to_string(index=False))

# ---------- gambar rilis (gaya 16_final_figs_release_en.py) ----------
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "DejaVu Sans"], "mathtext.fontset": "dejavusans",
                     "font.size": 9, "axes.labelsize": 8.5, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
                     "axes.spines.top": False, "axes.spines.right": False})
W2 = 6.85; LIM = 1250
VMAX = max(plt.hexbin(Z[f"{s}__y"], Z[f"{s}__p"], gridsize=40, extent=(0, LIM, 0, LIM)).get_array().max() for s in SITES); plt.close("all")
fig, axes = plt.subplots(2, 3, figsize=(W2, 4.7), sharex=True, sharey=True)
for k, (ax, s) in enumerate(zip(axes.flat, SITES)):
    y, p = Z[f"{s}__y"], Z[f"{s}__p"]; r = T.set_index("site").loc[s]
    hb = ax.hexbin(y, p, gridsize=40, bins="log", cmap="viridis", mincnt=1, extent=(0, LIM, 0, LIM), vmin=1, vmax=VMAX)
    ax.plot([0, LIM], [0, LIM], "r--", lw=0.8)
    ax.set_xlim(0, LIM); ax.set_ylim(0, LIM); ax.set_aspect("equal")
    ax.set_xticks([0, 400, 800, 1200]); ax.set_yticks([0, 400, 800, 1200])
    # 2026-10-12: nama stasiun pindah ke judul panel; kotak metrik 2 baris, opak bertepi tipis, di kiri atas (prediksi > ~1060 W m⁻², kosong di
    # semua panel). Sebelumnya kotak semi-transparan 3 baris tampak hanya di bagian yang menumpuk hexbin sehingga terlihat menutupi "m⁻²".
    ax.text(0.03, 0.97, f"$R^2$ = {r.R2:.3f}\nRMSE = {r.RMSE:.0f} W m$^{{-2}}$", transform=ax.transAxes, ha="left", va="top",
            fontsize=7, linespacing=1.3, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", lw=0.5, alpha=1.0), zorder=5)
    ax.text(0.0, 1.03, rf"$\mathbf{{({'abcdef'[k]})}}$  {LAB[s]}", transform=ax.transAxes, fontsize=8.5, ha="left", va="bottom")
    if k % 3 == 0: ax.set_ylabel("Predicted GHI (W m$^{-2}$)")
    if k >= 3: ax.set_xlabel("Observed GHI (W m$^{-2}$)")
fig.tight_layout(rect=[0, 0, 0.92, 1])
cax = fig.add_axes([0.93, 0.15, 0.015, 0.7]); cbar = fig.colorbar(hb, cax=cax); cbar.set_label("count", fontsize=7.5); cbar.ax.tick_params(labelsize=6.5)
for ext in ("png", "pdf"): fig.savefig(os.path.join(FIN, f"FigS05.{ext}"), dpi=600 if ext == "png" else 300)
fig.savefig(os.path.join(SUB, "FigS5.eps"), format="eps")
print("  -> FigS05", flush=True)
