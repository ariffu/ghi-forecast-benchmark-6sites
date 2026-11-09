# -*- coding: utf-8 -*-
"""Manuskrip V6, analisis 04 — mengisi tabel MANUSKRIP_v6.md dan ESM_v6.md dari keluaran V6 (V6.10, P2F 44), dan menulis angka teks.
Turunan dari Manuskrip_versi5/analisis/v4_04_isi_tabel.py (format dan definisi sama), dengan perubahan V6:
  - Tabel 1 dan S12 dari provenance V6.10 (v6_02_data_dan_sampel.py); koordinat Bengkulu dan Jambi (ASRS) menurut pengguna;
  - Tabel S1 tanpa uji penjajaran SYNOP (basis data V6.10 sudah membawa laporan SYNOP maju ≤ 50 menit);
  - Tabel S2 dibangkitkan dari data (ketersediaan tahun latih), Tabel S3 dari metrik protokol V6;
  - Tabel S8 dan S11 dari tahap 114 (V6.10).
Setiap tabel ditulis di antara <!-- NAMA:MULAI --> dan <!-- NAMA:SELESAI -->. Angka teks: ../hasil/angka_teks_v6.json.
Jalankan: DATA_DIR/CLEARSKY_DIR/CLP_EKSTRA_DIR = V6.10, FEATSET=P2F, PYTHONIOENCODING=utf-8 python -u v6_04_isi_tabel.py"""
import os, re, sys, json, glob, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); V6 = os.path.dirname(HERE); ROOT = os.path.dirname(V6)
P = os.path.join(ROOT, "paper_v2_clpbanten"); PV = os.path.join(V6, "pipeline"); RR = os.path.join(V6, "protokol", "hasil"); DP = os.path.join(RR, "daftar_periksa")
H = os.path.join(V6, "hasil"); T114 = os.path.join(P, "114_pendukung_v610"); sys.path.insert(0, P)
import _common
from _common import prepare, split_idx
assert _common.FEATSET == "P2F" and len(_common.P2_AKTIF) == 44
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
LAB = dict(banten="Banten", bengkulu="Bengkulu", jambi="Jambi", jogja="Yogyakarta", kalbar="West Kalimantan", semarang="Central Java")
M8 = ["LightGBM", "CatBoost", "XGBoost", "MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"]
HD = ["LightGBM", "CatBoost", "XGBoost", "MLP", "LSTM", "Transformer", "LSTM-hybrid", "Transformer-hybrid"]; NM = dict(zip(M8, HD)); NN = M8[3:]
def f(x, k=3): v = round(float(x), k); v = 0.0 if v == 0 else v; return f"−{abs(v):.{k}f}" if v < 0 else f"{v:.{k}f}"
def sg(x, k=3): v = round(float(x), k); v = 0.0 if v == 0 else v; return f"−{abs(v):.{k}f}" if v < 0 else f"+{v:.{k}f}"
def sep(*w): return "|" + "|".join("-" * abs(n) + (":" if n > 0 else "") for n in w) + "|"
def ci4(d, lo, hi): return f"{sg(d, 4)} [{sg(lo, 4)}, {sg(hi, 4)}]"
T, A = {}, {}

# ================= Tabel 1 =================
SG = pd.read_csv(os.path.join(H, "sumber_ghi.csv")).set_index(["site", "tahun"])
META = dict(banten=("96733", "6.261°S", "106.751°E", 27), bengkulu=("96255", "3.865°S", "102.312°E", 9), jambi=("96191", "1.601°S", "103.494°E", 24),
            jogja=("96851", "7.731°S", "110.354°E", 182), kalbar=("96583", "0.075°N", "109.191°E", 2), semarang=("96835", "6.985°S", "110.381°E", 6))
L = ["| Station | WMO ID | Latitude | Longitude | Elevation (m a.s.l.) | Logger GHI in 2025 (%) | Measured GHI in 2025 (%) |", sep(-16, -8, 10, 11, 9, 10, 10)]
for s in SITES: m = META[s]; r = SG.loc[(s, 2025)]; L.append(f"| {LAB[s]} | {m[0]} | {m[1]} | {m[2]} | {m[3]} | {r.logger_pct:.1f} | {r.terukur_pct:.1f} |")
T["TABEL1"] = "\n".join(L)
A["logger_2025"] = {s: float(SG.loc[(s, 2025), "logger_pct"]) for s in SITES}; A["terukur_2025"] = {s: float(SG.loc[(s, 2025), "terukur_pct"]) for s in SITES}

