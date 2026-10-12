# -*- coding: utf-8 -*-
"""Tahap 50 — Evaluasi himpunan prediktor: P0 (104, naskah), P1 "bersih" (64), P2 "ringkas" (43).

Desain dan aturan keputusan ditulis SEBELUM hasil: 50_prediktor/DESAIN_TERKUNCI_50.md.
Model: LightGBM residual (konfigurasi ablasi, lgbm() di 27) dan CatBoost direct (konfigurasi utama 04c).
Target rata-rata jam, mask elevasi > 5°, split 2022–2023 / 2024 / 2025, 6 situs. Pemilihan himpunan (K1) hanya
memakai R² validasi 2024; tahun uji 2025 hanya dilaporkan. Uji reproduksi: LightGBM T1+CLP = 07_replication,
CatBoost P0 = 04c (assert |ΔR²| < 1e-4).
Keluaran: 50_prediktor/{himpunan_prediktor,hasil_himpunan,ablasi_himpunan}.csv, preds_<situs>.npz, RINGKASAN_50.md.
Jalankan (WAJIB FEATSET=P0, karena skrip ini sendiri yang menyaring 104 -> 64 -> 43):
  FEATSET=P0 PYTHONIOENCODING=utf-8 python -u 50_evaluasi_prediktor.py > logs/50_evaluasi_prediktor.log 2>&1
Mode langit cerah mengikuti CLEARSKY (bawaan IP = Ineichen–Perez, 2026-10-08; SIMPLE = run asli 2026-10-06, arsip
_arsip_P2_cs1100/50_prediktor/). Pada IP, pipeline acuan berisi 43 prediktor, jadi uji reproduksi memakai P2:
LightGBM T1+CLP dengan pengelompokan P2 = 07_replication, CatBoost P2 = 04c. Aturan R1–R6 dan kriteria K1 tidak berubah.
"""
import os, sys, time, json, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.metrics import r2_score
from catboost import CatBoostRegressor
B = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, B)
import _common
from _common import split_idx, SITES
from _blockboot import delta_r2
OUT = os.path.join(B, "50_prediktor"); os.makedirs(OUT, exist_ok=True)
t0 = time.time()
def log(*a): print(*a, flush=True)
_src = open(os.path.join(B, "27_block_bootstrap.py"), encoding="utf-8").read(); ns = {"lgb": lgb, "os": os}
exec(_src[_src.index("def lgbm():"):_src.index("def setup(")], ns)          # lgbm() dan groups() identik 27
lgbm, groups = ns["lgbm"], ns["groups"]
assert _common.FEATSET == "P0", "jalankan dengan FEATSET=P0 (pembanding 104 vs 43)"
IP = _common.CLEARSKY == "IP"; REP = "P2" if IP else "P0"   # himpunan acuan uji reproduksi
def groups_p2(fs):                                   # pengelompokan pipeline P2 (groups() membaca env FEATSET)
    old = os.environ.get("FEATSET"); os.environ["FEATSET"] = "P2"
    try: return groups(fs)
    finally: os.environ["FEATSET"] = old

