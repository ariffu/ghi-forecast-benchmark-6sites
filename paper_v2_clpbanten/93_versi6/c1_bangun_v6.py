# -*- coding: utf-8 -*-
"""Tahap 93: bangun Balai_data_v6 dari Balai_data_v5_final87 dengan perbaikan P1–P4 (DESAIN_93.md). P5 (CLP Jambi) menyusul lewat c3.
Membaca V5 dan DB v2 hanya-baca; menulis folder baru."""
import os, json, shutil, duckdb, numpy as np, pandas as pd
pd.set_option("display.width", 240); pd.set_option("display.max_columns", 40)
HERE = os.path.dirname(os.path.abspath(__file__)); V5 = r"C:\Users\ariff\Documents\Balai_data_v5_final87"; V6 = r"C:\Users\ariff\Documents\Balai_data_v6"
DB = r"C:\Users\ariff\Documents\Balai Obsidian\Balai\solardata_new_v2\solar_harmonised_clpbanten_v2.duckdb"
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; TOL = 0.006; MAXAGE = 18
assert not os.path.exists(os.path.join(V6, "SHA256.txt")), "V6 sudah dibekukan; jangan ditimpa"
for sub in ("00_data", "00_data_rawfill", "provenance"): os.makedirs(os.path.join(V6, sub), exist_ok=True)
num = lambda d, c: pd.to_numeric(d[c], errors="coerce").astype("float64")
def turunan_lain(d):                                     # salinan definisi 86_basis_final.turunan_lain
    T, H, P, W, Rn, Co, Ct = (num(d, c) for c in ("aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_rain_mm", "clp_cot", "clp_cth_km")); o = {}
    for m, k in ((10, 1), (30, 3), (60, 6)): o[f"aws_temp_lag_{m}m"] = T.shift(k)
    o["aws_temp_delta_60m"] = T - T.shift(6); o["aws_temp_roll_180m_mean"] = T.rolling(18, min_periods=1).mean(); o["aws_rh_lag_60m"] = H.shift(6); o["aws_rh_delta_60m"] = H - H.shift(6); o["aws_rh_roll_180m_mean"] = H.rolling(18, min_periods=1).mean()
    o["aws_pressure_lag_60m"] = P.shift(6); o["aws_pressure_delta_60m"] = P - P.shift(6); o["aws_wind_speed_roll_180m_mean"] = W.rolling(18, min_periods=1).mean(); o["aws_rain_sum_180m"] = Rn.rolling(18, min_periods=1).sum()
    o["clp_cot_lag_60m"] = Co.shift(6); o["clp_cot_delta_60m"] = Co - Co.shift(6); o["clp_cot_roll_180m_mean"] = Co.rolling(18, min_periods=1).mean(); o["clp_cth_lag_60m"] = Ct.shift(6); o["clp_cth_roll_180m_mean"] = Ct.rolling(18, min_periods=1).mean()
    return o
def resolusi(a):
    x = a[np.isfinite(a)][:200000]
    for r in (1.0, 0.1, 0.01):
        if np.mean(np.abs(x / r - np.round(x / r)) < 1e-6) > 0.95: return r
    return 0.0
def blok(a, TOL=TOL):
    n = len(a); H = np.arange(0, n, 6); hv = a[H]; nh = len(H); lin_full = np.zeros(nh, bool)
    p, q, m = hv[:-2], hv[2:], hv[1:-1]; lin_full[1:-1] = np.isfinite(p) & np.isfinite(q) & np.isfinite(m) & (np.abs(q - p) > TOL) & (np.abs(m - (p + q) / 2) < TOL)
    obs = np.zeros(n, bool); obs[H] = np.isfinite(hv) & ~lin_full; interp = np.zeros(n, bool)
    v0, v1 = hv[:-1], hv[1:]; ok = np.isfinite(v0) & np.isfinite(v1) & (np.abs(v1 - v0) > TOL)
    seg = np.stack([a[H[:-1] + k] if (H[:-1] + k < n).all() else np.r_[a[H[:-2] + k], np.nan] for k in range(1, 6)], 1)
    lin = np.stack([v0 + (v1 - v0) * k / 6 for k in range(1, 6)], 1); on = ok & np.isfinite(seg).all(1) & (np.abs(seg - lin) < TOL).all(1)
    for k in range(1, 6): interp[H[:-1][on] + k] = True
    interp[H[lin_full]] = True
    return obs, interp
def kausal(a, idx, ct=None):
    tol = max(0.006, resolusi(a) / 2 + 0.001); obs, interp = blok(a, tol); n = len(a); pos = np.maximum.accumulate(np.where(obs, np.arange(n), -1)); age = np.where(pos >= 0, np.arange(n) - pos, 10 ** 9)
    anc = np.where(pos >= 0, a[np.clip(pos, 0, None)], np.nan)
    if ct is not None:
        key = idx.month * 1440 + idx.hour * 60 + idx.minute; c = pd.Series(key).map(ct).to_numpy(float); c0 = np.where(pos >= 0, c[np.clip(pos, 0, None)], np.nan); anc = anc + (c - c0)
    val = np.where(age <= MAXAGE, anc, np.nan); return np.where(interp, val, a), interp
