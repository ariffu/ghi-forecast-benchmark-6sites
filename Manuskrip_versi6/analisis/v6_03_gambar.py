# Manuskrip V6: dibuat oleh analisis/00d_siapkan_gambar_hasil_v6.py dari Manuskrip_versi5/analisis/v4_03_gambar.py (sha256 e304cbe5c2344b23…); jangan disunting langsung.
# -*- coding: utf-8 -*-
"""Naskah v5 (salinan skrip v4, jalur diubah), analisis 03 — gambar naskah (Fig. 2–5) dan angka turunan (2026-10-23).

Sumber (tanpa pelatihan ulang):
  - rerun protokol baku: hasil/daftar_periksa/{tabel3_baru.csv, metrik_per_seed.csv, catboost_vs_ridge_baru.csv}, prediksi seed 42
  - ablasi LightGBM tahap 27: replication_ablation_block.csv, preds_replication_<situs>.npz
  - ablasi CatBoost residual: ../hasil/ablasi_catboost_residual.csv (analisis 02)
  - analisis 01: ../hasil/{a_konvergensi, b_galat_kelas, c_clp_kelas}.csv
  - uji sinyal sintetis (training mirip, uji 07): hasil/sinyal_sintetis.csv
Keluaran (versi satu kebaruan, 2026-10-23; FigS2 ditambahkan 2026-10-25): ../gambar/Fig3_konvergensi, Fig4_ablasi, Fig5_manfaat_clp,
FigS1_kontrol_konvergensi, FigS2_shap_bengkulu (.png/.pdf);
../hasil/angka_gambar.json
Jalankan: python -u 03_gambar_v4.py
"""
import os, json, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.patheffects as pe
HERE =os.path.dirname(os.path.abspath(__file__)); V4 = os.path.dirname(HERE); ROOT = os.path.dirname(V4)
P = os.path.join(ROOT, "paper_v2_clpbanten"); PV = os.path.join(V4, "pipeline"); RR = os.path.join(V4, "protokol", "hasil"); H = os.path.join(V4, "hasil")
G = os.path.join(V4, "gambar"); os.makedirs(G, exist_ok=True)
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
LAB = dict(banten="Banten", bengkulu="Bengkulu", jambi="Jambi", jogja="Yogyakarta", kalbar="West Kalimantan", semarang="Central Java")
M8 = ["LightGBM", "CatBoost", "XGBoost", "MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"]
ML = dict(LightGBM="LightGBM", CatBoost="CatBoost", XGBoost="XGBoost", MLP="MLP", LSTM="LSTM", Transformer="Transformer",
          LSTM_hybrid="LSTM-hybrid", Transformer_hybrid="Transformer-hybrid")
COL = dict(LightGBM="#1b5e20", CatBoost="#43a047", XGBoost="#a5d6a7", MLP="#ef6c00", LSTM="#1565c0", Transformer="#6a1b9a",
           LSTM_hybrid="#64b5f6", Transformer_hybrid="#ba68c8")
MK = dict(LightGBM="o", CatBoost="s", XGBoost="D", MLP="^", LSTM="v", Transformer="<", LSTM_hybrid=">", Transformer_hybrid="P")
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7.5,
                     "ytick.labelsize": 7.5, "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300})
