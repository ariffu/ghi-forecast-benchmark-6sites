# -*- coding: utf-8 -*-
"""Tahap 93 P5: CLP Jambi dari kotak 11×11 berpusat di ASRS (sta6007_jambi.zip, CSV CLP_sta6007_jambi_YYYY-MM-DD.csv).
Skala ganda dibalik, t = T + 10, konvensi kosong V5 (00_data) dan rawfill, turunan CLP dihitung ulang.
Bila unduhan belum lengkap 1.461 hari, skrip berjalan KERING: hasil ke scratchpad, V6 tidak disentuh.
Jalankan: python c3_clp_jambi.py [lokasi_zip]"""
import os, re, io, sys, json, zipfile, numpy as np, pandas as pd
pd.set_option("display.width", 240); pd.set_option("display.max_columns", 40)
HERE = os.path.dirname(os.path.abspath(__file__)); ZIP = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\ariff\Documents\sta6007_jambi.zip"
V5 = r"C:\Users\ariff\Documents\Balai_data_v5_final87"; V6 = r"C:\Users\ariff\Documents\Balai_data_v6"
KERING_DIR = os.environ.get("KERING_DIR", os.path.join(HERE, "_kering"))
SK = {"CLOT": (0.01, 0.0), "CLTT": (0.01, 150.0), "CLTH": (0.001, 0.0), "CLER_23": (0.01, 0.0)}
z = zipfile.ZipFile(ZIP); F = sorted((re.search(r"(\d{4}-\d\d-\d\d)", n).group(1), n) for n in z.namelist() if re.search(r"CLP_sta6007_jambi_\d{4}-\d\d-\d\d\.csv$", n))
hari = pd.to_datetime([a for a, _ in F]); lengkap = len(hari) == 1461 and hari.min() == pd.Timestamp("2022-01-01") and hari.max() == pd.Timestamp("2025-12-31")
print(f"CSV baru: {len(F)} hari, {hari.min().date()}–{hari.max().date()}, lengkap {lengkap}")
L = [pd.read_csv(io.BytesIO(z.read(n))) for _, n in F]; C = pd.concat(L, ignore_index=True); C["tt"] = pd.to_datetime(C.timestamp)
assert C.station_lat.round(3).eq(-1.602).all() and C.station_lon.round(3).eq(103.485).all() and C.grid_size.eq("11x11").all(), "pusat atau ukuran kotak tidak sesuai"
assert ((C.tt - pd.Timedelta(hours=7)) == pd.to_datetime(C.file_timestamp_utc)).all() and not C.tt.duplicated().any()
# skala ganda: per hari, median CTT < 160 K mustahil secara fisis
dmed = C.groupby(C.tt.dt.date).CLTT_mean.median(); ganda_hari = set(dmed[dmed < 160].index); g = C.tt.dt.date.isin(ganda_hari).to_numpy()
print("hari skala ganda:", len(ganda_hari), "mulai", min(ganda_hari) if ganda_hari else None, "| hari normal:", int((dmed >= 160).sum()))
for v, (sc, of) in SK.items():
    for st in ("mean", "median", "min", "max"):
        c = f"{v}_{st}"
        if c in C: C.loc[g, c] = (C.loc[g, c] - of) / sc
    if f"{v}_std" in C: C.loc[g, f"{v}_std"] = C.loc[g, f"{v}_std"] / sc
for c, lo, hi in (("CLOT_mean", 0, 150), ("CLTT_mean", 180, 315), ("CLTH_mean", 0, 20), ("CLER_23_mean", 0, 100)):
    x = C[c].dropna(); bad = int(((x < lo - 1e-6) | (x > hi + 1e-6)).sum()); print(f"  {c}: p1 {x.quantile(.01):.2f} p50 {x.median():.2f} p99 {x.quantile(.99):.2f}, di luar [{lo},{hi}] {bad}"); assert bad == 0
