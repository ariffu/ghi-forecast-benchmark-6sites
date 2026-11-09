import numpy as np, pandas as pd
for s in ("banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"):
    d = pd.read_parquet(rf"C:\Users\ariff\Documents\Balai_data_v6\00_data\{s}_full.parquet", columns=["ts_wib", "ghi_wm2", "dhi_wm2", "dni_wm2", "solar_elev_deg"]); q = pd.read_parquet(rf"C:\Users\ariff\Documents\Balai_data_v6_1\qc\{s}_qc.parquet"); cs = pd.read_parquet(rf"C:\Users\ariff\Documents\Balai_data_v6_1\clearsky\{s}_ineichen.parquet")
    kc = (d.ghi_wm2 / cs.ghi_cs.where(cs.ghi_cs > 50)); m = (d.solar_elev_deg > 30) & (kc > 0.8) & (d.dni_wm2 < 10)
    idx = pd.DatetimeIndex(d.ts_wib); print(f"{s}: DNI < 10 saat k_c > 0,8 dan elevasi > 30°: {int(m.sum())} slot; per kode {q.qc_dni[m].value_counts().to_dict()}; per tahun-triwulan {pd.Series(idx[m].to_period('Q')).value_counts().sort_index().head(8).astype(int).to_dict()}; DHI/GHI median {float((d.dhi_wm2 / d.ghi_wm2)[m].median()):.2f}")