W2 = 7.0
def panel(ax, t, x=-0.12, y=1.04): ax.text(x, y, t, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")
def save(fig, n): fig.savefig(os.path.join(G, n + ".png"), bbox_inches="tight"); fig.savefig(os.path.join(G, n + ".pdf"), bbox_inches="tight"); plt.close(fig)
def r2(y, p): return 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()

T3 = pd.read_csv(os.path.join(RR, "daftar_periksa", "tabel3_baru.csv")).set_index(["blok", "site"])
R2m = T3.xs("R2", level="blok").loc[SITES]
MS = pd.read_csv(os.path.join(RR, "daftar_periksa", "metrik_per_seed.csv"))
SD = MS[MS.model.isin(M8)].groupby(["site", "model"]).R2.std(ddof=1).unstack().loc[SITES, M8]
BR = pd.read_csv(os.path.join(RR, "daftar_periksa", "catboost_vs_ridge_baru.csv")).set_index("site").loc[SITES]
AK = pd.read_csv(os.path.join(H, "a_konvergensi.csv")).set_index("site").loc[SITES]
RB = pd.read_csv(os.path.join(PV, "27_block_bootstrap", "replication_ablation_block.csv")).set_index(["site", "effect"])
CB = pd.read_csv(os.path.join(H, "ablasi_catboost_residual.csv")).set_index(["site", "effect"])
BG = pd.read_csv(os.path.join(H, "b_galat_kelas.csv")); CC = pd.read_csv(os.path.join(H, "c_clp_kelas.csv"))
J = {}

# CLP: porsi sisa galat model inti yang dihapus
clp_share = {}
for s in SITES:
    Z = np.load(os.path.join(PV, "27_block_bootstrap", f"preds_replication_{s}.npz"), allow_pickle=True)
    a, b_ = r2(Z["y"], Z["T1"]), r2(Z["y"], Z["T1+CLP"]); clp_share[s] = 100 * (b_ - a) / (1 - a)
J["clp_porsi_sisa_pct"] = [min(clp_share.values()), max(clp_share.values())]
J["clp_porsi_sisa_per_situs"] = {s: float(v) for s, v in clp_share.items()}   # tanpa pembulatan: 04 membulatkan sekali (pembulatan ganda membuat Banten 7,65 → 7,7)

# ---------- Fig. 2: konvergensi ----------
spread = R2m[M8].max(axis=1) - R2m[M8].min(axis=1)
# panel a: tangga R² per stasiun (smart persistence → ridge → rentang delapan arsitektur; opsi B, analisis 12, dipilih 2026-10-25)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(W2, 3.0), gridspec_kw={"width_ratios": [1.5, 1], "wspace": 0.45})
x = np.arange(len(SITES)); lo8 = R2m[M8].min(axis=1); hi8 = R2m[M8].max(axis=1)
for s, yy in zip(SITES, x):
    a1.plot([R2m.loc[s, "SP"], lo8[s]], [yy, yy], color="#c9c8c3", lw=1.0, zorder=1)
    a1.plot(R2m.loc[s, "SP"], yy, "o", ms=5, mfc="white", mec="#8a8984", mew=1.0, zorder=3)
    a1.plot(R2m.loc[s, "Ridge"], yy, "o", ms=5, color="#52514e", zorder=3)
    a1.add_patch(plt.Rectangle((lo8[s], yy - 0.22), hi8[s] - lo8[s], 0.44, color="#2a78d6", lw=0, zorder=3))
    a1.text(hi8[s] + 0.004, yy, f"{hi8[s] - lo8[s]:.3f}", va="center", ha="left", fontsize=6.3, color="#52514e")
a1.set_yticks(x); a1.set_yticklabels([LAB[s] for s in SITES]); a1.set_ylim(len(SITES) - 0.5, -0.6); a1.tick_params(axis="y", length=0)
a1.set_xlim(0.58, 0.94); a1.set_xlabel("$R^2$ (test year 2025)"); a1.grid(axis="x", lw=0.3, color="0.9")
h = [Line2D([], [], ls="", marker="o", ms=5, mfc="white", mec="#8a8984", label="Smart persistence"),
     Line2D([], [], ls="", marker="o", ms=5, color="#52514e", label="Ridge regression"),
     Patch(color="#2a78d6", label="Range of the eight architectures (value = spread)")]
a1.legend(handles=h, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.01), fontsize=6.4, handletextpad=0.3, columnspacing=0.9)
panel(a1, "a", x=-0.3, y=1.04)
w = 0.2
comp = [(spread, "Spread of the eight architectures", "#9e9e9e"), (AK.C3_dR2, "Combining all eight (stacking)", "#212121"),
        (pd.Series({s: RB.loc[(s, "dCLP"), "dR2"] for s in SITES}), "Adding satellite cloud (CLP)", "#2e7d32"),
        (BR.dR2, "CatBoost − ridge", "#90a4ae")]