# ================= Tabel 3 dan 4 =================
T3 = pd.read_csv(os.path.join(DP, "tabel3_baru.csv")).set_index(["blok", "site"]); R2 = T3.xs("R2", level="blok").loc[SITES]; SK = T3.xs("skill", level="blok").loc[SITES]
CB = pd.read_csv(os.path.join(DP, "catboost_baru.csv")).set_index("site").loc[SITES]
L = ["| Station | Smart persistence R² | Ridge R² | CatBoost R² | CatBoost RMSE (W m⁻²) | Skill score vs smart persistence | Skill score vs CP reference | Spread of eight architectures | Most accurate architecture |",
     sep(-15, 9, 7, 8, 9, 9, 9, 9, -11)]
for s in SITES:
    r = R2.loc[s]; L.append(f"| {LAB[s]} | {f(r.SP)} | {f(r.Ridge)} | {f(CB.loc[s, 'R2'])} | {CB.loc[s, 'RMSE']:.1f} | {f(CB.loc[s, 'skill_pers'])} | {f(CB.loc[s, 'skill_cp'])} | {f(r.Spread)} | {NM[r[M8].astype(float).idxmax()]} |")
T["TABEL3"] = "\n".join(L)
RB = pd.read_csv(os.path.join(PV, "27_block_bootstrap", "replication_ablation_block.csv")).set_index(["site", "effect"])
AC = pd.read_csv(os.path.join(H, "ablasi_catboost_residual.csv")).set_index(["site", "effect"])
def e(D, s, k): v = D.loc[(s, k)]; return sg(v.dR2) + ("*" if v.sig_block == "yes" else "")
L = ["| Station | CLP | 95% CI | AWS | SYNOP cloud | AWS on top of CLP | SYNOP cloud on top of CLP | CLP, CatBoost |", sep(-15, 8, -14, 8, 8, 9, 9, 9)]
for s in SITES:
    v = RB.loc[(s, "dCLP")]
    L.append(f"| {LAB[s]} | {e(RB, s, 'dCLP')} | [{f(v.blk_lo)}, {f(v.blk_hi)}] | {e(RB, s, 'dAWS')} | {e(RB, s, 'dSYNOP')} | {e(RB, s, 'dAWS|CLP')} | {e(RB, s, 'dSYNOP|CLP')} | {e(AC, s, 'dCLP')} |")
T["TABEL4"] = "\n".join(L)

# ================= ESM S4–S7, S9, S10 (definisi sama dengan v5) =================
W11 = (-18, 9, 6, 8, 8, 8, 6, 6, 9, 8, 9, 6)
L = ["| Station | Smart persistence | Ridge | " + " | ".join(HD) + " | Spread |", sep(*W11), "| *R²* |" + " |" * 11]
for s in SITES:
    r = R2.loc[s]; b = r[M8].astype(float).idxmax(); L.append(f"| {LAB[s]} | {f(r.SP)} | {f(r.Ridge)} | " + " | ".join(f"**{f(r[m])}**" if m == b else f(r[m]) for m in M8) + f" | {f(r.Spread)} |")
L.append("| *Skill score* |" + " |" * 11)
for s in SITES:
    r = SK.loc[s]; b = r[M8].astype(float).idxmax(); L.append(f"| {LAB[s]} | — | {f(r.Ridge)} | " + " | ".join(f"**{f(r[m])}**" if m == b else f(r[m]) for m in M8) + f" | {f(r.Spread)} |")
T["ESM_R2"] = "\n".join(L)
S4 = pd.read_csv(os.path.join(DP, "tabelS4_baru.csv")).set_index(["blok", "site"]); MS = pd.read_csv(os.path.join(DP, "metrik_per_seed.csv"))
REF = MS[MS.model.isin(["SmartPersistence", "Ridge"])].set_index(["site", "model"])
L = ["| Station | Smart persistence | Ridge | " + " | ".join(HD) + " |", sep(*W11[:-1])]
for blk, lab in [("RMSE", "*RMSE (W m⁻²)*"), ("MAE", "*MAE (W m⁻²)*")]:
    L.append(f"| {lab} |" + " |" * 10)
    for s in SITES:
        a = S4.loc[(blk, s)]; b = a[M8].astype(float).idxmin(); ref = " | ".join(f"{REF.loc[(s, k), blk]:.1f}" for k in ["SmartPersistence", "Ridge"])
        L.append(f"| {LAB[s]} | {ref} | " + " | ".join(f"**{a[m]:.1f}**" if m == b else f"{a[m]:.1f}" for m in M8) + " |")
L.append("| *Residual R²* |" + " |" * 10)
for s in SITES:
    a = S4.loc[("R2_residual", s)]; b = a[M8].astype(float).idxmax()
    L.append(f"| {LAB[s]} | — | {REF.loc[(s, 'Ridge'), 'R2_res']:.3f} | " + " | ".join(f"**{a[m]:.3f}**" if m == b else f"{a[m]:.3f}" for m in M8) + " |")
