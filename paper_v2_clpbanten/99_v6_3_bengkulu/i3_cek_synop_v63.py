# -*- coding: utf-8 -*-
"""Tahap 98 H8: konfirmasi anemometer dan tekanan AWS Bengkulu 2024–2025 dengan SYNOP Stasiun Klimatologi Bengkulu (job_13401.csv dari pengguna).
Hanya membaca. Kolom nama pengamat tidak dibaca. Argumen: jalur CSV."""
import os, sys, numpy as np, pandas as pd
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
HERE = r"C:\Users\ariff\Documents\Balai Obsidian\Balai\solardata_new_v2\paper_v2_clpbanten\99_v6_3_bengkulu"; V = r"C:\Users\ariff\Documents\Balai_data_v6_3"; CSV = sys.argv[1]
K = ["station_name", "data_timestamp", "wind_indicator_iw", "wind_dir_deg_dd", "wind_speed_ff", "pressure_qfe_mb_derived", "pressure_qff_mb_derived", "temp_drybulb_c_tttttt", "relative_humidity_pc", "qc_flag"]
S = pd.read_csv(CSV, usecols=K); S["t_utc"] = pd.to_datetime(S.data_timestamp)
print("baris", len(S), "stasiun", S.station_name.unique().tolist(), "rentang", S.t_utc.min(), "–", S.t_utc.max(), "duplikat waktu", int(S.t_utc.duplicated().sum()))
print("jam UTC:", S.t_utc.dt.hour.value_counts().sort_index().to_dict()); print("iw:", S.wind_indicator_iw.value_counts().to_dict(), "qc_flag:", S.qc_flag.value_counts().to_dict())
S = S.drop_duplicates("t_utc", keep="last").set_index("t_utc").sort_index()
S["ff_ms"] = S.wind_speed_ff * np.where(S.wind_indicator_iw.isin([3, 4]), 0.514444, 1.0)   # iw 3/4 = knot (WMO 1855)
S["t_wib"] = S.index + pd.Timedelta(hours=7)
d = pd.read_parquet(os.path.join(V, "00_data", "bengkulu_full.parquet"), columns=["ts_wib", "aws_wind_speed_ms", "aws_wind_dir_deg", "aws_pressure_hpa", "aws_temp_c", "synop_wind_speed_kt", "synop_pressure_hpa", "synop_temp_c"]).set_index("ts_wib")
r1 = pd.read_parquet(os.path.join(r"C:\Users\ariff\Documents\Balai_data_v6_1", "00_data", "bengkulu_full.parquet"), columns=["ts_wib", "aws_pressure_hpa"]).set_index("ts_wib").aws_pressure_hpa
# keselarasan waktu: suhu SYNOP lawan suhu AWS pada geseran −30…+30 menit (label slot AWS)
for lag in range(-3, 4):
    a = d.aws_temp_c.reindex(S.t_wib + pd.Timedelta(minutes=10 * lag)).to_numpy(); b = S.temp_drybulb_c_tttttt.to_numpy(); m = np.isfinite(a) & np.isfinite(b)
    print(f"  suhu SYNOP–AWS geser {lag * 10:+d} mnt: RMSE {np.sqrt(np.mean((a[m] - b[m]) ** 2)):.3f} (n {m.sum()})")
A = d.reindex(S.t_wib); S["aws_ff"] = A.aws_wind_speed_ms.to_numpy(); S["aws_dd"] = A.aws_wind_dir_deg.to_numpy(); S["aws_p"] = A.aws_pressure_hpa.to_numpy(); S["aws_p_v61"] = r1.reindex(S.t_wib).to_numpy()
S["db_synop_ff_ms"] = A.synop_wind_speed_kt.to_numpy() * 0.514444; S["db_synop_p"] = A.synop_pressure_hpa.to_numpy()
S["bulan"] = S.t_wib.dt.to_period("M").astype(str)
def bl(g):
    m = g.ff_ms.notna() & g.aws_ff.notna()
    return pd.Series(dict(n=int(m.sum()), synop_ms_rerata=round(g.ff_ms[m].mean(), 2), aws_ms_rerata=round(g.aws_ff[m].mean(), 2), synop_tenang_pct=round(100 * (g.ff_ms[m] == 0).mean(), 1), aws_nol_pct=round(100 * (g.aws_ff[m] == 0).mean(), 1),
                          aws_nol_saat_synop_ge2ms_pct=round(100 * ((g.aws_ff[m] == 0) & (g.ff_ms[m] >= 2)).sum() / max((g.ff_ms[m] >= 2).sum(), 1), 1),
                          r=round(float(np.corrcoef(g.ff_ms[m], g.aws_ff[m])[0, 1]), 2) if m.sum() > 30 and g.aws_ff[m].std() > 0 else np.nan,
                          p_qfe_minus_aws=round(float((g.pressure_qfe_mb_derived - g.aws_p).median()), 2), p_rmse=round(float(np.sqrt(((g.pressure_qfe_mb_derived - g.aws_p) ** 2).mean())), 2)))
T = S.groupby("bulan").apply(bl); T.to_csv(os.path.join(HERE, "i3_synop_bengkulu_bulanan_v63.csv")); print(T.to_string())
# tekanan: slot yang dikosongkan saringan V6.2 — apa kata SYNOP?
pv = pd.read_parquet(os.path.join(V, "provenance", "bengkulu_provenance.parquet"), columns=["ts_wib", "aws_lonjakan_tekanan"]).set_index("ts_wib").aws_lonjakan_tekanan
S["dibuang"] = pv.reindex(S.t_wib).to_numpy(); m = S.dibuang.fillna(False).astype(bool) & S.pressure_qfe_mb_derived.notna() & S.aws_p_v61.notna()
k = ~S.dibuang.fillna(False).astype(bool) & S.pressure_qfe_mb_derived.notna() & S.aws_p.notna()
print("Tekanan: slot SYNOP yang di AWS V6.2 dikosongkan:", int(m.sum()), "| |QFE − AWS V6.1| median", round(float((S.pressure_qfe_mb_derived - S.aws_p_v61)[m].abs().median()), 2),
      "| slot dipertahankan |QFE − AWS| median", round(float((S.pressure_qfe_mb_derived - S.aws_p)[k].abs().median()), 2), "p95", round(float((S.pressure_qfe_mb_derived - S.aws_p)[k].abs().quantile(.95)), 2))
# berkas pengguna lawan SYNOP di DB
w = S.ff_ms.notna() & S.db_synop_ff_ms.notna(); print("Angin berkas lawan synop DB: n", int(w.sum()), "sama (±0,01):", round(float((np.abs(S.ff_ms - S.db_synop_ff_ms)[w] < 0.01).mean()), 3),
      "| tekanan QFF lawan synop DB sama (±0,05):", round(float((np.abs(S.pressure_qff_mb_derived - S.db_synop_p) < 0.05)[S.db_synop_p.notna() & S.pressure_qff_mb_derived.notna()].mean()), 3))
# arah: AWS lawan SYNOP saat angin ≥ 2 m/s
m = (S.ff_ms >= 2) & (S.aws_ff >= 1) & S.aws_dd.notna() & S.wind_dir_deg_dd.between(1, 360)
dd = np.abs((S.aws_dd - S.wind_dir_deg_dd)[m] + 180) % 360 - 180; print("Arah AWS–SYNOP (angin ≥ 2 m/s): n", int(m.sum()), "median |selisih|", round(float(dd.abs().median()), 1), "°, bias", round(float(dd.median()), 1), "°")
