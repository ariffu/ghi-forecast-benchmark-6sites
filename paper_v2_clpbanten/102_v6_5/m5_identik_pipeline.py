# -*- coding: utf-8 -*-
"""Tahap 102: V6.5 lawan V6.3 — folder non-meteorologi identik (hash), kolom non-MET identik, provenance V6.3 utuh; pipeline P2F enam stasiun."""
import os, sys, subprocess, hashlib, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); V3 = r"C:\Users\ariff\Documents\Balai_data_v6_3"; V5 = r"C:\Users\ariff\Documents\Balai_data_v6_5"
sys.path.insert(0, os.path.join(B, "100_meteo_synop")); from j2_bangun_v64 import MET
h = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
for sub in ("clearsky", "qc", "clp_ekstra"):
    for f in sorted(os.listdir(os.path.join(V3, sub))): assert h(os.path.join(V3, sub, f)) == h(os.path.join(V5, sub, f)), (sub, f)
print("clearsky, qc, clp_ekstra identik dengan V6.3")
for s in ("banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"):
    for var in ("00_data", "00_data_rawfill"):
        a = pd.read_parquet(os.path.join(V3, var, f"{s}_full.parquet")); b = pd.read_parquet(os.path.join(V5, var, f"{s}_full.parquet"))
        assert list(a.columns) == list(b.columns) and (a.dtypes == b.dtypes).all(); beda = [c for c in a.columns if not a[c].equals(b[c])]; assert set(beda) <= set(MET), set(beda) - set(MET)
    pa, pb = pd.read_parquet(os.path.join(V3, "provenance", f"{s}_provenance.parquet")), pd.read_parquet(os.path.join(V5, "provenance", f"{s}_provenance.parquet"))
    assert all(pa[c].equals(pb[c]) for c in pa.columns); print(s, "kolom MET berubah:", len(beda), "| provenance baru:", len(pb.columns) - len(pa.columns))
kode = r'''
import sys, numpy as np; sys.path.insert(0, r"%s"); import _common
for s in _common.SITES:
    df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean"); d = df.iloc[te]
    print(s, len(feats), len(tr), len(va), len(te), round(float(np.nanmean(d.base_mean)), 3), "kosong uji suhu/rh/tekanan/angin:", [round(float(d[c].isna().mean()), 3) for c in ("aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms")])
''' % B
env = dict(os.environ, DATA_DIR=os.path.join(V5, "00_data"), CLEARSKY_DIR=os.path.join(V5, "clearsky"), CLP_EKSTRA_DIR=os.path.join(V5, "clp_ekstra"), FEATSET="P2F", PYTHONIOENCODING="utf-8")
o = subprocess.run([sys.executable, "-c", kode], capture_output=True, text=True, env=env, cwd=B); print(o.stdout); print(o.stderr[-500:] if o.returncode else "")
