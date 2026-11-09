# -*- coding: utf-8 -*-
"""Tahap 112 Y1: audit teknik dataset V6.10 (hanya membaca).
D1 skema dan tipe seragam (6 stasiun × 2 varian); D2 kunci waktu; D3 kolom kosong/konstan/duplikat; D4 rentang fisis per kolom;
D5 konsistensi turunan dan target; D6 beda 00_data lawan 00_data_rawfill; D7 integritas split dan salinan target di prediktor (P2F); D8 jejak versi."""
import os, sys, glob, json, numpy as np, pandas as pd
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 160)
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); V = r"C:\Users\ariff\Documents\Balai_data_v6_10"
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
BATAS = {"ghi_wm2": (0, 1500), "dhi_wm2": (0, 1000), "dni_wm2": (0, 1200), "reflected_wm2": (0, 500), "nett_wm2": (-200, 1500), "aws_ghi_wm2": (0, 1500), "aws_temp_c": (10, 42), "aws_rh_pct": (0, 100),
         "aws_pressure_hpa": (900, 1030), "aws_wind_speed_ms": (0, 40), "aws_wind_dir_deg": (0, 360), "aws_wind_dir_sin": (-1, 1), "aws_wind_dir_cos": (-1, 1), "aws_rain_mm": (0, 60), "clp_cot": (0, 150),
         "clp_cth_km": (0, 20), "clp_ctt_k": (180, 315), "clp_cer_um": (0, 100), "clp_cloud_present_int": (0, 1), "solar_elev_deg": (-90, 90), "decl_noaa_deg": (-23.5, 23.5), "eot_min": (-17, 17),
         "synop_temp_c": (10, 42), "synop_rh_pct": (0, 100), "synop_pressure_hpa": (900, 1030), "synop_visibility_km": (0, 80), "synop_cloud_cover_oktas": (0, 9), "synop_cl": (0, 9), "synop_cm": (0, 9),
         "synop_ch": (0, 9), "synop_present_weather_ww": (0, 99), "aod_500nm": (0, 6), "angstrom_exp": (-1, 3), "sunshine_slot_min": (0, 10)}
O = {k: [] for k in ("D1", "D2", "D3", "D4", "D5", "D6", "D7")}; skema = {}
for s in S:
    dd = {v: pd.read_parquet(os.path.join(V, v, f"{s}_full.parquet")) for v in ("00_data", "00_data_rawfill")}; d = dd["00_data"]
    for v, x in dd.items(): skema[(s, v)] = [(c, str(t)) for c, t in x.dtypes.items()]
    t = d.ts_wib; dif = t.diff().dropna().unique()
    O["D2"].append(dict(stasiun=s, baris=len(d), unik=bool(t.is_unique), urut=bool(t.is_monotonic_increasing), langkah=str(sorted(set(pd.to_timedelta(dif))))[:40], tz=str(getattr(t.dt, "tz", None)),
                        awal=str(t.min()), akhir=str(t.max()), site_id=",".join(map(str, d.site_id.unique()))))
    num = d.select_dtypes(include=[np.number, "bool"]).columns
    kosong = [c for c in d.columns if d[c].isna().all()]; konst = [c for c in num if d[c].nunique(dropna=True) <= 1 and not d[c].isna().all()]
    sig = {}; dup = []
    for c in num:
        k = pd.util.hash_pandas_object(d[c].astype("float64"), index=False).sum()
        if k in sig and np.array_equal(d[c].to_numpy(float), d[sig[k]].to_numpy(float), equal_nan=True): dup.append(f"{c}={sig[k]}")
        else: sig[k] = c
    O["D3"].append(dict(stasiun=s, kolom_kosong=",".join(kosong), kolom_konstan=",".join(konst), kolom_duplikat=",".join(dup)))
    for c, (lo, hi) in BATAS.items():
        if c not in d: continue
        x = pd.to_numeric(d[c], errors="coerce"); n_out = int(((x < lo - 1e-6) | (x > hi + 1e-6)).sum())
        if n_out: O["D4"].append(dict(stasiun=s, kolom=c, di_luar=n_out, min=float(x.min()), maks=float(x.max())))
    G = d.ghi_wm2; K = pd.to_numeric(d.kt)
    cek = {"ghi_actual_h1 = GHI(t+60)": (d.ghi_actual_h1, G.shift(-6)), "ghi_actual_h6 = GHI(t+360)": (d.ghi_actual_h6, G.shift(-36)), "ghi_lag_10m = GHI(t−10)": (d.ghi_lag_10m, G.shift(1)),
           "ghi_delta_60m": (d.ghi_delta_60m, G - G.shift(6)), "kt_lag_60m": (d.kt_lag_60m, K.shift(6)), "kt_delta_10m": (d.kt_delta_10m, K - K.shift(1)), "kt_roll_60m_mean": (d.kt_roll_60m_mean, K.rolling(6, min_periods=1).mean()),
           "clear_sky_ghi_h1 = cs(t+60)": (d.clear_sky_ghi_h1, d.clear_sky_ghi.shift(-6)), "clp_cot_lag_60m": (d.clp_cot_lag_60m, d.clp_cot.shift(6)), "clp_cot_delta_60m": (d.clp_cot_delta_60m, d.clp_cot - d.clp_cot.shift(6)),
           "clp_cot_roll_180m_mean": (d.clp_cot_roll_180m_mean, d.clp_cot.rolling(18, min_periods=1).mean()), "clp_cth_lag_60m": (d.clp_cth_lag_60m, d.clp_cth_km.shift(6)),
           "aws_rain_sum_180m": (d.aws_rain_sum_180m, d.aws_rain_mm.rolling(18, min_periods=1).sum()), "aws_temp_delta_60m": (d.aws_temp_delta_60m, d.aws_temp_c - d.aws_temp_c.shift(6)),
           "clp_cloud_present_int = COT≥1": (d.clp_cloud_present_int, (d.clp_cot >= 1).astype(float).where(d.clp_cot.notna()))}
    for nm, (a, b) in cek.items():
        a, b = pd.to_numeric(a).to_numpy(float), pd.to_numeric(b).to_numpy(float); m = np.isfinite(a) & np.isfinite(b)
        O["D5"].append(dict(stasiun=s, cek=nm, sama_pct=round(100 * float(np.isclose(a[m], b[m], atol=1e-4).mean()), 3) if m.any() else np.nan, nan_beda=int((np.isfinite(a) != np.isfinite(b)).sum())))
    r = dd["00_data_rawfill"]; beda = [c for c in d.columns if not d[c].equals(r[c])]
    O["D6"].append(dict(stasiun=s, kolom_beda=",".join(beda), n=len(beda)))
    print(s, "selesai", flush=True)
