# -*- coding: utf-8 -*-
"""Tahap 99 amandemen 1: tekanan AWS datar ≥ 3 jam diganti isian kausal SYNOP database (cara 2), di Balai_data_v6_3 (draf, belum beku)."""
import os, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); V3 = r"C:\Users\ariff\Documents\Balai_data_v6_3"
assert not os.path.exists(os.path.join(V3, "SHA256.txt")), "V6.3 sudah beku"
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; LAP = {}
def datar(x):
    s = pd.Series(x); g = (s != s.shift()).cumsum(); r = s.groupby(g).transform("size").to_numpy(); return (r >= 18) & np.isfinite(x)
def isi(s, a, t, lat_ok, kal, umur_maks=180):
    md = t.hour * 60 + t.minute; cl = pd.Series(a[lat_ok]).groupby([t.month[lat_ok], md[lat_ok]]).mean()
    last = pd.Series(s, index=t).ffill().to_numpy(); t0 = pd.DatetimeIndex(pd.Series(np.where(np.isfinite(s), t, pd.NaT), index=t).ffill())
    age = ((t - t0).total_seconds() / 60).to_numpy(); md0 = np.nan_to_num(t0.hour * 60 + t0.minute, nan=0).astype(int)
    x = kal + last + cl.reindex(list(zip(t.month, md))).to_numpy() - cl.reindex(list(zip(t0.month.fillna(1).astype(int), md0))).to_numpy(); x[~(age <= umur_maks)] = np.nan; return x
for s in S:
    L = {}
    for var in ("00_data", "00_data_rawfill"):
        p = os.path.join(V3, var, f"{s}_full.parquet"); d = pd.read_parquet(p); dt = d.dtypes; old = d.copy(); t = pd.DatetimeIndex(d.ts_wib)
        a = d.aws_pressure_hpa.to_numpy(float).copy(); sp = d.synop_pressure_hpa.to_numpy(float); m = datar(a)
        if not m.any(): L[var] = dict(datar=0); continue
        ok = (t.year <= 2023) & ~m & np.isfinite(a); kal = float(np.median((a - sp)[ok & np.isfinite(sp)]))
        x = isi(sp, a, t, ok, kal)
        # kausalitas: potong SYNOP sesudah titik acak, isian sebelumnya harus sama
        for cut in ("2022-02-10 03:20", "2022-03-25 16:40"):
            c = t > pd.Timestamp(cut); s2 = sp.copy(); s2[c] = np.nan; assert np.allclose(isi(s2, a, t, ok, kal)[~c], x[~c], equal_nan=True)
        d.loc[m, "aws_pressure_hpa"] = x[m]; P = pd.to_numeric(d.aws_pressure_hpa)
        d["aws_pressure_lag_60m"] = P.shift(6).to_numpy(); d["aws_pressure_delta_60m"] = (P - P.shift(6)).to_numpy()
        for c in d.columns:
            if str(dt[c]) != str(d[c].dtype): d[c] = d[c].astype(dt[c])
        beda = sorted(c for c in d.columns if not d[c].equals(old[c])); assert set(beda) <= {"aws_pressure_hpa", "aws_pressure_lag_60m", "aws_pressure_delta_60m"}, beda
        assert np.array_equal(np.nan_to_num(a[~m], nan=-1), np.nan_to_num(d.aws_pressure_hpa.to_numpy(float)[~m], nan=-1))
        sisa = int(datar(d.aws_pressure_hpa.to_numpy(float)).sum()); d.to_parquet(p, index=False)
        el = d.solar_elev_deg.to_numpy(float)
        L[var] = dict(datar=int(m.sum()), kalibrasi=round(kal, 3), terisi=int(np.isfinite(x[m]).sum()), terisi_siang_el5=round(float(np.isfinite(x[m & (el > 5)]).mean()), 3) if (m & (el > 5)).any() else None, sisa_datar=sisa,
                      per_bulan=pd.Series(m).groupby(t.to_period("M").astype(str)).sum().loc[lambda v: v > 0].astype(int).to_dict())
        if var == "00_data": M0 = m & np.isfinite(x)
    if L["00_data"]["datar"]:
        pv = os.path.join(V3, "provenance", f"{s}_provenance.parquet"); P_ = pd.read_parquet(pv); P_["aws_isi_synop_tekanan_datar"] = M0; P_.to_parquet(pv, index=False)
    else:
        pv = os.path.join(V3, "provenance", f"{s}_provenance.parquet"); P_ = pd.read_parquet(pv); P_["aws_isi_synop_tekanan_datar"] = False; P_.to_parquet(pv, index=False)
    LAP[s] = L; print(s, json.dumps(L["00_data"], ensure_ascii=False), flush=True)
json.dump(LAP, open(os.path.join(HERE, "i4_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
