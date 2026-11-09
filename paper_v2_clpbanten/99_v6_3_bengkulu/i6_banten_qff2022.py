# -*- coding: utf-8 -*-
"""Tahap 99 amandemen 2: tekanan Banten 1 Jan – 31 Mar 2022 (QFF mentah) dan slot datar ≥ 3 jam diganti isian kausal SYNOP DB; dihitung ulang dari V6.2.
Juga menambah kolom provenance aws_isi_synop_tekanan (False) di stasiun yang belum punya. V6.3 masih draf."""
import os, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); V2 = r"C:\Users\ariff\Documents\Balai_data_v6_2"; V3 = r"C:\Users\ariff\Documents\Balai_data_v6_3"
assert not os.path.exists(os.path.join(V3, "SHA256.txt")), "V6.3 sudah beku"
def datar(x):
    s = pd.Series(x); g = (s != s.shift()).cumsum(); r = s.groupby(g).transform("size").to_numpy(); return (r >= 18) & np.isfinite(x)
def isi(s, a, t, lat_ok, kal, umur_maks=180):
    md = t.hour * 60 + t.minute; cl = pd.Series(a[lat_ok]).groupby([t.month[lat_ok], md[lat_ok]]).mean()
    last = pd.Series(s, index=t).ffill().to_numpy(); t0 = pd.DatetimeIndex(pd.Series(np.where(np.isfinite(s), t, pd.NaT), index=t).ffill())
    age = ((t - t0).total_seconds() / 60).to_numpy(); md0 = np.nan_to_num(t0.hour * 60 + t0.minute, nan=0).astype(int)
    x = kal + last + cl.reindex(list(zip(t.month, md))).to_numpy() - cl.reindex(list(zip(t0.month.fillna(1).astype(int), md0))).to_numpy(); x[~(age <= umur_maks)] = np.nan; return x
LAP = {}
for var in ("00_data", "00_data_rawfill"):
    a2 = pd.read_parquet(os.path.join(V2, var, "banten_full.parquet"), columns=["ts_wib", "aws_pressure_hpa"]); p = os.path.join(V3, var, "banten_full.parquet"); d = pd.read_parquet(p); dt = d.dtypes; t = pd.DatetimeIndex(d.ts_wib)
    a = a2.aws_pressure_hpa.to_numpy(float).copy(); sp = d.synop_pressure_hpa.to_numpy(float)
    per = (t >= "2022-01-01") & (t < "2022-04-01"); fl = datar(a) & ~per; m = per | fl
    ok = (t.year <= 2023) & ~m & np.isfinite(a); kal = float(np.median((a - sp)[ok & np.isfinite(sp)])); x = isi(sp, a, t, ok, kal)
    for cut in ("2022-02-10 03:20", "2022-03-25 16:40", "2023-06-01 12:00"):
        c = t > pd.Timestamp(cut); s2 = sp.copy(); s2[c] = np.nan; assert np.allclose(isi(s2, a, t, ok, kal)[~c], x[~c], equal_nan=True)
    new = a.copy(); new[m] = x[m]; d["aws_pressure_hpa"] = new; P = pd.to_numeric(d.aws_pressure_hpa)
    d["aws_pressure_lag_60m"] = P.shift(6).to_numpy(); d["aws_pressure_delta_60m"] = (P - P.shift(6)).to_numpy()
    for c in d.columns:
        if str(dt[c]) != str(d[c].dtype): d[c] = d[c].astype(dt[c])
    d.to_parquet(p, index=False); el = d.solar_elev_deg.to_numpy(float)
    LAP[var] = dict(kalibrasi=round(kal, 3), periode_slot=int(per.sum()), periode_terisi=int(np.isfinite(x[per]).sum()), datar_lain=int(fl.sum()), datar_lain_terisi=int(np.isfinite(x[fl]).sum()),
                    origin_el5_terisi=round(float(np.isfinite(x[m & (el > 5)]).mean()), 3), langkah_gt2=int((np.abs(np.diff(new, prepend=np.nan)) > 2).sum()), sisa_datar=int(datar(new).sum()))
    if var == "00_data": MP, MF = per & np.isfinite(x), fl & np.isfinite(x)
for s in ("banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"):
    pv = os.path.join(V3, "provenance", f"{s}_provenance.parquet"); P_ = pd.read_parquet(pv)
    if s == "banten": P_["aws_isi_synop_tekanan"] = MP; P_["aws_isi_synop_tekanan_datar"] = MF
    elif "aws_isi_synop_tekanan" not in P_: P_.insert(list(P_.columns).index("aws_isi_synop_tekanan_datar"), "aws_isi_synop_tekanan", False)
    P_.to_parquet(pv, index=False)
json.dump(LAP, open(os.path.join(HERE, "i6_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(LAP, ensure_ascii=False, indent=1))
