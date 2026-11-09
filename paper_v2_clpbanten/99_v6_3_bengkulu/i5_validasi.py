# -*- coding: utf-8 -*-
"""Tahap 99 validasi akhir V6.3 terhadap V6.2: kolom berubah, provenance, folder lain identik, pipeline P2F enam stasiun, pasang S2 dan langkah tekanan."""
import os, sys, subprocess, hashlib, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); V2 = r"C:\Users\ariff\Documents\Balai_data_v6_2"; V3 = r"C:\Users\ariff\Documents\Balai_data_v6_3"
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; LON = dict(banten=106.7509, bengkulu=102.311998, jambi=103.4944, jogja=110.353578, kalbar=109.1905, semarang=110.3812)
h = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
for sub in ("clearsky", "qc", "clp_ekstra"):
    for f in sorted(os.listdir(os.path.join(V2, sub))): assert h(os.path.join(V2, sub, f)) == h(os.path.join(V3, sub, f)), (sub, f)
print("clearsky, qc, clp_ekstra identik dengan V6.2")
R = []
for s in S:
    r = dict(stasiun=s)
    for var in ("00_data", "00_data_rawfill"):
        a = pd.read_parquet(os.path.join(V2, var, f"{s}_full.parquet")); b = pd.read_parquet(os.path.join(V3, var, f"{s}_full.parquet")); assert list(a.columns) == list(b.columns) and (a.dtypes == b.dtypes).all()
        r[f"{var}_berubah"] = ",".join(sorted(c for c in a.columns if not a[c].equals(b[c])))
    pa, pb = pd.read_parquet(os.path.join(V2, "provenance", f"{s}_provenance.parquet")), pd.read_parquet(os.path.join(V3, "provenance", f"{s}_provenance.parquet"))
    assert all(pa[c].equals(pb[c]) for c in pa.columns); r["prov_baru"] = ",".join(c for c in pb.columns if c not in pa.columns)
    t = pd.DatetimeIndex(b.ts_wib); p = pd.to_numeric(b.aws_pressure_hpa); x = p.to_numpy(float)
    g = (p != p.shift()).cumsum(); r["datar_3j"] = int(((p.groupby(g).transform("size") >= 18) & p.notna()).sum())
    r["langkah_gt2"] = int((np.abs(np.diff(x, prepend=np.nan)) > 2).sum())
    pa_ = p - p.rolling(144, center=True, min_periods=60).mean(); w = pa_.notna().to_numpy(); lst = ((t.hour * 60 + t.minute + (LON[s] - 105) * 4) % 1440).to_numpy()
    ang = 2 * np.pi * 2 * lst[w] / 1440; co = np.linalg.lstsq(np.c_[np.cos(ang), np.sin(ang), np.ones(w.sum())], pa_.to_numpy()[w], rcond=None)[0]
    r["S2_amp"] = round(float(np.hypot(*co[:2])), 2); r["S2_puncak"] = f"{int((np.degrees(np.arctan2(co[1], co[0])) % 360) / 360 * 720) // 60:02d}:{int((np.degrees(np.arctan2(co[1], co[0])) % 360) / 360 * 720) % 60:02d}"
    R.append(r)
T = pd.DataFrame(R); T.to_csv(os.path.join(HERE, "i5_validasi.csv"), index=False); pd.set_option("display.width", 260); pd.set_option("display.max_colwidth", 120); print(T.to_string(index=False))
kode = r'''
import sys, numpy as np; sys.path.insert(0, r"%s"); import _common
for s in _common.SITES:
    df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean"); d = df.iloc[te]
    print(s, len(feats), len(tr), len(va), len(te), round(float(np.nanmean(d.base_mean)), 3), "kosong uji: tekanan", round(float(d.aws_pressure_hpa.isna().mean()), 3), "angin", round(float(d.aws_wind_speed_ms.isna().mean()), 3), "frac", round(float(d.clp_cloud_frac.isna().mean()), 3))
''' % B
env = dict(os.environ, DATA_DIR=os.path.join(V3, "00_data"), CLEARSKY_DIR=os.path.join(V3, "clearsky"), CLP_EKSTRA_DIR=os.path.join(V3, "clp_ekstra"), FEATSET="P2F", PYTHONIOENCODING="utf-8")
o = subprocess.run([sys.executable, "-c", kode], capture_output=True, text=True, env=env, cwd=B); print(o.stdout); print(o.stderr[-500:] if o.returncode else "")
