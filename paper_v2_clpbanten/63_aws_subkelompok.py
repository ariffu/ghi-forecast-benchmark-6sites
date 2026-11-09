# -*- coding: utf-8 -*-
"""Tahap 63 — subkelompok AWS di atas core+CLP (audit bahasa F6, LAPORAN §31). Analisis POST HOC, tidak dikunci sebelum hasil.

Pertanyaan: mengapa AWS menambah skill di atas CLP di Banten (+0.007), lebih banyak daripada tanpa CLP (+0.005)?
- Tiap situs: LightGBM (setelan identik 27_block_bootstrap.lgbm) pada core+CLP+subkelompok AWS
  (humidity, temperature, pressure, wind, rain), dibanding core+CLP tersimpan (27_block_bootstrap/preds_replication_*.npz).
- Porsi gain AWS|CLP (prediksi tersimpan) pada origin 10:00–14:00 WIB.
- Banten: kecepatan saja vs arah saja; porsi gain angin pada siang hari dengan angin sektor barat (225–315°).
Keluaran: 63_aws_subkelompok/{subkelompok_6situs.csv, banten_angin.csv}.
Jalankan: PYTHONIOENCODING=utf-8 python -u 63_aws_subkelompok.py
"""
import os, sys, time, numpy as np, pandas as pd, lightgbm as lgb
B = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, B)
import _common
from _blockboot import delta_r2
from _common import split_idx
OUT = os.path.join(B, "63_aws_subkelompok"); os.makedirs(OUT, exist_ok=True)
assert _common.FEATSET in ("P2", "P2F") and _common.CLEARSKY == "IP"
_src = open(os.path.join(B, "27_block_bootstrap.py"), encoding="utf-8").read()
exec(_src[_src.index("def lgbm():"):_src.index("def check(")])          # lgbm, groups, setup, run — identik tahap 27
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
SUB = {"humidity": ["aws_rh_pct", "aws_rh_delta_60m"], "temperature": ["aws_temp_c", "aws_temp_delta_60m"],
       "pressure": ["aws_pressure_hpa", "aws_pressure_delta_60m"], "wind": ["aws_wind_speed_ms", "aws_wind_dir_sin", "aws_wind_dir_cos"],
       "rain": ["aws_rain_mm", "aws_rain_sum_180m"]}
def interaction(y, pa1, pb1, pa0, pb0, day, nb=2000, seed=11):
    """[R²(pa1) − R²(pb1)] − [R²(pa0) − R²(pb0)] dengan CI bootstrap blok harian (statistik cukup harian, seperti _blockboot)."""
    y = np.asarray(y, float); days, inv = np.unique(np.asarray(day), return_inverse=True); D = len(days)
    e = lambda p: np.bincount(inv, (y - np.asarray(p, float)) ** 2, D)
    num_d = (e(pb1) - e(pa1)) - (e(pb0) - e(pa0)); n_d = np.bincount(inv, minlength=D).astype(float)
    sy, syy = np.bincount(inv, y, D), np.bincount(inv, y * y, D)
    rng = np.random.default_rng(seed); C = np.empty((nb, D))
    for i in range(nb): C[i] = np.bincount(rng.integers(0, D, D), minlength=D)
    bs = (C @ num_d) / (C @ syy - (C @ sy) ** 2 / (C @ n_d))
    lo, hi = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
    return dict(dR2=num_d.sum() / ((y - y.mean()) ** 2).sum(), blk_lo=lo, blk_hi=hi, sig_block="yes" if lo > 0 or hi < 0 else "no")
