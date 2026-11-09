# Manuskrip V6: dibuat oleh analisis/00b_siapkan_analisis_v6.py dari Manuskrip_versi5\protokol\04_daftar_periksa.py (sha256 42e3b1e728d738ba…); jangan disunting langsung.
# -*- coding: utf-8 -*-
"""Rerun 04 — angka pengganti untuk daftar periksa naskah (2026-10-23). TANPA pelatihan ulang.

Status: DATA DUKUNG untuk pembimbing. TIDAK dipakai mengubah naskah, ESM atau LAPORAN sebelum ada arahan.
Menghitung, dari prediksi uji rerun (hasil/nn, hasil/pohon) dan keluaran pipeline yang tidak berubah, setiap angka naskah/ESM
yang akan berganti bila Tabel 3 diganti rerun (rerata 5 seed, target residual seragam). Definisi metrik dan uji sama dengan
builder naskah (paper_v2_clpbanten/49_build_manuskrip_v3.py, 52_build_esm_v3.py, _multiseed.py, 60_skill_linear.py):
  skill = 1 − RMSE/RMSE_SP; R² residual = 1 − SSE/Σ(r − r̄)², r = ȳ − ŷ_SP; nRMSE = RMSE / rerata ȳ uji; bias = rerata(ŷ − ȳ);
  uji berpasangan = bootstrap blok harian (_blockboot.delta_r2, 2000 ulangan, seed 11), signifikan bila CI 95% tidak memuat nol.
Angka per model = rerata 5 seed (42, 1, 2, 3, 4); uji berpasangan per seed (satu run = satu uji, seperti "150 single-seed runs").
Pemeriksaan reproduksi: y/b/hari rerun identik dengan prediksi pipeline (62, 60); prediksi CatBoost lama (62) mereproduksi
contoh_hari.csv (Fig. S5); CatBoost residual seed 42 dibandingkan dengan Tabel S7 kolom A (tahap 09, juga CatBoost residual).
Keluaran: hasil/daftar_periksa/*.csv dan angka_baru.json. Jalankan: python -u 04_daftar_periksa.py
"""
import os, sys, json, math, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE)); P = os.path.join(ROOT, "paper_v2_clpbanten"); PV = os.path.join(os.path.dirname(HERE), "pipeline"); TETAP = []
sys.path.insert(0, P)
import _blockboot as bb
OUT = os.path.join(HERE, "hasil", "daftar_periksa"); os.makedirs(OUT, exist_ok=True)
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
LAB = dict(banten="Banten", bengkulu="Bengkulu", jambi="Jambi", jogja="Yogyakarta", kalbar="West Kalimantan", semarang="Central Java")
TREES = ["LightGBM", "CatBoost", "XGBoost"]; NN = ["MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"]; M8 = TREES + NN
SEEDS = [42, 1, 2, 3, 4]
def up3(x): return math.ceil(round(x, 6) * 1000) / 1000
def r2(y, p): return 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
def rmse(y, p): return float(np.sqrt(((y - p) ** 2).mean()))
def pred(site, m, s):
    d = "pohon" if m in TREES else "nn"
    return np.load(os.path.join(HERE, "hasil", d, f"pred_{site}_{m}_s{s}.npy")).astype(float)

Z62 = np.load(os.path.join(P, "62_scatter_6situs", "preds_cb_6situs.npz")); ZL = np.load(os.path.join(PV, "60_skill_linear", "preds_linear.npz"))
REF = pd.read_csv(os.path.join(PV, "13_reference_skill_6situs", "reference_skill_6situs.csv")).set_index("site").loc[SITES]
PP = pd.read_csv(os.path.join(P, "04b_arch_6situs", "arch_6situs_R2_matrix.csv")).set_index("site").loc[SITES]   # target sesaat (tidak di-rerun)
V9 = pd.read_csv(os.path.join(P, "09_sensitivity_mean", "sensitivity_variants_mean.csv")).set_index("site").loc[SITES]
C69 = pd.read_csv(os.path.join(P, "69_timeseries", "contoh_hari.csv")).set_index("kind")

