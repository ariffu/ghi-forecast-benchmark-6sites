import os, numpy as np, pandas as pd
V5 = r"C:\Users\ariff\Documents\Balai_data_v5_final87\00_data"
for s in ("bengkulu", "jogja", "kalbar", "semarang"):
    B = pd.read_parquet(f"_csv_baru_dibalik_{s}.parquet"); B["t"] = pd.to_datetime(B.timestamp) + pd.Timedelta(minutes=10); B = B.set_index("t")
    V = pd.read_parquet(os.path.join(V5, f"{s}_full.parquet"), columns=["ts_wib", "clp_cot", "solar_elev_deg"]).set_index("ts_wib"); v = V.clp_cot
    ada = B.source_file.reindex(V.index).notna(); o = v.notna() & ~ada
    prev, nxt = v.shift(1), v.shift(-1); mid = (prev + nxt) / 2
    jam = pd.Series(V.index[o].strftime("%H:%M")).value_counts().head(4).to_dict()
    print(f"{s}: tanpa berkas tetapi V5 berisi {int(o.sum())}; jam terbanyak {jam}; = slot sebelumnya {np.isclose(v[o], prev[o]).mean():.3f}; = rata-rata sebelum/sesudah {np.isclose(v[o], mid[o]).mean():.3f}; = slot sesudahnya {np.isclose(v[o], nxt[o]).mean():.3f}")
    n = o & (V.solar_elev_deg < 0); print(f"   malam: {int(n.sum())} slot; = slot sebelumnya {np.isclose(v[n], prev[n]).mean():.3f}; contoh {V.index[n][:3].tolist()} nilai {v[n][:3].round(2).tolist()}")
