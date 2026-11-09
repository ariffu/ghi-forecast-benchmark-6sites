# -*- coding: utf-8 -*-
"""Tahap 99: bangun Balai_data_v6_3 dari Balai_data_v6_2 (hanya dibaca): angin dan tekanan Bengkulu diisi kausal dari SYNOP (DESAIN_99.md).
Argumen: jalur job_13401.csv. Belum dibekukan (perbaikan Banten menyusul)."""
import os, sys, json, shutil, hashlib, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); V2 = r"C:\Users\ariff\Documents\Balai_data_v6_2"; V3 = r"C:\Users\ariff\Documents\Balai_data_v6_3"; CSV = sys.argv[1]
assert not os.path.exists(os.path.join(V3, "SHA256.txt")), "V6.3 sudah beku"
PER = {"angin": ("2024-07-01", "2025-09-01"), "tekanan": ("2024-04-01", "2025-09-01")}
if os.path.exists(V3): shutil.rmtree(V3)
shutil.copytree(V2, V3, copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("SHA256.txt", "README.md"))
F = pd.read_csv(CSV, usecols=["data_timestamp", "wind_indicator_iw", "wind_speed_ff", "pressure_qfe_mb_derived", "pressure_qff_mb_derived"]); F["t"] = pd.to_datetime(F.data_timestamp) + pd.Timedelta(hours=7)
F = F.drop_duplicates("t", keep="last").set_index("t"); assert F.wind_indicator_iw.isin([3, 4, 9999]).all()
Fw = (F.wind_speed_ff.where(F.wind_speed_ff < 200) * 0.514444); Fp = F.pressure_qfe_mb_derived.where(F.pressure_qfe_mb_derived.between(950, 1050))
C_QFF_QFE = float((F.pressure_qff_mb_derived - F.pressure_qfe_mb_derived).median())
def deret(d, t):
    ws = (d.synop_wind_speed_kt.where(d.synop_wind_speed_kt < 200) * 0.514444).to_numpy(float).copy(); ps = (d.synop_pressure_hpa - C_QFF_QFE).to_numpy(float).copy()
    ix = pd.Series(np.arange(len(t)), index=t); j = ix.reindex(F.index).dropna().astype(int).to_numpy(); k = F.index.isin(t)
    ws[j] = Fw[k].to_numpy(); ps[j] = Fp[k].to_numpy(); return ws, ps
def isi(s, a_lat, t, lat, kal, umur_maks=180):
    md = t.hour * 60 + t.minute; cl = pd.Series(a_lat[lat]).groupby([t.month[lat], md[lat]]).mean()
    S = pd.Series(s, index=t); last = S.ffill().to_numpy(); t0 = pd.DatetimeIndex(pd.Series(np.where(np.isfinite(s), t, pd.NaT), index=t).ffill())
    age = ((t - t0).total_seconds() / 60).to_numpy(); md0 = np.nan_to_num(t0.hour * 60 + t0.minute, nan=0).astype(int)
    c_t = cl.reindex(list(zip(t.month, md))).to_numpy(); c_0 = cl.reindex(list(zip(t0.month.fillna(1).astype(int), md0))).to_numpy()
    x = kal[0] * last + kal[1] + c_t - c_0; x[~(age <= umur_maks)] = np.nan; return x, age
