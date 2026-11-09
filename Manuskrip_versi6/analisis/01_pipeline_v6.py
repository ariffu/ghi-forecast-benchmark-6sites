# Manuskrip V6: dibuat oleh 00_siapkan_pipeline_v6.py dari Manuskrip_versi5/analisis/01_pipeline_v5.py (sha256 adab6fe25d2176f2…); jangan disunting langsung.
# Jalankan: DATA_DIR, CLEARSKY_DIR, CLP_EKSTRA_DIR = Balai_data_v6_10/…, FEATSET=P2F, PYTHONIOENCODING=utf-8 python -u 01_pipeline_v6.py
# -*- coding: utf-8 -*-
"""Naskah v5, analisis 01 — analisis pendukung pada seri v5 untuk keenam stasiun.
Konfigurasi dan kode inti disalin dari tahap 27, 19, 18b, 28, 31, 60, 13b, 63, dan analisis 02 v4; TETAP kosong sejak penyeragaman (tahap 82).
Keluaran ../pipeline/<tahap>/ dan ../hasil/ dengan skema sama dengan keluaran asli.
Jalankan: PYTHONIOENCODING=utf-8 SCR_V5=<kerja> python -u 01_pipeline_v5.py
"""
import os, sys, time, json, glob, shutil, warnings, numpy as np, pandas as pd, duckdb, lightgbm as lgb
warnings.simplefilter("ignore")
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error
from catboost import CatBoostRegressor
HERE = os.path.dirname(os.path.abspath(__file__)); V5 = os.path.dirname(HERE); ROOT = os.path.dirname(V5)
B = os.path.join(ROOT, "paper_v2_clpbanten"); sys.path.insert(0, B)
import _common
from _common import split_idx
from _blockboot import delta_r2
assert _common.FEATSET == "P2F" and _common.CLEARSKY == "IP" and len(_common.P2_AKTIF) == 44   # Manuskrip V6
_V610 = r"C:\Users\ariff\Documents\Balai_data_v6_10"; _KOTAK = r"C:\Users\ariff\Documents\Balai_kotak_v6_10"
for _k, _d in (("DATA_DIR", "00_data"), ("CLEARSKY_DIR", "clearsky"), ("CLP_EKSTRA_DIR", "clp_ekstra")): assert os.path.normcase(os.environ.get(_k, "")) == os.path.normcase(os.path.join(_V610, _d)), _k
D0, DR = os.path.join(_V610, "00_data"), os.path.join(_V610, "00_data_rawfill"); PL = os.path.join(V5, "pipeline"); HS = os.path.join(V5, "hasil")
os.makedirs(HS, exist_ok=True)
UBAH = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; TETAP = []; SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
t0 = time.time()
def log(*a): print(f"[{time.time() - t0:6.0f}s]", *a, flush=True)
def outdir(*p):
    d = os.path.join(PL, *p); os.makedirs(d, exist_ok=True); return d
_src = open(os.path.join(B, "27_block_bootstrap.py"), encoding="utf-8").read()
exec(_src[_src.index("def lgbm():"):_src.index("def check(")])                        # lgbm, groups, setup, run identik tahap 27
_common.DATA = D0
gabung = lambda baru, lama, by="site": pd.concat([pd.DataFrame(baru), lama[lama[by].isin(TETAP)]], ignore_index=True)

# ---------- tahap 27: ablasi LightGBM ----------
O27 = outdir("27_block_bootstrap"); O19 = outdir("19_sens_clp_fill"); rows27, rows19, Z27 = [], [], {}
def rmsk(y, p1, pc, pf, n_tr_av, variant, s):
    n = len(y); bi = np.random.default_rng(11).integers(0, n, size=(2000, n))
    def br(p): e = (y - p) ** 2; ee = e[bi]; mu = y[bi].mean(1); return 1 - ee.mean(1) / ((y[bi] - mu[:, None]) ** 2).mean(1)
    lo, hi = np.percentile(br(pc) - br(p1), [2.5, 97.5])
    return dict(variant=variant, site=s, n_test=n, clp_cot_avail_test=round(float(n_tr_av), 4), T1=round(r2_score(y, p1), 4), T1_CLP=round(r2_score(y, pc), 4), FULL=round(r2_score(y, pf), 4), dCLP=round(r2_score(y, pc) - r2_score(y, p1), 4), dCLP_lo=round(lo, 4), dCLP_hi=round(hi, 4))