for k, (v, l, c) in enumerate(comp): a2.barh(x + (k - 1.5) * w, v.loc[SITES], w, color=c, label=l)
a2.set_yticks(x); a2.set_yticklabels([LAB[s] for s in SITES]); a2.invert_yaxis(); a2.set_xlabel("Difference in $R^2$")
a2.set_xlim(0, 0.06); a2.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.4, -0.2), fontsize=5.9); a2.grid(axis="x", lw=0.3, color="0.85"); panel(a2, "b", y=1.04)
save(fig, "Fig3_konvergensi")

# ---------- Fig. 3: informasi yang sama ----------
Y = np.load(os.path.join(RR, "nn", "yb_bengkulu.npz"), allow_pickle=True); yb, bb_ = Y["y"], Y["b"]
K = np.array([np.load(os.path.join(RR, "pohon" if m in M8[:3] else "nn", f"pred_bengkulu_{m}_s42.npy")).astype(float) - bb_ for m in M8])
CM = np.corrcoef(K)
SY = pd.read_csv(os.path.join(P, "114_pendukung_v610", "a3_sintetis", "sinyal_sintetis.csv"))   # Manuskrip V6: V6.10
fig = plt.figure(figsize=(W2, 3.4)); gs = fig.add_gridspec(1, 2, width_ratios=[1.1, 1.0], wspace=0.55)
a1 = fig.add_subplot(gs[0]); im = a1.imshow(CM, vmin=0.85, vmax=1.0, cmap="Greens")
a1.set_xticks(range(8)); a1.set_yticks(range(8)); full = [ML[m] for m in M8]   # nama lengkap (singkatan tidak didefinisikan di keterangan)
a1.set_xticklabels(full, rotation=90, fontsize=6.3); a1.set_yticklabels(full, fontsize=6.3)
for i in range(8):
    for j in range(8):
        if i != j: a1.text(j, i, f"{CM[i, j]:.2f}"[1:], ha="center", va="center", fontsize=4.8, color="white" if CM[i, j] > 0.95 else "black")
a1.set_title("Correlation of corrections to\nsmart persistence (Bengkulu)", fontsize=7.0, loc="left"); panel(a1, "a", x=-0.62, y=1.02)
if False:
    xx = np.arange(len(SITES))
    a2.errorbar(xx - 0.12, AK.C1_dR2, yerr=[AK.C1_dR2 - AK.C1_lo, AK.C1_hi - AK.C1_dR2], fmt="o", ms=3.5, color="#757575", capsize=1.5, lw=0.8, label="Mean of eight")
    a2.errorbar(xx + 0.12, AK.C3_dR2, yerr=[AK.C3_dR2 - AK.C3_lo, AK.C3_hi - AK.C3_dR2], fmt="s", ms=3.5, color="#212121", capsize=1.5, lw=0.8, label="Stacking (cross-fitted)")
    a2.scatter(xx, [RB.loc[(s, "dCLP"), "dR2"] for s in SITES], marker="*", s=40, color="#2e7d32", label="Adding CLP (core model)", zorder=3)
    a2.set_xticks(xx); a2.set_xticklabels([LAB[s][:4] + ("." if len(LAB[s]) > 4 else "") for s in SITES], rotation=60, fontsize=6.5)
    a2.set_ylabel("Gain in $R^2$"); a2.axhline(0.002, ls=":", lw=0.7, color="0.4"); a2.set_ylim(0, 0.032)
    a2.legend(frameon=False, fontsize=5.6, loc="upper center", bbox_to_anchor=(0.45, -0.33)); a2.set_title("$\\bf{b}$  Combining models vs\nadding information", fontsize=7.0, loc="left", x=-0.3)
a3 = fig.add_subplot(gs[1]); scen = ["S_A tabular", "S_B sekuens", "S_C setara"]
slab = ["Signal in\npredictors", "Signal in\nwindow", "Equal\ninformation"]
mods = [("LightGBM, 43 fitur", "LightGBM (44 predictors)", "#2e7d32", "o"), ("BiLSTM, jendela", "BiLSTM (2-h window)", "#1565c0", "s"),
        ("BiLSTM-hibrid, jendela + 43 fitur", "BiLSTM-hybrid (both)", "#64b5f6", "D")]
