# -*- coding: utf-8 -*-
"""Tahap 31 — Uji sensitivitas waktu CLP (CLP dilag 10 menit). DESAIN & TAFSIRAN DIKUNCI SEBELUM HASIL (2026-10-03).

Fakta (tahap 28 & cek nama file): label CLP = waktu nominal file Himawari L2CLP (awal scan full-disk, UTC+7).
Indonesia terpindai ~4–6 menit setelah awal scan. Di 00_data, 5 situs memakai label T pada origin T (observasi ≈ T+5 min),
Kalbar memakai label T−10 (observasi ≈ T−5 min).

Varian (CLP = 10 kolom clp_* mentah + turunannya, digeser utuh pada grid 10-menit lengkap; fitur lain tidak berubah):
  V0   = 00_data apa adanya
  L10  = CLP digeser +1 slot (nilai dari T−10)        -> 5 situs: konvensi diseragamkan dg Kalbar; Kalbar: kontrol penuaan
  L20  = CLP digeser +2 slot (nilai dari T−20)        -> kurva penuaan informasi (konteks)
  H    = set "diseragamkan konservatif" = L10 untuk 5 situs + V0 untuk Kalbar
Model (konfigurasi identik skrip asli; V0 wajib mereproduksi CSV): LightGBM residual T1 & T1+CLP (07b) -> ΔR²(CLP);
CatBoost direct headline 104 prediktor (04c). Uji: block bootstrap harian (_blockboot, seed 11).
Diagnostik: (a) korelasi Spearman COT(T) vs k_t(T+k·10 min), k = −3..+3, siang (elevasi > 15°);
(b) asimetri pagi–sore k_t pada hari cerah sebagai petunjuk konvensi label GHI.
ATURAN TAFSIR (a priori):
  1. Kesimpulan ROBUST terhadap waktu CLP bila di bawah H: ΔR²(CLP) tetap signifikan 6/6 DAN |ΔR² CatBoost (H − V0)| < 0,002 di setiap situs.
  2. Perbandingan biaya langkah V0→L10 (5 situs) vs L10→L20 dan vs kontrol Kalbar hanya INDIKATIF untuk look-ahead
     (penuaan informasi dan hilangnya look-ahead tidak dapat dipisahkan sepenuhnya).
RERUN (2026-10-06, 43 prediktor): 00_data kini berkonvensi B (t−10 di semua situs). V0 direkonstruksi persis = 00_data dengan 10 kolom CLP
digeser −1 slot di 5 situs (00_build_data membuat B = V0.shift(1); hanya baris terakhir 2025, malam hari, yang hilang); Kalbar tidak berubah.
Uji reproduksi CSV pipeline dilakukan pada varian H (= data pipeline). Desain, varian, dan aturan tafsir tidak berubah.
Output: 31_clp_lag/*.csv, plots/31_clp_lag.png.  Jalankan: python -u 31_clp_lag_sensitivity.py
"""
import os, sys, time, json, numpy as np, pandas as pd, lightgbm as lgb
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score, mean_squared_error
B = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, B)
import _common
from _common import split_idx, SITES, savefig
from _blockboot import delta_r2
import matplotlib.pyplot as plt
OUT = os.path.join(B, "31_clp_lag"); os.makedirs(OUT, exist_ok=True)
CLP10 = ["clp_cot", "clp_cth_km", "clp_ctt_k", "clp_cer_um", "clp_cloud_present_int",
         "clp_cot_lag_60m", "clp_cot_delta_60m", "clp_cot_roll_180m_mean", "clp_cth_lag_60m", "clp_cth_roll_180m_mean"]