for s in UBAH:
    S, feats = setup(s, D0); T1, CLP, SYN, AWS, SYNC, T4 = groups(feats)
    Pz = {k: run(S, fs) for k, fs in {"T1": T1, "T1+CLP": T1 + CLP, "T1+AWS": T1 + AWS, "T1+SYNcloud": T1 + SYNC, "T1+CLP+AWS": T1 + CLP + AWS, "T1+CLP+SYNcloud": T1 + CLP + SYNC}.items()}
    np.savez(os.path.join(O27, f"preds_replication_{s}.npz"), y=S["y"], day=S["day"].astype(str), **Pz); Z27[s] = Pz
    for a, b_, lab in [("T1+CLP", "T1", "dCLP"), ("T1+AWS", "T1", "dAWS"), ("T1+SYNcloud", "T1", "dSYNOP"), ("T1+CLP+AWS", "T1+CLP", "dAWS|CLP"), ("T1+CLP+SYNcloud", "T1+CLP", "dSYNOP|CLP")]:
        r = delta_r2(S["y"], Pz[a], Pz[b_], S["day"]); r.update(site=s, effect=lab); rows27.append(r)
    pf = run(S, feats); rows19.append(rmsk(S["y"], Pz["T1"], Pz["T1+CLP"], pf, S["te"]["clp_cot"].notna().mean(), "masked (utama)", s))
    Sr, fr = setup(s, DR); T1r, CLPr, *_ = groups(fr); assert np.allclose(Sr["y"], S["y"])
    rows19.append(rmsk(Sr["y"], run(Sr, T1r), run(Sr, T1r + CLPr), run(Sr, fr), Sr["te"]["clp_cot"].notna().mean(), "raw fill (COT=0)", s))
    _common.DATA = D0                                                                 # setup() mengganti folder secara global; tahap berikutnya harus membaca data utama
    log(s, "ablasi LightGBM dan isian CLP selesai")
for s in TETAP: shutil.copyfile(os.path.join(B, "27_block_bootstrap", f"preds_replication_{s}.npz"), os.path.join(O27, f"preds_replication_{s}.npz"))
gabung(rows27, pd.read_csv(os.path.join(B, "27_block_bootstrap", "replication_ablation_block.csv"))).to_csv(os.path.join(O27, "replication_ablation_block.csv"), index=False)
gabung(rows19, pd.read_csv(os.path.join(B, "19_sens_clp_fill", "sens_clp_fill.csv"))).to_csv(os.path.join(O19, "sens_clp_fill.csv"), index=False)

