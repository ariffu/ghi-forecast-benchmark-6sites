# -*- coding: utf-8 -*-
"""Tahap 97 cek: bawaan (V5, P2) tetap 43; V6.2 + P2F = 44 dengan clp_cloud_frac; rawfill memakai fraksi raw; grup ablasi CLP memuat fraksi."""
import os, sys, subprocess
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); V2 = r"C:\Users\ariff\Documents\Balai_data_v6_2"
kode = r'''
import sys, os, numpy as np; sys.path.insert(0, r"%s"); import _common
src = open(os.path.join(r"%s", "27_block_bootstrap.py"), encoding="utf-8").read(); exec(src[src.index("def groups(feats):"):src.index("def setup(")])
for s in (_common.SITES if os.environ.get("SEMUA") else ["jambi"]):
    df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean"); d = df.iloc[te]
    G = groups(feats); clp = [f for g in G if isinstance(g, list) for f in g if f.startswith("clp_")]
    fr = df["clp_cloud_frac"].to_numpy(float) if "clp_cloud_frac" in df else None
    print(s, _common.FEATSET, len(feats), "frac_di_feats:", "clp_cloud_frac" in feats, "frac_di_grup_CLP:", "clp_cloud_frac" in G[1],
          "isi_frac_latih/uji:", None if fr is None else (round(float(np.isfinite(fr[tr]).mean()), 3), round(float(np.isfinite(fr[te]).mean()), 3)),
          "frac_min:", None if fr is None else round(float(np.nanmin(fr)), 3), "base_mean_uji:", round(float(np.nanmean(d.base_mean)), 3))
''' % (B, B)
for lab, env in (("bawaan V5", {}),
                 ("V6.2 P2", {"DATA_DIR": os.path.join(V2, "00_data"), "CLEARSKY_DIR": os.path.join(V2, "clearsky")}),
                 ("V6.2 P2F", {"DATA_DIR": os.path.join(V2, "00_data"), "CLEARSKY_DIR": os.path.join(V2, "clearsky"), "FEATSET": "P2F", "CLP_EKSTRA_DIR": os.path.join(V2, "clp_ekstra"), "SEMUA": "1"}),
                 ("V6.2 rawfill P2F", {"DATA_DIR": os.path.join(V2, "00_data_rawfill"), "CLEARSKY_DIR": os.path.join(V2, "clearsky"), "FEATSET": "P2F", "CLP_EKSTRA_DIR": os.path.join(V2, "clp_ekstra")})):
    e = dict(os.environ); [e.pop(k, None) for k in ("DATA_DIR", "CLEARSKY_DIR", "FEATSET", "CLP_EKSTRA_DIR", "SEMUA")]; e.update(env); e["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, "-c", kode], capture_output=True, text=True, env=e, cwd=B); print("==", lab); print(r.stdout.strip()); print(r.stderr.strip()[-500:] if r.returncode else "")
