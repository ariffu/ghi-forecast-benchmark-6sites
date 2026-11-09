# -*- coding: utf-8 -*-
"""Tahap 109: bangun Balai_data_v6_9 dari Balai_data_v6_8 (hanya dibaca) — okta (N), CM, CH SYNOP Yogyakarta diisi dari berkas pengguna
(synop staklim mlati 22-25.csv, diringkas v1_cek_okta.py ke v1_synop_awan_jogja.parquet), lalu as-of 60 menit (aturan V6.6). Kolom lain tidak berubah."""
import os, sys, json, shutil, subprocess, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); V8 = r"C:\Users\ariff\Documents\Balai_data_v6_8"; V9 = r"C:\Users\ariff\Documents\Balai_data_v6_9"; V3 = r"C:\Users\ariff\Documents\Balai_data_v6_3"
sys.path.insert(0, os.path.join(B, "103_meteo_mulus")); from n2_bangun_v66 import asof
assert not os.path.exists(os.path.join(V9, "SHA256.txt")), "V6.9 sudah beku"
if os.path.exists(V9): shutil.rmtree(V9)
shutil.copytree(V8, V9, copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("SHA256.txt", "README.md"))
F = pd.read_parquet(os.path.join(HERE, "v1_synop_awan_jogja.parquet"))
KOL = {"synop_cloud_cover_oktas": "cloud_cover_oktas_m", "synop_cm": "cloud_med_type_cm", "synop_ch": "cloud_high_type_ch"}
d3 = pd.read_parquet(os.path.join(V3, "00_data", "jogja_full.parquet"), columns=["ts_wib", "synop_temp_c", "synop_pressure_hpa", "synop_visibility_km", "synop_present_weather_ww"] + list(KOL))
t = pd.DatetimeIndex(d3.ts_wib); rep = (d3[["synop_temp_c", "synop_pressure_hpa", "synop_visibility_km", "synop_present_weather_ww"]].notna().any(axis=1).to_numpy()) | t.isin(F.index)
LAP = {}; OUT = {}
for c, fc in KOL.items():
    lama = d3[c].to_numpy(float); baru = F[fc].reindex(t).to_numpy(float); baru = np.where((baru >= 0) & (baru <= 9), baru, np.nan)
    both = np.isfinite(lama) & np.isfinite(baru); konflik = int((both & (lama != baru)).sum())
    lap = np.where(np.isfinite(lama), lama, baru)                     # nilai laporan: database bila ada (sama 99,9%), selain itu berkas
    v, umur = asof(lap, rep, t.to_numpy(), 60); OUT[c] = v
    LAP[c] = dict(laporan_db=int(np.isfinite(lama).sum()), laporan_berkas=int(np.isfinite(baru).sum()), konflik_db_berkas=konflik, laporan_baru_terisi=int((~np.isfinite(lama) & np.isfinite(baru)).sum()), slot_terisi_asof=int(np.isfinite(v).sum()))
for var in ("00_data", "00_data_rawfill"):
    f = os.path.join(V9, var, "jogja_full.parquet"); d = pd.read_parquet(f); dt = d.dtypes; old = d.copy()
    for c, v in OUT.items():
        o = old[c].to_numpy(float); assert np.array_equal(v[np.isfinite(o)], o[np.isfinite(o)]) or (np.abs(v[np.isfinite(o)] - o[np.isfinite(o)]) > 0).sum() <= LAP[c]["konflik_db_berkas"] * 6, c
        d[c] = v
    for col in d.columns:
        if str(dt[col]) != str(d[col].dtype): d[col] = d[col].astype(dt[col])
    beda = {col for col in d.columns if not d[col].equals(old[col])}; assert beda <= set(KOL), beda
    d.to_parquet(f, index=False)
pv = os.path.join(V9, "provenance", "jogja_provenance.parquet"); P_ = pd.read_parquet(pv); P_["synop_awan_dari_berkas"] = ~np.isfinite(d3.synop_cloud_cover_oktas.to_numpy(float)) & np.isfinite(F.cloud_cover_oktas_m.reindex(t).to_numpy(float)); P_.to_parquet(pv, index=False)
for s in ("banten", "bengkulu", "jambi", "kalbar", "semarang"):
    pv = os.path.join(V9, "provenance", f"{s}_provenance.parquet"); P_ = pd.read_parquet(pv); P_["synop_awan_dari_berkas"] = False; P_.to_parquet(pv, index=False)
d = pd.read_parquet(os.path.join(V9, "00_data", "jogja_full.parquet")); org = (d.solar_elev_deg > 5).to_numpy(); yr = t.year.to_numpy()
for c in KOL: LAP[c]["origin_terisi_per_tahun"] = {int(y): round(float(np.isfinite(d[c].to_numpy(float))[org & (yr == y)].mean()), 3) for y in range(2022, 2026)}
N = d.synop_cloud_cover_oktas.where(d.synop_cloud_cover_oktas <= 8); LAP["okta_rata_per_jam_wib"] = N[(t.minute == 0)].groupby(t[t.minute == 0].hour).mean().round(2).dropna().to_dict()
json.dump(LAP, open(os.path.join(HERE, "v2_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(LAP, ensure_ascii=False, indent=1))
kode = r'''
import sys, numpy as np; sys.path.insert(0, r"%s"); import _common
for s in _common.SITES:
    df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean"); d = df.iloc[tr]
    print(s, len(feats), len(tr), round(float(np.nanmean(df.iloc[te].base_mean)), 3), "kosong latih okta/CM/CH:", [round(float(d[c].isna().mean()), 3) for c in ("synop_cloud_cover_oktas", "synop_cm", "synop_ch")])
''' % B
env = dict(os.environ, DATA_DIR=os.path.join(V9, "00_data"), CLEARSKY_DIR=os.path.join(V9, "clearsky"), CLP_EKSTRA_DIR=os.path.join(V9, "clp_ekstra"), FEATSET="P2F", PYTHONIOENCODING="utf-8")
o = subprocess.run([sys.executable, "-c", kode], capture_output=True, text=True, env=env, cwd=B); print(o.stdout); print(o.stderr[-400:] if o.returncode else "")
