# -*- coding: utf-8 -*-
"""Tahap 111: bangun Balai_data_v6_10 dari Balai_data_v6_9 (hanya dibaca) — synop_cloud_cover_oktas Banten dan Bengkulu diganti tutupan awan total N
(cloud_cover_oktas_m) dari tabel SYNOP sumber (sebelumnya Nh = cloud_low_cover_oktas), lalu as-of 60 menit (aturan V6.6). Kolom lain tidak berubah."""
import os, sys, json, shutil, subprocess, duckdb, numpy as np, pandas as pd
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); V9 = r"C:\Users\ariff\Documents\Balai_data_v6_9"; V10 = r"C:\Users\ariff\Documents\Balai_data_v6_10"; V3 = r"C:\Users\ariff\Documents\Balai_data_v6_3"
DB = r"C:\Users\ariff\Documents\Balai Obsidian\Balai\solardata_new_v2\solar_harmonised_clpbanten_v2.duckdb"
sys.path.insert(0, os.path.join(B, "103_meteo_mulus")); from n2_bangun_v66 import asof
SRC = dict(banten=("banten.synoppondokbetung", "timestamp_wib"), bengkulu=("bengkulu.synop_bengkulu_quality_final", "ts_wib"))
assert not os.path.exists(os.path.join(V10, "SHA256.txt")), "V6.10 sudah beku"
if os.path.exists(V10): shutil.rmtree(V10)
shutil.copytree(V9, V10, copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("SHA256.txt", "README.md"))
c = duckdb.connect(DB, read_only=True); LAP = {}
for s, (tab, tc) in SRC.items():
    S = c.execute(f"select {tc} as t, cloud_cover_oktas_m as n, cloud_low_cover_oktas as nh from {tab}").df(); S["t"] = pd.to_datetime(S.t); S = S.drop_duplicates("t").set_index("t")
    d3 = pd.read_parquet(os.path.join(V3, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "synop_temp_c", "synop_pressure_hpa", "synop_visibility_km", "synop_present_weather_ww", "synop_cloud_cover_oktas"])
    t = pd.DatetimeIndex(d3.ts_wib); rep = d3[["synop_temp_c", "synop_pressure_hpa", "synop_visibility_km", "synop_present_weather_ww"]].notna().any(axis=1).to_numpy()
    N = pd.to_numeric(S.n, errors="coerce").reindex(t).to_numpy(float); N = np.where((N >= 0) & (N <= 9), N, np.nan); Nh = pd.to_numeric(S.nh, errors="coerce").reindex(t).to_numpy(float)
    lama = d3.synop_cloud_cover_oktas.to_numpy(float); m = np.isfinite(lama) & np.isfinite(Nh)
    cek_nh = float((lama[m] == Nh[m]).mean()); assert cek_nh > 0.99, (s, cek_nh)                 # memastikan kolom lama memang Nh
    lap = np.where(rep, N, np.nan); v, umur = asof(lap, rep, t.to_numpy(), 60)
    for var in ("00_data", "00_data_rawfill"):
        f = os.path.join(V10, var, f"{s}_full.parquet"); d = pd.read_parquet(f); dt = d.dtypes; old = d.copy(); d["synop_cloud_cover_oktas"] = v
        for col in d.columns:
            if str(dt[col]) != str(d[col].dtype): d[col] = d[col].astype(dt[col])
        beda = {col for col in d.columns if not d[col].equals(old[col])}; assert beda <= {"synop_cloud_cover_oktas"}, beda
        d.to_parquet(f, index=False)
    pv = os.path.join(V10, "provenance", f"{s}_provenance.parquet"); P_ = pd.read_parquet(pv); P_["synop_okta_N_sumber"] = rep & np.isfinite(N); P_.to_parquet(pv, index=False)
    d = pd.read_parquet(os.path.join(V10, "00_data", f"{s}_full.parquet")); cs = pd.read_parquet(os.path.join(V10, "clearsky", f"{s}_ineichen.parquet")).ghi_cs.to_numpy(); el = d.solar_elev_deg.to_numpy(float)
    with np.errstate(all="ignore"): kc = np.where((el > 20) & (cs > 50), d.ghi_wm2.to_numpy(float) / cs, np.nan)
    j = (t.minute == 0) & np.isfinite(v) & (v <= 8) & np.isfinite(kc); j_old = (t.minute == 0) & np.isfinite(lama) & (lama <= 8) & np.isfinite(kc)
    org = el > 5; yr = t.year.to_numpy()
    LAP[s] = dict(kolom_lama_sama_Nh=round(cek_nh, 4), laporan_N=int((rep & np.isfinite(N)).sum()), rata_lama_Nh=round(float(np.nanmean(np.where(lama <= 8, lama, np.nan))), 2), rata_baru_N=round(float(np.nanmean(np.where(v <= 8, v, np.nan))), 2),
                  okta8_pct_baru=round(100 * float((v[(t.minute == 0) & np.isfinite(v)] == 8).mean()), 1), rho_kc_lama=round(float(spearmanr(lama[j_old], kc[j_old]).correlation), 3), rho_kc_baru=round(float(spearmanr(v[j], kc[j]).correlation), 3),
                  origin_terisi_per_tahun={int(y): round(float(np.isfinite(v)[org & (yr == y)].mean()), 3) for y in range(2022, 2026)},
                  okta_per_jam_wib=pd.Series(np.where(v <= 8, v, np.nan)[t.minute == 0]).groupby(t[t.minute == 0].hour).mean().round(2).dropna().to_dict())
    print(s, json.dumps(LAP[s], ensure_ascii=False), flush=True)
for s in ("jambi", "jogja", "kalbar", "semarang"):
    pv = os.path.join(V10, "provenance", f"{s}_provenance.parquet"); P_ = pd.read_parquet(pv); P_["synop_okta_N_sumber"] = False; P_.to_parquet(pv, index=False)
json.dump(LAP, open(os.path.join(HERE, "x1_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
kode = r'''
import sys, numpy as np; sys.path.insert(0, r"%s"); import _common
for s in _common.SITES:
    df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean")
    print(s, len(feats), len(tr), round(float(np.nanmean(df.iloc[te].base_mean)), 3), "okta kosong latih/uji", round(float(df.iloc[tr].synop_cloud_cover_oktas.isna().mean()), 3), round(float(df.iloc[te].synop_cloud_cover_oktas.isna().mean()), 3))
''' % B
env = dict(os.environ, DATA_DIR=os.path.join(V10, "00_data"), CLEARSKY_DIR=os.path.join(V10, "clearsky"), CLP_EKSTRA_DIR=os.path.join(V10, "clp_ekstra"), FEATSET="P2F", PYTHONIOENCODING="utf-8")
o = subprocess.run([sys.executable, "-c", kode], capture_output=True, text=True, env=env, cwd=B); print(o.stdout); print(o.stderr[-400:] if o.returncode else "")