# ---------- tahap 18b: SYNOP dibawa maju ----------
s18 = open(os.path.join(B, "18b_synop_asof_6situs.py"), encoding="utf-8").read(); s18 = s18[:s18.index('if sys.argv[1] == "run":')]
s18 = s18.replace("X = apply_clearsky(X, site)", "X = apply_clearsky(X, site); X = _common.add_clp_ekstra(X, site) if _common.FEATSET == 'P2F' else X")   # Manuskrip V6: prediktor ke-44
ns18 = {"__file__": os.path.join(B, "18b_synop_asof_6situs.py"), "_common": _common}; exec(compile(s18.replace('os.environ.get("DATA_DIR", "00_data")', repr(D0)), "18b", "exec"), ns18)
rows18 = []
pairs = [("T1+SYNcloud_orig", "T1"), ("T1+SYNcloud_asof", "T1"), ("T1+SYNall_orig", "T1"), ("T1+SYNall_asof", "T1"), ("T1+CLP+SYNcloud_orig", "T1+CLP"), ("T1+CLP+SYNcloud_asof", "T1+CLP"), ("T1+CLP+SYNall_orig", "T1+CLP"), ("T1+CLP+SYNall_asof", "T1+CLP"), ("T1+CLP", "T1")]
for s in UBAH:
    X, feats, SYN, y, b, itr, iva, ite = ns18["load"](s); CFG = ns18["configs"](feats, SYN); d = X.solar_elev_deg.to_numpy() > 5
    av = (float(np.mean(~np.isnan(X.synop_temp_c.to_numpy()[d]))), float(np.mean(~np.isnan(X.synop_temp_c_asof.to_numpy()[d])))); Pp = {}
    for k, fs in CFG.items():
        mm = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.03, num_leaves=63, min_child_samples=50, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=0.1, random_state=42, n_jobs=-1, verbose=-1)
        mm.fit(X.iloc[itr][fs], y[itr] - b[itr], eval_set=[(X.iloc[iva][fs], y[iva] - b[iva])], callbacks=[lgb.early_stopping(80, verbose=False)]); Pp[k] = b[ite] + mm.predict(X.iloc[ite][fs])
    yt = y[ite]; n = len(yt); bi = np.random.default_rng(0).integers(0, n, size=(2000, n)); r2f = lambda q: 1 - ((yt - q) ** 2).sum() / ((yt - yt.mean()) ** 2).sum()
    def br(p): e = (yt[bi] - p[bi]) ** 2; mu = yt[bi].mean(1); return 1 - e.mean(1) / ((yt[bi] - mu[:, None]) ** 2).mean(1)
    for a, c in pairs:
        dd = br(Pp[a]) - br(Pp[c]); rows18.append(dict(site=s, config=a, vs=c, dR2=round(r2f(Pp[a]) - r2f(Pp[c]), 4), CI_lo=round(np.percentile(dd, 2.5), 4), CI_hi=round(np.percentile(dd, 97.5), 4), avail_orig=round(av[0], 4), avail_asof=round(av[1], 4)))
    log(s, "SYNOP dibawa maju selesai")
gabung(rows18, pd.read_csv(os.path.join(B, "18_synop_asof", "6situs", "synop_asof_6situs.csv"))).to_csv(os.path.join(outdir("18_synop_asof", "6situs"), "synop_asof_6situs.csv"), index=False)

# ---------- tahap 28 (E1, E2) dan 31 (latensi): LightGBM saja, CatBoost tidak dipakai naskah ----------
SPAT = ["clps_cot_std", "clps_cot_min", "clps_cot_max", "clps_cth_std", "clps_cloud_frac_lag_60m", "clps_cot_std_lag_60m"]   # Manuskrip V6: clps_cloud_frac = clp_cloud_frac (prediktor ke-44)
CLP10 = ["clp_cot", "clp_cth_km", "clp_ctt_k", "clp_cer_um", "clp_cloud_present_int", "clp_cot_lag_60m", "clp_cot_delta_60m", "clp_cot_roll_180m_mean", "clp_cth_lag_60m", "clp_cth_roll_180m_mean"]
def lfit(tr, va, te, b, fs, ytr, yva):
    m = lgbm(); m.fit(tr[fs], ytr, eval_set=[(va[fs], yva)], eval_metric="l2", callbacks=[lgb.early_stopping(80, verbose=False)]); return b + m.predict(te[fs])