q = C.CLTT_mean.notna() & C.CLTH_mean.notna(); r = np.corrcoef(C.CLTT_mean[q], C.CLTH_mean[q])[0, 1]; print("  r CTT–CTH", round(r, 3)); assert r < -0.95
# ke grid V5: t = T + 10
B5 = pd.read_parquet(os.path.join(V5, "00_data", "jambi_full.parquet")); R5 = pd.read_parquet(os.path.join(V5, "00_data_rawfill", "jambi_full.parquet")); t = pd.DatetimeIndex(B5.ts_wib)
X = C.set_index(C.tt + pd.Timedelta(minutes=10)).reindex(t); ada = X.source_file.notna().to_numpy()
cot = X.CLOT_mean.to_numpy(float); cer = X.CLER_23_mean.to_numpy(float); cer = np.where(cer == 0, np.nan, cer)
baru = {"clp_cot": cot, "clp_cth_km": X.CLTH_mean.to_numpy(float), "clp_ctt_k": X.CLTT_mean.to_numpy(float), "clp_cer_um": cer, "clp_cloud_present_int": np.where(np.isfinite(cot), (cot >= 1).astype(float), np.nan)}
# konvensi rawfill V5: lihat apa yang diisikan pada slot yang kosong di 00_data
m = B5.clp_cot.isna() & R5.clp_cot.notna(); conv = {c: R5.loc[m, c].value_counts(dropna=False).head(3).to_dict() for c in ("clp_cot", "clp_cth_km", "clp_ctt_k", "clp_cer_um", "clp_cloud_present_int")}
print("konvensi rawfill V5 pada slot kosong:", conv)
isi_raw = {"clp_cot": 0.0, "clp_cth_km": 0.0, "clp_cer_um": 0.0, "clp_cloud_present_int": 0.0, "clp_ctt_k": None}   # sesuai konvensi rawfill V5 di atas; CTT rawfill tidak konstan dan bukan prediktor → kosong
fill = ada & ~np.isfinite(cot)                         # berkas ada, tidak ada retrieval
raw = {c: np.where(fill, isi_raw[c] if isi_raw[c] is not None else np.nan, v) for c, v in baru.items()}
def turunan(d):
    Co, Ct = pd.to_numeric(d.clp_cot), pd.to_numeric(d.clp_cth_km)
    return {"clp_cot_lag_60m": Co.shift(6), "clp_cot_delta_60m": Co - Co.shift(6), "clp_cot_roll_180m_mean": Co.rolling(18, min_periods=1).mean(), "clp_cth_lag_60m": Ct.shift(6), "clp_cth_roll_180m_mean": Ct.rolling(18, min_periods=1).mean()}
src = os.path.join(V6, "00_data", "jambi_full.parquet")
if not os.path.exists(src): src = os.path.join(V5, "00_data", "jambi_full.parquet")
outdir = os.path.join(V6, "00_data") if lengkap else os.path.join(KERING_DIR, "00_data"); os.makedirs(outdir, exist_ok=True)
rdir = os.path.join(V6, "00_data_rawfill") if lengkap else os.path.join(KERING_DIR, "00_data_rawfill"); os.makedirs(rdir, exist_ok=True)
lap = {}
for lab, path, new, od in (("00_data", src, baru, outdir), ("00_data_rawfill", src.replace("00_data", "00_data_rawfill"), raw, rdir)):
    d = pd.read_parquet(path); dt = d.dtypes; old = d.copy()
    cak = ada if lengkap else ada                          # kering: hanya periode yang sudah terunduh diganti
    for c, v in new.items(): d[c] = np.where(cak, v, d[c].to_numpy(float) if lengkap is False else np.nan)
    for k, v in turunan(d).items(): d[k] = v.to_numpy()
    for c in d.columns:
        if str(dt[c]) != str(d[c].dtype): d[c] = d[c].astype(dt[c])
    assert list(d.columns) == list(old.columns) and (d.dtypes == dt).all()
    beda = [c for c in d.columns if not c.startswith("clp_") and not d[c].equals(old[c])]; assert not beda, beda
    day = (d.solar_elev_deg > 5).to_numpy()
    w = day & np.isfinite(old.clp_cot.to_numpy(float)) & np.isfinite(d.clp_cot.to_numpy(float)) & cak
    lap[lab] = dict(slot_diganti=int(cak.sum()), r_cot_lawan_kotak_lama=round(float(np.corrcoef(old.clp_cot[w], d.clp_cot[w])[0, 1]), 3), kosong_siang_lama=round(float(np.isnan(old.clp_cot.to_numpy(float))[day & cak].mean()), 4), kosong_siang_baru=round(float(np.isnan(d.clp_cot.to_numpy(float))[day & cak].mean()), 4),
                    isi_menurut_elevasi=pd.Series(np.isfinite(d.clp_cot.to_numpy(float))[cak]).groupby(pd.cut(d.solar_elev_deg[cak], [5, 7.5, 10, 15, 90]).to_numpy(), observed=True).mean().round(3).rename(index=str).to_dict())
    d.to_parquet(os.path.join(od, "jambi_full.parquet"), index=False)
print(json.dumps(lap, ensure_ascii=False, indent=1))
if lengkap:
    pv = pd.read_parquet(os.path.join(V6, "provenance", "jambi_provenance.parquet")); pv["clp_jambi_asrs"] = ada; pv.to_parquet(os.path.join(V6, "provenance", "jambi_provenance.parquet"), index=False)
    print("P5 diterapkan ke V6.")
else: print("KERING: unduhan belum lengkap; hasil di", KERING_DIR, "— V6 tidak diubah.")
json.dump(lap, open(os.path.join(HERE, "c3_laporan.json" if lengkap else "c3_laporan_kering.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
