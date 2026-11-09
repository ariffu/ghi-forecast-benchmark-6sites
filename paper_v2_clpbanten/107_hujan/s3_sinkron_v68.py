# -*- coding: utf-8 -*-
"""Tahap 107 s1: sinkronisasi hujan AWS (V6.7, per 10 menit) dengan SYNOP (RR 3 jam 'last', 6 jam, 24 jam; reset 00 UTC = 07.00 WIB). Hanya membaca.
Konvensi hari hujan: (07.00 kemarin, 07.00 hari ini] — slot 07.00 milik hari sebelumnya (data mentah Banten: kumulatif ditahan sampai 07.00, reset 07.10).
Periode SYNOP berakhir di jam laporan T (WIB): RR_last 3 jam pada 10/13/16/19 WIB (03/06/09/12 UTC), RR6 pada 13 dan 19 WIB, RR24 pada 07 WIB.
AWS untuk periode (T−Δ, T]: jumlah slot berlabel (T−Δ, T] (A) dan [T−Δ, T) (B) — dua kemungkinan arti label slot."""
import os, duckdb, numpy as np, pandas as pd
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_8"
DB = r"C:\Users\ariff\Documents\Balai Obsidian\Balai\solardata_new_v2\solar_harmonised_clpbanten_v2.duckdb"
SY = dict(banten=("banten.synopcompletefilledv", "timestamp_wib", None, "synop_rainfall_6h_mm", "synop_rainfall_24h_mm", "rainfall_24h_fill_method"),
          bengkulu=("bengkulu.synop_bengkulu_quality_final", "ts_wib", "rainfall_last_mm", "rainfall_6h_rrr", "rainfall_24h_rrrr", None),
          jambi=("jambi.synop_jambi_combined", "waktu", "rainfall_last_mm", "rainfall_6h_mm", "rainfall_24h_mm", None),
          jogja=("jogja.synop_jogja", "timestamp_wib", "synop_rainfall_last_mm", "synop_rainfall_6h_mm", "synop_rainfall_24h_mm", None),
          kalbar=("kalbar.synop_unified", "timestamp_wib", "rainfall_last_mm_filled", "rainfall_6h_mm_filled", "rainfall_24h_mm_filled", None),
          semarang=("semarang.synop_semarang", "data_timestamp_wib", "synop_rainfall_last_mm", "synop_rainfall_6h_mm", "synop_rainfall_24h_mm", None))
c = duckdb.connect(DB, read_only=True); R, Q = [], []
for s, (tab, tc, cl, c6, c24, fm) in SY.items():
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "aws_rain_mm"]); r = d.set_index("ts_wib").aws_rain_mm.astype(float)
    cols = ", ".join([f"{tc} as t"] + [f"{x} as {n}" for x, n in ((cl, "rr3"), (c6, "rr6"), (c24, "rr24"), (fm, "fm")) if x])
    S = c.execute(f"select {cols} from {tab}").df(); S["t"] = pd.to_datetime(S.t); S = S.drop_duplicates("t").set_index("t").sort_index()
    if s == "jambi" and S.index.hour.isin([0, 3]).mean() > 0.5: S.index = S.index + pd.Timedelta(hours=7)
    if fm: S.loc[S.fm.notna(), "rr24"] = np.nan           # Banten: hanya RR24 asli, bukan hasil isian
    cs = r.fillna(0).cumsum()
    def aws_sum(T, jam, geser):
        a = cs.reindex(T - pd.Timedelta(minutes=geser)).to_numpy(); b = cs.reindex(T - pd.Timedelta(hours=jam) - pd.Timedelta(minutes=geser)).to_numpy(); return a - b
    for nm, jam, jams in (("rr3", 3, (10, 13, 16, 19)), ("rr6", 6, (13, 19)), ("rr24", 24, (7,))):
        if nm not in S: continue
        x = S[nm].where((S[nm] >= 0) & (S[nm] < 500)); x = x[x.index.hour.isin(jams) & (x.index.minute == 0) & (x.index >= "2022-01-02") & (x.index <= "2025-12-31 23:00")].dropna()
        for lab, g in (("A (T-Δ,T]", 0), ("B [T-Δ,T)", 10)):
            a = aws_sum(x.index, jam, g); m = np.isfinite(a); y = x.to_numpy()[m]; a = a[m]
            R.append(dict(stasiun=s, periode=nm, label=lab, n=int(m.sum()), syn_mm=round(float(y.sum())), aws_mm=round(float(a.sum())), rasio=round(float(a.sum() / max(y.sum(), 1e-9)), 3), r=round(float(np.corrcoef(a, y)[0, 1]), 3),
                          mae=round(float(np.mean(np.abs(a - y))), 2), aws0_syn_gt2=int(((a < 0.2) & (y > 2)).sum()), aws_gt2_syn0=int(((a > 2) & (y < 0.2)).sum())))
    # slot 07.00: apakah berisi total 24 jam sebelumnya (dobel hitung)?
    t7 = r.index[(r.index.hour == 7) & (r.index.minute == 0)]; v7 = r.reindex(t7).to_numpy(); prev = (cs.reindex(t7 - pd.Timedelta(minutes=10)).to_numpy() - cs.reindex(t7 - pd.Timedelta(hours=24)).to_numpy())
    m = (v7 > 0.5) & (prev > 0.5); Q.append(dict(stasiun=s, hari_v07_gt0_5=int((v7 > 0.5).sum()), v07_total_mm=round(float(np.nansum(v7))), v07_per_total_hujan_pct=round(100 * float(np.nansum(v7) / r.sum()), 1),
                                                 median_v07_per_jumlah_23j50=round(float(np.median(v7[m] / prev[m])), 3) if m.any() else np.nan, v07_dalam_10pct_jumlah=int((m & (np.abs(v7 - prev) <= 0.1 * prev + 0.2)).sum())))
    print(s, "selesai", flush=True)
T = pd.DataFrame(R); T.to_csv(os.path.join(HERE, "s3_sinkron_v68.csv"), index=False); print(T.to_string(index=False))
TQ = pd.DataFrame(Q); TQ.to_csv(os.path.join(HERE, "s3_slot0700_v68.csv"), index=False); print("== slot 07.00"); print(TQ.to_string(index=False))
