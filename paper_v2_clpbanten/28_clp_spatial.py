# -*- coding: utf-8 -*-
"""Tahap 28 — (C) Fitur tekstur spasial CLP. DESAIN DIKUNCI SEBELUM HASIL DILIHAT (2026-10-03).

Latar: clp_cot model = rata-rata COT atas piksel BERAWAN dalam kotak 11×11 piksel (buffer 30 km); model tidak
tahu fraksi awan maupun heterogenitas awan dalam kotak. Tabel sumber CLP menyimpan statistik kotak yang belum dipakai.

Data (read-only DB v2): statistik dari tabel sumber yang SAMA dengan clp_cot (diverifikasi: CLOT_mean/cot_consolidated
== clp_cot persis pada baris yang sama; offset waktu empiris 0 menit, Kalbar +10 menit). Kebijakan mask sama dengan
00_data: NaN bila clp_retrieval_ok bukan TRUE. Lag 60 menit = 6 slot pada grid 10-menit lengkap.

Fitur SPAT (7, tetap):  clps_cot_std, clps_cot_min, clps_cot_max, clps_cloud_frac (= CLOT_coverage = piksel ber-COT/121),
                         clps_cth_std, clps_cloud_frac_lag_60m, clps_cot_std_lag_60m
Eksperimen (target mean, protokol A, train 2022–23 / val 2024 / test 2025, konfigurasi identik skrip asli):
  E1 LightGBM residual (07b): T1+CLP           vs T1+CLP+SPAT
  E2 LightGBM residual (07b): FULL (himpunan aktif; P2 = 43) vs FULL+SPAT (+7)
  E3 CatBoost direct  (04c):  himpunan aktif  vs himpunan aktif + 7   <- HEADLINE
  Baseline tiap eksperimen WAJIB mereproduksi CSV asli.
Uji: ΔR² dengan block bootstrap harian (_blockboot, seed 11, 2000).
ATURAN KEPUTUSAN (a priori): "bermakna" bila ΔR² ≥ 0,002 DAN batas bawah CI blok > 0 (konsisten Sect. 2.8).
Luaran sekunder (a priori): ΔR² siang 10–14 WIB dan langit berawan sebagian (k_t 0,30–0,65) pada E3.
Output: 28_clp_spatial/{data/, *.csv, preds_*.npz}, plots/28_clp_spatial_dR2.png
Jalankan: python -u 28_clp_spatial.py
"""
import os, sys, time, json, numpy as np, pandas as pd, duckdb, lightgbm as lgb
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score, mean_squared_error
B = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, B)
import _common
from _common import split_idx, SITES, savefig
from _blockboot import delta_r2
import matplotlib.pyplot as plt
OUT = os.path.join(B, "28_clp_spatial"); DOUT = os.path.join(OUT, "data"); os.makedirs(DOUT, exist_ok=True)
DB = r"C:\Users\ariff\Documents\Balai Obsidian\Balai\solardata_new_v2\solar_harmonised_clpbanten_v2.duckdb"
prov = json.load(open(os.path.join(B, "00_data", "provenance.json"))); assert os.path.getmtime(DB) == prov["mtime"], "DB berubah sejak 00_data"
t0 = time.time()
def log(*a): print(*a, flush=True)
SRC = {"banten": ("banten.clp_banten", "timestamp_wib", "CLOT_mean", 0), "bengkulu": ("bengkulu.clp_bengkulu_quality_final", "ts_wib", "cot_consolidated", 0),
       "jambi": ("jambi.clp_jambi", "timestamp", "CLOT_mean", 0), "jogja": ("jogja.clp_jogja_combined", "timestamp", "CLOT_mean", 0),
       "kalbar": ("kalbar.clp_pontianak", "timestamp_wib", "CLOT_mean", 10), "semarang": ("semarang.clp_semarang", "timestamp_wib", "CLOT_mean", 0)}
if prov.get("clp_harmonised"):                       # konvensi seragam (keputusan B): label T-10 di origin T untuk semua situs
    SRC = {k: (v[0], v[1], v[2], 10) for k, v in SRC.items()}
log(f"offset CLP (menit): { {k: v[3] for k, v in SRC.items()} }  (clp_harmonised={prov.get('clp_harmonised')})")
SPAT = ["clps_cot_std", "clps_cot_min", "clps_cot_max", "clps_cloud_frac", "clps_cth_std", "clps_cloud_frac_lag_60m", "clps_cot_std_lag_60m"]