# titik, bukan batang: sumbu y tidak dimulai dari nol, jadi batang akan melebih-lebihkan selisih
for k, (m, l, c, mk) in enumerate(mods):
    v = [SY[(SY.skenario == sc) & (SY.model == m)].R2.iloc[0] for sc in scen]
    a3.plot(np.arange(3) + (k - 1) * 0.22, v, mk, ms=5, color=c, ls="", label=l, zorder=3)
for i, sc in enumerate(scen):
    mx = SY[SY.skenario == sc].R2_maks.iloc[0]; a3.plot([i - 0.4, i + 0.4], [mx, mx], color="k", lw=0.9)
a3.plot([], [], color="k", lw=0.9, label="Known ceiling"); a3.set_ylim(0.85, 0.985); a3.set_xticks(range(3)); a3.set_xticklabels(slab, fontsize=6.3)
a3.set_xlim(-0.6, 2.6); a3.grid(axis="y", lw=0.3, color="0.88")
a3.set_ylabel("$R^2$ (synthetic target)"); a3.legend(frameon=False, fontsize=6.0, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
a3.set_title("Synthetic-signal control (Bengkulu)", fontsize=7.0, loc="left"); panel(a3, "b", x=-0.3, y=1.02)
save(fig, "FigS1_kontrol_konvergensi")
J["koreksi_corr_bengkulu"] = [float(CM[np.triu_indices(8, 1)].min()), float(np.median(CM[np.triu_indices(8, 1)]))]

# ---------- Fig. 4: ablasi sumber ----------
EFF = [("dCLP", "+ CLP", "#2e7d32"), ("dAWS", "+ AWS", "#ef6c00"), ("dSYNOP", "+ SYNOP cloud", "#6a1b9a"),
       ("dAWS|CLP", "+ AWS on top of CLP", "#ffb74d"), ("dSYNOP|CLP", "+ SYNOP on top of CLP", "#b39ddb")]
fig, ax = plt.subplots(figsize=(W2, 2.7)); w = 0.15
for k, (e, l, c) in enumerate(EFF):
    v = np.array([RB.loc[(s, e), "dR2"] for s in SITES]); lo = np.array([RB.loc[(s, e), "blk_lo"] for s in SITES]); hi = np.array([RB.loc[(s, e), "blk_hi"] for s in SITES])
    ax.bar(x + (k - 2) * w, v, w, color=c, label=l + " (LightGBM)", yerr=[v - lo, hi - v], error_kw=dict(lw=0.6, capsize=1.2))
# CatBoost di kiri batang CLP dengan CI sendiri, agar CI LightGBM tidak terbaca sebagai CI CatBoost
vc = np.array([CB.loc[(s, "dCLP"), "dR2"] for s in SITES]); lc = np.array([CB.loc[(s, "dCLP"), "blk_lo"] for s in SITES]); hc = np.array([CB.loc[(s, "dCLP"), "blk_hi"] for s in SITES])
ax.errorbar(x - 2 * w - 0.13, vc, yerr=[vc - lc, hc - vc], fmt="D", ms=3.6, color="k", elinewidth=0.6, capsize=1.2, zorder=4, label="+ CLP (CatBoost)")
ax.axhline(0, color="k", lw=0.6); ax.axhline(0.002, ls=":", lw=0.7, color="0.4")
ax.text(len(SITES) - 0.52, 0.0024, "0.002", ha="right", va="bottom", fontsize=6.2, color="0.35")
ax.set_xticks(x); ax.set_xticklabels([LAB[s] for s in SITES]); ax.set_ylabel("Change in $R^2$ (95% CI)")
ax.legend(ncol=3, frameon=False, fontsize=6.3, loc="upper left"); ax.set_ylim(-0.004, 0.042)
save(fig, "Fig4_ablasi")

# ---------- Fig. 5: di mana galat tersisa dan di mana CLP membantu ----------
fig, (a2, a1) = plt.subplots(1, 2, figsize=(W2, 2.9), gridspec_kw={"width_ratios": [1.25, 1]})
cls = [("waktu", "06–10", "06–10 WIB"), ("waktu", "10–14", "10–14 WIB"), ("waktu", "14–18", "14–18 WIB"),
       ("perubahan", "stabil", "Stable"), ("perubahan", "sedang", "Moderate"), ("perubahan", "berubah", "Changing")]
for i, (g, k, l) in enumerate(cls):
    d = BG[(BG.grup == g) & (BG.kelas == k)]
    a1.bar(i - 0.18, d.porsi_sampel.mean() * 100, 0.36, color="#d9d8d3", label="Share of forecasts" if i == 0 else None)
    # abu-abu gelap, bukan merah: merah sudah dipakai untuk Yogyakarta di panel a
    a1.bar(i + 0.18, d.porsi_SSE_CatBoost.mean() * 100, 0.36, color="#52514e", label="Share of squared error" if i == 0 else None)
    a1.plot([i + 0.18] * 2, [d.porsi_SSE_CatBoost.min() * 100, d.porsi_SSE_CatBoost.max() * 100], color="k", lw=0.9,
            path_effects=[pe.withStroke(linewidth=2.4, foreground="white")])
a1.plot([], [], color="k", lw=0.9, label="Range over stations")
a1.set_xticks(range(6)); a1.set_xticklabels([c[2] for c in cls], rotation=35, ha="right"); a1.set_ylabel("% (mean of six stations)")
a1.axvline(2.5, color="0.6", lw=0.5); a1.text(1, 84, "Time of origin", ha="center", va="center", fontsize=6.8)
a1.text(4, 84, "Persistence-error\ntercile", ha="center", va="center", fontsize=6.8, linespacing=1.0)
a1.set_ylim(0, 92); a1.legend(frameon=False, fontsize=6.0, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.3)); panel(a1, "b")
cls2 = [("langit", "cerah", "Clear"), ("langit", "berawan sebagian", "Partly\ncloudy"), ("langit", "mendung", "Overcast"),
        ("perubahan", "stabil", "Stable"), ("perubahan", "sedang", "Moderate"), ("perubahan", "berubah", "Changing")]
