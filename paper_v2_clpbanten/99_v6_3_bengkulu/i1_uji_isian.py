# -*- coding: utf-8 -*-
"""Tahap 99: uji akurasi isian kausal SYNOP (cara 2 tahap 92) untuk angin dan tekanan Bengkulu pada periode AWS sehat.
Isian slot t: x̂(t) = kal(S(t0)) + [x̄(bulan, t) − x̄(bulan, t0)]; t0 = laporan SYNOP terakhir ≤ t; kosong bila umur > 3 jam.
x̄ = klimatologi AWS 2022–2023 (tahun latih) per bulan × menit-hari; kal = regresi linear AWS ~ SYNOP 2022–2023 pada jam laporan.
Diuji pada Jan–Jun 2024 (angin sehat) dan Jan–Mar 2024 (tekanan sehat) terhadap logger AWS. Hanya membaca. Argumen: job_13401.csv."""
import os, sys, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); V2 = r"C:\Users\ariff\Documents\Balai_data_v6_2"; CSV = sys.argv[1]
d = pd.read_parquet(os.path.join(V2, "00_data", "bengkulu_full.parquet"), columns=["ts_wib", "aws_wind_speed_ms", "aws_pressure_hpa", "synop_wind_speed_kt", "synop_pressure_hpa"]).set_index("ts_wib")
t = d.index; md = t.hour * 60 + t.minute
F = pd.read_csv(CSV, usecols=["data_timestamp", "wind_indicator_iw", "wind_speed_ff", "pressure_qfe_mb_derived", "pressure_qff_mb_derived"]); F["t"] = pd.to_datetime(F.data_timestamp) + pd.Timedelta(hours=7); F = F.set_index("t")
F = F[(F.wind_speed_ff < 200) & F.pressure_qfe_mb_derived.between(950, 1050)]
c_qff_qfe = float((F.pressure_qff_mb_derived - F.pressure_qfe_mb_derived).median()); print("QFF − QFE (berkas) median", round(c_qff_qfe, 3), "IQR", np.round(np.percentile(F.pressure_qff_mb_derived - F.pressure_qfe_mb_derived, [25, 75]), 2))
# deret SYNOP per slot: 2022–2023 dari DB (QFF − c → QFE), 2024–2025 dari berkas pengguna
ws = d.synop_wind_speed_kt.where(d.synop_wind_speed_kt < 200) * 0.514444; ps = d.synop_pressure_hpa - c_qff_qfe
ws.loc[F.index.intersection(t)] = (F.wind_speed_ff * 0.514444).reindex(F.index.intersection(t)); ps.loc[F.index.intersection(t)] = F.pressure_qfe_mb_derived.reindex(F.index.intersection(t))
lat = t.year <= 2023
def kal(a, s):
    m = lat & np.isfinite(a) & np.isfinite(s); b, c = np.polyfit(s[m], a[m], 1); return float(b), float(c)
def clim(a):
    return pd.Series(a[lat]).groupby([t.month[lat], md[lat]]).mean()
def isi(s, cl, k):
    S = pd.Series(s, index=t); last = S.where(S.notna()).ffill(); t0 = pd.Series(np.where(S.notna(), t, pd.NaT), index=t).ffill()
    age = (t - pd.DatetimeIndex(t0)).total_seconds() / 60; md0 = pd.DatetimeIndex(t0).hour * 60 + pd.DatetimeIndex(t0).minute
    c_t = cl.reindex(list(zip(t.month, md))).to_numpy(); c_0 = cl.reindex(list(zip(t.month, md0.fillna(0).astype(int)))).to_numpy()
    out = k[0] * last.to_numpy() + k[1] + c_t - c_0; out[(age > 180) | ~np.isfinite(age)] = np.nan; return out, age.to_numpy()
LAP = dict(qff_minus_qfe=c_qff_qfe)
for var, a, s, uji in (("angin", d.aws_wind_speed_ms.to_numpy(float), ws.to_numpy(float), ("2024-01-01", "2024-07-01")), ("tekanan", d.aws_pressure_hpa.to_numpy(float), ps.to_numpy(float), ("2024-01-01", "2024-04-01"))):
    k = kal(a, s) if var == "angin" else (1.0, float(np.nanmedian((a - s)[lat & np.isfinite(a) & np.isfinite(s)])))
    x, age = isi(s, clim(a), k)
    if var == "angin": x = np.clip(x, 0, None)
    w = (t >= uji[0]) & (t < uji[1]) & np.isfinite(x) & np.isfinite(a); L = dict(kalibrasi=k, n=int(w.sum()))
    for lo, hi in ((0, 0), (10, 60), (70, 120), (130, 180)):
        m = w & (age >= lo) & (age <= hi); L[f"umur_{lo}-{hi}"] = dict(n=int(m.sum()), rmse=round(float(np.sqrt(np.mean((x[m] - a[m]) ** 2))), 3), bias=round(float(np.mean(x[m] - a[m])), 3), r=round(float(np.corrcoef(x[m], a[m])[0, 1]), 3))
    # pembanding: variabilitas alami logger (selisih 60 menit)
    L["acuan_|x(t)−x(t−60)|_rmse"] = round(float(np.sqrt(np.nanmean((a[w] - pd.Series(a).shift(6).to_numpy()[w]) ** 2))), 3); LAP[var] = L
    print(var, json.dumps(L, ensure_ascii=False))
json.dump(LAP, open(os.path.join(HERE, "i1_uji_isian.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