rows28, rows31 = [], []
for s in UBAH:
    df, feats, yr = _common.prepare(s); T1, CLP, *_ = groups(feats)
    sp = duckdb.connect().execute("SELECT * FROM read_parquet(?) ORDER BY ts_wib", [os.path.join(_KOTAK, f"{s}_clp_kotak.parquet")]).df(); assert (sp.ts_wib.to_numpy() == df.ts_wib.to_numpy()).all()
    d2 = df.copy()
    assert np.allclose(sp.clps_cloud_frac.to_numpy(float), df.clp_cloud_frac.to_numpy(float), equal_nan=True)   # Manuskrip V6
    for c in SPAT: d2[c] = sp[c].to_numpy(float)
    itr, iva, ite = split_idx(d2, yr, "mean"); tr, va, te = d2.iloc[itr], d2.iloc[iva], d2.iloc[ite]
    ytr, yva = (tr.y_mean - tr.base_mean).to_numpy(), (va.y_mean - va.base_mean).to_numpy(); y, b_ = te.y_mean.to_numpy(), te.base_mean.to_numpy(); day = te.ts_wib.dt.date.to_numpy()
    for e, base in (("E1", T1 + CLP), ("E2", feats)):
        p0, p1 = lfit(tr, va, te, b_, base, ytr, yva), lfit(tr, va, te, b_, base + SPAT, ytr, yva); r = delta_r2(y, p1, p0, day, record=False)
        r.update(site=s, exp=e, R2_base=r2_score(y, p0), R2_spat=r2_score(y, p1), RMSE_base=float(np.sqrt(mean_squared_error(y, p0))), RMSE_spat=float(np.sqrt(mean_squared_error(y, p1)))); r["meaningful"] = "YES" if r["dR2"] >= 0.002 and r["blk_lo"] > 0 else "no"; rows28.append(r)
    d0 = df.copy()                                                                    # rekonstruksi V0 seperti tahap 31; Kalimantan Barat sudah t−10 di data, jadi V0 = data apa adanya
    if s != "kalbar": d0[CLP10] = d0[CLP10].shift(-1)
    pT = None
    for v, k in [("V0", 0), ("L10", 1), ("L20", 2)]:
        dv = d0.copy()
        if k: dv[CLP10] = dv[CLP10].shift(k)
        tr, va, te = dv.iloc[itr], dv.iloc[iva], dv.iloc[ite]
        if pT is None: pT = lfit(tr, va, te, b_, T1, ytr, yva)
        pc = lfit(tr, va, te, b_, T1 + CLP, ytr, yva); q = delta_r2(y, pc, pT, day, record=False)
        rows31.append(dict(site=s, variant=v, R2_T1CLP=r2_score(y, pc), dCLP=q["dR2"], dCLP_lo=q["blk_lo"], dCLP_hi=q["blk_hi"]))
    log(s, "statistik kotak dan latensi selesai")
gabung(rows28, pd.read_csv(os.path.join(B, "28_clp_spatial", "clp_spatial_results.csv"))).to_csv(os.path.join(outdir("28_clp_spatial"), "clp_spatial_results.csv"), index=False)
gabung(rows31, pd.read_csv(os.path.join(B, "31_clp_lag", "clp_lag_results.csv"))).to_csv(os.path.join(outdir("31_clp_lag"), "clp_lag_results.csv"), index=False)