T["ESM_GALAT"] = "\n".join(L)
S6 = pd.read_csv(os.path.join(DP, "tabelS6b_baru.csv")).set_index("site").loc[SITES]
L = ["| Station | " + " | ".join(HD[3:]) + " | Spread, seed 42 | Spread, seed means | Spread, range over seeds |", sep(-15, 13, 13, 13, 13, 13, 7, 7, 13)]
for s in SITES:
    r = S6.loc[s]; L.append(f"| {LAB[s]} | " + " | ".join(f"{r[m + '_rerata']:.4f} ± {r[m + '_sd']:.4f}" for m in NN) + f" | {r.spread_seed42:.4f} | {r.spread_rerata_seed:.4f} | {r.spread_seed_min:.4f}–{r.spread_seed_max:.4f} |")
T["ESM_SEED"] = "\n".join(L)
UJ = pd.read_csv(os.path.join(DP, "uji_berpasangan_per_seed.csv")); UJ = UJ[UJ.vs == "LightGBM"]
UJ["arah"] = np.where(UJ.sig_block == "no", "not different", np.where(UJ.dR2 > 0, "more accurate", "less accurate"))
U = UJ.groupby(["model", "arah"]).size().unstack(fill_value=0).reindex(M8[1:]).fillna(0).astype(int)
L = ["| Architecture | Runs | Significantly more accurate | Not different | Significantly less accurate | Mean ΔR² |", sep(-16, 6, 12, 10, 12, 9)]
for m in M8[1:]:
    d = UJ[UJ.model == m]; L.append(f"| {NM[m]} | {len(d)} | {U.loc[m].get('more accurate', 0)} | {U.loc[m].get('not different', 0)} | {U.loc[m].get('less accurate', 0)} | {sg(d.dR2.mean(), 4)} |")
T["ESM_UJI"] = "\n".join(L)
A["uji_nn_mean_dR2"] = {m: float(UJ[UJ.model == m].dR2.mean()) for m in NN}
AK = pd.read_csv(os.path.join(H, "a_konvergensi.csv")).set_index("site").loc[SITES]
JG = json.load(open(os.path.join(H, "angka_gambar.json"), encoding="utf-8"))
L = ["| Station | Correlation of corrections, median (min) | Correlation of errors, median (min) | RMS difference between forecasts, median (W m⁻²) | Mean of eight, ΔR² [95% CI] | Stacking, ΔR² [95% CI] | Remaining error removed by stacking (%) | Remaining error removed by CLP (%) |",
     sep(-13, 10, 10, 9, -18, -18, 9, 9)]
for s in SITES:
    a = AK.loc[s]
    L.append(f"| {LAB[s]} | {a.corr_koreksi_med:.2f} ({a.corr_koreksi_min:.2f}) | {a.err_corr_med:.2f} ({a.err_corr_min:.2f}) | {a.rms_beda_pred_med:.1f} | "
             f"{ci4(a.C1_dR2, a.C1_lo, a.C1_hi)} | {ci4(a.C3_dR2, a.C3_lo, a.C3_hi)} | {a.C3_porsi_sisa_pct:.1f} | {JG['clp_porsi_sisa_per_situs'][s]:.1f} |")
T["ESM_KONV"] = "\n".join(L)
L = ["| Station | CLP | AWS | SYNOP cloud | AWS on top of CLP | SYNOP cloud on top of CLP |", sep(-16, -18, -18, -18, -18, -18)]
for s in SITES:
    L.append(f"| {LAB[s]} | " + " | ".join(ci4(AC.loc[(s, k), 'dR2'], AC.loc[(s, k), 'blk_lo'], AC.loc[(s, k), 'blk_hi']) + ("*" if AC.loc[(s, k), "sig_block"] == "yes" else "")
                                         for k in ["dCLP", "dAWS", "dSYNOP", "dAWS|CLP", "dSYNOP|CLP"]) + " |")
T["ESM_CB"] = "\n".join(L)
BG = pd.read_csv(os.path.join(H, "b_galat_kelas.csv")); CC = pd.read_csv(os.path.join(H, "c_clp_kelas.csv"))
KL = [("langit", "cerah", "Clear ($k_t$ > 0.65)"), ("langit", "berawan sebagian", "Partly cloudy (0.30 < $k_t$ ≤ 0.65)"), ("langit", "mendung", "Overcast ($k_t$ ≤ 0.30)"),
      ("waktu", "06–10", "06–10 WIB"), ("waktu", "10–14", "10–14 WIB"), ("waktu", "14–18", "14–18 WIB"),
      ("perubahan", "stabil", "Stable (lowest third)"), ("perubahan", "sedang", "Moderate"), ("perubahan", "berubah", "Changing (highest third)")]