rows, boot, cek, D = [], [], [], {}
for s in SITES:
    Y = np.load(os.path.join(HERE, "hasil", "nn", f"yb_{s}.npz"), allow_pickle=True); y, b, day = Y["y"], Y["b"], Y["day"]
    if s in TETAP: assert np.allclose(y, Z62[f"{s}__y"]) and np.allclose(b, Z62[f"{s}__b"]), f"{s}: y/b rerun ≠ tahap 62"
    assert np.allclose(y, ZL[f"{s}__y"]) and np.allclose(b, ZL[f"{s}__b"]), f"{s}: y/b rerun ≠ tahap 60"
    r = y - b; vr = ((r - r.mean()) ** 2).sum(); rsp = rmse(y, b)
    D[s] = dict(y=y, b=b, day=day)
    def met(p, model, seed):
        return dict(site=s, model=model, seed=seed, R2=r2(y, p), RMSE=rmse(y, p), MAE=float(np.abs(y - p).mean()),
                    bias=float((p - y).mean()), skill=1 - rmse(y, p) / rsp, R2_res=1 - ((y - p) ** 2).sum() / vr)
    rows.append(met(b, "SmartPersistence", 0)); rows.append(met(ZL[f"{s}__linear"], "Ridge", 0))
    if s in TETAP: rows.append(met(Z62[f"{s}__p"], "CatBoost_lama_langsung", 42))
    lg = pred(s, "LightGBM", 42)
    for m in M8:
        for sd in SEEDS:
            p = pred(s, m, sd); rows.append(met(p, m, sd))
            if m != "LightGBM":
                o = bb.delta_r2(y, p, lg, day, record=False); boot.append(dict(site=s, model=m, seed=sd, vs="LightGBM", **o))
    for sd in SEEDS:   # CatBoost − ridge (Table 3 teks §3.1, Sect. 4, kesimpulan)
        o = bb.delta_r2(y, pred(s, "CatBoost", sd), ZL[f"{s}__linear"], day, record=False); boot.append(dict(site=s, model="CatBoost", seed=sd, vs="Ridge", **o))

R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "metrik_per_seed.csv"), index=False)
BT = pd.DataFrame(boot); BT.to_csv(os.path.join(OUT, "uji_berpasangan_per_seed.csv"), index=False)
MEAN = R.groupby(["site", "model"])[["R2", "RMSE", "MAE", "bias", "skill", "R2_res"]].mean()
W = lambda c, ms=M8: MEAN[c].unstack().loc[SITES, ms]
R2m, SKm, RMm, MAm, RRm = W("R2"), W("skill"), W("RMSE"), W("MAE"), W("R2_res")
SP_R2 = MEAN.R2.unstack().loc[SITES, "SmartPersistence"]; RID = MEAN.unstack().loc[SITES]
spr = R2m.max(axis=1) - R2m.min(axis=1); spr_sk = SKm.max(axis=1) - SKm.min(axis=1); spr_rm = RMm.max(axis=1) - RMm.min(axis=1)
best, weak = R2m.idxmax(axis=1), R2m.idxmin(axis=1)
ybar = pd.Series({s: D[s]["y"].mean() for s in SITES})

# ---- Tabel 3 (R² dan skill, rerata 5 seed) dan Tabel S4 ----
T3 = pd.concat({"R2": R2m.assign(SP=SP_R2, Ridge=RID[("R2", "Ridge")], Spread=spr),
                "skill": SKm.assign(Ridge=RID[("skill", "Ridge")], Spread=spr_sk)}, names=["blok"])
T3.to_csv(os.path.join(OUT, "tabel3_baru.csv"))
S4 = pd.concat({"RMSE": RMm, "MAE": MAm, "R2_residual": RRm, "nRMSE_pct": RMm.div(ybar, axis=0) * 100}, names=["blok"])
S4.to_csv(os.path.join(OUT, "tabelS4_baru.csv"))

# ---- CatBoost: angka utama, Tabel S5, Fig. S1/S2 ----
cbs = R[R.model == "CatBoost"].set_index(["site", "seed"])
CB = pd.DataFrame({"R2": R2m.CatBoost, "RMSE": RMm.CatBoost, "MAE": MAm.CatBoost, "bias": MEAN.bias.unstack().loc[SITES, "CatBoost"],
                   "nRMSE_pct": 100 * RMm.CatBoost / ybar, "skill_pers": SKm.CatBoost, "RMSE_ref": REF.RMSE_ref,
                   "skill_cp": 1 - RMm.CatBoost / REF.RMSE_ref, "R2_s42": cbs.xs(42, level="seed").R2.loc[SITES],
                   "RMSE_s42": cbs.xs(42, level="seed").RMSE.loc[SITES], "bias_s42": cbs.xs(42, level="seed").bias.loc[SITES],
                   "R2_lama": R[R.model == "CatBoost_lama_langsung"].set_index("site").R2.reindex(SITES),
                   "S7_A_r2_tahap09": V9.A_r2, "R2_sesaat_tahap04b": PP.CatBoost})