# ---------- tahap 60 (Ridge) dan 13b (referensi CP) ----------
ZL0 = np.load(os.path.join(B, "60_skill_linear", "preds_linear.npz")); ZL = {k: ZL0[k] for k in ZL0.files if k.split("__")[0] in TETAP}
REF0 = pd.read_csv(os.path.join(B, "13_reference_skill_6situs", "reference_skill_6situs.csv")); rows13 = []
def rm(a, c): return float(np.sqrt(np.mean((a - c) ** 2)))
for s in UBAH:
    df, feats, yr = _common.prepare(s); itr, iva, ite = split_idx(df, yr, "mean"); tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
    y, b_ = te.y_mean.to_numpy(float), te.base_mean.to_numpy(float); X = lambda d: d[feats].astype("float64")
    med = X(tr).median().fillna(0.0); mu = X(tr).fillna(med).mean(); sd = X(tr).fillna(med).std().replace(0, 1).fillna(1); Z = lambda d: ((X(d).fillna(med) - mu) / sd).to_numpy()
    Ztr, Zva, Zte = Z(tr), Z(va), Z(te); rtr = (tr.y_mean - tr.base_mean).to_numpy(float); vb, vy = va.base_mean.to_numpy(float), va.y_mean.to_numpy(float); best = None
    for a in [10.0 ** k for k in range(-2, 6)]:
        m = Ridge(alpha=a).fit(Ztr, rtr); v = r2_score(vy, vb + m.predict(Zva))
        if best is None or v > best[0]: best = (v, a, m)
    ZL[f"{s}__linear"] = b_ + best[2].predict(Zte); ZL[f"{s}__y"] = y; ZL[f"{s}__b"] = b_
    cmap = tr.assign(h=tr.ts_wib.dt.hour).groupby("h").y_mean.mean(); clim = lambda f: f.ts_wib.dt.hour.map(cmap).to_numpy(float)
    yv, pv, cv = va.y_mean.to_numpy(float), va.base_mean.to_numpy(float), clim(va); fill = np.nanmean(cv); cv = np.where(np.isnan(cv), fill, cv)
    ba, br_ = None, np.inf
    for a in np.linspace(0, 1, 101):
        r = rm(a * cv + (1 - a) * pv, yv)
        if r < br_: ba, br_ = a, r
    ct = np.where(np.isnan(clim(te)), fill, clim(te)); ref = ba * ct + (1 - ba) * b_
    rows13.append(dict(site=s, alpha=round(ba, 2), RMSE_clim=round(rm(ct, y), 1), RMSE_pers=round(rm(b_, y), 1), RMSE_ref=round(rm(ref, y), 1)))
    log(s, f"Ridge R² {r2_score(y, ZL[f'{s}__linear']):.4f}, α {best[1]:g}; CP α {ba:.2f}, RMSE referensi {rm(ref, y):.1f}")
np.savez(os.path.join(outdir("60_skill_linear"), "preds_linear.npz"), **ZL)
gabung(rows13, REF0).to_csv(os.path.join(outdir("13_reference_skill_6situs"), "reference_skill_6situs.csv"), index=False)

# ---------- tahap 63: subkelompok AWS ----------
s63 = open(os.path.join(B, "63_aws_subkelompok.py"), encoding="utf-8").read(); exec(s63[s63.index('SUB = {"humidity"'):s63.index("t0 = time.time(); rows, rows_b, rows_n")])
rw63, rb63, rn63 = [], [], []
for s in UBAH:
    S, feats = setup(s, D0); T1, CLP, SYN, AWS, SYNC, T4 = groups(feats); assert sorted(sum(SUB.values(), [])) == sorted(AWS)
    Z = np.load(os.path.join(O27, f"preds_replication_{s}.npz"), allow_pickle=True); assert np.allclose(Z["y"], S["y"])
    y, day, pc, pa = S["y"], S["day"], Z["T1+CLP"], Z["T1+CLP+AWS"]; h = S["te"].ts_wib.dt.hour.to_numpy(); mid = (h >= 10) & (h < 14); sst = ((y - y.mean()) ** 2).sum(); red = lambda p: (y - pc) ** 2 - (y - p) ** 2
    r = delta_r2(y, pa, pc, day); rw63.append(dict(site=s, subgroup="all", **{k: r[k] for k in ("dR2", "blk_lo", "blk_hi", "sig_block")}, dR2_midday=red(pa)[mid].sum() / sst)); Pw = {}
    for k, fs in SUB.items():
        Pw[k] = run(S, T1 + CLP + fs); r = delta_r2(y, Pw[k], pc, day); rw63.append(dict(site=s, subgroup=k, **{c: r[c] for c in ("dR2", "blk_lo", "blk_hi", "sig_block")}, dR2_midday=red(Pw[k])[mid].sum() / sst))
    if s == "banten":
        te = S["te"]; deg = (np.degrees(np.arctan2(te.aws_wind_dir_sin, te.aws_wind_dir_cos)) + 360) % 360; west = ((deg > 225) & (deg <= 315)).to_numpy()
        for lab, fs in [("speed", SUB["wind"][:1]), ("direction", SUB["wind"][1:])]:
            r = delta_r2(y, run(S, T1 + CLP + fs), pc, day); rb63.append(dict(test=lab, **{c: r[c] for c in ("dR2", "blk_lo", "blk_hi", "sig_block")}))
        rw = red(Pw["wind"]); rb63.append(dict(test="wind_midday_west_share", dR2=rw[mid & west].sum() / rw.sum(), frac_rows=(mid & west).mean())); rb63.append(dict(test="wind_midday_share", dR2=rw[mid].sum() / rw.sum(), frac_rows=mid.mean()))
    log(s, "subkelompok AWS selesai")