L = ["| Class | Share of forecasts (%) | Share of squared error (%) | Skill score vs smart persistence | RMSE reduction by CLP (%) | Stations with a significant reduction / increase |", sep(-22, 9, 9, 11, 11, 11)]
rg = lambda a, z: f"{a:.0f}" if f"{a:.0f}" == f"{z:.0f}" else f"{a:.0f}–{z:.0f}"
for g, k, l in KL:
    b = BG[(BG.grup == g) & (BG.kelas == k)]; c = CC[(CC.grup == g) & (CC.kelas == k)]
    L.append(f"| {l} | {rg(100 * b.porsi_sampel.min(), 100 * b.porsi_sampel.max())} | {rg(100 * b.porsi_SSE_CatBoost.min(), 100 * b.porsi_SSE_CatBoost.max())} | "
             f"{f(b.skill.min(), 2)} to {f(b.skill.max(), 2)} | {f(c.turun_pct.min(), 1)} to {f(c.turun_pct.max(), 1)} | {int((c.lo > 0).sum())} / {int((c.hi < 0).sum())} |")
    A[f"kelas|{g}|{k}"] = dict(porsi=[float(b.porsi_sampel.min()), float(b.porsi_sampel.max())], sse=[float(b.porsi_SSE_CatBoost.min()), float(b.porsi_SSE_CatBoost.max())],
                               skill=[float(b.skill.min()), float(b.skill.max())], clp=[float(c.turun_pct.min()), float(c.turun_pct.max())], n_turun=int((c.lo > 0).sum()), n_naik=int((c.hi < 0).sum()),
                               rmse_sp=[float(b.RMSE_SP.min()), float(b.RMSE_SP.max())], rmse_cb=[float(b.RMSE_CatBoost.min()), float(b.RMSE_CatBoost.max())])
T["ESM_KELAS"] = "\n".join(L)
L = ["| Station | Clear | Partly cloudy | Overcast | Stable | Moderate | Changing | All |", sep(-14, -12, -12, -12, -12, -12, -12, -12)]
for s in SITES:
    row = []
    for g, k in [("langit", "cerah"), ("langit", "berawan sebagian"), ("langit", "mendung"), ("perubahan", "stabil"), ("perubahan", "sedang"), ("perubahan", "berubah"), ("semua", "semua")]:
        c = CC[(CC.site == s) & (CC.grup == g) & (CC.kelas == k)].iloc[0]; row.append(f"{f(c.turun_pct, 1)} [{f(c.lo, 1)}, {f(c.hi, 1)}]")
    L.append(f"| {LAB[s]} | " + " | ".join(row) + " |")
T["ESM_CLPKELAS"] = "\n".join(L)
A["clp_semua_turun_pct"] = {s: float(CC[(CC.site == s) & (CC.grup == "semua")].turun_pct.iloc[0]) for s in SITES}
A["clp_semua_turun_W"] = {s: float(CC[(CC.site == s) & (CC.grup == "semua")].turun_W.iloc[0]) for s in SITES}

# ================= ESM S1: kepekaan =================
FI = pd.read_csv(os.path.join(PV, "19_sens_clp_fill", "sens_clp_fill.csv")); fm, fr = FI[FI.variant.str.startswith("masked")].set_index("site"), FI[FI.variant.str.startswith("raw")].set_index("site")
SP_ = pd.read_csv(os.path.join(PV, "28_clp_spatial", "clp_spatial_results.csv")).set_index(["site", "exp"])
LG = pd.read_csv(os.path.join(PV, "31_clp_lag", "clp_lag_results.csv")).set_index(["site", "variant"])
L = ["| Station | ΔR²(CLP): missing retrievals masked → stored values | Box statistics added to core + CLP | Box statistics added to all 44 predictors | ΔR²(CLP): adopted timing → 10 min later (loss) |",
     sep(-12, -16, -18, -18, -17)]
lat = {}
for s in SITES:
    a, d = ("V0", "L10") if s == "kalbar" else ("L10", "L20"); c0, c1 = LG.loc[(s, a), "dCLP"], LG.loc[(s, d), "dCLP"]; lat[s] = 100 * (c0 - c1) / c0
    e1, e2 = SP_.loc[(s, "E1")], SP_.loc[(s, "E2")]
    L.append(f"| {LAB[s]} | {sg(fm.loc[s, 'dCLP'], 4)} → {sg(fr.loc[s, 'dCLP'], 4)} | {ci4(e1.dR2, e1.blk_lo, e1.blk_hi)} | {ci4(e2.dR2, e2.blk_lo, e2.blk_hi)} | {sg(c0, 4)} → {sg(c1, 4)} ({lat[s]:.0f}%) |")
