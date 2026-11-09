import os, numpy as np, pandas as pd
V6 = r"C:\Users\ariff\Documents\Balai_data_v6\00_data"; R = {}
for s in ("banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"):
    d = pd.read_parquet(os.path.join(V6, f"{s}_full.parquet")); t = pd.DatetimeIndex(d.ts_wib); e = d.solar_elev_deg; c = d.clp_cot
    Co, Ct = c, d.clp_cth_km
    ok = all(np.allclose(a, b, equal_nan=True) for a, b in ((d.clp_cot_lag_60m, Co.shift(6)), (d.clp_cot_delta_60m, Co - Co.shift(6)), (d.clp_cot_roll_180m_mean, Co.rolling(18, min_periods=1).mean()), (d.clp_cth_lag_60m, Ct.shift(6)), (d.clp_cth_roll_180m_mean, Ct.rolling(18, min_periods=1).mean())))
    R[s] = dict(turunan_cocok=ok, isi_0950=round(float(c[t.strftime("%H:%M") == "09:50"].notna().mean()), 4), isi_malam=int((c.notna() & (e < -2)).sum()), cot_150=int((c > 150).sum()), isi_siang=round(float(c[e > 15].notna().mean()), 4),
                cth_luar=int(((d.clp_cth_km < 0) | (d.clp_cth_km > 20)).sum()), runtun_sama_6=int(((c == c.shift(1)) & (c == c.shift(5)) & c.notna() & (c > 0)).sum()))
print(pd.DataFrame(R).to_string())
