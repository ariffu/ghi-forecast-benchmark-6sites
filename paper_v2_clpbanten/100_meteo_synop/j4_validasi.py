# -*- coding: utf-8 -*-
"""Tahap 100 validasi akhir V6.4 terhadap V6.3: kolom berubah hanya meteorologi AWS; folder lain identik; satuan angin Banten; siklus harian; pipeline P2F."""
import os, sys, subprocess, hashlib, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); V3 = r"C:\Users\ariff\Documents\Balai_data_v6_3"; V4 = r"C:\Users\ariff\Documents\Balai_data_v6_4"
sys.path.insert(0, HERE); from j2_bangun_v64 import MET
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; LON = dict(banten=106.7509, bengkulu=102.311998, jambi=103.4944, jogja=110.353578, kalbar=109.1905, semarang=110.3812)
h = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
for sub in ("clearsky", "qc", "clp_ekstra"):
    for f in sorted(os.listdir(os.path.join(V3, sub))): assert h(os.path.join(V3, sub, f)) == h(os.path.join(V4, sub, f)), (sub, f)
print("clearsky, qc, clp_ekstra identik dengan V6.3")
R = []
for s in S:
    r = dict(stasiun=s)
    for var in ("00_data", "00_data_rawfill"):
        a = pd.read_parquet(os.path.join(V3, var, f"{s}_full.parquet")); b = pd.read_parquet(os.path.join(V4, var, f"{s}_full.parquet")); assert list(a.columns) == list(b.columns) and (a.dtypes == b.dtypes).all()
        beda = [c for c in a.columns if not a[c].equals(b[c])]; assert set(beda) <= set(MET), set(beda) - set(MET); r[f"{var}_kolom_berubah"] = len(beda)
    t = pd.DatetimeIndex(b.ts_wib); kt = b.synop_wind_speed_kt.to_numpy(float); w = b.aws_wind_speed_ms.to_numpy(float)
    r["angin_sama_knot_V63"] = int(((np.abs(a.aws_wind_speed_ms.to_numpy(float) - kt) < 0.02) & (kt >= 1) & (np.abs(a.aws_wind_speed_ms.to_numpy(float) - kt * 0.514444) > 0.05)).sum())
    r["angin_sama_knot_V64"] = int(((np.abs(w - kt) < 0.02) & (kt >= 1) & (np.abs(w - kt * 0.514444) > 0.05)).sum())
    T = b.aws_temp_c; prof = T.groupby(t.hour * 60 + t.minute).mean(); r["suhu_puncak_wib"] = f"{int(prof.idxmax()) // 60:02d}:{int(prof.idxmax()) % 60:02d}"; r["suhu_lembah_wib"] = f"{int(prof.idxmin()) // 60:02d}:{int(prof.idxmin()) % 60:02d}"
    p = pd.to_numeric(b.aws_pressure_hpa); pa = p - p.rolling(144, center=True, min_periods=60).mean(); m = pa.notna().to_numpy(); lst = ((t.hour * 60 + t.minute + (LON[s] - 105) * 4) % 1440).to_numpy()
    ang = 2 * np.pi * 2 * lst[m] / 1440; co = np.linalg.lstsq(np.c_[np.cos(ang), np.sin(ang), np.ones(m.sum())], pa.to_numpy()[m], rcond=None)[0]; ph = (np.degrees(np.arctan2(co[1], co[0])) % 360) / 360 * 720
    r["S2_amp"] = round(float(np.hypot(*co[:2])), 2); r["S2_puncak"] = f"{int(ph) // 60:02d}:{int(ph) % 60:02d}"; r["tekanan_median"] = round(float(p.median()), 1)
    for c in ("aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms"):
        x = pd.to_numeric(b[c]); r[f"{c}_kosong_siang"] = round(float(x[(b.solar_elev_deg > 5).to_numpy()].isna().mean()), 3)
    r["rh_luar_0_100"] = int(((b.aws_rh_pct < 0) | (b.aws_rh_pct > 100)).sum()); r["angin_negatif"] = int((b.aws_wind_speed_ms < 0).sum())
    sc = b.aws_wind_dir_sin ** 2 + b.aws_wind_dir_cos ** 2; r["sin2cos2_maks_dev"] = round(float((sc - 1).abs().max()), 6) if sc.notna().any() else np.nan
    R.append(r)
T = pd.DataFrame(R); T.to_csv(os.path.join(HERE, "j4_validasi.csv"), index=False); pd.set_option("display.width", 250); print(T.T.to_string())
kode = r'''
import sys, numpy as np; sys.path.insert(0, r"%s"); import _common
for s in _common.SITES:
    df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean"); d = df.iloc[te]
    print(s, len(feats), len(tr), len(va), len(te), round(float(np.nanmean(d.base_mean)), 3))
''' % B
env = dict(os.environ, DATA_DIR=os.path.join(V4, "00_data"), CLEARSKY_DIR=os.path.join(V4, "clearsky"), CLP_EKSTRA_DIR=os.path.join(V4, "clp_ekstra"), FEATSET="P2F", PYTHONIOENCODING="utf-8")
o = subprocess.run([sys.executable, "-c", kode], capture_output=True, text=True, env=env, cwd=B); print(o.stdout); print(o.stderr[-500:] if o.returncode else "")
