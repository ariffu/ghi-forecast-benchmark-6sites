# Manuskrip V6: dibuat oleh analisis/00b_siapkan_analisis_v6.py dari Manuskrip_versi5\analisis\v4_01_analisis_tanpa_latih.py (sha256 852ebe0f7ee265a8…); jangan disunting langsung.
# -*- coding: utf-8 -*-
"""Naskah v5 (salinan skrip v4, jalur diubah), analisis 01 — analisis penjelas tanpa pelatihan ulang (2026-10-23).

Menjawab masukan pembimbing bahwa naskah v3 "hanya menyajikan data dari hasil model": analisis ini menjelaskan MENGAPA
arsitektur konvergen dan DI MANA/MENGAPA awan satelit menambah skill. Semua dari prediksi uji 2025 yang sudah ada:
  - rerun protokol baku (8 arsitektur × 6 stasiun × 5 seed, target residual seragam): ../../rerun protokol baku/hasil/{nn,pohon}
  - ablasi sumber LightGBM (tahap 27): paper_v2_clpbanten/27_block_bootstrap/preds_replication_<situs>.npz
Bagian:
  A. Diagnostik konvergensi (run seed 42 per arsitektur): korelasi galat, korelasi koreksi terhadap smart persistence (ŷ − ŷ_SP),
     selisih RMS antar-prediksi, kombinasi rerata 8 model (C1) dan stacking OLS cross-fitted hari genap/ganjil (C3) terhadap
     model tunggal terbaik; porsi sisa galat yang hilang. Bootstrap blok harian (_blockboot, 2000 ulangan, seed 11).
  B. Anggaran galat CatBoost (seed 42) dan smart persistence menurut kondisi langit di origin (k_t basis data: cerah > 0,65,
     berawan sebagian 0,30–0,65, mendung ≤ 0,30), waktu origin (06–10, 10–14, 14–18 WIB) dan tersil galat persistence
     |ȳ − ŷ_SP| (stabil / sedang / berubah; stratifikasi diagnostik pasca-kejadian, bukan prediktor).
  C. Sumbangan CLP (LightGBM inti vs inti + CLP) per kelas yang sama: penurunan RMSE (%) dengan CI bootstrap blok harian.
  D. Deskriptor per stasiun (n = 6, deskriptif): R² persistence, porsi berawan sebagian, skill CatBoost, ΔR²(CLP), R² residual.
Keluaran: ../hasil/a_konvergensi.csv, b_galat_kelas.csv, c_clp_kelas.csv, d_stasiun.csv, angka_analisis.json.
Jalankan: PYTHONIOENCODING=utf-8 FEATSET=P2 CLEARSKY=IP python -u 01_analisis_tanpa_latih.py
"""
import os, sys, json, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); V4 = os.path.dirname(HERE); ROOT = os.path.dirname(V4)
P = os.path.join(ROOT, "paper_v2_clpbanten"); PV = os.path.join(V4, "pipeline"); RR = os.path.join(V4, "protokol", "hasil")
sys.path.insert(0, P)
import _common, _blockboot as bb
from _common import prepare, split_idx, SITES
assert _common.FEATSET == "P2F" and _common.CLEARSKY == "IP" and len(_common.P2_AKTIF) == 44   # Manuskrip V6
OUT = os.path.join(V4, "hasil"); os.makedirs(OUT, exist_ok=True)
TREES = ["LightGBM", "CatBoost", "XGBoost"]; NN = ["MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"]; M8 = TREES + NN
SEEDS = [42, 1, 2, 3, 4]; NB = 2000
def pred(s, m, sd): return np.load(os.path.join(RR, "pohon" if m in TREES else "nn", f"pred_{s}_{m}_s{sd}.npy")).astype(float)
def r2(y, p): return 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
def rmse(y, p): return float(np.sqrt(((y - p) ** 2).mean()))
def boot_C(day, seed=11):
    days, inv = np.unique(day, return_inverse=True); D = len(days); rng = np.random.default_rng(seed)
    C = np.empty((NB, D))
    for i in range(NB): C[i] = np.bincount(rng.integers(0, D, D), minlength=D)
    return C, inv, D
def rmse_red_ci(ea2, eb2, mask, C, inv, D):
    """penurunan RMSE (%) model b terhadap a pada subset mask; CI bootstrap blok harian"""
    n = np.bincount(inv[mask], minlength=D).astype(float)
    sa, sb = np.bincount(inv[mask], ea2[mask], D), np.bincount(inv[mask], eb2[mask], D)
    ra, rb = np.sqrt((C @ sa) / (C @ n)), np.sqrt((C @ sb) / (C @ n)); red = 100 * (1 - rb / ra)
    point = 100 * (1 - np.sqrt(eb2[mask].mean()) / np.sqrt(ea2[mask].mean()))
    return point, float(np.percentile(red, 2.5)), float(np.percentile(red, 97.5))

