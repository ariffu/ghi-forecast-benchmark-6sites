import os, numpy as np, pandas as pd
V5 = r"C:\Users\ariff\Documents\Balai_data_v5_final87\00_data"; PV6 = r"C:\Users\ariff\Documents\Balai_data_v6\provenance"
for s in ("banten", "bengkulu", "jogja", "kalbar", "semarang"):
    B = pd.read_parquet(f"_csv_baru_dibalik_{s}.parquet"); B["t"] = pd.to_datetime(B.timestamp) + pd.Timedelta(minutes=10); B = B.set_index("t")
    V = pd.read_parquet(os.path.join(V5, f"{s}_full.parquet"), columns=["ts_wib", "clp_cot", "solar_elev_deg"]).set_index("ts_wib")
    c = B.CLOT_mean.reindex(V.index); ada = B.source_file.reindex(V.index).notna(); o = V.clp_cot.notna() & c.isna()
    if s == "bengkulu": o &= ~pd.read_parquet(os.path.join(PV6, "bengkulu_provenance.parquet")).set_index("ts_wib").clp_gagal_dikosongkan.reindex(V.index).fillna(False).astype(bool)
    e = V.solar_elev_deg; print(f"{s}: V5 berisi, CSV baru kosong {int(o.sum())}: berkas ada {int((o & ada).sum())}, tanpa berkas {int((o & ~ada).sum())}; elevasi >5° {int((o & (e > 5)).sum())}; elevasi p50 {e[o].median():.1f}; jam {pd.Series(V.index[o].hour).value_counts().sort_index().head(14).to_dict()}; COT V5 p50 {V.clp_cot[o].median():.2f}")