# ---------------- aturan (DESAIN_TERKUNCI_50.md) ----------------
R = {"R1": ["is_day_noaa", "is_day_cooper", "synop_rainfall_24h_mm", "synop_sunshine_h", "sunshine_slot_min", "sunshine_cum_min"],
     "R2": ["nett_wm2", "solar_elev_deg", "solar_elev_h1", "ghi_cs_t60", "elev_sin_t60", "kt_std_1h", "clp_ctt_k"],
     "R3": ["kt_cooper", "solar_elev_cooper_deg", "clear_sky_ghi_cooper"],
     "R4": [f"solar_elev_h{i}" for i in range(2, 7)] + [f"clear_sky_ghi_h{i}" for i in range(2, 7)] + [f"is_day_h{i}" for i in range(1, 7)],
     "R5": ["synop_temp_c", "synop_dewpoint_c", "synop_rh_pct", "synop_pressure_hpa", "synop_wind_dir_deg", "synop_wind_speed_kt",
            "aws_ghi_wm2", "aws_wind_dir_deg"],
     "R6": ["ghi_lag_10m", "ghi_lag_20m", "ghi_lag_30m", "ghi_lag_60m", "ghi_delta_10m", "ghi_delta_60m", "accel_ghi_20m",
            "kt_lag_10m", "kt_lag_20m", "kt_lag_30m", "kt_lag_60m", "accel_kt_20m", "clp_cot_lag_60m",
            "aws_temp_lag_10m", "aws_temp_lag_30m", "aws_temp_lag_60m", "aws_rh_lag_60m", "aws_pressure_lag_60m",
            "aws_temp_roll_180m_mean", "aws_rh_roll_180m_mean", "aws_wind_speed_roll_180m_mean"]}
assert [len(v) for v in R.values()] == [6, 7, 3, 16, 8, 21]
DROP1 = set(R["R1"] + R["R2"] + R["R3"] + R["R4"] + R["R5"])
ref07 = pd.read_csv(os.path.join(B, "07_replication", "replication_ablation_mean.csv")).set_index("site")
ref04 = pd.read_csv(os.path.join(B, "04c_mean_6situs", "baseline_mean_6situs.csv")).set_index("site")

def fit_lgb(d, fs):
    m = lgbm(); m.fit(d["tr"][fs], d["ytr"], eval_set=[(d["va"][fs], d["yva"])], eval_metric="l2", callbacks=[lgb.early_stopping(80, verbose=False)])
    return d["va"].base_mean.to_numpy() + m.predict(d["va"][fs]), d["b"] + m.predict(d["te"][fs]), m.best_iteration_
def fit_cb(d, fs):                                     # identik 04c_mean_6situs.py
    X = d["df"][fs]; Xtr = X.iloc[d["itr"]]; med = Xtr.median().fillna(0.0)
    cb = CatBoostRegressor(iterations=2500, learning_rate=0.03, depth=6, loss_function="RMSE", verbose=0, random_seed=42)
    cb.fit(Xtr.fillna(med), d["yall"][d["itr"]], eval_set=(X.iloc[d["iva"]].fillna(med), d["yall"][d["iva"]]), early_stopping_rounds=200, use_best_model=True)
    return cb.predict(X.iloc[d["iva"]].fillna(med)), cb.predict(X.iloc[d["ite"]].fillna(med)), cb.get_best_iteration()
def rmse(y, p): return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(p)) ** 2)))

