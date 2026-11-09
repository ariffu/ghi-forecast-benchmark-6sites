import numpy as np, pandas as pd
for s in ("bengkulu", "kalbar", "banten"):
    d = pd.read_parquet(rf"C:\Users\ariff\Documents\Balai_data_v6\00_data\{s}_full.parquet", columns=["ts_wib", "ghi_wm2", "dhi_wm2", "dni_wm2", "solar_elev_deg"]); q = pd.read_parquet(rf"C:\Users\ariff\Documents\Balai_data_v6_1\qc\{s}_qc.parquet"); cs = pd.read_parquet(rf"C:\Users\ariff\Documents\Balai_data_v6_1\clearsky\{s}_ineichen.parquet")
    p = pd.read_parquet(rf"C:\Users\ariff\Documents\Balai_data_v6\provenance\{s}_provenance.parquet", columns=["dni_status", "ghi_sumber"])
    idx = pd.DatetimeIndex(d.ts_wib); m = (d.solar_elev_deg > 30).to_numpy(); kb = (d.dni_wm2 / cs.dni_cs.where(cs.dni_cs > 100)).to_numpy(); kc = (d.ghi_wm2 / cs.ghi_cs.where(cs.ghi_cs > 50)).to_numpy()
    T = pd.DataFrame({"ym": idx.to_period("Q"), "kode": q.qc_dni, "kb": kb, "kc": kc, "dhi_ghi": (d.dhi_wm2 / d.ghi_wm2).to_numpy(), "st": p.dni_status, "src": p.ghi_sumber})[m]
    g = T.groupby(["ym", "kode"]).agg(n=("kb", "size"), kb_p95=("kb", lambda x: round(x.quantile(.95), 3)), kc_p95=("kc", lambda x: round(x.quantile(.95), 3)), difus_p05=("dhi_ghi", lambda x: round(x.quantile(.05), 3))).reset_index()
    print("==", s); print(g[g.n > 50].pivot(index="ym", columns="kode", values="kb_p95").to_string())
    if s == "bengkulu": print(g[(g.kode <= 1) & (g.n > 50)].to_string(index=False)); print("status DNI kode 0 di 2023–24:", T[(T.kode == 0) & (T.ym.astype(str).str[:4].isin(["2023", "2024"]))].st.value_counts().to_dict(), "| sumber GHI:", T[(T.kode == 0) & (T.ym.astype(str).str[:4].isin(["2023", "2024"]))].src.value_counts().to_dict())