RA, RB, RC, RD = [], [], [], []
for s in SITES:
    df, feats, yr = prepare(s, l_filter=5); tr, va, te = split_idx(df, yr, tgt="mean"); t = df.iloc[te]
    y, b = t.y_mean.to_numpy(float), t.base_mean.to_numpy(float); day = t.ts_wib.dt.date.astype(str).to_numpy()
    kt = t.kt_clearness.to_numpy(float); hr = t.ts_wib.dt.hour.to_numpy()
    Y = np.load(os.path.join(RR, "nn", f"yb_{s}.npz"), allow_pickle=True); assert np.allclose(Y["y"], y) and np.allclose(Y["b"], b), s
    Z = np.load(os.path.join(PV, "27_block_bootstrap", f"preds_replication_{s}.npz"), allow_pickle=True); assert np.allclose(Z["y"], y), s
    C, inv, D = boot_C(day)
    # ---------- A. konvergensi ----------
    P42 = {m: pred(s, m, 42) for m in M8}; R42 = {m: r2(y, P42[m]) for m in M8}; best = max(R42, key=R42.get)
    E = np.array([y - P42[m] for m in M8]); K = np.array([P42[m] - b for m in M8])
    iu = np.triu_indices(8, 1); ce = np.corrcoef(E)[iu]; ck = np.corrcoef(K)[iu]
    dp = np.array([rmse(P42[M8[i]], P42[M8[j]]) for i, j in zip(*iu)])
    c1 = np.mean([P42[m] for m in M8], axis=0)
    X = np.column_stack([np.ones_like(y)] + [P42[m] for m in M8]); even = np.array([int(d[-2:]) % 2 == 0 for d in day]); c3 = np.empty_like(y)
    for fit, app in [(even, ~even), (~even, even)]:
        w = np.linalg.lstsq(X[fit], y[fit], rcond=None)[0]; c3[app] = X[app] @ w
    a1 = bb.delta_r2(y, c1, P42[best], day, record=False); a3 = bb.delta_r2(y, c3, P42[best], day, record=False)
    sp = R42[best]
    RA.append(dict(site=s, best_single=best, R2_best=sp, R2_SP=r2(y, b), err_corr_min=ce.min(), err_corr_med=np.median(ce),
                   corr_koreksi_min=ck.min(), corr_koreksi_med=np.median(ck), rms_beda_pred_med=np.median(dp), rms_beda_pred_maks=dp.max(),
                   RMSE_best=rmse(y, P42[best]), C1_dR2=a1["dR2"], C1_lo=a1["blk_lo"], C1_hi=a1["blk_hi"],
                   C3_dR2=a3["dR2"], C3_lo=a3["blk_lo"], C3_hi=a3["blk_hi"], C3_porsi_sisa_pct=100 * a3["dR2"] / (1 - sp),
                   spread_seed42=max(R42.values()) - min(R42.values())))
    # ---------- B. anggaran galat ----------
    pcb = P42["CatBoost"]; ecb2, esp2 = (y - pcb) ** 2, (y - b) ** 2
    q1, q2 = np.quantile(np.abs(y - b), [1 / 3, 2 / 3])
    CL = {"langit": {"cerah": kt > 0.65, "berawan sebagian": (kt > 0.30) & (kt <= 0.65), "mendung": kt <= 0.30},
          "waktu": {"06–10": (hr >= 6) & (hr < 10), "10–14": (hr >= 10) & (hr < 14), "14–18": (hr >= 14) & (hr < 18)},
          "perubahan": {"stabil": np.abs(y - b) <= q1, "sedang": (np.abs(y - b) > q1) & (np.abs(y - b) <= q2), "berubah": np.abs(y - b) > q2}}
    assert all(sum(m.sum() for m in g.values()) == len(y) for k, g in CL.items() if k != "waktu"), "kelas tidak menutup semua baris"
    e1, e2 = (y - Z["T1"]) ** 2, (y - Z["T1+CLP"]) ** 2
    for grp, g in CL.items():
        for k, mk in g.items():
            RB.append(dict(site=s, grup=grp, kelas=k, n=int(mk.sum()), porsi_sampel=mk.mean(), porsi_SSE_CatBoost=ecb2[mk].sum() / ecb2.sum(),
                           RMSE_CatBoost=np.sqrt(ecb2[mk].mean()), RMSE_SP=np.sqrt(esp2[mk].mean()), skill=1 - np.sqrt(ecb2[mk].mean() / esp2[mk].mean()),
                           ybar=y[mk].mean()))
            pt, lo, hi = rmse_red_ci(e1, e2, mk, C, inv, D)
            RC.append(dict(site=s, grup=grp, kelas=k, n=int(mk.sum()), RMSE_inti=np.sqrt(e1[mk].mean()), RMSE_inti_CLP=np.sqrt(e2[mk].mean()),
                           turun_W=np.sqrt(e1[mk].mean()) - np.sqrt(e2[mk].mean()), turun_pct=pt, lo=lo, hi=hi))
    pt, lo, hi = rmse_red_ci(e1, e2, np.ones_like(y, bool), C, inv, D)
    RC.append(dict(site=s, grup="semua", kelas="semua", n=len(y), RMSE_inti=np.sqrt(e1.mean()), RMSE_inti_CLP=np.sqrt(e2.mean()),
                   turun_W=np.sqrt(e1.mean()) - np.sqrt(e2.mean()), turun_pct=pt, lo=lo, hi=hi))
    # ---------- D. deskriptor stasiun ----------
    pcb5 = np.mean([pred(s, "CatBoost", sd) for sd in SEEDS], axis=0); r = y - b
    RD.append(dict(site=s, R2_SP=r2(y, b), porsi_berawan_sebagian=((kt > 0.30) & (kt <= 0.65)).mean(), porsi_mendung=(kt <= 0.30).mean(),
                   sd_galat_SP=np.std(r), skill_CatBoost=np.mean([1 - rmse(y, pred(s, "CatBoost", sd)) / rmse(y, b) for sd in SEEDS]),
                   R2_residual_CatBoost=np.mean([1 - ((y - pred(s, "CatBoost", sd)) ** 2).sum() / ((r - r.mean()) ** 2).sum() for sd in SEEDS]),
                   dR2_CLP_LightGBM=r2(y, Z["T1+CLP"]) - r2(y, Z["T1"]), ybar=y.mean()))
    print(f"{s}: selesai", flush=True)

