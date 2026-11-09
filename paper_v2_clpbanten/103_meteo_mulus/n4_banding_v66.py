# -*- coding: utf-8 -*-
"""Tahap 100 j1: AWS lawan SYNOP per stasiun × bulan pada jam laporan (V6.3, hanya membaca).
Angin disamakan satuannya: SYNOP knot × 0,514444 → m/s. Tekanan: selisih AWS − SYNOP dibanding harapan hipsometrik (QFF − tekanan sensor)."""
import os, numpy as np, pandas as pd
pd.set_option("display.width", 280); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_6"
ALT = dict(banten=27, bengkulu=9, jambi=24, jogja=182, kalbar=2, semarang=6); R = []; K = []
for s, h in ALT.items():
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_wind_dir_deg",
                                                                              "synop_temp_c", "synop_rh_pct", "synop_pressure_hpa", "synop_wind_speed_kt", "synop_wind_dir_deg", "synop_dewpoint_c"])
    pv = pd.read_parquet(os.path.join(V, "provenance", f"{s}_provenance.parquet")); t = pd.DatetimeIndex(d.ts_wib)
    S = d.synop_temp_c.notna() | d.synop_pressure_hpa.notna(); x = d[S.to_numpy()].copy(); tt = t[S.to_numpy()]
    for c in ("synop_wind_speed_kt", "synop_wind_dir_deg", "synop_pressure_hpa", "synop_temp_c", "synop_rh_pct"):
        x.loc[(x[c] > 2000) | (x[c] < -90), c] = np.nan     # kode hilang 9999
    x["sw"] = x.synop_wind_speed_kt * 0.514444; x["dp"] = x.aws_pressure_hpa - x.synop_pressure_hpa
    Tv = (x.synop_temp_c + 273.15).median(); harap = float(x.synop_pressure_hpa.median() * (1 - np.exp(-9.80665 * h / (287.05 * Tv))))
    lat = tt.year <= 2023
    K.append(dict(stasiun=s, ketinggian_m=h, AWS_minus_SYNOP_latih=round(float(x.dp[lat].median()), 2), harapan_jika_SYNOP_QFF=round(-harap, 2), harapan_jika_SYNOP_QFE=0.0,
                  aws_sama_synop_persis=round(float((x.dp.abs() < 0.05).mean()), 3), sumber_aws_kausal={c: int(pv[c].sum()) for c in pv.columns if c.startswith("aws_kausal")},
                  synop_kt_resolusi=str(sorted(x.synop_wind_speed_kt.dropna().unique())[:6]), aws_ms_nilai_terbanyak=str(x.aws_wind_speed_ms.round(2).value_counts().head(4).to_dict())))
    kal = dict(T=float((x.aws_temp_c - x.synop_temp_c)[lat].median()), RH=float((x.aws_rh_pct - x.synop_rh_pct)[lat].median()), P=float(x.dp[lat].median()))
    mw = lat & (x.sw > 1) & x.aws_wind_speed_ms.notna(); kal["Wr"] = float(x.aws_wind_speed_ms[mw].mean() / x.sw[mw].mean()) if mw.sum() > 100 else np.nan
    for mo, g in x.groupby(tt.to_period("M").astype(str)):
        w = g.sw.notna() & g.aws_wind_speed_ms.notna(); dd = (np.abs((g.aws_wind_dir_deg - g.synop_wind_dir_deg) + 180) % 360 - 180).abs()[(g.sw >= 2) & (g.aws_wind_speed_ms >= 0.5)]
        R.append(dict(stasiun=s, bulan=mo, n=len(g), T_dev=round(float((g.aws_temp_c - g.synop_temp_c).median() - kal["T"]), 2), RH_dev=round(float((g.aws_rh_pct - g.synop_rh_pct).median() - kal["RH"]), 2),
                      P_dev=round(float(g.dp.median() - kal["P"]), 2), P_jam_dev_gt1_pct=round(100 * float(((g.dp - kal["P"]).abs() > 1)[g.dp.notna()].mean()), 1) if g.dp.notna().any() else np.nan,
                      W_rasio_rel=round(float(g.aws_wind_speed_ms[w].mean() / g.sw[w].mean() / kal["Wr"]), 2) if w.sum() > 30 and g.sw[w].mean() > 0 else np.nan,
                      W_r=round(float(np.corrcoef(g.aws_wind_speed_ms[w], g.sw[w])[0, 1]), 2) if w.sum() > 30 and g.aws_wind_speed_ms[w].std() > 0 and g.sw[w].std() > 0 else np.nan,
                      W_aws0_synop_ge2_pct=round(100 * float(((g.aws_wind_speed_ms == 0) & (g.sw >= 2))[w].sum() / max(((g.sw >= 2) & w).sum(), 1)), 1),
                      D_med=round(float(dd.median()), 0) if len(dd) > 20 else np.nan, synop_isi=round(float(g.synop_wind_speed_kt.notna().mean()), 2), aws_angin_isi=round(float(g.aws_wind_speed_ms.notna().mean()), 2)))
T = pd.DataFrame(R); T.to_csv(os.path.join(HERE, "n4_bulanan_v66.csv"), index=False); Kt = pd.DataFrame(K); Kt.to_csv(os.path.join(HERE, "n4_konvensi_v66.csv"), index=False)
print(Kt.T.to_string())
f = T[(T.T_dev.abs() > 0.5) | (T.RH_dev.abs() > 3) | (T.P_dev.abs() > 0.5) | (T.P_jam_dev_gt1_pct > 10) | ((T.W_rasio_rel - 1).abs() > 0.3) | (T.W_r < 0.5) | (T.W_aws0_synop_ge2_pct > 5) | (T.D_med > 45)]
print("== bulan janggal:"); print(f.to_string(index=False))