CB["S10_delta_baru"] = CB.R2 - CB.R2_sesaat_tahap04b
CB.to_csv(os.path.join(OUT, "catboost_baru.csv"))
for s in SITES:
    cek.append(f"Tabel S7 kolom A (tahap 09, CatBoost residual seed 42) {s}: {V9.loc[s, 'A_r2']:.4f} vs rerun seed 42 {CB.loc[s, 'R2_s42']:.4f}")

# ---- CatBoost − ridge ----
BR = BT[BT.vs == "Ridge"].groupby("site").agg(dR2=("dR2", "mean"), lo_min=("blk_lo", "min"), n_sig=("sig_block", lambda v: int((v == "yes").sum()))).loc[SITES]
BR["ratio_vs_spread"] = BR.dR2 / spr; BR["min_arch_minus_ridge"] = R2m.min(axis=1) - RID[("R2", "Ridge")]
BR.to_csv(os.path.join(OUT, "catboost_vs_ridge_baru.csv"))

# ---- uji 150 run tunggal jaringan saraf (dan pohon) vs LightGBM ----
BL = BT[BT.vs == "LightGBM"].copy(); BL["arah"] = np.where(BL.sig_block == "no", "tidak beda", np.where(BL.dR2 > 0, "lebih akurat", "kurang akurat"))
U = BL.groupby(["model", "arah"]).size().unstack(fill_value=0); U.to_csv(os.path.join(OUT, "uji_vs_lightgbm_ringkas.csv"))
BLn = BL[BL.model.isin(NN)]

# ---- Tabel S6(b): SD seed, rentang per seed ----
nn_sd = R[R.model.isin(NN)].groupby(["site", "model"]).R2.std(ddof=1).unstack().loc[SITES, NN]
nn_mu = R2m[NN]
per_seed = {sd: R[(R.model.isin(M8)) & (R.seed == sd)].pivot(index="site", columns="model", values="R2").loc[SITES, M8] for sd in SEEDS}
spr_seed = pd.DataFrame({sd: v.max(axis=1) - v.min(axis=1) for sd, v in per_seed.items()})
S6 = pd.concat([nn_mu.add_suffix("_rerata"), nn_sd.add_suffix("_sd")], axis=1)
S6["spread_seed42"] = spr_seed[42]; S6["spread_rerata_seed"] = spr; S6["spread_seed_min"] = spr_seed.min(axis=1); S6["spread_seed_max"] = spr_seed.max(axis=1)
S6.to_csv(os.path.join(OUT, "tabelS6b_baru.csv"))
sd_stack = nn_sd.stack()

# ---- Fig. S5: contoh hari Bengkulu ----
y, b, day = D["bengkulu"]["y"], D["bengkulu"]["b"], pd.Series(D["bengkulu"]["day"]).astype(str).to_numpy()
p_old = Z62["bengkulu__p"]; p42 = pred("bengkulu", "CatBoost", 42); pav = np.mean([pred("bengkulu", "CatBoost", sd) for sd in SEEDS], axis=0)
ch = []
for k, row in (C69.iterrows() if "bengkulu" in TETAP else []):     # contoh hari v4 memakai seri DB v2; tidak dipakai naskah v5
    mk = day == str(row.day); assert mk.sum() == row.n, f"Fig. S5 {k}: n {mk.sum()} ≠ {row.n}"
    old = rmse(y[mk], p_old[mk]); assert abs(old - row.rmse_cb) < 0.06, f"Fig. S5 {k}: prediksi lama tidak mereproduksi RMSE"
    ch.append(dict(kind=k, day=row.day, n=int(row.n), rmse_cb_lama=row.rmse_cb, rmse_cb_s42=rmse(y[mk], p42[mk]),
                   rmse_cb_rerata5=float(np.mean([rmse(y[mk], pred('bengkulu', 'CatBoost', sd)[mk]) for sd in SEEDS])),
                   rmse_cb_ensambel5=rmse(y[mk], pav[mk]), rmse_sp=row.rmse_sp))
CH = pd.DataFrame(ch); CH.to_csv(os.path.join(OUT, "contoh_hari_baru.csv"), index=False)

