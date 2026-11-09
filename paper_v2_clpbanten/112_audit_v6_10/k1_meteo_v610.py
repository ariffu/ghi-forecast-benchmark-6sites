# -*- coding: utf-8 -*-
"""Tahap 112 (salinan untuk V6.10) uji khusus V6.6 (hanya membaca):
K1 lompatan 10 menit (V6.5 lawan V6.6), termasuk di batas minggu isian;
K2 konsistensi fisis meteorologi (titik embun, antikorelasi suhu–RH harian, tendensi tekanan 3 jam, angin maksimum);
K3 komposisi sumber per split (latih/validasi/uji) pada origin elevasi > 5°: logger terkoreksi, berasal SYNOP, kosong;
K4 variabilitas 10 menit: logger lawan segmen berasal SYNOP (risiko pergeseran sebaran)."""
import os, numpy as np, pandas as pd
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
HERE = os.path.dirname(os.path.abspath(__file__)); V3 = r"C:\Users\ariff\Documents\Balai_data_v6_9"; V4 = r"C:\Users\ariff\Documents\Balai_data_v6_10"
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
VAR = dict(suhu=("aws_temp_c", 2.0, ["aws_kausal_suhu"]), rh=("aws_rh_pct", 10.0, ["aws_kausal_rh"]), tekanan=("aws_pressure_hpa", 1.0, ["aws_kausal_tekanan", "aws_isi_synop_tekanan", "aws_isi_synop_tekanan_datar"]),
           angin=("aws_wind_speed_ms", 5.0, ["aws_kausal_angin", "aws_isi_synop_angin"]))
O = {k: [] for k in ("K1", "K2", "K3", "K4")}
for s in S:
    a = pd.read_parquet(os.path.join(V3, "00_data", f"{s}_full.parquet")); b = pd.read_parquet(os.path.join(V4, "00_data", f"{s}_full.parquet")); p = pd.read_parquet(os.path.join(V4, "provenance", f"{s}_provenance.parquet"))
    t = pd.DatetimeIndex(b.ts_wib); el = b.solar_elev_deg.to_numpy(float); yr = t.year.to_numpy(); org = el > 5
    for v, (c, thr, kf) in VAR.items():
        x3, x4 = a[c].to_numpy(float), b[c].to_numpy(float); d3, d4 = np.abs(np.diff(x3, prepend=np.nan)), np.abs(np.diff(x4, prepend=np.nan))
        isi = p[f"met_isi_{v}"].to_numpy(bool); batas = isi != np.r_[isi[:1], isi[:-1]]
        O["K1"].append(dict(stasiun=s, var=v, ambang=thr, lompat_V63=int((d3 > thr).sum()), lompat_V64=int((d4 > thr).sum()), di_batas_isian_V64=int(((d4 > thr) & (batas | np.r_[batas[1:], False])).sum()),
                            p99_V63=round(float(np.nanpercentile(d3, 99)), 3), p99_V64=round(float(np.nanpercentile(d4, 99)), 3)))
        syn = np.logical_or.reduce([p[k].to_numpy(bool) for k in kf if k in p] + [isi, p[f"met_sisipan_{v}"].to_numpy(bool)])
        for lab, m in (("latih", yr <= 2023), ("validasi", yr == 2024), ("uji", yr == 2025)):
            mm = org & m; O["K3"].append(dict(stasiun=s, var=v, split=lab, logger=round(float((mm & ~syn & np.isfinite(x4)).sum() / mm.sum()), 3), dari_synop=round(float((mm & syn & np.isfinite(x4)).sum() / mm.sum()), 3), kosong=round(float((mm & ~np.isfinite(x4)).sum() / mm.sum()), 3)))
        lg = ~syn & np.r_[False, ~syn[:-1]]; sy = syn & np.r_[False, syn[:-1]]
        O["K4"].append(dict(stasiun=s, var=v, sd_dif10_logger=round(float(np.nanstd(np.diff(x4, prepend=np.nan)[lg & org])), 3), sd_dif10_dari_synop=round(float(np.nanstd(np.diff(x4, prepend=np.nan)[sy & org])), 3) if (sy & org).sum() > 500 else np.nan))
    T, H, P, W = (b[c].to_numpy(float) for c in ("aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms"))
    es = lambda x: 6.112 * np.exp(17.62 * x / (243.12 + x))
    with np.errstate(all="ignore"): g = np.log(es(T) * H / 100 / 6.112); Td = 243.12 * g / (17.62 - g)
    hp = pd.DataFrame({"T": T, "H": H}).groupby(t.hour).mean(); dP3 = np.abs(P - pd.Series(P).shift(18).to_numpy())
    O["K2"].append(dict(stasiun=s, Td_p1=round(float(np.nanpercentile(Td, 1)), 1), Td_p99=round(float(np.nanpercentile(Td, 99)), 1), Td_gt_T=int((Td > T + 0.01).sum()),
                        r_harian_suhu_rh=round(float(hp["T"].corr(hp["H"])), 3), tendensi3j_gt3hPa=int((dP3 > 3).sum()), tendensi3j_p999=round(float(np.nanpercentile(dP3, 99.9)), 2),
                        angin_maks=round(float(np.nanmax(W)), 1), angin_gt15=int((W > 15).sum()), suhu_min=round(float(np.nanmin(T)), 1), suhu_maks=round(float(np.nanmax(T)), 1)))
    print(s, "selesai", flush=True)
for k, L in O.items():
    T_ = pd.DataFrame(L); T_.to_csv(os.path.join(HERE, f"{k}.csv"), index=False); print("==", k); print(T_.to_string(index=False))
