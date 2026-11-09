# -*- coding: utf-8 -*-
"""Tahap 93: (1) slot CLP Bengkulu yang dikosongkan P3 — apakah CSV baru juga tanpa retrieval? (2) slot yang beda antara CSV baru dan V5 di Semarang, Kalbar, Bengkulu, Jogja. Hanya membaca."""
import os, numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
HERE = os.path.dirname(os.path.abspath(__file__)); V5 = r"C:\Users\ariff\Documents\Balai_data_v5_final87\00_data"; PV6 = r"C:\Users\ariff\Documents\Balai_data_v6\provenance"
for s in ("bengkulu", "semarang", "kalbar", "jogja"):
    B = pd.read_parquet(os.path.join(HERE, f"_csv_baru_dibalik_{s}.parquet")); B["t"] = pd.to_datetime(B.timestamp) + pd.Timedelta(minutes=10); B = B.set_index("t")
    V = pd.read_parquet(os.path.join(V5, f"{s}_full.parquet"), columns=["ts_wib", "clp_cot", "solar_elev_deg"]).set_index("ts_wib")
    c = B.CLOT_mean.reindex(V.index); v = V.clp_cot; e = V.solar_elev_deg
    if s == "bengkulu":
        g = pd.read_parquet(os.path.join(PV6, "bengkulu_provenance.parquet")).set_index("ts_wib").clp_gagal_dikosongkan.reindex(V.index).fillna(False).astype(bool)
        print(f"bengkulu: slot P3 {int(g.sum())}; CSV baru tanpa retrieval {int((g & c.isna()).sum())}, berisi {int((g & c.notna()).sum())}; elevasi median {e[g].median():.1f}°")
        print("   CSV baru berisi di slot P3, sama dengan V5:", int((g & c.notna() & np.isclose(c, v)).sum()), "| cloud_class di slot itu:", B.cloud_class.reindex(V.index)[g].value_counts().head(5).to_dict())
    w = c.notna() & v.notna(); d = w & ~np.isclose(c, v, atol=1e-4); only_v5 = v.notna() & c.isna(); only_new = c.notna() & v.isna()
    print(f"{s}: beda nilai {int(d.sum())} slot (elevasi median {e[d].median():.1f}°, per tahun {pd.Series(V.index[d].year).value_counts().sort_index().to_dict()}); V5 saja {int(only_v5.sum())}; baru saja {int(only_new.sum())}")
    if d.sum():
        x = pd.DataFrame({"v5": v[d], "baru": c[d]}).head(6); print(x.to_string())
        rasio = (v[d] / c[d]).replace([np.inf, -np.inf], np.nan); print("   rasio V5/baru p10/p50/p90:", rasio.quantile([.1, .5, .9]).round(3).tolist(), "| V5 = 150 (batas):", int((v[d] == 150).sum()), "| geser waktu ±10 mnt cocok:", int((np.isclose(v[d], c.shift(1)[d]) | np.isclose(v[d], c.shift(-1)[d])).sum()))
