# -*- coding: utf-8 -*-
"""Tahap 96: bangun Balai_data_v6_2 dari Balai_data_v6_1 (hanya dibaca) dengan perbaikan F1–F4 (DESAIN_96.md)."""
import os, re, io, json, shutil, zipfile, numpy as np, pandas as pd, pvlib
HERE = os.path.dirname(os.path.abspath(__file__)); V1 = r"C:\Users\ariff\Documents\Balai_data_v6_1"; V2 = r"C:\Users\ariff\Documents\Balai_data_v6_2"
ZIP = r"C:\Users\ariff\Documents\6lokasi_output_chips.zip"
assert not os.path.exists(os.path.join(V2, "SHA256.txt")), "V6.2 sudah beku"
META = dict(banten=(-6.26147, 106.7509, 27), bengkulu=(-3.864930, 102.311998, 9), jambi=(-1.60111, 103.4944, 24), jogja=(-7.731064, 110.353578, 182), kalbar=(0.07489, 109.1905, 2), semarang=(-6.9847, 110.3812, 6))
LOK = {"banten": "sta6016_banten", "bengkulu": "sta6009_bengkulu", "jambi": "sta6007_jambi", "jogja": "sta6010_jogja", "kalbar": "sta6003_kalbar", "semarang": "sta6018_jateng"}
LAP = {}
# salin V6.1 tanpa atribut hanya-baca
if os.path.exists(V2): shutil.rmtree(V2)
shutil.copytree(V1, V2, copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("SHA256.txt", "README.md"))
# ---------- F1 clear-sky Bengkulu (cara d1_clearsky.py tahap 94) ----------
la, lo, alt = META["bengkulu"]; t1 = pd.date_range("2022-01-01 00:00", "2026-01-01 00:59", freq="1min", tz="Etc/GMT-7")
loc = pvlib.location.Location(la, lo, tz="Etc/GMT-7", altitude=alt); lt = pvlib.clearsky.lookup_linke_turbidity(t1, la, lo, interp_turbidity=True)
g = loc.get_clearsky(t1, model="ineichen", linke_turbidity=lt).groupby(t1.floor("10min")).mean()
p = os.path.join(V2, "clearsky", "bengkulu_ineichen.parquet"); old = pd.read_parquet(p); idx = pd.DatetimeIndex(old.ts_wib).tz_localize("Etc/GMT-7"); g = g.reindex(idx); assert g.notna().all().all()
new = pd.DataFrame({"ts_wib": old.ts_wib.values, "ghi_cs": g.ghi.to_numpy(), "dni_cs": g.dni.to_numpy(), "dhi_cs": g.dhi.to_numpy()}); assert list(new.dtypes) == list(old.dtypes); new.to_parquet(p, index=False)
ok = old.ghi_cs.to_numpy() > 50; r = new.ghi_cs.to_numpy()[ok] / old.ghi_cs.to_numpy()[ok]
LAP["F1"] = dict(rasio_median=round(float(np.median(r)), 5), rasio_min=round(float(r.min()), 4), rasio_maks=round(float(r.max()), 4), linke_rerata=round(float(lt.mean()), 4))
pj = os.path.join(V2, "clearsky", "provenance.json"); P = json.load(open(pj, encoding="utf-8"))
P["sites"]["bengkulu"] = dict(latitude=la, longitude=lo, altitude_m=alt, linke_min=float(lt.min()), linke_max=float(lt.max()), catatan="V6.2: koordinat Stasiun Klimatologi Bengkulu dari pengguna (2026-11-08); V6.1 memakai Tabel 1 −3,8607; 102,3381")
json.dump(P, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# ---------- F4 (+F1) bendera QC: logika d2_qc.py tahap 94, ditambah bit 8 ----------
SEK = {"portal", "db", "db_trapesium", "tabel_10min", "lainnya"}; DB_UKUR = {"measured", "measured_qc_corrected"}
def qc(s):
    la, lo, alt = META[s]
    d = pd.read_parquet(os.path.join(V1, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "ghi_wm2", "dhi_wm2", "dni_wm2", "reflected_wm2", "solar_elev_deg"])
    p = pd.read_parquet(os.path.join(V1, "provenance", f"{s}_provenance.parquet"), columns=["ts_wib", "ghi_sumber", "ghi_origin_v2", "dhi_status", "dni_status", "refl_status"])
    idx = pd.DatetimeIndex(d.ts_wib).tz_localize("Etc/GMT-7"); sp = pvlib.solarposition.get_solarposition(idx + pd.Timedelta(minutes=5), la, lo, altitude=alt)
    Z = sp.apparent_zenith.to_numpy(); mu = np.cos(np.radians(Z)); el = 90 - Z; Sa = 1361.0 * (1 + 0.033 * np.cos(2 * np.pi * idx.dayofyear.to_numpy() / 365.0))
    G, Dh, Dn, Rf = (d[c].to_numpy(float) for c in ("ghi_wm2", "dhi_wm2", "dni_wm2", "reflected_wm2"))
    gs, g2, ds, ns, rs = (p[c].astype(str).to_numpy() for c in ("ghi_sumber", "ghi_origin_v2", "dhi_status", "dni_status", "refl_status"))
    qg = np.full(len(d), 9, np.int8); qg[gs == "logger"] = 0
    sek = np.isin(gs, list(SEK)); qg[sek] = 1; qg[sek & (gs == "db") & ~np.isin(g2, list(DB_UKUR))] = 3
    qg[gs == "batas_fisis"] = 2; qg[gs == "estimasi_aws"] = 3; qg[gs == "malam"] = 8
    def kode(st, base):
        q = np.full(len(d), 9, np.int8); a = (st == "asli") | (st == "logger_2022"); q[a] = np.where(st[a] == "logger_2022", 0, base[a])
        q[st == "diperbaiki_tahap85"] = 2; q[np.isin(st, ["model_isi", "hitung_neraca", "albedo"])] = 3; return q
    qd, qn, qr = kode(ds, np.where(qg == 2, 1, qg)), kode(ns, np.where(qg == 2, 1, qg)), kode(rs, np.where(qg == 2, 1, qg))
    mu_t = np.sin(np.radians(d.solar_elev_deg.to_numpy(float)))
    with np.errstate(all="ignore"): tutup = (G > 50) & ((np.abs(G - (Dh + Dn * mu)) < 0.5) | (np.abs(G - (Dh + Dn * mu_t)) < 0.5)) & np.isin(ds, ["asli"]) & np.isin(ns, ["asli"])
    qd[tutup & (qd < 3)] = 3; qn[tutup & (qn < 3)] = 3
    malam = el <= 0
    for q, x in ((qg, G), (qd, Dh), (qn, Dn), (qr, Rf)):
        q[malam & np.isfinite(x)] = 8; q[~np.isfinite(x)] = 9
    u = np.zeros(len(d), np.uint16); dy = mu > 0
    with np.errstate(all="ignore"):
        m12 = np.where(dy, mu, 0) ** 1.2; m02 = np.where(dy, mu, 0) ** 0.2
        tests = [(G < -4) | (G > Sa * 1.5 * m12 + 100), (Dh < -4) | (Dh > Sa * 0.95 * m12 + 50), (Dn < -4) | (Dn > Sa), (G > Sa * 1.2 * m12 + 50), (Dh > Sa * 0.75 * m12 + 30), (Dn > Sa * 0.95 * m02 + 10)]
        ratio = G / (Dh + Dn * mu); cmp = (G > 50) & (((Z < 75) & (np.abs(ratio - 1) > 0.08)) | ((Z >= 75) & (Z < 93) & (np.abs(ratio - 1) > 0.15)))
        dif = (G > 50) & (((Z < 75) & (Dh / G > 1.05)) | ((Z >= 75) & (Z < 93) & (Dh / G > 1.10)))
        kdr = (el > 30) & (G > 300) & (Dh / G < 0.1)                                     # bit 8 (V6.2): k_d < 0,1 tidak fisis di atmosfer tropis
    for b, t in enumerate(tests + [cmp, dif, kdr]): u[dy & np.nan_to_num(t, nan=False).astype(bool)] |= np.uint16(1 << b)
    return pd.DataFrame({"ts_wib": d.ts_wib.values, "qc_ghi": qg, "qc_dhi": qd, "qc_dni": qn, "qc_refl": qr, "qc_uji": u}), el
LAP["F4"] = {}
for s in META:
    Q, el = qc(s); o = pd.read_parquet(os.path.join(V1, "qc", f"{s}_qc.parquet"))
    sama = {c: bool((Q[c].to_numpy() == o[c].to_numpy()).all()) for c in ("qc_ghi", "qc_dhi", "qc_dni", "qc_refl")}; sama["qc_uji_bit0_7"] = bool(((Q.qc_uji.to_numpy() & 0xFF) == o.qc_uji.to_numpy().astype(np.uint16)).all())
    beda = int(((Q.qc_uji.to_numpy() & 0xFF) != o.qc_uji.to_numpy().astype(np.uint16)).sum())
    if s != "bengkulu": assert all(sama.values()), (s, sama)
    Q.to_parquet(os.path.join(V2, "qc", f"{s}_qc.parquet"), index=False)
    b8 = ((Q.qc_uji.to_numpy() >> 8) & 1).astype(bool)
    LAP["F4"][s] = dict(sama_dengan_v6_1=sama, slot_bit0_7_berubah=beda, bit8_kd_lt0_1=int(b8.sum()), bit8_per_tahun=pd.Series(b8).groupby(pd.DatetimeIndex(Q.ts_wib).year).sum().astype(int).to_dict(),
                        bit8_kode_dhi=pd.Series(Q.qc_dhi.to_numpy()[b8]).value_counts().astype(int).to_dict())
# ---------- F3 lonjakan tekanan ----------
def lonjakan(x, maks=1):
    """Blok 1..maks slot yang melompat > 1,5 hPa lalu kembali (amandemen 1: maks = 6, yaitu ≤ 60 menit)."""
    x = np.asarray(x, float); n = len(x); a = np.r_[np.nan, np.diff(x)]; m = np.zeros(n, bool)
    with np.errstate(invalid="ignore"): big = np.where(np.abs(a) > 1.5)[0]
    for i in big:
        if m[i] or not np.isfinite(x[i - 1]): continue
        for j in range(i + 1, min(i + maks, n - 1) + 1):
            if not np.isfinite(x[j]) or not np.isfinite(a[j]): break
            if abs(a[j]) > 1.5 and np.sign(a[j]) != np.sign(a[i]) and abs(x[j] - x[i - 1]) < 0.5 * min(abs(a[i]), abs(a[j])) and np.all(np.isfinite(x[i:j])):
                m[i:j] = True; break
    return m
LAP["F3"] = {}
for s in META:
    L = {}
    for var in ("00_data", "00_data_rawfill"):
        f = os.path.join(V2, var, f"{s}_full.parquet"); d = pd.read_parquet(f); dt = d.dtypes; old = d.copy()
        x = d.aws_pressure_hpa.to_numpy(float).copy(); m = lonjakan(x, maks=6); m1 = lonjakan(x, maks=1)
        d.loc[m, "aws_pressure_hpa"] = np.nan; P_ = pd.to_numeric(d.aws_pressure_hpa)
        d["aws_pressure_lag_60m"] = P_.shift(6).to_numpy(); d["aws_pressure_delta_60m"] = (P_ - P_.shift(6)).to_numpy()
        for c in d.columns:
            if str(dt[c]) != str(d[c].dtype): d[c] = d[c].astype(dt[c])
        assert list(d.columns) == list(old.columns) and (d.dtypes == dt).all()
        beda = [c for c in d.columns if not d[c].equals(old[c])]; assert set(beda) <= {"aws_pressure_hpa", "aws_pressure_lag_60m", "aws_pressure_delta_60m"}, beda
        ts = pd.DatetimeIndex(d.ts_wib); T = d.aws_temp_c.to_numpy(float); H = d.aws_rh_pct.to_numpy(float)
        L[var] = dict(lonjakan=int(m.sum()), satu_slot=int(m1.sum()), blok_2_6_slot=int((m & ~m1).sum()), per_tahun=pd.Series(m).groupby(ts.year).sum().astype(int).to_dict(), median_besar=round(float(np.median(np.abs(x - (np.r_[np.nan, x[:-1]] + np.r_[x[1:], np.nan]) / 2)[m])), 2) if m.any() else None,
                      suhu_ikut_lonjak=int((m & (np.abs(T - np.r_[np.nan, T[:-1]]) > 2)).sum()), rh_ikut_lonjak=int((m & (np.abs(H - np.r_[np.nan, H[:-1]]) > 10)).sum()))
        d.to_parquet(f, index=False)
        if var == "00_data": M0 = m
    pv = os.path.join(V2, "provenance", f"{s}_provenance.parquet"); P_ = pd.read_parquet(pv); P_["aws_lonjakan_tekanan"] = M0; P_.to_parquet(pv, index=False)
    LAP["F3"][s] = L
# ---------- F2 fraksi awan dan zenit CLP ----------
z = zipfile.ZipFile(ZIP); NM = z.namelist(); os.makedirs(os.path.join(V2, "clp_ekstra"), exist_ok=True); LAP["F2"] = {}
for s, site in LOK.items():
    la, lo, alt = META[s]
    F = sorted(n for n in NM if re.search(rf"{site}/CLP_{site}_\d{{4}}-\d\d-\d\d\.csv$", n)); assert len(F) == 1461
    C = pd.concat([pd.read_csv(io.BytesIO(z.read(n))).reindex(columns=["timestamp", "file_timestamp_utc", "source_file", "total_pixels", "CLOT_count"]) for n in F], ignore_index=True)
    C["tt"] = pd.to_datetime(C.timestamp); assert not C.tt.duplicated().any()
    d = pd.read_parquet(os.path.join(V2, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "clp_cot"]); t = pd.DatetimeIndex(d.ts_wib)
    X = C.set_index(C.tt + pd.Timedelta(minutes=10)).reindex(t); ada = X.source_file.notna().to_numpy()
    tot = X.total_pixels.to_numpy(float); assert np.all(np.isin(tot[ada], [110, 121]))
    frac = np.where(ada, np.nan_to_num(X.CLOT_count.to_numpy(float), nan=0.0) / tot, np.nan)
    tu = pd.DatetimeIndex(pd.to_datetime(X.file_timestamp_utc)); sza = np.full(len(t), np.nan)
    sp = pvlib.solarposition.get_solarposition(tu[ada].tz_localize("UTC") + pd.Timedelta(minutes=5), la, lo, altitude=alt); sza[ada] = sp.zenith.to_numpy()
    q = np.full(len(t), 9, np.int8); q[ada & (sza < 70)] = 0; q[ada & (sza >= 70) & (sza < 80)] = 1; q[ada & (sza >= 80)] = 2
    frac00 = np.where(q == 2, np.nan, frac)
    cot = d.clp_cot.to_numpy(float); cek = bool(np.all(frac[np.isfinite(cot)] > 0))
    E = pd.DataFrame({"ts_wib": d.ts_wib.values, "clp_cloud_frac": frac00, "clp_cloud_frac_raw": frac, "clp_sza_scan_deg": sza, "qc_clp_sza": q})
    E.to_parquet(os.path.join(V2, "clp_ekstra", f"{s}_clp_ekstra.parquet"), index=False)
    LAP["F2"][s] = dict(slot_berkas=int(ada.sum()), frac_isi=int(np.isfinite(frac00).sum()), qc_sza=pd.Series(q).value_counts().sort_index().astype(int).to_dict(), cot_ada_selalu_frac_gt0=cek,
                        frac_median_siang=round(float(np.nanmedian(frac00[q == 0])), 3), frac_nol_siang=round(float(np.mean(frac00[q == 0] == 0)), 3))
    print("F2", s, LAP["F2"][s], flush=True)
json.dump(LAP, open(os.path.join(HERE, "f1_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: v for k, v in LAP.items() if k != "F2"}, ensure_ascii=False, indent=1, default=str)); print("SELESAI")