O63 = outdir("63_aws_subkelompok"); gabung(rw63, pd.read_csv(os.path.join(B, "63_aws_subkelompok", "subkelompok_6situs.csv"))).to_csv(os.path.join(O63, "subkelompok_6situs.csv"), index=False); pd.DataFrame(rb63).to_csv(os.path.join(O63, "banten_angin.csv"), index=False)

# ---------- analisis 02 v4: ablasi CatBoost residual ----------
rowsC, r2C = [], []
RF = pd.read_csv(os.path.join(V5, "protokol", "hasil", "pohon", "metrik_pohon.csv")).query("model == 'CatBoost' and seed == 42").set_index("site").R2
for s in UBAH:
    df, feats, yr = _common.prepare(s, l_filter=5); tr, va, te = split_idx(df, yr, tgt="mean"); y = df.y_mean.to_numpy(); b_ = df.base_mean.to_numpy(); day = df.ts_wib.dt.date.to_numpy()[te]
    T1, CLP, SYN, AWS, SYNC, T4 = groups(feats); Pr = {}
    for k, fs in {"FULL": feats, "T1": T1, "T1+CLP": T1 + CLP, "T1+AWS": T1 + AWS, "T1+SYNcloud": T1 + SYNC, "T1+CLP+AWS": T1 + CLP + AWS, "T1+CLP+SYNcloud": T1 + CLP + SYNC}.items():
        X = df[fs]; med = X.iloc[tr].median().fillna(0.0)
        m = CatBoostRegressor(iterations=2500, learning_rate=0.03, depth=6, loss_function="RMSE", verbose=0, random_seed=42, thread_count=3, allow_writing_files=False)
        m.fit(X.iloc[tr].fillna(med), y[tr] - b_[tr], eval_set=(X.iloc[va].fillna(med), y[va] - b_[va]), early_stopping_rounds=200, use_best_model=True)
        Pr[k] = b_[te] + m.predict(X.iloc[te].fillna(med)); r2C.append(dict(site=s, config=k, R2=r2_score(y[te], Pr[k]), n_feat=len(fs), n_trees=int(m.tree_count_)))
    d = r2_score(y[te], Pr["FULL"]) - RF[s]; log(s, f"CatBoost FULL vs protokol baku seed 42: {d:+.5f}"); assert abs(d) < 5e-4, s
    np.savez(os.path.join(HS, f"preds_ablasi_cb_{s}.npz"), y=y[te], b=b_[te], day=day.astype(str), **Pr)
    for a, c, lab in [("T1+CLP", "T1", "dCLP"), ("T1+AWS", "T1", "dAWS"), ("T1+SYNcloud", "T1", "dSYNOP"), ("T1+CLP+AWS", "T1+CLP", "dAWS|CLP"), ("T1+CLP+SYNcloud", "T1+CLP", "dSYNOP|CLP")]:
        r = delta_r2(y[te], Pr[a], Pr[c], day, record=False); r.update(site=s, effect=lab); rowsC.append(r)
pd.DataFrame(rowsC).to_csv(os.path.join(HS, "ablasi_catboost_residual.csv"), index=False)
pd.DataFrame(r2C).to_csv(os.path.join(HS, "ablasi_catboost_residual_r2.csv"), index=False)
log("SELESAI analisis 01 v6")
