# -*- coding: utf-8 -*-
"""Tahap 103 n1: audit V6.5 — (a) lompatan 10 menit per variabel meteorologi AWS (ambang suhu 2 °C, RH 10%, tekanan 1 hPa, angin 5 m/s),
(b) ketersediaan setiap kolom meteorologi (AWS dan SYNOP) di semua slot dan di origin elevasi > 5°, per split. Hanya membaca."""
import os, numpy as np, pandas as pd
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_5"
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
THR = dict(aws_temp_c=2.0, aws_rh_pct=10.0, aws_pressure_hpa=1.0, aws_wind_speed_ms=5.0)
KOL = ["aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_wind_dir_sin", "aws_wind_dir_cos", "aws_rain_mm", "aws_temp_delta_60m", "aws_rh_delta_60m",
       "aws_pressure_delta_60m", "aws_rain_sum_180m", "synop_visibility_km", "synop_cloud_cover_oktas", "synop_cl", "synop_cm", "synop_ch", "synop_present_weather_ww"]
A, J = [], []
for s in S:
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet")); t = pd.DatetimeIndex(d.ts_wib); el = d.solar_elev_deg.to_numpy(float); org = el > 5; yr = t.year.to_numpy()
    for c, thr in THR.items():
        x = d[c].to_numpy(float); dx = np.abs(np.diff(x, prepend=np.nan)); j = dx > thr
        J.append(dict(stasiun=s, var=c, lompat=int(j.sum()), lompat_origin=int((j & org).sum()), p999=round(float(np.nanpercentile(dx, 99.9)), 2), maks=round(float(np.nanmax(dx)), 2)))
    for c in KOL:
        x = pd.to_numeric(d[c], errors="coerce").to_numpy(float); r = dict(stasiun=s, kolom=c, isi_semua=round(float(np.isfinite(x).mean()), 3))
        for lab, m in (("latih", yr <= 2023), ("val", yr == 2024), ("uji", yr == 2025)): r[f"isi_origin_{lab}"] = round(float(np.isfinite(x[org & m]).mean()), 3)
        A.append(r)
TJ = pd.DataFrame(J); TJ.to_csv(os.path.join(HERE, "n1_lompatan_v65.csv"), index=False); print("== lompatan V6.5"); print(TJ.to_string(index=False))
TA = pd.DataFrame(A); TA.to_csv(os.path.join(HERE, "n1_ketersediaan_v65.csv"), index=False); print("== ketersediaan (fraksi terisi)"); print(TA.to_string(index=False))