LAP = dict(qff_minus_qfe=C_QFF_QFE, sumber_sha256=hashlib.sha256(open(CSV, "rb").read()).hexdigest())
for var in ("00_data", "00_data_rawfill"):
    p = os.path.join(V3, var, "bengkulu_full.parquet"); d = pd.read_parquet(p); dt = d.dtypes; old = d.copy(); t = pd.DatetimeIndex(d.ts_wib); lat = t.year <= 2023
    ws, ps = deret(d, t)
    aw, ap = d.aws_wind_speed_ms.to_numpy(float), d.aws_pressure_hpa.to_numpy(float)
    m = lat & np.isfinite(aw) & np.isfinite(ws); KW = tuple(map(float, np.polyfit(ws[m], aw[m], 1)))
    m = lat & np.isfinite(ap) & np.isfinite(ps); KP = (1.0, float(np.median(ap[m] - ps[m])))
    xw, agew = isi(ws, aw, t, lat, KW); xw = np.clip(xw, 0, None); xp, agep = isi(ps, ap, t, lat, KP)
    # uji kausalitas: potong SYNOP sesudah beberapa waktu, isian sebelum potongan harus identik
    for cut in ("2024-08-15 12:34", "2025-01-10 09:05", "2025-06-30 18:55"):
        c = t > pd.Timestamp(cut); w2 = ws.copy(); w2[c] = np.nan; p2 = ps.copy(); p2[c] = np.nan
        a1, _ = isi(w2, aw, t, lat, KW); b1, _ = isi(p2, ap, t, lat, KP); ok = ~c
        assert np.allclose(np.clip(a1, 0, None)[ok], xw[ok], equal_nan=True) and np.allclose(b1[ok], xp[ok], equal_nan=True), cut
    iw = (t >= PER["angin"][0]) & (t < PER["angin"][1]); ip = (t >= PER["tekanan"][0]) & (t < PER["tekanan"][1])
    d.loc[iw, "aws_wind_speed_ms"] = xw[iw]; d.loc[ip, "aws_pressure_hpa"] = xp[ip]
    W = pd.to_numeric(d.aws_wind_speed_ms); P = pd.to_numeric(d.aws_pressure_hpa)
    d["aws_wind_speed_roll_180m_mean"] = W.rolling(18, min_periods=1).mean().to_numpy(); d["aws_pressure_lag_60m"] = P.shift(6).to_numpy(); d["aws_pressure_delta_60m"] = (P - P.shift(6)).to_numpy()
    for c in d.columns:
        if str(dt[c]) != str(d[c].dtype): d[c] = d[c].astype(dt[c])
    assert list(d.columns) == list(old.columns) and (d.dtypes == dt).all()
    beda = sorted(c for c in d.columns if not d[c].equals(old[c])); BOLEH = {"aws_wind_speed_ms", "aws_wind_speed_roll_180m_mean", "aws_pressure_hpa", "aws_pressure_lag_60m", "aws_pressure_delta_60m"}
    assert set(beda) <= BOLEH, beda
    jam = iw & np.isfinite(ws); assert np.allclose(d.aws_wind_speed_ms.to_numpy(float)[jam], np.clip(KW[0] * ws[jam] + KW[1], 0, None))
    jam = ip & np.isfinite(ps); assert np.allclose(d.aws_pressure_hpa.to_numpy(float)[jam], ps[jam] + KP[1])
    luar = ~(iw | ip); assert np.array_equal(np.nan_to_num(old.aws_pressure_hpa.to_numpy(float)[luar], nan=-1), np.nan_to_num(d.aws_pressure_hpa.to_numpy(float)[luar], nan=-1))
    d.to_parquet(p, index=False)
    LAP[var] = dict(kal_angin=KW, kal_tekanan=KP, kolom_berubah=beda, angin_slot_periode=int(iw.sum()), angin_terisi=int(np.isfinite(xw[iw]).sum()), tekanan_slot_periode=int(ip.sum()), tekanan_terisi=int(np.isfinite(xp[ip]).sum()),
                    siang_el5_angin_terisi=round(float(np.isfinite(xw[iw & (d.solar_elev_deg.to_numpy(float) > 5)]).mean()), 4), siang_el5_tekanan_terisi=round(float(np.isfinite(xp[ip & (d.solar_elev_deg.to_numpy(float) > 5)]).mean()), 4))
    if var == "00_data": IW, IP = iw & np.isfinite(xw), ip & np.isfinite(xp)
pv = os.path.join(V3, "provenance", "bengkulu_provenance.parquet"); P_ = pd.read_parquet(pv); P_["aws_isi_synop_angin"] = IW; P_["aws_isi_synop_tekanan"] = IP; P_.to_parquet(pv, index=False)
json.dump(LAP, open(os.path.join(HERE, "i2_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(json.dumps(LAP, ensure_ascii=False, indent=1)); print("SELESAI")