for i, (g, k, l) in enumerate(cls2):
    for j, s in enumerate(SITES):
        d = CC[(CC.site == s) & (CC.grup == g) & (CC.kelas == k)].iloc[0]
        a2.errorbar(i + (j - 2.5) * 0.11, d.turun_pct, yerr=[[d.turun_pct - d.lo], [d.hi - d.turun_pct]], fmt="o", ms=2.6, lw=0.6,
                    color=plt.cm.tab10(j), label=LAB[s] if i == 0 else None)
a2.axhline(0, color="k", lw=0.6); a2.axvline(2.5, color="0.6", lw=0.5)
a2.set_xticks(range(6)); a2.set_xticklabels([c[2] for c in cls2], fontsize=6.2); a2.set_ylabel("RMSE reduction by CLP (%, 95% CI)")
a2.text(1, 23.5, "Sky condition at origin", ha="center", fontsize=6.8); a2.text(4, 23.5, "Persistence-error tercile", ha="center", fontsize=6.8)
a2.set_ylim(-14, 25); a2.legend(frameon=False, fontsize=5.8, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.17)); panel(a2, "a")
save(fig, "Fig5_manfaat_clp")

# ---------- Fig. S2: atribusi fitur Bengkulu (digambar ulang dengan gaya v4 dari keluaran tahap 02b; 2026-10-25) ----------
# LightGBM konfigurasi ablasi (Tabel S3); kurva seleksi pada 43 prediktor memberi R² uji 0,910, bukan 0,908 LightGBM utama
NAME = {"kt": "$k_c$", "dhi_wm2": "DHI", "dni_wm2": "DNI", "ghi_wm2": "GHI", "reflected_wm2": "Reflected irradiance",
        "clear_sky_ghi": "Clear-sky GHI", "clear_sky_ghi_h1": "Clear-sky GHI (t + 1 h)", "decl_noaa_deg": "Solar declination", "eot_min": "Equation of time",
        "kt_delta_10m": "Δ$k_c$ (10 min)", "kt_delta_20m": "Δ$k_c$ (20 min)", "kt_delta_30m": "Δ$k_c$ (30 min)", "kt_delta_60m": "Δ$k_c$ (60 min)",
        "kt_roll_30m_mean": "$k_c$ mean (30 min)", "kt_roll_60m_mean": "$k_c$ mean (60 min)", "kt_roll_30m_std": "$k_c$ s.d. (30 min)",
        "kt_roll_60m_std": "$k_c$ s.d. (60 min)", "kt_std_3h": "$k_c$ s.d. (3 h)", "clp_cot": "COT", "clp_cth_km": "CTH", "clp_cer_um": "Effective radius",
        "clp_cloud_present_int": "Cloud flag", "clp_cloud_frac": "Cloud fraction", "clp_cot_delta_60m": "ΔCOT (60 min)", "clp_cot_roll_180m_mean": "COT mean (3 h)",
        "clp_cth_lag_60m": "CTH (60 min earlier)", "clp_cth_roll_180m_mean": "CTH mean (3 h)", "aws_temp_c": "Temperature (AWS)",
        "aws_rh_pct": "Relative humidity (AWS)", "aws_pressure_hpa": "Pressure (AWS)", "aws_wind_speed_ms": "Wind speed (AWS)",
        "aws_wind_dir_sin": "Wind direction (sin)", "aws_wind_dir_cos": "Wind direction (cos)", "aws_rain_mm": "Rainfall (10 min)",
        "aws_rain_sum_180m": "Rainfall (3 h)", "aws_temp_delta_60m": "ΔTemperature (60 min)", "aws_rh_delta_60m": "ΔRH (60 min)",
        "aws_pressure_delta_60m": "ΔPressure (60 min)", "synop_cloud_cover_oktas": "Total cloud cover (SYNOP)", "synop_cl": "Low cloud type",
        "synop_cm": "Middle cloud type", "synop_ch": "High cloud type", "synop_visibility_km": "Visibility (SYNOP)", "synop_present_weather_ww": "Present weather (SYNOP)"}