t0 = time.time()
def log(*a): print(*a, flush=True)
def groups(feats):                                    # identik 07b
    def grp(f):
        if f.startswith("clp_"): return "D"
        if f.startswith("synop_"): return "E"
        if f.startswith("aws_"): return "F"
        if f.startswith(("clear_sky","solar_elev","decl_","eot_","is_day","elev_sin")): return "B"
        if f.startswith(("kt_lag","kt_delta","kt_roll","kt_std","kt_cooper")) or f=="kt": return "C2"
        if f.startswith(("ghi_lag","ghi_delta")): return "C1"
        if f.startswith(("ghi_wm2","dhi_","dni_","nett_","reflected","sunshine")): return "A"
        return "B"
    T4 = ([f for f in feats if f.startswith("accel_") or "_std_" in f] if os.environ.get("FEATSET", "P2") == "P0" else [])   # P2: kelompok eksperimental dilebur ke inti
    G = {g: [] for g in ["A","B","C1","C2","D","E","F"]}
    for f in feats:
        if f in T4: continue
        G[grp(f)].append(f)
    return G["A"]+G["B"]+G["C1"]+G["C2"], G["D"]
ref07 = pd.read_csv(os.path.join(B, "07_replication", "replication_ablation_mean.csv")).set_index("site")
ref04 = pd.read_csv(os.path.join(B, "04c_mean_6situs", "baseline_mean_6situs.csv")).set_index("site")
def check(name, got, ref):
    ok = abs(round(got, 4) - ref) < 1e-4 + 1e-9; log(f"    reproduksi {name:24s} refit={got:.4f} csv={ref:.4f} {'OK' if ok else 'BEDA'}"); assert ok, name

