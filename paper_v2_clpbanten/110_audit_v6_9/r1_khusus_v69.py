# -*- coding: utf-8 -*-
"""Tahap 104 uji khusus V6.6 (hanya membaca):
O1 konsistensi turunan (lag/delta/rolling/sin-cos dihitung ulang persis dari kolom dasar);
O2 komposisi mode penaksir per split pada origin (logger / koreksi SYNOP / rambat) dan lama rambat tanpa pengamatan;
O3 realisme rambat: deret rambat ≥ 3 jam dibanding logger sehat stasiun lain pada jam yang sama (variabilitas, siklus harian);
O4 siklus harian suhu/RH dan pasang S2 V6.6 lawan V6.3 (logger asli);
O5 kolom SYNOP as-of: nilai di :10–:50 sama persis dengan laporan jam itu, umur ≤ 50 menit, kode dalam rentang."""
import os, numpy as np, pandas as pd
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 50); pd.set_option("display.max_rows", 300)
HERE = os.path.dirname(os.path.abspath(__file__)); V3 = r"C:\Users\ariff\Documents\Balai_data_v6_3"; V6 = r"C:\Users\ariff\Documents\Balai_data_v6_9"
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; LON = dict(banten=106.7509, bengkulu=102.311998, jambi=103.4944, jogja=110.353578, kalbar=109.1905, semarang=110.3812)
SYN = ["synop_visibility_km", "synop_cloud_cover_oktas", "synop_cl", "synop_cm", "synop_ch", "synop_present_weather_ww"]
O = {k: [] for k in ("O1", "O2", "O3", "O4", "O5")}
for s in S:
    d = pd.read_parquet(os.path.join(V6, "00_data", f"{s}_full.parquet")); p = pd.read_parquet(os.path.join(V6, "provenance", f"{s}_provenance.parquet")); d3 = pd.read_parquet(os.path.join(V3, "00_data", f"{s}_full.parquet"))
    t = pd.DatetimeIndex(d.ts_wib); el = d.solar_elev_deg.to_numpy(float); org = el > 5; yr = t.year.to_numpy()
    T, H, P, W, D = (pd.to_numeric(d[c]) for c in ("aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_wind_dir_deg"))
    cek = {"aws_temp_lag_60m": T.shift(6), "aws_temp_delta_60m": T - T.shift(6), "aws_temp_roll_180m_mean": T.rolling(18, min_periods=1).mean(), "aws_rh_delta_60m": H - H.shift(6),
           "aws_pressure_delta_60m": P - P.shift(6), "aws_wind_speed_roll_180m_mean": W.rolling(18, min_periods=1).mean(), "aws_wind_dir_sin": np.sin(np.radians(D)), "aws_wind_dir_cos": np.cos(np.radians(D))}
    for c, v in cek.items():
        a, b = d[c].to_numpy(float), np.asarray(v, float); O["O1"].append(dict(stasiun=s, kolom=c, maks_selisih=float(np.nanmax(np.abs(a - b))) if np.isfinite(a - b).any() else 0.0, nan_beda=int((np.isnan(a) != np.isnan(b)).sum())))
    for v in ("suhu", "rh", "tekanan", "angin"):
        m = p[f"mulus_mode_{v}"].to_numpy()
        for lab, ms in (("latih", yr <= 2023), ("val", yr == 2024), ("uji", yr == 2025)):
            mm = org & ms; O["O2"].append(dict(stasiun=s, var=v, split=lab, logger=round(float((m[mm] == 0).mean()), 3), synop=round(float((m[mm] == 1).mean()), 3), rambat=round(float((m[mm] == 2).mean()), 3)))
        r = pd.Series(m == 2); g = (r != r.shift()).cumsum(); ln = r.groupby(g).transform("size").to_numpy() * r.to_numpy()
        O2b = dict(stasiun=s, var=v, rambat_runtun_maks_jam=round(float(ln.max()) / 6, 1), rambat_ge3jam_pct=round(100 * float((ln >= 18).mean()), 2), origin_rambat_ge3jam_pct=round(100 * float((ln[org] >= 18).mean()), 2))
        O["O3"].append(O2b | dict(sd_dif10_rambat=round(float(np.nanstd(np.diff(d[{"suhu": "aws_temp_c", "rh": "aws_rh_pct", "tekanan": "aws_pressure_hpa", "angin": "aws_wind_speed_ms"}[v]].to_numpy(float), prepend=np.nan)[ln >= 18])), 3) if (ln >= 18).any() else np.nan,
                                  sd_dif10_logger=round(float(np.nanstd(np.diff(d[{"suhu": "aws_temp_c", "rh": "aws_rh_pct", "tekanan": "aws_pressure_hpa", "angin": "aws_wind_speed_ms"}[v]].to_numpy(float), prepend=np.nan)[m == 0])), 3) if (m == 0).any() else np.nan))
    r4 = dict(stasiun=s)
    for lab, dd in (("V6.3", d3), ("V6.6", d)):
        for c, nm in (("aws_temp_c", "suhu"), ("aws_rh_pct", "rh")):
            prof = pd.to_numeric(dd[c]).groupby(t.hour * 60 + t.minute).mean(); r4[f"{nm}_puncak_{lab}"] = f"{int(prof.idxmax()) // 60:02d}:{int(prof.idxmax()) % 60:02d}"; r4[f"{nm}_lembah_{lab}"] = f"{int(prof.idxmin()) // 60:02d}:{int(prof.idxmin()) % 60:02d}"; r4[f"{nm}_amp_{lab}"] = round(float(prof.max() - prof.min()), 2)
        pp = pd.to_numeric(dd.aws_pressure_hpa); pa = pp - pp.rolling(144, center=True, min_periods=60).mean(); w = pa.notna().to_numpy(); lst = ((t.hour * 60 + t.minute + (LON[s] - 105) * 4) % 1440).to_numpy()
        ang = 2 * np.pi * 2 * lst[w] / 1440; co = np.linalg.lstsq(np.c_[np.cos(ang), np.sin(ang), np.ones(w.sum())], pa.to_numpy()[w], rcond=None)[0]; r4[f"S2_amp_{lab}"] = round(float(np.hypot(*co[:2])), 2)
    O["O4"].append(r4)
    rep = d3[["synop_temp_c", "synop_pressure_hpa", "synop_visibility_km", "synop_present_weather_ww"]].notna().any(axis=1).to_numpy(); umur = p.synop_asof_umur_mnt.to_numpy(float)
    g = np.cumsum(rep)
    for c in SYN:
        x6 = d[c].to_numpy(float); x3 = d3[c].to_numpy(float); src = pd.Series(np.where(rep, x3, np.nan)).groupby(g).transform("first").to_numpy()
        m = np.isfinite(x6); O["O5"].append(dict(stasiun=s, kolom=c, terisi=int(m.sum()), sama_laporan=bool(np.allclose(x6[m], src[m], equal_nan=False)), umur_maks=float(np.nanmax(umur[m])) if m.any() else np.nan,
                                                  laporan_asli_berubah=int((rep & (np.nan_to_num(x6, nan=-9) != np.nan_to_num(x3, nan=-9))).sum()), nilai_min=float(np.nanmin(x6)) if m.any() else np.nan, nilai_maks=float(np.nanmax(x6)) if m.any() else np.nan))
    print(s, "selesai", flush=True)
for k, L in O.items():
    T_ = pd.DataFrame(L); T_.to_csv(os.path.join(HERE, f"{k}.csv"), index=False); print("==", k); print(T_.to_string(index=False))