T["ESM_ROBUST"] = "\n".join(L)
A.update(latensi_pct=lat, kotak_E1=[float(SP_.xs("E1", level="exp").dR2.min()), float(SP_.xs("E1", level="exp").dR2.max())], kotak_E2=[float(SP_.xs("E2", level="exp").dR2.min()), float(SP_.xs("E2", level="exp").dR2.max())],
         kotak_E2_bermakna=[s for s in SITES if SP_.loc[(s, "E2"), "meaningful"] == "YES"], kotak_E1_bermakna=[s for s in SITES if SP_.loc[(s, "E1"), "meaningful"] == "YES"],
         isi_clp_maks=float((fm.dCLP - fr.dCLP).abs().max()))

# ================= ESM S2: daftar prediktor dengan ketersediaan tahun latih (dari data) =================
DESK = {"ghi_wm2": ("GHI (pyranometer)", "measured"), "dhi_wm2": ("diffuse horizontal irradiance", "measured or modelled"), "dni_wm2": ("direct normal irradiance", "measured or modelled"),
        "reflected_wm2": ("reflected irradiance", "measured"), "decl_noaa_deg": ("solar declination", "model"), "eot_min": ("equation of time", "model"),
        "clear_sky_ghi": ("clear-sky GHI at t (slot mean)", "model"), "kt": ("clear-sky index $k_c$ = GHI / clear-sky GHI", "derived"), "clear_sky_ghi_h1": ("clear-sky GHI at t + 1 h (slot mean)", "model"),
        "kt_delta_10m": ("change in $k_c$ over 10 min", "derived"), "kt_delta_20m": ("change in $k_c$ over 20 min", "derived"), "kt_delta_30m": ("change in $k_c$ over 30 min", "derived"),
        "kt_delta_60m": ("change in $k_c$ over 60 min", "derived"), "kt_roll_30m_mean": ("30-min mean of $k_c$", "derived"), "kt_roll_30m_std": ("30-min standard deviation of $k_c$", "derived"),
        "kt_roll_60m_mean": ("60-min mean of $k_c$", "derived"), "kt_roll_60m_std": ("60-min standard deviation of $k_c$", "derived"), "kt_std_3h": ("3-h standard deviation of $k_c$", "derived"),
        "clp_cot": ("cloud optical thickness (COT)", "measured"), "clp_cth_km": ("cloud-top height (CTH)", "measured"), "clp_cer_um": ("cloud effective radius", "measured"),
        "clp_cloud_present_int": ("cloud flag (mean COT ≥ 1)", "derived"), "clp_cloud_frac": ("cloud fraction (share of box pixels with a COT retrieval)", "measured"),
        "clp_cot_delta_60m": ("change in COT over 60 min", "derived"), "clp_cot_roll_180m_mean": ("3-h mean of COT", "derived"), "clp_cth_lag_60m": ("CTH 60 min earlier", "derived"),
        "clp_cth_roll_180m_mean": ("3-h mean of CTH", "derived"), "synop_visibility_km": ("visibility", "measured"), "synop_cloud_cover_oktas": ("total cloud cover N (okta)", "measured"),
        "synop_cl": ("low-cloud type (CL)", "measured"), "synop_cm": ("middle-cloud type (CM)", "measured"), "synop_ch": ("high-cloud type (CH)", "measured"),
        "synop_present_weather_ww": ("present weather (ww)", "measured"), "aws_temp_c": ("air temperature", "measured"), "aws_rh_pct": ("relative humidity", "measured"),
        "aws_pressure_hpa": ("station pressure", "measured"), "aws_wind_speed_ms": ("wind speed", "measured"), "aws_wind_dir_sin": ("wind direction (sine; 0 when calm)", "measured"),
        "aws_wind_dir_cos": ("wind direction (cosine; 0 when calm)", "measured"), "aws_rain_mm": ("10-min rainfall", "measured"), "aws_temp_delta_60m": ("change in air temperature over 60 min", "derived"),
        "aws_rh_delta_60m": ("change in relative humidity over 60 min", "derived"), "aws_pressure_delta_60m": ("change in pressure over 60 min", "derived"), "aws_rain_sum_180m": ("3-h rainfall", "derived")}