# ---- ringkasan angka (json) ----
J = dict(
    spread_R2=[spr.min(), spr.max()], spread_R2_per_site=spr.round(4).to_dict(), spread_skill=[spr_sk.min(), spr_sk.max()],
    spread_RMSE_max=float(spr_rm.max()), best=best.to_dict(), weakest=weak.to_dict(), n_tree_best=int(best.isin(TREES).sum()),
    mlp_gap_max=float((R2m.max(axis=1) - R2m.MLP).max()), mlp_gap_up3=up3(float((R2m.max(axis=1) - R2m.MLP).max())),
    n_mlp_weakest=int((weak == "MLP").sum()),
    CB_R2=[CB.R2.min(), CB.R2.max()], CB_RMSE=[CB.RMSE.min(), CB.RMSE.max()], CB_nRMSE=[CB.nRMSE_pct.min(), CB.nRMSE_pct.max()],
    CB_bias=[CB.bias.min(), CB.bias.max()], CB_skill_pers=[CB.skill_pers.min(), CB.skill_pers.max()], CB_skill_cp=[CB.skill_cp.min(), CB.skill_cp.max()],
    abstract_R2=f"{CB.R2.min():.2f}–{CB.R2.max():.2f}", abstract_RMSE=f"{CB.RMSE.min():.0f}–{CB.RMSE.max():.0f}",
    ridge_R2=[RID[("R2", "Ridge")].min(), RID[("R2", "Ridge")].max()], ridge_skill=[RID[("skill", "Ridge")].min(), RID[("skill", "Ridge")].max()],
    CB_minus_ridge=[BR.dR2.min(), BR.dR2.max()], CB_ridge_all_seeds_sig=bool((BR.n_sig == 5).all()),
    ratio_gain_to_spread=[BR.ratio_vs_spread.min(), BR.ratio_vs_spread.max()], all_arch_above_ridge=bool((BR.min_arch_minus_ridge > 0).all()),
    T1RULE=bool((BR.dR2 > spr).all() and (BR.n_sig == 5).all()),
    nn_runs=int(len(BLn)), nn_runs_sig_better=int((BLn.arah == "lebih akurat").sum()), nn_runs_sig_worse=int((BLn.arah == "kurang akurat").sum()),
    nn_runs_ns=int((BLn.arah == "tidak beda").sum()),
    seed_sd_median=float(sd_stack.median()), seed_sd_max=float(sd_stack.max()), seed_sd_argmax=list(sd_stack.idxmax()),
    seed_se5_median=float(sd_stack.median() / np.sqrt(5)), seed_se5_max=float(sd_stack.max() / np.sqrt(5)),
    spread_seed42=[float(spr_seed[42].min()), float(spr_seed[42].max())], spread_single_seeds=[float(spr_seed.min().min()), float(spr_seed.max().max())],
    spread_median=float(spr.median()), S10_delta=[CB.S10_delta_baru.min(), CB.S10_delta_baru.max()],
    S7_max_abs_diff_s42=float((CB.R2_s42 - CB.S7_A_r2_tahap09).abs().max()),
    contoh_hari={r.kind: dict(s42=round(r.rmse_cb_s42, 1), rerata5=round(r.rmse_cb_rerata5, 1), sp=r.rmse_sp) for r in CH.itertuples()},
    fig5a=R2m[["LightGBM", "CatBoost", "XGBoost", "MLP"]].assign(SP=SP_R2).round(4).to_dict(orient="index"))
json.dump(J, open(os.path.join(OUT, "angka_baru.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)

pd.DataFrame([dict(site=s, pohon_terbaik_minus_js_terbaik=R2m.loc[s, TREES].max() - R2m.loc[s, NN].max(), rentang_jaringan_saraf_rerun=R2m.loc[s, NN].max() - R2m.loc[s, NN].min()) for s in SITES]).to_csv(os.path.join(OUT, "rentang_per_stasiun.csv"), index=False)
pd.set_option("display.width", 220)
print("== Tabel 3 baru (R², rerata 5 seed)\n", T3.loc["R2"].round(4).to_string())
print("\n== skill\n", T3.loc["skill"].round(3).to_string())
print("\n== CatBoost\n", CB.round(4).to_string())
print("\n== CatBoost − ridge\n", BR.round(4).to_string())
print("\n== uji vs LightGBM per seed\n", U.to_string())
print("\n== Tabel S6(b)\n", S6.round(4).to_string())
print("\n== Tabel S4 RMSE\n", RMm.round(1).to_string()); print("\n== MAE\n", MAm.round(1).to_string())
print("\n== R² residual\n", RRm.round(3).to_string()); print("\n== nRMSE\n", (RMm.div(ybar, axis=0) * 100).round(1).to_string())
print("\n== Fig. S5\n", CH.round(1).to_string())
print("\n== cek\n" + "\n".join(cek))
print("\n== ringkas\n" + json.dumps({k: v for k, v in J.items() if k not in ("fig5a", "spread_R2_per_site")}, ensure_ascii=False, default=float))