rows, diag_xc, diag_asym, P_all = [], [], [], {}
for s in SITES:
    log(f"\n== {s} ({time.time()-t0:.0f}s) ==")
    _common.DATA = os.path.join(B, "00_data"); df0, feats, yr = _common.prepare(s)
    HARM = json.load(open(os.path.join(B, "00_data", "provenance.json"))).get("clp_harmonised") is True
    if HARM and s != "kalbar": df0[CLP10] = df0[CLP10].shift(-1)      # rekonstruksi V0 (konvensi campuran lama)
    HV = "V0" if (s == "kalbar" or not HARM) else "L10"               # varian yang sama dengan data pipeline
    assert df0.ts_wib.diff().dropna().eq(pd.Timedelta(minutes=10)).all(), "grid 10-menit tidak lengkap"
    itr, iva, ite = split_idx(df0, yr, "mean"); T1, CLP = groups(feats)
    # ---- diagnostik (a): korelasi silang COT(T) vs kt(T+k) ----
    d = df0[(df0.solar_elev_deg > 15)].index
    for k in range(-3, 4):
        kt_k = df0.kt_clearness.shift(-k)                          # kt pada T + k·10 min
        m = df0.clp_cot.notna() & kt_k.notna() & df0.kt_clearness.notna() & (df0.solar_elev_deg > 15) & (df0.solar_elev_deg.shift(-k) > 15)
        diag_xc.append(dict(site=s, k_slot=k, minutes=10 * k, n=int(m.sum()),
                            spearman=float(df0.clp_cot[m].rank().corr(kt_k[m].rank()))))
    # ---- diagnostik (b): asimetri pagi–sore kt pada hari cerah ----
    dd = df0.assign(date=df0.ts_wib.dt.date, h=df0.ts_wib.dt.hour + df0.ts_wib.dt.minute / 60)
    day = dd[(dd.solar_elev_deg > 20)].groupby("date").kt_clearness.agg(["median", "std", "count"])
    clear = day[(day["median"] > 0.70) & (day["std"] < 0.06) & (day["count"] >= 40)].index
    cd = dd[dd.date.isin(clear) & (dd.solar_elev_deg.between(20, 50))]
    noon = cd.loc[cd.groupby("date").solar_elev_deg.idxmax(), ["date", "h"]].set_index("date").h
    cd = cd.assign(dh=cd.h - cd.date.map(noon))
    am, pm = cd[cd.dh < -0.5], cd[cd.dh > 0.5]
    diag_asym.append(dict(site=s, clear_days=len(clear), kt_am=float(am.kt_clearness.median()), kt_pm=float(pm.kt_clearness.median()),
                          pm_minus_am=float(pm.kt_clearness.median() - am.kt_clearness.median())))
    # ---- model ----
    res = {}
    for v, k in [("V0", 0), ("L10", 1), ("L20", 2)]:
        df = df0.copy()
        if k: df[CLP10] = df[CLP10].shift(k)
        tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
        ytr, yva = (tr.y_mean - tr.base_mean).to_numpy(), (va.y_mean - va.base_mean).to_numpy()
        y, b, dayv = te.y_mean.to_numpy(), te.base_mean.to_numpy(), te.ts_wib.dt.date.to_numpy()
        def lgb_fit(fs):
            m = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=63, min_child_samples=50, subsample=0.8, subsample_freq=1,
                                  colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1, random_state=42, n_jobs=-1, verbose=-1)
            m.fit(tr[fs], ytr, eval_set=[(va[fs], yva)], eval_metric="l2", callbacks=[lgb.early_stopping(80, verbose=False)])
            return b + m.predict(te[fs])
        X = df[feats]; med = X.iloc[itr].median().fillna(0.0); yy = df.y_mean.to_numpy()
        cb = CatBoostRegressor(iterations=2500, learning_rate=0.03, depth=6, loss_function="RMSE", verbose=0, random_seed=42)
        cb.fit(X.iloc[itr].fillna(med), yy[itr], eval_set=(X.iloc[iva].fillna(med), yy[iva]), early_stopping_rounds=200, use_best_model=True)
        res[v] = dict(y=y, day=dayv, T1=(lgb_fit(T1) if v == "V0" else res["V0"]["T1"]), T1CLP=lgb_fit(T1 + CLP), CB=cb.predict(X.iloc[ite].fillna(med)))
        if v == HV:
            check(f"{s} T1+CLP", r2_score(y, res[v]["T1CLP"]), ref07.loc[s, "T1_CLP"]); check(f"{s} CatBoost", r2_score(y, res[v]["CB"]), ref04.loc[s, "CB_R2"])
        dclp = delta_r2(y, res[v]["T1CLP"], res[v]["T1"], dayv, record=False)
        r = dict(site=s, variant=v, R2_T1CLP=r2_score(y, res[v]["T1CLP"]), dCLP=dclp["dR2"], dCLP_lo=dclp["blk_lo"], dCLP_hi=dclp["blk_hi"],
                 R2_CB=r2_score(y, res[v]["CB"]), RMSE_CB=float(np.sqrt(mean_squared_error(y, res[v]["CB"]))))
        if v != "V0":
            dcb = delta_r2(y, res[v]["CB"], res["V0"]["CB"], dayv, record=False)
            r.update(dCB_vs_V0=dcb["dR2"], dCB_lo=dcb["blk_lo"], dCB_hi=dcb["blk_hi"])
        rows.append(r)
        log(f"    {v:4s} R2 T1+CLP={r['R2_T1CLP']:.4f} dCLP={r['dCLP']:+.4f} [{r['dCLP_lo']:+.4f},{r['dCLP_hi']:+.4f}]  CatBoost R2={r['R2_CB']:.4f}"
            + (f"  dCB vs V0={r['dCB_vs_V0']:+.4f} [{r['dCB_lo']:+.4f},{r['dCB_hi']:+.4f}]" if v != "V0" else ""))
    P_all[s] = res
R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "clp_lag_results.csv"), index=False)
XC = pd.DataFrame(diag_xc); XC.to_csv(os.path.join(OUT, "diag_crosscorr_cot_kt.csv"), index=False)
AS = pd.DataFrame(diag_asym); AS.to_csv(os.path.join(OUT, "diag_clearday_am_pm.csv"), index=False)