GRUP = lambda c: "Satellite cloud (CLP)" if c.startswith("clp_") else "SYNOP" if c.startswith("synop_") else "Surface meteorology (AWS)" if c.startswith("aws_") else "Core"
AV, AVU, SYN_AV = {}, {}, {}
for s in SITES:
    df, feats, yr = prepare(s, l_filter=5); tr, va, te = split_idx(df, yr, tgt="mean"); assert len(feats) == 44
    AV[s] = df.iloc[tr][feats].notna().mean() * 100; AVU[s] = df.iloc[te][feats].notna().mean() * 100
    SYN_AV[s] = float(df.iloc[te]["synop_cloud_cover_oktas"].notna().mean() * 100)
AVd = pd.DataFrame(AV); AVt = pd.DataFrame(AVU)
order = sorted(feats, key=lambda c: ["Core", "Satellite cloud (CLP)", "SYNOP", "Surface meteorology (AWS)"].index(GRUP(c)))
def rgp(v):
    lo, hi = np.floor(v.min() + 1e-9), np.floor(v.max() + 1e-9); lo = 100 if v.min() >= 99.95 else lo; hi = 100 if v.max() >= 99.95 else hi
    return f"{lo:.0f}" if lo == hi else f"{lo:.0f}–{hi:.0f}"
L = ["| Group | Predictor | Description | Origin | Availability (%) |", sep(-14, -24, -34, -9, 8)]
for c in order: L.append(f"| {GRUP(c)} | `{c}` | {DESK[c][0]} | {DESK[c][1]} | {rgp(AVd.loc[c])} |")
T["ESM_PRED"] = "\n".join(L)
A["ketersediaan_latih_min"] = float(AVd.min().min()); A["synop_okta_uji_pct"] = SYN_AV
A["tersedia_kurang_100"] = {c: [float(AVd.loc[c].min()), float(AVd.loc[c].max())] for c in order if AVd.loc[c].min() < 99.95}

# ================= ESM S3: parameter jaringan saraf dan epoch =================
MN = pd.concat([pd.read_csv(fp) for fp in glob.glob(os.path.join(RR, "nn", "metrik_*.csv"))]).drop_duplicates(["site", "model", "seed"])
A["n_parameter"] = {m: int(MN[MN.model == m].n_parameter.iloc[0]) for m in NN}; assert all(MN[MN.model == m].n_parameter.nunique() == 1 for m in NN)
ep = MN.groupby(["site", "model"]).epoch_terbaik.median(); A["epoch_median"] = [float(ep.min()), float(ep.max())]; A["epoch_berhenti_maks"] = int(MN.epoch_berhenti.max())

# ================= ESM S8: kontrol sinyal sintetis (tahap 114 a3) =================
SY = pd.read_csv(os.path.join(T114, "a3_sintetis", "sinyal_sintetis.csv")); SD = pd.read_csv(os.path.join(T114, "a3_sintetis", "sinyal_sintetis_delta.csv"))
SCN = [("S_A tabular", "Signal only in the 44 predictors"), ("S_B sekuens", "Signal only in the 2-h window"), ("S_C setara", "Equal information")]
MOD = [("LightGBM, 43 fitur", "LightGBM, 44 predictors"), ("LightGBM, 43 fitur + jendela", "LightGBM, 44 predictors + window"), ("BiLSTM, jendela", "BiLSTM, 2-h window"), ("BiLSTM-hibrid, jendela + 43 fitur", "BiLSTM-hybrid, window + 44 predictors")]
L = ["| Model | " + " | ".join(l for _, l in SCN) + " |", sep(-30, 12, 12, 12)]
L.append("| Known ceiling (noise-free signal) | " + " | ".join(f"{SY[SY.skenario == k].R2_maks.iloc[0]:.4f}" for k, _ in SCN) + " |")
L.append("| Ceiling without the scenario-specific signal | " + " | ".join(f"{SY[SY.skenario == k].R2_bersama.iloc[0]:.4f}" for k, _ in SCN) + " |")
for m, l in MOD: L.append(f"| {l} | " + " | ".join(f"{SY[(SY.skenario == k) & (SY.model == m)].R2.iloc[0]:.4f}" for k, _ in SCN) + " |")
T["ESM_SINTETIS"] = "\n".join(L)
dd = lambda k: SD[(SD.skenario == k) & (SD.uji == "tree-43 − BiLSTM")].iloc[0]
A["sintetis"] = {k: dict(dR2=float(dd(k).dR2), lo=float(dd(k).blk_lo), hi=float(dd(k).blk_hi)) for k, _ in SCN}
r2s = lambda k, m: float(SY[(SY.skenario == k) & (SY.model == m)].R2.iloc[0])
gapA, gapB = r2s("S_A tabular", MOD[0][0]) - r2s("S_A tabular", MOD[2][0]), r2s("S_B sekuens", MOD[2][0]) - r2s("S_B sekuens", MOD[0][0])
mxC = float(SY[SY.skenario == "S_C setara"].R2_maks.iloc[0]); gC = r2s("S_C setara", MOD[0][0]) - r2s("S_C setara", MOD[2][0])
A["sintetis_aturan"] = dict(T1=bool(gapA >= 0.05 and dd("S_A tabular").blk_lo > 0), T2=bool(gapB >= 0.05 and dd("S_B sekuens").blk_hi < 0),
                           T3=bool(abs(gC) <= 0.01 and min(r2s("S_C setara", MOD[0][0]), r2s("S_C setara", MOD[2][0])) >= mxC - 0.02),
                           T4=bool((r2s("S_A tabular", MOD[3][0]) - r2s("S_A tabular", MOD[2][0])) / gapA >= 0.5 and (r2s("S_B sekuens", MOD[1][0]) - r2s("S_B sekuens", MOD[0][0])) / gapB >= 0.5),
                           gap_beda=[min(gapA, gapB), max(gapA, gapB)], jarak_setara_maks=float(max(mxC - r2s("S_C setara", m) for m, _ in MOD)))

