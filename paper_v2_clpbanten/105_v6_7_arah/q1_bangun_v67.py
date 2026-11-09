# -*- coding: utf-8 -*-
"""Tahap 105: bangun Balai_data_v6_7 dari Balai_data_v6_6 (hanya dibaca) — arah angin saat tenang/tidak diketahui -> sin = cos = 0 (DESAIN_105.md)."""
import os, sys, json, shutil, subprocess, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); V6 = r"C:\Users\ariff\Documents\Balai_data_v6_6"; V7 = r"C:\Users\ariff\Documents\Balai_data_v6_7"
assert not os.path.exists(os.path.join(V7, "SHA256.txt")), "V6.7 sudah beku"
if os.path.exists(V7): shutil.rmtree(V7)
shutil.copytree(V6, V7, copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("SHA256.txt", "README.md"))
UB = {"aws_wind_dir_deg", "aws_wind_dir_sin", "aws_wind_dir_cos"}; LAP = {}
for s in ("banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"):
    p = pd.read_parquet(os.path.join(V7, "provenance", f"{s}_provenance.parquet")); mode = p.mulus_mode_arah.to_numpy()
    tahan = pd.Series(mode == 2); g = (tahan != tahan.shift()).cumsum(); lama = tahan.groupby(g).cumcount().to_numpy() + 1; lama[~tahan.to_numpy()] = 0   # slot sejak mulai ditahan (kausal)
    for var in ("00_data", "00_data_rawfill"):
        f = os.path.join(V7, var, f"{s}_full.parquet"); d = pd.read_parquet(f); dt = d.dtypes; old = d.copy()
        W = d.aws_wind_speed_ms.to_numpy(float); D = d.aws_wind_dir_deg.to_numpy(float)
        kode = np.zeros(len(d), np.int8); kode[lama > 6] = 3; kode[D == 0] = 2; kode[W < 0.5] = 1
        tanpa = kode > 0; ada = np.isfinite(D) & ~tanpa
        d["aws_wind_dir_deg"] = np.where(ada, D, np.nan)
        d["aws_wind_dir_sin"] = np.where(ada, np.sin(np.radians(D)), np.where(np.isfinite(D) | tanpa, 0.0, np.nan))
        d["aws_wind_dir_cos"] = np.where(ada, np.cos(np.radians(D)), np.where(np.isfinite(D) | tanpa, 0.0, np.nan))
        if not np.isfinite(old.aws_wind_dir_deg.to_numpy(float)).any() and not np.isfinite(D).any(): d["aws_wind_dir_sin"], d["aws_wind_dir_cos"] = old.aws_wind_dir_sin, old.aws_wind_dir_cos
        for c in d.columns:
            if str(dt[c]) != str(d[c].dtype): d[c] = d[c].astype(dt[c])
        beda = {c for c in d.columns if not d[c].equals(old[c])}; assert beda <= UB, beda - UB
        ss = d.aws_wind_dir_sin ** 2 + d.aws_wind_dir_cos ** 2; assert ss.dropna().round(9).isin([0.0, 1.0]).all(); assert not (d.aws_wind_dir_deg == 0).any()
        d.to_parquet(f, index=False)
        if var == "00_data":
            org = (d.solar_elev_deg > 5).to_numpy()
            LAP[s] = dict(origin_tanpa_arah_pct=round(100 * float(tanpa[org].mean()), 2), calm=round(100 * float((kode[org] == 1).mean()), 2), kode0=round(100 * float((kode[org] == 2).mean()), 2),
                          tahan_gt60=round(100 * float((kode[org] == 3).mean()), 2), sincos_isi=round(float(d.aws_wind_dir_sin.notna().mean()), 4), K = None)
            K = kode
    p["arah_tanpa_arah"] = K; p.to_parquet(os.path.join(V7, "provenance", f"{s}_provenance.parquet"), index=False); LAP[s].pop("K"); print(s, LAP[s], flush=True)
json.dump(LAP, open(os.path.join(HERE, "q1_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
kode_ = r'''
import sys, numpy as np; sys.path.insert(0, r"%s"); import _common
for s in _common.SITES:
    df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean"); d = df.iloc[te]
    print(s, len(feats), len(te), round(float(np.nanmean(d.base_mean)), 3), "sin kosong uji", round(float(d.aws_wind_dir_sin.isna().mean()), 4))
''' % B
env = dict(os.environ, DATA_DIR=os.path.join(V7, "00_data"), CLEARSKY_DIR=os.path.join(V7, "clearsky"), CLP_EKSTRA_DIR=os.path.join(V7, "clp_ekstra"), FEATSET="P2F", PYTHONIOENCODING="utf-8")
o = subprocess.run([sys.executable, "-c", kode_], capture_output=True, text=True, env=env, cwd=B); print(o.stdout); print(o.stderr[-400:] if o.returncode else "")