ref = skema[("banten", "00_data")]; O["D1"] = [dict(stasiun=k[0], varian=k[1], n_kolom=len(v), sama_dengan_banten=v == ref) for k, v in skema.items()]
# D7 split dan salinan target (lewat pipeline P2F)
kode = r'''
import sys, json, numpy as np, pandas as pd; sys.path.insert(0, r"%s"); import _common
out = []
for s in _common.SITES:
    df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean"); t = df.ts_wib
    tgt_end = t.iloc[tr] + pd.Timedelta(minutes=60)
    r = dict(stasiun=s, n_feat=len(feats), latih=len(tr), val=len(va), uji=len(te), tumpang=int(len(set(tr) & set(va)) + len(set(va) & set(te)) + len(set(tr) & set(te))),
             latih_maks=str(t.iloc[tr].max()), val_min=str(t.iloc[va].min()), val_maks=str(t.iloc[va].max()), uji_min=str(t.iloc[te].min()), target_latih_lewat_2023=int((tgt_end.dt.year > 2023).sum()))
    y = df.y_mean.to_numpy(); ya = df.ghi_actual_h1.to_numpy(); sal = []
    for f in feats:
        x = pd.to_numeric(df[f], errors="coerce").to_numpy(float); m = np.isfinite(x) & np.isfinite(y)
        if m.sum() > 1000 and (np.isclose(x[m], y[m], atol=1e-3).mean() > 0.5 or np.isclose(x[m], ya[m], atol=1e-3).mean() > 0.5): sal.append(f)
        c = np.corrcoef(x[m], y[m])[0, 1] if m.sum() > 1000 and np.nanstd(x[m]) > 0 else 0
        if abs(c) > 0.995: sal.append(f + "(r>0.995)")
    r["prediktor_salinan_target"] = ",".join(sal); out.append(r)
print(json.dumps(out))
''' % B
import subprocess
env = dict(os.environ, DATA_DIR=os.path.join(V, "00_data"), CLEARSKY_DIR=os.path.join(V, "clearsky"), CLP_EKSTRA_DIR=os.path.join(V, "clp_ekstra"), FEATSET="P2F", PYTHONIOENCODING="utf-8")
o = subprocess.run([sys.executable, "-c", kode], capture_output=True, text=True, env=env, cwd=B); O["D7"] = json.loads(o.stdout.strip().splitlines()[-1]) if o.returncode == 0 else [dict(galat=o.stderr[-300:])]
for k, L in O.items():
    T = pd.DataFrame(L); T.to_csv(os.path.join(HERE, f"{k}.csv"), index=False); print("==", k); print(T.to_string(index=False) if len(T) else "  (tidak ada)")
# D8 jejak versi
R8 = []
for p in sorted(glob.glob(r"C:\Users\ariff\Documents\Balai_data_v6*")):
    fs = [f for f in glob.glob(os.path.join(p, "**", "*"), recursive=True) if os.path.isfile(f)]
    R8.append(dict(versi=os.path.basename(p), berkas=len(fs), sha256=os.path.exists(os.path.join(p, "SHA256.txt")), readme=os.path.exists(os.path.join(p, "README.md")), hanya_baca=all(not os.access(f, os.W_OK) for f in fs)))
T8 = pd.DataFrame(R8); T8.to_csv(os.path.join(HERE, "D8.csv"), index=False); print("== D8"); print(T8.to_string(index=False))