# ================= 1. bangun fitur spasial =================
con = duckdb.connect(DB, read_only=True); QC = []
for s, (tb, tc, mcol, off) in SRC.items():
    base = duckdb.connect().execute(f"SELECT ts_wib, clp_cot FROM read_parquet('{os.path.join(B,'00_data',s+'_full.parquet').replace(chr(92),'/')}') ORDER BY ts_wib").df()
    ok = con.execute("SELECT CAST(timestamp_wib AS TIMESTAMP) AS ts_wib, clp_retrieval_ok FROM std.master_10min_all WHERE site_id=?", [s]).df()
    src = con.execute(f"SELECT CAST({tc} AS TIMESTAMP) AS t, {mcol} AS m, CLOT_std, CLOT_min, CLOT_max, CLOT_coverage, CLTH_std FROM {tb}").df()
    assert not src.t.duplicated().any()
    src["ts_wib"] = src.t + pd.Timedelta(minutes=off)
    d = base.merge(src.drop(columns="t"), on="ts_wib", how="left").merge(ok, on="ts_wib", how="left")
    assert len(d) == len(base) == 210384 and (d.ts_wib.to_numpy() == base.ts_wib.to_numpy()).all()
    both = d.m.notna() & d.clp_cot.notna(); exact = (np.abs(d.m - d.clp_cot) < 1e-6) & both
    keep = d.clp_retrieval_ok.fillna(False).astype(bool).to_numpy()
    out = pd.DataFrame({"ts_wib": d.ts_wib, "clps_cot_std": d.CLOT_std, "clps_cot_min": d.CLOT_min, "clps_cot_max": d.CLOT_max,
                        "clps_cloud_frac": d.CLOT_coverage, "clps_cth_std": d.CLTH_std})
    for c in out.columns[1:]: out.loc[~keep, c] = np.nan                              # kebijakan mask = 00_data
    out["clps_cloud_frac_lag_60m"] = out.clps_cloud_frac.shift(6); out["clps_cot_std_lag_60m"] = out.clps_cot_std.shift(6)
    p = os.path.join(DOUT, f"{s}_clp_spatial.parquet").replace("\\", "/"); w = duckdb.connect(); w.register("o", out)
    w.execute(f"COPY (SELECT * FROM o) TO '{p}' (FORMAT PARQUET, COMPRESSION ZSTD)"); w.close()
    day = d.ts_wib.dt.hour.between(6, 17).to_numpy()
    QC.append(dict(site=s, source=tb, offset_min=off, clp_cot_nonnull=int(d.clp_cot.notna().sum()), mean_matched=int(both.sum()),
                   exact_match_frac=round(exact.sum() / max(both.sum(), 1), 5),
                   spat_cover_of_clp_cot=round(float((out.clps_cloud_frac.notna() & d.clp_cot.notna()).sum() / d.clp_cot.notna().sum()), 4),
                   cloud_frac_mean_day=round(float(out.clps_cloud_frac[day].mean()), 3)))
    log("  data", QC[-1]); assert QC[-1]["exact_match_frac"] >= 0.999, f"{s}: CLOT_mean tidak cocok dengan clp_cot"
pd.DataFrame(QC).to_csv(os.path.join(OUT, "qc_spatial_build.csv"), index=False)

# ================= 2. eksperimen =================
def groups(feats):
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
    ok = abs(round(got, 4) - ref) < 1e-4 + 1e-9; log(f"    reproduksi {name:22s} refit={got:.4f} csv={ref:.4f} {'OK' if ok else 'BEDA'}"); assert ok, name