t0 = time.time(); rows, rows_b, rows_n = [], [], []
for s in SITES:
    S, feats = setup(s); T1, CLP, SYN, AWS, SYNC, T4 = groups(feats); assert sorted(sum(SUB.values(), [])) == sorted(AWS)
    Z = np.load(os.path.join(B, "27_block_bootstrap", f"preds_replication_{s}.npz"), allow_pickle=True); assert np.allclose(Z["y"], S["y"])
    y, day, pc, pa = S["y"], S["day"], Z["T1+CLP"], Z["T1+CLP+AWS"]
    h = S["te"].ts_wib.dt.hour.to_numpy(); mid = (h >= 10) & (h < 14); sst = ((y - y.mean()) ** 2).sum()
    red = lambda p: (y - pc) ** 2 - (y - p) ** 2
    r = delta_r2(y, pa, pc, day); rows.append(dict(site=s, subgroup="all", **{k: r[k] for k in ("dR2", "blk_lo", "blk_hi", "sig_block")},
                                                    dR2_midday=red(pa)[mid].sum() / sst))
    P = {}
    for k, fs in SUB.items():
        P[k] = run(S, T1 + CLP + fs); r = delta_r2(y, P[k], pc, day)
        rows.append(dict(site=s, subgroup=k, **{c: r[c] for c in ("dR2", "blk_lo", "blk_hi", "sig_block")}, dR2_midday=red(P[k])[mid].sum() / sst))
        print(f"{s:9s} +{k:12s} dR2={r['dR2']:+.4f} [{r['blk_lo']:+.4f}, {r['blk_hi']:+.4f}] ({time.time()-t0:.0f}s)", flush=True)
    if s == "banten":
        te = S["te"]; deg = (np.degrees(np.arctan2(te.aws_wind_dir_sin, te.aws_wind_dir_cos)) + 360) % 360
        west = ((deg > 225) & (deg <= 315)).to_numpy()
        for lab, fs in [("speed", SUB["wind"][:1]), ("direction", SUB["wind"][1:])]:
            r = delta_r2(y, run(S, T1 + CLP + fs), pc, day); rows_b.append(dict(test=lab, **{c: r[c] for c in ("dR2", "blk_lo", "blk_hi", "sig_block")}))
        rw = red(P["wind"]); rows_b.append(dict(test="wind_midday_west_share", dR2=rw[mid & west].sum() / rw.sum(), frac_rows=(mid & west).mean()))
        rows_b.append(dict(test="wind_midday_share", dR2=rw[mid].sum() / rw.sum(), frac_rows=mid.mean()))
        cl = (te.clp_cloud_present_int > 0).to_numpy(); cl_ok = te.clp_cloud_present_int.notna().to_numpy()
        rows_b.append(dict(test="wind_cloudy_buffer_share", dR2=rw[cl & cl_ok].sum() / rw.sum(), frac_rows=(cl & cl_ok).mean()))
    # angin tanpa CLP (core+wind vs core) dan AWS tanpa CLP, untuk membandingkan dengan gain di atas CLP
    p0 = Z["T1"]; pwo = run(S, T1 + SUB["wind"]); r = delta_r2(y, pwo, p0, day); rw0 = (y - p0) ** 2 - (y - pwo) ** 2
    rows_n.append(dict(site=s, test="wind | core", **{c: r[c] for c in ("dR2", "blk_lo", "blk_hi", "sig_block")}, dR2_midday=rw0[mid].sum() / sst))
    r = delta_r2(y, Z["T1+AWS"], p0, day); rows_n.append(dict(site=s, test="AWS | core", **{c: r[c] for c in ("dR2", "blk_lo", "blk_hi", "sig_block")}))
    # interaksi angin×CLP = ΔR²(angin | core+CLP) − ΔR²(angin | core), bootstrap blok harian (resampel hari identik _blockboot: seed 11, 2000)
    it = interaction(y, P["wind"], pc, pwo, p0, day)
    rows_n.append(dict(site=s, test="interaction wind x CLP", **it))
    print(f"{s:9s} wind|core={rows_n[-3]['dR2']:+.4f}  AWS|core={rows_n[-2]['dR2']:+.4f}  selisih(wind|CLP − wind|core)={rows_n[-1]['dR2']:+.4f}", flush=True)
pd.DataFrame(rows).to_csv(os.path.join(OUT, "subkelompok_6situs.csv"), index=False)
pd.DataFrame(rows_b).to_csv(os.path.join(OUT, "banten_angin.csv"), index=False)
pd.DataFrame(rows_n).to_csv(os.path.join(OUT, "angin_tanpa_dengan_clp.csv"), index=False)
print(pd.DataFrame(rows_n).round(4).to_string(index=False))
print(pd.DataFrame(rows).round(4).to_string(index=False)); print(pd.DataFrame(rows_b).round(4).to_string(index=False))
print(f"selesai {time.time()-t0:.0f}s -> {OUT}")