rows, abl, members = [], [], None
for s in SITES:
    log(f"\n===== {s} ({time.time()-t0:.0f}s) =====")
    df, feats, yr = _common.prepare(s); itr, iva, ite = split_idx(df, yr, "mean")
    tr, va, te = df.iloc[itr], df.iloc[iva], df.iloc[ite]
    d = dict(df=df, itr=itr, iva=iva, ite=ite, tr=tr, va=va, te=te, yall=df.y_mean.to_numpy(),
             ytr=(tr.y_mean - tr.base_mean).to_numpy(), yva=(va.y_mean - va.base_mean).to_numpy(),
             y=te.y_mean.to_numpy(), b=te.base_mean.to_numpy(), day=te.ts_wib.dt.date.to_numpy())
    T1, CLP, SYN, AWS, SYNC, T4 = groups(feats)
    assert len(feats) == 104 and all(f in feats for v in R.values() for f in v), "daftar aturan tidak cocok dengan prediktor"
    P = {"P0": list(feats)}; P["P1"] = [f for f in feats if f not in DROP1]; P["P2"] = [f for f in P["P1"] if f not in R["R6"]]
    assert (len(P["P1"]), len(P["P2"])) == (64, 43), (len(P["P1"]), len(P["P2"]))
    if members is None:
        gname = {**{f: "inti (T1)" for f in T1}, **{f: "CLP" for f in CLP}, **{f: "SYNOP" for f in SYN}, **{f: "AWS" for f in AWS}, **{f: "eksperimental" for f in T4}}
        rule = {f: k for k, v in R.items() for f in v}
        members = pd.DataFrame([dict(prediktor=f, kelompok_naskah=gname[f], aturan_dibuang=rule.get(f, ""), P1=int(f in P["P1"]), P2=int(f in P["P2"])) for f in feats])
        members.to_csv(os.path.join(OUT, "himpunan_prediktor.csv"), index=False)
    # identitas R6 (data latih)
    for lag, dl in [("kt_lag_10m", "kt_delta_10m"), ("kt_lag_60m", "kt_delta_60m"), ("clp_cot_lag_60m", "clp_cot_delta_60m")]:
        base = "clp_cot" if lag.startswith("clp") else "kt"; e = (tr[base] - tr[lag] - tr[dl]).abs()
        log(f"  identitas {base} − {lag} − {dl}: maks |sisa| = {e.max():.2e} (n={e.notna().sum()})")
    e = (tr.accel_kt_20m - (2 * tr.kt_delta_10m - tr.kt_delta_20m)).abs(); log(f"  identitas accel_kt_20m − (2Δ10 − Δ20): maks |sisa| = {e.max():.2e}")
    # reproduksi
    fs_rep = (lambda g: g[0] + g[1])(groups_p2(P["P2"])) if IP else T1 + CLP
    _, pt, _ = fit_lgb(d, fs_rep); r = r2_score(d["y"], pt); ok = abs(round(r, 4) - ref07.loc[s, "T1_CLP"]) < 1e-4 + 1e-9
    log(f"  reproduksi LightGBM T1+CLP: refit={r:.4f} csv={ref07.loc[s, 'T1_CLP']:.4f} {'OK' if ok else 'BEDA'}"); assert ok
    pred = {}
    for model, fit in [("LightGBM", fit_lgb), ("CatBoost", fit_cb)]:
        for k in ["P0", "P1", "P2"]:
            pv, pt, it = fit(d, P[k]); pred[(model, k)] = pt
            yv = va.y_mean.to_numpy()
            rows.append(dict(site=s, model=model, set=k, n_feat=len(P[k]), val_R2=r2_score(yv, pv), test_R2=r2_score(d["y"], pt),
                             test_RMSE=rmse(d["y"], pt), best_iter=int(it)))
            log(f"  {model:8s} {k} ({len(P[k]):3d}): val R²={rows[-1]['val_R2']:.4f} uji R²={rows[-1]['test_R2']:.4f} "
                f"RMSE={rows[-1]['test_RMSE']:.1f} iter={it} ({time.time()-t0:.0f}s)")
            if model == "CatBoost" and k == REP:
                ok = abs(round(rows[-1]["test_R2"], 4) - ref04.loc[s, "CB_R2"]) < 1e-4 + 1e-9
                log(f"  reproduksi CatBoost {REP}: refit={rows[-1]['test_R2']:.4f} csv={ref04.loc[s, 'CB_R2']:.4f} {'OK' if ok else 'BEDA'}"); assert ok
        for k in ["P1", "P2"]:
            bb = delta_r2(d["y"], pred[(model, k)], pred[(model, "P0")], d["day"], record=False)
            rr = next(x for x in rows if x["site"] == s and x["model"] == model and x["set"] == k)
            rr.update(dR2_vs_P0=bb["dR2"], blk_lo=bb["blk_lo"], blk_hi=bb["blk_hi"], sig=bb["sig_block"])
            log(f"    {model} {k} − P0: ΔR²={bb['dR2']:+.4f} [{bb['blk_lo']:+.4f}, {bb['blk_hi']:+.4f}] sig={bb['sig_block']}")
    # ablasi dalam P1 dan P2 (LightGBM)
    for k in ["P1", "P2"]:
        core = [f for f in P[k] if f in T1 or f in T4]; clp = [f for f in P[k] if f in CLP]; aws = [f for f in P[k] if f in AWS]
        assert all(f in P[k] for f in SYNC)
        cfg = {"core": core, "core+CLP": core + clp, "core+AWS": core + aws, "core+SYNC": core + SYNC,
               "core+CLP+AWS": core + clp + aws, "core+CLP+SYNC": core + clp + SYNC}
        A = {c: fit_lgb(d, fs)[1] for c, fs in cfg.items()}; A["full"] = pred[("LightGBM", k)]
        log(f"  ablasi {k}: inti={len(core)} CLP={len(clp)} AWS={len(aws)} SYNC={len(SYNC)} | " + " ".join(f"{c}={r2_score(d['y'], v):.4f}" for c, v in A.items()))
        for a, b_, lab in [("core+CLP", "core", "CLP"), ("core+AWS", "core", "AWS"), ("core+SYNC", "core", "SYNOP cloud"),
                           ("core+CLP+AWS", "core+CLP", "AWS | CLP"), ("core+CLP+SYNC", "core+CLP", "SYNOP cloud | CLP"), ("full", "core+CLP", "sisa | CLP")]:
            bb = delta_r2(d["y"], A[a], A[b_], d["day"], record=False)
            abl.append(dict(site=s, set=k, effect=lab, R2_a=r2_score(d["y"], A[a]), R2_b=r2_score(d["y"], A[b_]), dR2=bb["dR2"],
                            blk_lo=bb["blk_lo"], blk_hi=bb["blk_hi"], sig=bb["sig_block"]))
        log("    " + " | ".join(f"{x['effect']} {x['dR2']:+.4f}{'*' if x['sig'] == 'yes' else ''}" for x in abl if x["site"] == s and x["set"] == k))
    np.savez(os.path.join(OUT, f"preds_{s}.npz"), y=d["y"], b=d["b"], day=d["day"].astype(str), **{f"{m}_{k}": v for (m, k), v in pred.items()})
    del df, tr, va, te, d

