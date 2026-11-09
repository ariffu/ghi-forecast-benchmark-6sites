# -*- coding: utf-8 -*-
"""Tahap 96 validasi V6.2 terhadap V6.1 (DESAIN_96.md §Validasi)."""
import os, sys, subprocess, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE)
V1 = r"C:\Users\ariff\Documents\Balai_data_v6_1"; V2 = r"C:\Users\ariff\Documents\Balai_data_v6_2"; S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
BOLEH = {"aws_pressure_hpa", "aws_pressure_lag_60m", "aws_pressure_delta_60m"}; R = []
for s in S:
    r = dict(stasiun=s)
    for var in ("00_data", "00_data_rawfill"):
        a = pd.read_parquet(os.path.join(V1, var, f"{s}_full.parquet")); b = pd.read_parquet(os.path.join(V2, var, f"{s}_full.parquet"))
        assert list(a.columns) == list(b.columns) and (a.dtypes == b.dtypes).all()
        beda = sorted(c for c in a.columns if not a[c].equals(b[c])); assert set(beda) <= BOLEH, (s, var, beda)
        p1, p2 = a.aws_pressure_hpa.to_numpy(float), b.aws_pressure_hpa.to_numpy(float); w = np.isfinite(p2)
        assert np.array_equal(p1[w], p2[w])                                              # tekanan yang tersisa tidak berubah
        r[f"{var}_kolom_beda"] = ",".join(beda); r[f"{var}_tekanan_dibuang"] = int((np.isfinite(p1) & ~w).sum())
    el = a.solar_elev_deg.to_numpy(float); r["dibuang_%_siang"] = round(100 * float(((np.isfinite(p1) & ~w) & (el > 0)).sum() / max((np.isfinite(p1) & (el > 0)).sum(), 1)), 2)
    pa, pb = pd.read_parquet(os.path.join(V1, "provenance", f"{s}_provenance.parquet")), pd.read_parquet(os.path.join(V2, "provenance", f"{s}_provenance.parquet"))
    assert all(pa[c].equals(pb[c]) for c in pa.columns) and list(pb.columns) == list(pa.columns) + ["aws_lonjakan_tekanan"]
    assert int(pb.aws_lonjakan_tekanan.sum()) == r["00_data_tekanan_dibuang"]
    ca, cb = pd.read_parquet(os.path.join(V1, "clearsky", f"{s}_ineichen.parquet")), pd.read_parquet(os.path.join(V2, "clearsky", f"{s}_ineichen.parquet"))
    r["clearsky_sama"] = bool(ca.equals(cb)); assert r["clearsky_sama"] == (s != "bengkulu")
    qa, qb = pd.read_parquet(os.path.join(V1, "qc", f"{s}_qc.parquet")), pd.read_parquet(os.path.join(V2, "qc", f"{s}_qc.parquet"))
    r["qc_slot_beda_selain_bit8"] = int(((qa[["qc_ghi", "qc_dhi", "qc_dni", "qc_refl"]].to_numpy() != qb[["qc_ghi", "qc_dhi", "qc_dni", "qc_refl"]].to_numpy()).any(axis=1) | ((qb.qc_uji.to_numpy() & 0xFF) != qa.qc_uji.to_numpy())).sum())
    r["qc_uji_dtype"] = str(qb.qc_uji.dtype); r["bit8"] = int(((qb.qc_uji.to_numpy() >> 8) & 1).sum())
    e = pd.read_parquet(os.path.join(V2, "clp_ekstra", f"{s}_clp_ekstra.parquet")); assert (e.ts_wib.values == b.ts_wib.values).all()
    f = e.clp_cloud_frac.to_numpy(); r["frac_rentang"] = f"{np.nanmin(f):.3f}–{np.nanmax(f):.3f}"
    cot = b.clp_cot.to_numpy(float); m = np.isfinite(cot) & np.isfinite(f); r["frac_saat_cot_ada_min"] = round(float(f[m].min()), 3)
    r["frac_tanpa_cot_siang_median"] = round(float(np.nanmedian(f[~np.isfinite(cot) & (e.qc_clp_sza.to_numpy() == 0)])), 3)
    R.append(r); print(s, flush=True)
T = pd.DataFrame(R); T.to_csv(os.path.join(HERE, "f2_validasi.csv"), index=False); pd.set_option("display.width", 250); print(T.T.to_string())
# pipeline naskah dengan V6.2
kode = r'''
import sys, numpy as np; sys.path.insert(0, r"%s"); import _common
for s in _common.SITES:
    df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean"); d = df.iloc[te]
    print(s, _common.CS_DIR.split("\\")[-2], len(feats), len(tr), len(va), len(te), round(float(np.nanmean(d.base_mean)), 3))
''' % B
env = dict(os.environ, DATA_DIR=os.path.join(V2, "00_data"), CLEARSKY_DIR=os.path.join(V2, "clearsky"), PYTHONIOENCODING="utf-8")
out = subprocess.run([sys.executable, "-c", kode], capture_output=True, text=True, env=env, cwd=B); print(out.stdout); print(out.stderr[-600:] if out.returncode else "")