# ================= ESM S11: pencarian hiperparameter dan walk-forward (tahap 114 a4, a1) =================
pa4 = os.path.join(T114, "a4_tuning", "ringkasan_a4.json")
if os.path.exists(pa4):
    J4 = json.load(open(pa4, encoding="utf-8")); sl, sn = J4["selected"]["LightGBM"], J4["selected"]["LSTM"]
    dl, dn = J4["d_LightGBM"], J4["d_LSTM"]; vt = J4["val_R2"]; tt = J4["test_R2"]
    desc_l = "default retained" if sl["config"] == 0 else f"learning rate {sl['learning_rate']:.3f}, {sl['num_leaves']} leaves, min. {sl['min_child_samples']} samples per leaf, row/column subsampling {sl['subsample']:.2f}/{sl['colsample_bytree']:.2f}, L1 {sl['reg_alpha']:.2g}, L2 {sl['reg_lambda']:.2g}"
    SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"); man, ek = f"{sn['lr']:.1e}".split("e-")
    desc_n = "default retained" if sn["config"] == 0 else f"{sn['layers']} layer{'s' if sn['layers'] > 1 else ''} × {sn['hidden']} units, dropout {sn['dropout']:.2f}, head {sn['head']}, learning rate {man} × 10⁻{str(int(ek)).translate(SUP)}, batch {sn['batch']}"
    L = ["| Model | Selected setting | Validation R²: default → tuned | Configurations better than default on validation | Test R²: default → tuned | ΔR² [95% CI] |", sep(-8, -30, -12, 9, -12, -16)]
    L.append(f"| LightGBM | {desc_l} | {vt['LightGBM_default']:.4f} → {vt['LightGBM_tuned']:.4f} | {J4['n_better_val']['LightGBM']} of 29 | {tt['LightGBM_default']:.4f} → {tt['LightGBM_tuned']:.4f} | {ci4(dl['dR2'], dl['blk_lo'], dl['blk_hi'])} |")
    L.append(f"| LSTM | {desc_n} | {vt['LSTM_default']:.4f} → {vt['LSTM_tuned']:.4f} | {J4['n_better_val']['LSTM']} of 29 | {tt['LSTM_default_mean']:.4f} → {tt['LSTM_tuned_mean']:.4f} | {sg(dn['dR2_mean'], 4)}; ensemble {ci4(dn['ens_dR2'], dn['blk_lo'], dn['blk_hi'])} |")
    T["ESM_TUNING"] = "\n".join(L); A["tuning"] = dict(dLGB=dl["dR2"], dLSTM_mean=dn["dR2_mean"], dLSTM_ens=dn["ens_dR2"], lo=[dl["blk_lo"], dn["blk_lo"]], hi=[dl["blk_hi"], dn["blk_hi"]])
WF = pd.read_csv(os.path.join(T114, "a1_walkforward_bengkulu.csv")); A["walkforward"] = dict(mean=float(WF.R2.mean()), sd=float(WF.R2.std(ddof=1)), n=len(WF))
p5 = os.path.join(T114, "a5_seleksi.json")
if os.path.exists(p5): A["seleksi_val"] = json.load(open(p5))["selisih"]

