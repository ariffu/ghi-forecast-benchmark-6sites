# -*- coding: utf-8 -*-
"""Tahap 103 audit V6.6 terhadap syarat lolos DESAIN_103: lompatan, ketersediaan, identik non-meteorologi, pipeline P2F. (SYNOP bulanan: n4_banding_v66.py.)"""
import os, sys, subprocess, hashlib, numpy as np, pandas as pd
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 300)
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); V5 = r"C:\Users\ariff\Documents\Balai_data_v6_5"; V6 = r"C:\Users\ariff\Documents\Balai_data_v6_6"
sys.path.insert(0, os.path.join(B, "100_meteo_synop")); from j2_bangun_v64 import MET
SYN = ["synop_visibility_km", "synop_cloud_cover_oktas", "synop_cl", "synop_cm", "synop_ch", "synop_present_weather_ww"]
THR = dict(aws_temp_c=2.0, aws_rh_pct=10.0, aws_pressure_hpa=1.0, aws_wind_speed_ms=5.0)
h = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
for sub in ("clearsky", "qc", "clp_ekstra"):
    for f in sorted(os.listdir(os.path.join(V5, sub))): assert h(os.path.join(V5, sub, f)) == h(os.path.join(V6, sub, f)), (sub, f)
print("clearsky, qc, clp_ekstra identik dengan V6.5")
J, A = [], []
for s in ("banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"):
    for var in ("00_data", "00_data_rawfill"):
        a = pd.read_parquet(os.path.join(V5, var, f"{s}_full.parquet")); b = pd.read_parquet(os.path.join(V6, var, f"{s}_full.parquet"))
        assert list(a.columns) == list(b.columns) and (a.dtypes == b.dtypes).all(); beda = [c for c in a.columns if not a[c].equals(b[c])]; assert set(beda) <= set(MET) | set(SYN), set(beda) - set(MET) - set(SYN)
    t = pd.DatetimeIndex(b.ts_wib); org = b.solar_elev_deg.to_numpy(float) > 5; yr = t.year.to_numpy(); mulai = np.argmax(np.isfinite(b.aws_temp_c.to_numpy(float)))
    for c, thr in THR.items():
        for lab, d in (("V6.5", a), ("V6.6", b)):
            dx = np.abs(np.diff(d[c].to_numpy(float), prepend=np.nan)); J.append(dict(stasiun=s, var=c, versi=lab, lompat=int((dx > thr).sum()), p999=round(float(np.nanpercentile(dx, 99.9)), 3), maks=round(float(np.nanmax(dx)), 3)))
    for c in ["aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_wind_dir_sin", "aws_temp_delta_60m", "aws_pressure_delta_60m", "aws_wind_speed_roll_180m_mean"] + SYN:
        x = pd.to_numeric(b[c], errors="coerce").to_numpy(float); x5 = pd.to_numeric(a[c], errors="coerce").to_numpy(float)
        r = dict(stasiun=s, kolom=c, V65_origin=round(float(np.isfinite(x5[org]).mean()), 4), V66_origin=round(float(np.isfinite(x[org]).mean()), 4), V66_semua_sesudah_mulai=round(float(np.isfinite(x[mulai + 6:]).mean()), 4))
        for lab, m in (("latih", yr <= 2023), ("uji", yr == 2025)): r[f"V66_origin_{lab}"] = round(float(np.isfinite(x[org & m]).mean()), 4)
        A.append(r)
TJ = pd.DataFrame(J); TJ.to_csv(os.path.join(HERE, "n3_lompatan.csv"), index=False); print("== lompatan (ambang audit: suhu 2, RH 10, tekanan 1, angin 5)"); print(TJ.pivot_table(index=["stasiun", "var"], columns="versi", values=["lompat", "maks"]).to_string())
TA = pd.DataFrame(A); TA.to_csv(os.path.join(HERE, "n3_ketersediaan.csv"), index=False); print("== ketersediaan"); print(TA.to_string(index=False))
kode = r'''
import sys, numpy as np; sys.path.insert(0, r"%s"); import _common
for s in _common.SITES:
    df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean"); d = df.iloc[te]
    print(s, len(feats), len(tr), len(va), len(te), round(float(np.nanmean(d.base_mean)), 3), "prediktor dengan kosong uji > 1%%:", {f: round(float(d[f].isna().mean()), 3) for f in feats if d[f].isna().mean() > 0.01})
''' % B
env = dict(os.environ, DATA_DIR=os.path.join(V6, "00_data"), CLEARSKY_DIR=os.path.join(V6, "clearsky"), CLP_EKSTRA_DIR=os.path.join(V6, "clp_ekstra"), FEATSET="P2F", PYTHONIOENCODING="utf-8")
o = subprocess.run([sys.executable, "-c", kode], capture_output=True, text=True, env=env, cwd=B); print(o.stdout); print(o.stderr[-500:] if o.returncode else "")