A, Bt, Ct, Dt = pd.DataFrame(RA), pd.DataFrame(RB), pd.DataFrame(RC), pd.DataFrame(RD)
for d, f in [(A, "a_konvergensi.csv"), (Bt, "b_galat_kelas.csv"), (Ct, "c_clp_kelas.csv"), (Dt, "d_stasiun.csv")]: d.to_csv(os.path.join(OUT, f), index=False)
rho = lambda a, b_: float(pd.Series(Dt[a].values).rank().corr(pd.Series(Dt[b_].values).rank()))
J = dict(
    err_corr_min=float(A.err_corr_min.min()), err_corr_med=[float(A.err_corr_med.min()), float(A.err_corr_med.max())],
    corr_koreksi_min=float(A.corr_koreksi_min.min()), corr_koreksi_med=[float(A.corr_koreksi_med.min()), float(A.corr_koreksi_med.max())],
    rms_beda_pred_med=[float(A.rms_beda_pred_med.min()), float(A.rms_beda_pred_med.max())],
    C1_dR2=[float(A.C1_dR2.min()), float(A.C1_dR2.max())], C3_dR2=[float(A.C3_dR2.min()), float(A.C3_dR2.max())],
    C3_porsi_sisa_pct=[float(A.C3_porsi_sisa_pct.min()), float(A.C3_porsi_sisa_pct.max())],
    rho_skill_vs_R2SP=rho("skill_CatBoost", "R2_SP"), rho_dCLP_vs_R2SP=rho("dR2_CLP_LightGBM", "R2_SP"),
    rho_dCLP_vs_berawan=rho("dR2_CLP_LightGBM", "porsi_berawan_sebagian"), rho_skill_vs_berawan=rho("skill_CatBoost", "porsi_berawan_sebagian"),
    R2_residual=[float(Dt.R2_residual_CatBoost.min()), float(Dt.R2_residual_CatBoost.max())])
json.dump(J, open(os.path.join(OUT, "angka_analisis.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print("\n== A konvergensi\n", A.round(4).to_string(index=False))
print("\n== B anggaran galat\n", Bt.round(3).to_string(index=False))
print("\n== C CLP per kelas\n", Ct.round(2).to_string(index=False))
print("\n== D stasiun\n", Dt.round(4).to_string(index=False))
print("\n== ringkas\n", json.dumps(J, ensure_ascii=False))