# ---- set H (diseragamkan konservatif) & aturan tafsir ----
H = []
for s in SITES:
    v = "V0" if s == "kalbar" else "L10"; r = R[(R.site == s) & (R.variant == v)].iloc[0]; r0 = R[(R.site == s) & (R.variant == "V0")].iloc[0]
    H.append(dict(site=s, variant_used=v, dCLP=r.dCLP, dCLP_lo=r.dCLP_lo, dCLP_hi=r.dCLP_hi, CLP_sig=r.dCLP_lo > 0,
                  R2_CB_V0=r0.R2_CB, R2_CB_H=r.R2_CB, dCB=(r.R2_CB - r0.R2_CB), dCB_lo=(r.get("dCB_lo", 0.0) if v != "V0" else 0.0),
                  dCB_hi=(r.get("dCB_hi", 0.0) if v != "V0" else 0.0)))
H = pd.DataFrame(H); H.to_csv(os.path.join(OUT, "harmonised_H_vs_V0.csv"), index=False)
robust = bool(H.CLP_sig.all() and (H.dCB.abs() < 0.002).all())
# biaya per langkah (indikatif)
st = []
for s in SITES:
    g = R[R.site == s].set_index("variant")
    st.append(dict(site=s, step1_V0_to_L10_CB=g.loc["L10", "R2_CB"] - g.loc["V0", "R2_CB"], step2_L10_to_L20_CB=g.loc["L20", "R2_CB"] - g.loc["L10", "R2_CB"],
                   step1_dCLP=g.loc["L10", "dCLP"] - g.loc["V0", "dCLP"], step2_dCLP=g.loc["L20", "dCLP"] - g.loc["L10", "dCLP"]))
ST = pd.DataFrame(st); ST.to_csv(os.path.join(OUT, "step_costs.csv"), index=False)
pd.set_option("display.width", 220)
log("\n== Hasil per varian ==\n" + R.round(4).to_string(index=False))
log("\n== Set H (5 situs L10 + Kalbar V0) vs V0 ==\n" + H.round(4).to_string(index=False))
log(f"\nATURAN 1 (robust): CLP sig 6/6 = {bool(H.CLP_sig.all())}; max |dCB| = {H.dCB.abs().max():.4f} (< 0.002: {bool((H.dCB.abs() < 0.002).all())}) -> ROBUST = {robust}")
log("\n== Biaya per langkah lag (indikatif) ==\n" + ST.round(4).to_string(index=False))
log("\n== Diagnostik (a) Spearman COT(T) vs kt(T+k) ==\n" + XC.pivot(index="site", columns="minutes", values="spearman").round(4).to_string())
log("\n== Diagnostik (b) asimetri pagi-sore kt hari cerah ==\n" + AS.round(4).to_string(index=False))
# plot
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.8))
x = np.arange(len(SITES))
for i, v in enumerate(["V0", "L10", "L20"]):
    q = R[R.variant == v].set_index("site").loc[SITES]
    a1.bar(x + (i - 1) * 0.27, q.dCLP, 0.27, yerr=[q.dCLP - q.dCLP_lo, q.dCLP_hi - q.dCLP], capsize=2, label={"V0": "as built", "L10": "CLP lagged 10 min", "L20": "CLP lagged 20 min"}[v])
a1.set_xticks(x); a1.set_xticklabels(SITES, rotation=15); a1.set_ylabel("ΔR²(CLP) vs T1 (daily-block 95% CI)"); a1.legend(fontsize=7)
xc = XC.pivot(index="minutes", columns="site", values="spearman")
for s in SITES: a2.plot(xc.index, xc[s], "o-", ms=3, label=s, lw=1.5 if s == "kalbar" else 1.0, ls="--" if s == "kalbar" else "-")
a2.axvline(0, color="gray", lw=0.6); a2.set_xlabel("k_t taken at T + lag (min)"); a2.set_ylabel("Spearman ρ(COT at T, k_t)"); a2.legend(fontsize=7)
savefig(fig, "31_clp_lag.png")
log(f"SELESAI tahap 31 dalam {time.time()-t0:.0f}s")