def clim(a, idx):
    m = idx.year <= 2023; key = idx.month * 1440 + idx.hour * 60 + idx.minute; return pd.Series(a[m]).groupby(key[m]).mean()
con = duckdb.connect(DB, read_only=True)
st = con.execute("select ts_wib, clp_qc_status from bengkulu.ghi_forecast_1h_train_3h_rollback_2021_2025").df().drop_duplicates("ts_wib").set_index("ts_wib").clp_qc_status
CLPB = ["clp_cot", "clp_cth_km", "clp_ctt_k", "clp_cer_um", "clp_cloud_present_int"]; LAP = {}
for s in S:
    L = {}; out = {}
    for var in ("00_data", "00_data_rawfill"):
        d = pd.read_parquet(os.path.join(V5, var, f"{s}_full.parquet")); dt = d.dtypes; assert d.ts_wib.is_monotonic_increasing; idx = pd.DatetimeIndex(d.ts_wib); day = (d.solar_elev_deg > 5).to_numpy()
        if var == "00_data":                              # definisi turunan harus mereproduksi V5 lebih dulu
            o = turunan_lain(d); L["definisi_cocok"] = {k: round(float(np.isclose(v, num(d, k), atol=1e-6, equal_nan=True).mean()), 6) for k, v in o.items()}
        n = d.copy(); fl = {}
        for c, f in (("aws_temp_c", "suhu"), ("aws_rh_pct", "rh"), ("aws_pressure_hpa", "tekanan")):
            a = num(d, c).to_numpy(); y, it = kausal(a, idx, clim(a, idx))
            if c == "aws_rh_pct": y = np.clip(y, 0, 100)
            n[c] = y; fl[f"aws_kausal_{f}"] = it; L[f"{var}:{f}_diganti_siang"] = round(float(it[day & (idx.minute != 0)].mean()), 4)
        a = num(d, "aws_wind_speed_ms").to_numpy(); y, i1 = kausal(a, idx); n["aws_wind_speed_ms"] = y
        a = num(d, "aws_wind_dir_deg").to_numpy(); y, i2 = kausal(a, idx); n["aws_wind_dir_deg"] = y
        r = np.radians(n.aws_wind_dir_deg.to_numpy(float)); n["aws_wind_dir_sin"] = np.where(i2, np.sin(r), d.aws_wind_dir_sin); n["aws_wind_dir_cos"] = np.where(i2, np.cos(r), d.aws_wind_dir_cos)
        fl["aws_kausal_angin"] = i1 | i2; L[f"{var}:angin_diganti_siang"] = round(float((i1 | i2)[day & (idx.minute != 0)].mean()), 4)
        if var == "00_data":
            gg = np.zeros(len(d), bool)
            if s == "bengkulu":
                s_ = st.reindex(idx - pd.Timedelta(minutes=10)).to_numpy(); gg = (s_ == "fail_clp_sentinel_or_missing") & num(d, "clp_cot").notna().to_numpy()
                for c in CLPB: n[c] = np.where(gg, np.nan, num(d, c))
            fl["clp_gagal_dikosongkan"] = gg; L["clp_gagal_dikosongkan"] = int(gg.sum()); L["clp_gagal_dikosongkan_siang"] = int((gg & day).sum())
            z = (num(n, "clp_cer_um") == 0).to_numpy(); n["clp_cer_um"] = np.where(z, np.nan, num(n, "clp_cer_um")); fl["cer_nol_dikosongkan"] = z; L["cer_nol_dikosongkan"] = int(z.sum())
        o = turunan_lain(n)
        for k, v in o.items():
            if var == "00_data_rawfill" and k.startswith("clp_"): continue
            n[k] = v.to_numpy()
        for c in n.columns:
            if str(dt[c]) != str(n[c].dtype): n[c] = n[c].astype(dt[c])
        assert list(n.columns) == list(d.columns) and (n.dtypes == dt).all()
        # kolom yang tidak boleh berubah
        diubah = {"aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_wind_dir_deg", "aws_wind_dir_sin", "aws_wind_dir_cos"} | set(o) | (set(CLPB) if var == "00_data" else set())
        beda = [c for c in d.columns if c not in diubah and not d[c].equals(n[c])]; L[f"{var}:kolom_lain_berubah"] = beda
        n.to_parquet(os.path.join(V6, var, f"{s}_full.parquet"), index=False); out[var] = fl
    pv = pd.read_parquet(os.path.join(V5, "provenance", f"{s}_provenance.parquet"))
    for k, v in out["00_data"].items(): pv[k] = v
    pv["clp_jambi_asrs"] = False; pv.to_parquet(os.path.join(V6, "provenance", f"{s}_provenance.parquet"), index=False)
    LAP[s] = L; print(s, json.dumps(L, ensure_ascii=False), flush=True)
for f in ("provenance.json",):
    p = os.path.join(V5, "00_data", f)
    if os.path.exists(p): shutil.copyfile(p, os.path.join(V6, "00_data", f))
json.dump(LAP, open(os.path.join(HERE, "c1_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("SELESAI")