# ================= ESM S12: sumber GHI dan sampel evaluasi =================
SL = pd.read_csv(os.path.join(H, "sampel_logger.csv")).set_index(["site", "sampel"])
ACC = pd.read_csv(os.path.join(P, "79_banten_rebuild", "estimasi_aws_akurasi.csv")); acc = ACC[ACC.sampel == "semua"].set_index("sumber")
L = ["| Year | Logger (%) | Portal (%) | Database (%) | AWS-based estimate (%) |", sep(-6, 9, 9, 9, 9)]
for y_ in (2022, 2023, 2024, 2025):
    r = SG.loc[("banten", y_)]; L.append(f"| {y_} | {r.pct_logger:.1f} | {np.nan_to_num(r.pct_portal):.1f} | {np.nan_to_num(r.pct_db):.1f} | {np.nan_to_num(r.pct_estimasi_aws):.1f} |")
L += ["", "| Against the logger, hourly-mean target | Correlation | RMSE (W m⁻²) | Absolute bias (W m⁻²) |", sep(-20, 9, 9, 9)]
for k, lab in [("Portal", "Portal"), ("B_aws_tetangga", "AWS-based estimate")]: L.append(f"| {lab} | {acc.loc[k, 'r1j']:.3f} | {acc.loc[k, 'RMSE1j']:.1f} | {abs(acc.loc[k, 'bias1j']):.1f} |")
L += ["", "| Evaluation sample | Origins | Smart persistence R² | CatBoost R² | RMSE (W m⁻²) | Skill | CLP, LightGBM |", sep(-20, 9, 9, 9, 9, 9, 9)]
for k, lab in [("penuh", "All origins (main results)"), ("logger_portal", "Logger and portal"), ("logger", "Logger only")]:
    r = SL.loc[("banten", k)]; L.append(f"| {lab} | {int(r.n):,} | {r.SP:.3f} | {r.CatBoost:.3f} | {r.RMSE:.1f} | {r.skill:.3f} | {sg(r.dCLP_LGB)} |")
T["ESM_BANTEN"] = "\n".join(L)
L = ["| Station | Logger 2022 (%) | Logger 2023 (%) | Logger 2024 (%) | Logger 2025 (%) | Measured 2025 (%) |", sep(-20, 9, 9, 9, 9, 9)]
for s in SITES: L.append(f"| {LAB[s]} | " + " | ".join(f"{SG.loc[(s, y_), 'logger_pct']:.1f}" for y_ in (2022, 2023, 2024, 2025)) + f" | {SG.loc[(s, 2025), 'terukur_pct']:.1f} |")
L += ["", "| Station | Origins, all | Origins, logger only | CatBoost R², all | CatBoost R², logger only | RMSE, all (W m⁻²) | RMSE, logger only (W m⁻²) | CLP, all | CLP, logger only |", sep(-20, 9, 9, 9, 9, 9, 9, 9, 9)]
for s in SITES:
    a_, b_ = SL.loc[(s, "penuh")], SL.loc[(s, "logger")]
    L.append(f"| {LAB[s]} | {int(a_.n):,} | {int(b_.n):,} | {a_.CatBoost:.3f} | {b_.CatBoost:.3f} | {a_.RMSE:.1f} | {b_.RMSE:.1f} | {sg(a_.dCLP_CB)} | {sg(b_.dCLP_CB)} |")
T["ESM_ENAM"] = "\n".join(L)
SLo = SL.xs("logger", level="sampel").loc[SITES]; SLp = SL.xs("penuh", level="sampel").loc[SITES]
A["sampel_logger"] = dict(porsi_bukan_logger=[float(100 * (1 - SLo.porsi.max())), float(100 * (1 - SLo.porsi.min()))], cb=[float(SLo.CatBoost.min()), float(SLo.CatBoost.max())],
                          clp=[float(SLo.dCLP_CB.min()), float(SLo.dCLP_CB.max())], bukan_logger_per_situs={s: float(100 * (1 - SLo.loc[s, "porsi"])) for s in SITES})
A["sumber_2022"] = {s: float(SG.loc[(s, 2022), "logger_pct"]) for s in SITES}

# ================= tulis =================
json.dump(A, open(os.path.join(H, "angka_teks_v6.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
for fn in ["MANUSKRIP_v6.md", "ESM_v6.md"]:
    p = os.path.join(V6, fn)
    if not os.path.exists(p): continue
    t = open(p, encoding="utf-8").read(); n = 0
    for k, v in T.items():
        pat = re.compile(rf"(<!-- {re.escape(k)}:MULAI -->\n)(?:.*?\n)?(<!-- {re.escape(k)}:SELESAI -->)", re.S)
        if pat.search(t): t, c = pat.subn(lambda m: m.group(1) + v + "\n" + m.group(2), t); n += c
    open(p, "w", encoding="utf-8", newline="").write(t); print(f"{fn}: {n} tabel diisi")
open(os.path.join(H, "tabel_v6.md"), "w", encoding="utf-8").write("\n\n".join(f"### {k}\n\n{v}" for k, v in T.items())); print("tabel:", list(T))