rows, imp, strat = [], [], []
for s in SITES:
    log(f"\n== {s} ({time.time()-t0:.0f}s) ==")
    _common.DATA = os.path.join(B, "00_data"); df, feats, yr = _common.prepare(s)
    sp = duckdb.connect().execute(f"SELECT * FROM read_parquet('{os.path.join(DOUT, s + '_clp_spatial.parquet').replace(chr(92),'/')}') ORDER BY ts_wib").df()
    assert (sp.ts_wib.to_numpy() == df.ts_wib.to_numpy()).all()
    for c in SPAT: df[c] = sp[c].to_numpy(float)
    itr, iva, ite = split_idx(df, yr, "mean"); tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
    ytr, yva = (tr.y_mean - tr.base_mean).to_numpy(), (va.y_mean - va.base_mean).to_numpy()
    y, b = te.y_mean.to_numpy(), te.base_mean.to_numpy(); day = te.ts_wib.dt.date.to_numpy()
    hr, kt = te.ts_wib.dt.hour.to_numpy(), te.kt_clearness.to_numpy()   # kelas langit: indeks kecerahan
    T1, CLP = groups(feats)
    def lgb_fit(fs):
        m = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=63, min_child_samples=50, subsample=0.8, subsample_freq=1,
                              colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1, random_state=42, n_jobs=-1, verbose=-1)
        m.fit(tr[fs], ytr, eval_set=[(va[fs], yva)], eval_metric="l2", callbacks=[lgb.early_stopping(80, verbose=False)])
        return b + m.predict(te[fs]), m
    def cb_fit(fs):
        X = df[fs]; med = X.iloc[itr].median().fillna(0.0); yy = df.y_mean.to_numpy()
        m = CatBoostRegressor(iterations=2500, learning_rate=0.03, depth=6, loss_function="RMSE", verbose=0, random_seed=42)
        m.fit(X.iloc[itr].fillna(med), yy[itr], eval_set=(X.iloc[iva].fillna(med), yy[iva]), early_stopping_rounds=200, use_best_model=True)
        return m.predict(X.iloc[ite].fillna(med)), m
    P = {}
    P["E1_base"], _ = lgb_fit(T1 + CLP); check(f"{s} E1 T1+CLP", r2_score(y, P["E1_base"]), ref07.loc[s, "T1_CLP"])
    P["E1_spat"], _ = lgb_fit(T1 + CLP + SPAT)
    P["E2_base"], _ = lgb_fit(feats)
    P["E2_spat"], m2 = lgb_fit(feats + SPAT)
    P["E3_base"], _ = cb_fit(feats); check(f"{s} E3 CatBoost", r2_score(y, P["E3_base"]), ref04.loc[s, "CB_R2"])
    P["E3_spat"], m3 = cb_fit(feats + SPAT)
    np.savez(os.path.join(OUT, f"preds_{s}.npz"), y=y, day=day.astype(str), **P)
    for e in ["E1", "E2", "E3"]:
        r = delta_r2(y, P[f"{e}_spat"], P[f"{e}_base"], day, record=False)
        r.update(site=s, exp=e, R2_base=r2_score(y, P[f"{e}_base"]), R2_spat=r2_score(y, P[f"{e}_spat"]),
                 RMSE_base=float(np.sqrt(mean_squared_error(y, P[f"{e}_base"]))), RMSE_spat=float(np.sqrt(mean_squared_error(y, P[f"{e}_spat"]))))
        r["meaningful"] = "YES" if (r["dR2"] >= 0.002 and r["blk_lo"] > 0) else "no"; rows.append(r)
        log(f"    {e}: R2 {r['R2_base']:.4f} -> {r['R2_spat']:.4f}  dR2={r['dR2']:+.4f} CI_blok=[{r['blk_lo']:+.4f},{r['blk_hi']:+.4f}]  "
            f"RMSE {r['RMSE_base']:.1f}->{r['RMSE_spat']:.1f}  bermakna={r['meaningful']}")
    for nm, sel in [("midday 10-14", (hr >= 10) & (hr < 14)), ("partly cloudy kt 0.30-0.65", (kt > 0.30) & (kt <= 0.65))]:
        r = delta_r2(y[sel], P["E3_spat"][sel], P["E3_base"][sel], day[sel], record=False); r.update(site=s, subset=nm,
             R2_base=r2_score(y[sel], P["E3_base"][sel]), R2_spat=r2_score(y[sel], P["E3_spat"][sel])); strat.append(r)
    g = pd.Series(m2.booster_.feature_importance("gain"), index=feats + SPAT); gi = pd.Series(m3.get_feature_importance(), index=feats + SPAT)
    rk = gi.rank(ascending=False)
    imp.append(dict(site=s, E2_gain_share_SPAT=round(float(g[SPAT].sum() / g.sum()), 4), E3_importance_share_SPAT=round(float(gi[SPAT].sum() / gi.sum()), 4),
                    E3_best_SPAT=gi[SPAT].idxmax(), E3_best_SPAT_rank=int(rk[gi[SPAT].idxmax()]), E3_cloud_frac_rank=int(rk["clps_cloud_frac"])))
    log("    importance", imp[-1])
R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "clp_spatial_results.csv"), index=False)
ST = pd.DataFrame(strat); ST.to_csv(os.path.join(OUT, "clp_spatial_stratified_E3.csv"), index=False)
IM = pd.DataFrame(imp); IM.to_csv(os.path.join(OUT, "clp_spatial_importance.csv"), index=False)
log("\n" + R[["site","exp","R2_base","R2_spat","dR2","blk_lo","blk_hi","RMSE_base","RMSE_spat","meaningful"]].round(4).to_string(index=False))
log("\n" + ST[["site","subset","R2_base","R2_spat","dR2","blk_lo","blk_hi","sig_block"]].round(4).to_string(index=False))
log("\n" + IM.to_string(index=False))
# plot diagnostik
x = np.arange(len(SITES)); fig, ax = plt.subplots(figsize=(8, 3.6))
for i, e in enumerate(["E1", "E2", "E3"]):
    q = R[R.exp == e].set_index("site").loc[SITES]
    ax.bar(x + (i - 1) * 0.27, q.dR2, 0.27, yerr=[q.dR2 - q.blk_lo, q.blk_hi - q.dR2], capsize=2,
           label={"E1": "LightGBM T1+CLP", "E2": "LightGBM FULL", "E3": "CatBoost FULL (headline)"}[e])
ax.axhline(0, color="k", lw=0.7); ax.axhline(0.002, color="gray", ls=":", lw=0.8, label="resolution 0.002")
ax.set_xticks(x); ax.set_xticklabels(SITES, rotation=15); ax.set_ylabel("ΔR² (+CLP spatial texture)")
ax.set_title("Adding CLP spatial-texture predictors (hourly mean, test 2025; daily-block 95% CI)"); ax.legend(fontsize=7)
savefig(fig, "28_clp_spatial_dR2.png")
log(f"SELESAI tahap 28 dalam {time.time()-t0:.0f}s")