H = pd.DataFrame(rows); H.to_csv(os.path.join(OUT, "hasil_himpunan.csv"), index=False)
AB = pd.DataFrame(abl); AB.to_csv(os.path.join(OUT, "ablasi_himpunan.csv"), index=False)

# ---------------- keputusan ----------------
L = H[H.model == "LightGBM"].pivot(index="site", columns="set", values="val_R2")
K1 = {k: bool(((L[k] - L["P0"]) >= -0.002).all()) for k in ["P2", "P1"]}
chosen = "P2" if K1["P2"] else ("P1" if K1["P1"] else "P0")
def k3(k):
    a = AB[AB.set == k].set_index(["site", "effect"])
    return dict(CLP_sig_6=bool((a.xs("CLP", level="effect").sig == "yes").all()),
                AWS_CLP_le_001=bool((a.xs("AWS | CLP", level="effect").dR2 <= 0.01).all()),
                SYNC_le_0002=bool((a.xs("SYNOP cloud", level="effect").dR2 <= 0.002).all() and (a.xs("SYNOP cloud | CLP", level="effect").dR2 <= 0.002).all()))
dec = dict(K1_lolos=K1, terpilih=chosen, K3={k: k3(k) for k in ["P1", "P2"]}, durasi_s=round(time.time() - t0), clearsky=_common.CLEARSKY,
           dibuat=time.strftime("%Y-%m-%d %H:%M"))
json.dump(dec, open(os.path.join(OUT, "keputusan_50.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
log("\n===== KEPUTUSAN =====\n" + json.dumps(dec, indent=1, ensure_ascii=False))
log(f"SELESAI Tahap 50 dalam {time.time()-t0:.0f}s")
