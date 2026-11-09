# -*- coding: utf-8 -*-
"""Tahap 93 P5 (amandemen 2): CLP keenam stasiun dari ekstraksi ulang (6lokasi_output_chips.zip) ke Balai_data_v6.
Konvensi: t = T + 10; kosong bila tidak ada berkas atau retrieval; flag = COT ≥ 1; CER = 0 kosong (00_data);
rawfill: berkas ada tanpa retrieval → 0 (COT, CTH, CER, flag), CTT kosong. Turunan CLP dihitung ulang. Hanya kolom clp_* berubah."""
import os, re, io, json, zipfile, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ZIP = r"C:\Users\ariff\Documents\6lokasi_output_chips.zip"; V6 = r"C:\Users\ariff\Documents\Balai_data_v6"
assert not os.path.exists(os.path.join(V6, "SHA256.txt")), "V6 sudah beku"
LOK = {"banten": "sta6016_banten", "bengkulu": "sta6009_bengkulu", "jambi": "sta6007_jambi", "jogja": "sta6010_jogja", "kalbar": "sta6003_kalbar", "semarang": "sta6018_jateng"}
SK = {"CLOT": (0.01, 0.0), "CLTT": (0.01, 150.0), "CLTH": (0.001, 0.0), "CLER_23": (0.01, 0.0)}
z = zipfile.ZipFile(ZIP); NM = z.namelist(); LAP = {}
def turunan(d):
    Co, Ct = pd.to_numeric(d.clp_cot), pd.to_numeric(d.clp_cth_km)
    return {"clp_cot_lag_60m": Co.shift(6), "clp_cot_delta_60m": Co - Co.shift(6), "clp_cot_roll_180m_mean": Co.rolling(18, min_periods=1).mean(), "clp_cth_lag_60m": Ct.shift(6), "clp_cth_roll_180m_mean": Ct.rolling(18, min_periods=1).mean()}
for s, site in LOK.items():
    F = sorted(n for n in NM if re.search(rf"{site}/CLP_{site}_\d{{4}}-\d\d-\d\d\.csv$", n)); assert len(F) == 1461, (s, len(F))
    C = pd.concat([pd.read_csv(io.BytesIO(z.read(n))) for n in F], ignore_index=True); C["tt"] = pd.to_datetime(C.timestamp)
    assert C[["station_lat", "station_lon"]].drop_duplicates().shape[0] == 1 and C.buffer_km.eq(30).all() and not C.tt.duplicated().any()
    assert ((C.tt - pd.Timedelta(hours=7)) == pd.to_datetime(C.file_timestamp_utc)).all()
    dm = C.groupby(C.tt.dt.date).CLTT_mean.median(); gh = set(dm[dm < 160].index); g = C.tt.dt.date.isin(gh).to_numpy()
    for v, (sc, of) in SK.items():
        for st in ("mean", "median", "min", "max"):
            if f"{v}_{st}" in C: C.loc[g, f"{v}_{st}"] = (C.loc[g, f"{v}_{st}"] - of) / sc
    for c, lo, hi in (("CLOT_mean", 0, 150), ("CLTT_mean", 180, 315), ("CLTH_mean", 0, 20), ("CLER_23_mean", 0, 100)):
        x = C[c].dropna(); assert ((x >= lo - 1e-6) & (x <= hi + 1e-6)).all(), (s, c)
    p = os.path.join(V6, "00_data", f"{s}_full.parquet"); d0 = pd.read_parquet(p); t = pd.DatetimeIndex(d0.ts_wib)
    X = C.set_index(C.tt + pd.Timedelta(minutes=10)).reindex(t); ada = X.source_file.notna().to_numpy()
    cot = X.CLOT_mean.to_numpy(float); cer = X.CLER_23_mean.to_numpy(float)
    new = {"clp_cot": cot, "clp_cth_km": X.CLTH_mean.to_numpy(float), "clp_ctt_k": X.CLTT_mean.to_numpy(float), "clp_cer_um": np.where(cer == 0, np.nan, cer), "clp_cloud_present_int": np.where(np.isfinite(cot), (cot >= 1).astype(float), np.nan)}
    fill = ada & ~np.isfinite(cot)
    raw = {"clp_cot": np.where(fill, 0.0, cot), "clp_cth_km": np.where(fill, 0.0, X.CLTH_mean.to_numpy(float)), "clp_ctt_k": X.CLTT_mean.to_numpy(float), "clp_cer_um": np.where(fill, 0.0, cer), "clp_cloud_present_int": np.where(fill, 0.0, new["clp_cloud_present_int"])}
    L = dict(pusat=[float(C.station_lat.iloc[0]), float(C.station_lon.iloc[0])], grid=C.grid_size.iloc[0], hari_skala_ganda=len(gh), slot_berkas=int(ada.sum()), slot_retrieval=int(np.isfinite(cot).sum()))
    for var, NEW in (("00_data", new), ("00_data_rawfill", raw)):
        p = os.path.join(V6, var, f"{s}_full.parquet"); d = pd.read_parquet(p); dt = d.dtypes; old = d.copy()
        for c, v in NEW.items(): d[c] = v
        for k, v in turunan(d).items(): d[k] = v.to_numpy()
        for c in d.columns:
            if str(dt[c]) != str(d[c].dtype): d[c] = d[c].astype(dt[c])
        assert list(d.columns) == list(old.columns) and (d.dtypes == dt).all()
        beda = [c for c in d.columns if not c.startswith("clp_") and not d[c].equals(old[c])]; assert not beda, beda
        a, b = old.clp_cot.to_numpy(float), d.clp_cot.to_numpy(float); w = np.isfinite(a) & np.isfinite(b)
        L[var] = dict(cot_sama_dengan_sebelumnya=round(float(np.isclose(a[w], b[w], atol=1e-4).mean()), 4), kini_kosong=int((np.isfinite(a) & ~np.isfinite(b)).sum()), kini_berisi=int((~np.isfinite(a) & np.isfinite(b)).sum()))
        d.to_parquet(p, index=False)
    pv = pd.read_parquet(os.path.join(V6, "provenance", f"{s}_provenance.parquet")); pv["clp_sumber_ulang"] = ada
    if s == "jambi": pv["clp_jambi_asrs"] = ada
    pv.to_parquet(os.path.join(V6, "provenance", f"{s}_provenance.parquet"), index=False)
    LAP[s] = L; print(s, json.dumps(L, ensure_ascii=False), flush=True)
json.dump(LAP, open(os.path.join(HERE, "c6_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("SELESAI")