GRP = lambda f: "Satellite cloud (CLP)" if f.startswith("clp_") else "Surface meteorology (AWS)" if f.startswith("aws_") else "SYNOP" if f.startswith("synop_") else "Core"
GC = {"Core": "#8c8c8c", "Satellite cloud (CLP)": "#2e7d32", "Surface meteorology (AWS)": "#ef6c00", "SYNOP": "#6a1b9a"}   # warna kelompok = Fig. 4
SH = pd.read_csv(os.path.join(P, "114_pendukung_v610", "a2_shap", "shap_global_mean.csv")); SH.columns = ["f", "v"]; SH = SH.head(15)[::-1]
SS = pd.read_csv(os.path.join(P, "114_pendukung_v610", "a2_shap", "selection_sweep_mean.csv")).dropna()
fig, (a1, a2) = plt.subplots(1, 2, figsize=(W2, 3.1), gridspec_kw={"width_ratios": [1.15, 1], "wspace": 0.35})
a1.barh([NAME[f] for f in SH.f], SH.v, color=[GC[GRP(f)] for f in SH.f], height=0.72)
a1.set_xlabel("Mean |SHAP| (W m$^{-2}$)"); a1.tick_params(axis="y", length=0, labelsize=6.8); a1.grid(axis="x", lw=0.3, color="0.88")
a1.legend(handles=[Patch(color=c, label=k) for k, c in GC.items() if k in {GRP(f) for f in SH.f}], loc="lower right", frameon=False, fontsize=6.4)
panel(a1, "a", x=-0.55, y=1.0)
a2.plot(SS.K, SS.val_R2, "o--", ms=3.6, lw=1.0, color="#8a8984", label="Validation 2024")
a2.plot(SS.K, SS.test_R2, "s-", ms=3.6, lw=1.2, color="#0b0b0b", label="Test 2025")
a2.set_xlabel("Number of predictors retained (by importance rank)"); a2.set_ylabel("$R^2$"); a2.grid(lw=0.3, color="0.88")
a2.legend(frameon=False, loc="lower right", fontsize=6.6); panel(a2, "b", y=1.0)
save(fig, "FigS2_shap_bengkulu")
J["shap_seleksi_uji_44"] = float(SS.loc[SS.K == 44, "test_R2"].iloc[0])

json.dump(J, open(os.path.join(H, "angka_gambar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(J, ensure_ascii=False))
