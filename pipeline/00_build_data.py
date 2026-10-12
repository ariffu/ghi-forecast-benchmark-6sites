# -*- coding: utf-8 -*-
"""Tahap 00 — Integritas DB + rekonstruksi frame model (124 kolom) per situs dari
solar_harmonised_clpbanten_v2.duckdb (D21, data utama 6 situs).

Kontrak: hanya membaca std.* (read-only). DB v2 tidak lagi menyediakan view
std.model_base_10min_full; frame direkonstruksi dengan SQL yang IDENTIK dengan
definisi view lama di solar_new.duckdb:
  model_base_10min_signal  LEFT JOIN synop_canonical_10min (site_id, ts_wib)
  + lag/roll AWS & CLP (window sama)  + ghi_actual_h1..h6 = lead(ghi_wm2, 6k)
Urutan kolom disamakan dengan view lama agar urutan fitur model identik.
Output: 00_data/{site}_full.parquet, 00_data/qc_build.csv, 00_data/qc_vs_old.csv
Jalankan: python -u 00_build_data.py
"""
import os, hashlib, json, time, duckdb, numpy as np, pandas as pd
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("GHI_DB", "")
if not DB: raise SystemExit("Set env var GHI_DB to the path of the harmonised DuckDB database (std.* schema) (opened read-only).")
DB_OLD = os.environ.get("GHI_DB_OLD", "")
if not DB_OLD: raise SystemExit("Set env var GHI_DB_OLD to the path of the earlier DuckDB database used for the cell-by-cell comparison (opened read-only).")
SHA_EXPECT = "6b71844ccbe1bb952cd846eef07be4617eadcad0bd77e92772228c1f75539dd8"
OUT = os.path.join(BASE, "00_data"); os.makedirs(OUT, exist_ok=True)
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
def log(*a): print(*a, flush=True)

# ---- 1. integritas berkas ----
t0 = time.time(); h = hashlib.sha256()
with open(DB, "rb") as f:
    for blk in iter(lambda: f.read(1 << 24), b""): h.update(blk)
sha = h.hexdigest(); log(f"SHA-256 = {sha}  ({time.time()-t0:.0f}s)")
assert sha == SHA_EXPECT, "checksum DB TIDAK cocok dengan berkas .sha256 - hentikan"
mtime0 = os.path.getmtime(DB)

# KEBIJAKAN CLP (std.feature_usage_policy: use_with_flag): pada DB v2, slot tanpa retrieval
# satelit di 5 situs diisi COT=0/CTH=0 (isian, bukan observasi), sedangkan Banten v2 = NULL.
# Agar seragam & fisis: kolom CLP mentah di-NULL-kan bila clp_retrieval_ok bukan TRUE,
# SEBELUM lag/roll dihitung. Set MASK_CLP=0 (env) untuk varian sensitivitas "isian mentah".
MASK_CLP = os.environ.get("MASK_CLP", "1") == "1"
CLP_RAW = ["clp_cot", "clp_cth_km", "clp_ctt_k", "clp_cer_um", "clp_cloud_present_int"]
# CLOUD FLAG (audit M6, 2026-10-12; LAPORAN §31): clp_cloud_present_int di DB v2 TIDAK seragam antarsitus —
# Banten = [COT_mean_box >= 0.5], Bengkulu TERBALIK (1 bila COT <= 1), 4 situs lain = [COT_mean_box >= 1].
# Diseragamkan: flag = [clp_cot >= 1] dihitung ulang dari COT rata-rata kotak, NULL bila COT NULL (setelah masking).
FLAG_SQL = "CASE WHEN {c} IS NOT NULL THEN CAST({c} >= 1 AS INTEGER) END"
if MASK_CLP:
    REPL = ", ".join(f"CASE WHEN coalesce(f.clp_retrieval_ok, FALSE) THEN m.{c} END AS {c}" for c in CLP_RAW if c != "clp_cloud_present_int")
    REPL += ", CASE WHEN coalesce(f.clp_retrieval_ok, FALSE) THEN " + FLAG_SQL.format(c="m.clp_cot") + " END AS clp_cloud_present_int"
    SIGNAL = (f"(SELECT m.* REPLACE ({REPL}) FROM std.model_base_10min_signal m "
              "LEFT JOIN (SELECT site_id, CAST(timestamp_wib AS TIMESTAMP) AS ts_wib, clp_retrieval_ok "
              "FROM std.master_10min_all) f USING (site_id, ts_wib))")
else:
    SIGNAL = ("(SELECT m.* REPLACE (" + FLAG_SQL.format(c="m.clp_cot") + " AS clp_cloud_present_int) "
              "FROM std.model_base_10min_signal m)")
OUT = os.path.join(BASE, "00_data" if MASK_CLP else "00_data_rawfill"); os.makedirs(OUT, exist_ok=True)
log(f"MASK_CLP={MASK_CLP} -> {OUT}")
# KONVENSI WAKTU CLP (keputusan B, 2026-10-03; lihat 31_clp_lag_sensitivity.py & LAPORAN §13):
# label CLP = waktu nominal file Himawari (awal scan; Indonesia terpindai ±5 menit kemudian). Di std view DB v2,
# Kalbar memakai label T-10 pada origin T, 5 situs lain label T. Diseragamkan KONSERVATIF: semua situs label T-10
# (geser 10 kolom CLP +1 slot pada 5 situs), sehingga tidak ada informasi satelit yang lebih baru dari origin.
# HARMONISE_CLP=0 mereproduksi konvensi campuran lama (V0).
HARMONISE = os.environ.get("HARMONISE_CLP", "1") == "1"
CLP10 = ["clp_cot", "clp_cth_km", "clp_ctt_k", "clp_cer_um", "clp_cloud_present_int",
         "clp_cot_lag_60m", "clp_cot_delta_60m", "clp_cot_roll_180m_mean", "clp_cth_lag_60m", "clp_cth_roll_180m_mean"]
CLP_ALREADY_LAGGED = {"kalbar"}
log(f"HARMONISE_CLP={HARMONISE} (situs yang digeser +1 slot: {sorted(set(SITES) - CLP_ALREADY_LAGGED) if HARMONISE else '-'})")

SQL = """
WITH s AS (
  SELECT m.*, s.synop_temp_c, s.synop_dewpoint_c, s.synop_rh_pct, s.synop_pressure_hpa,
         s.synop_wind_dir_deg, s.synop_wind_speed_kt, s.synop_visibility_km, s.synop_cloud_cover_oktas,
         s.synop_cl, s.synop_cm, s.synop_ch, s.synop_present_weather_ww, s.synop_rainfall_24h_mm, s.synop_sunshine_h
  FROM __SIGNAL__ AS m
  LEFT JOIN std.synop_canonical_10min AS s USING (site_id, ts_wib)
  WHERE m.site_id = ?),
b AS (
  SELECT *,
    lead(ghi_wm2, 6)  OVER w AS ghi_actual_h1, lead(ghi_wm2, 12) OVER w AS ghi_actual_h2,
    lead(ghi_wm2, 18) OVER w AS ghi_actual_h3, lead(ghi_wm2, 24) OVER w AS ghi_actual_h4,
    lead(ghi_wm2, 30) OVER w AS ghi_actual_h5, lead(ghi_wm2, 36) OVER w AS ghi_actual_h6,
    lag(aws_temp_c, 1) OVER w AS _t1, lag(aws_temp_c, 3) OVER w AS _t3, lag(aws_temp_c, 6) OVER w AS _t6,
    avg(aws_temp_c) OVER (w ROWS BETWEEN 17 PRECEDING AND CURRENT ROW) AS _tr,
    lag(aws_rh_pct, 6) OVER w AS _r6,
    avg(aws_rh_pct) OVER (w ROWS BETWEEN 17 PRECEDING AND CURRENT ROW) AS _rr,
    lag(aws_pressure_hpa, 6) OVER w AS _p6,
    avg(aws_wind_speed_ms) OVER (w ROWS BETWEEN 17 PRECEDING AND CURRENT ROW) AS _wr,
    sum(aws_rain_mm) OVER (w ROWS BETWEEN 17 PRECEDING AND CURRENT ROW) AS _rain,
    lag(clp_cot, 6) OVER w AS _c6,
    avg(clp_cot) OVER (w ROWS BETWEEN 17 PRECEDING AND CURRENT ROW) AS _cr,
    lag(clp_cth_km, 6) OVER w AS _h6,
    avg(clp_cth_km) OVER (w ROWS BETWEEN 17 PRECEDING AND CURRENT ROW) AS _hr
  FROM s WINDOW w AS (PARTITION BY site_id ORDER BY ts_wib))
SELECT b.* EXCLUDE (_t1,_wr,_t3,_t6,_tr,_rr,_r6,_p6,_rain,_c6,_cr,_h6,_hr),
  _t1 AS aws_temp_lag_10m, _t3 AS aws_temp_lag_30m, _t6 AS aws_temp_lag_60m,
  (aws_temp_c - _t6) AS aws_temp_delta_60m, _tr AS aws_temp_roll_180m_mean,
  _r6 AS aws_rh_lag_60m, (aws_rh_pct - _r6) AS aws_rh_delta_60m, _rr AS aws_rh_roll_180m_mean,
  _p6 AS aws_pressure_lag_60m, (aws_pressure_hpa - _p6) AS aws_pressure_delta_60m,
  _wr AS aws_wind_speed_roll_180m_mean, _rain AS aws_rain_sum_180m,
  _c6 AS clp_cot_lag_60m, (clp_cot - _c6) AS clp_cot_delta_60m, _cr AS clp_cot_roll_180m_mean,
  _h6 AS clp_cth_lag_60m, _hr AS clp_cth_roll_180m_mean
FROM b ORDER BY ts_wib
""".replace("__SIGNAL__", SIGNAL)
old = duckdb.connect(DB_OLD, read_only=True)
OLD_COLS = [r[0] for r in old.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='std' "
                                       "AND table_name='model_base_10min_full' ORDER BY ordinal_position").fetchall()]
con = duckdb.connect(DB, read_only=True)
# duplikat kunci SYNOP akan menggandakan baris -> wajib dicek
dup = con.execute("SELECT site_id, count(*) - count(DISTINCT ts_wib) FROM std.synop_canonical_10min GROUP BY 1").fetchall()
log("duplikat kunci synop_canonical_10min:", dup); assert all(d[1] == 0 for d in dup)

KEY = ["ghi_wm2", "kt", "clp_cot", "clp_cth_km", "clp_ctt_k", "clp_cer_um", "aws_temp_c", "aws_rh_pct",
       "synop_cloud_cover_oktas", "ghi_actual_h1", "smart_persist_h1"]
qc, cmp = [], []
for site in SITES:
    t1 = time.time()
    df = con.execute(SQL, [site]).df()
    assert set(df.columns) == set(OLD_COLS), (set(df.columns) ^ set(OLD_COLS))
    df = df[OLD_COLS]
    # cek target terhadap view resmi DB v2 (target_ghi_h1, target_ghi_mean_1h)
    tg = con.execute("SELECT ts_wib, target_ghi_h1 FROM std.model_base_10min_targets WHERE site_id=? ORDER BY ts_wib", [site]).df()
    tm = con.execute("SELECT CAST(timestamp_wib AS TIMESTAMP) AS ts_wib, target_ghi_mean_1h FROM std.master_10min_all "
                     "WHERE site_id=? ORDER BY 1", [site]).df()
    chk = df[["ts_wib", "ghi_actual_h1", "ghi_wm2"]].merge(tg, on="ts_wib", how="left").merge(tm, on="ts_wib", how="left")
    d_h1 = np.nanmax(np.abs(chk.ghi_actual_h1 - chk.target_ghi_h1))
    g = chk.ghi_wm2.to_numpy(float); M = np.full((len(g), 6), np.nan)
    for k in range(1, 7): M[:-k, k-1] = g[k:]
    ym = np.where(np.isnan(M).any(1), np.nan, M.mean(1))
    both = ~np.isnan(ym) & chk.target_ghi_mean_1h.notna().to_numpy()
    d_mean = float(np.max(np.abs(ym[both] - chk.target_ghi_mean_1h.to_numpy(float)[both]))) if both.any() else np.nan
    _f, _c = df.clp_cloud_present_int, df.clp_cot                                  # cek flag seragam (M6)
    assert (_f.isna() == _c.isna()).all() and (_f[_c.notna()] == (_c[_c.notna()] >= 1).astype(int)).all(), f"{site}: flag CLP tidak seragam"
    if HARMONISE and site not in CLP_ALREADY_LAGGED:
        assert df.ts_wib.diff().dropna().eq(pd.Timedelta(minutes=10)).all()      # grid lengkap -> shift 1 baris = 10 menit
        df[CLP10] = df[CLP10].shift(1)
    p = os.path.join(OUT, f"{site}_full.parquet")
    wcon = duckdb.connect(); wcon.register("dfv", df)
    wcon.execute(f"COPY (SELECT * FROM dfv) TO '{p}' (FORMAT PARQUET, COMPRESSION ZSTD)"); wcon.close()
    day = df.solar_elev_deg > 0
    r = dict(site=site, n=len(df), n_distinct_ts=df.ts_wib.nunique(), t_min=str(df.ts_wib.min()), t_max=str(df.ts_wib.max()),
             n_cols=df.shape[1], maxdiff_h1_vs_targets=round(float(d_h1), 6), maxdiff_mean_vs_master=round(d_mean, 6),
             n_mean_compared=int(both.sum()),
             test_measured_frac=round(float((df.ghi_origin[(df.ts_wib.dt.year == 2025) & day] == "measured").mean()), 4),
             has_source_row_false=int((~df.has_source_row.astype(bool)).sum()))
    for c in KEY: r[f"nn_day_{c}"] = int(df.loc[day, c].notna().sum())
    qc.append(r)
    # banding dengan DB lama (yang dipakai manuskrip sebelumnya)
    o = old.execute("SELECT * FROM std.model_base_10min_full WHERE site_id=? ORDER BY ts_wib", [site]).df()
    mm = df.merge(o, on="ts_wib", suffixes=("", "_old"))
    for c in [c for c in OLD_COLS if c not in ("site_id", "ts_wib")]:
        a, b = mm[c], mm[c + "_old"]
        if a.dtype == object or b.dtype == object or str(a.dtype) in ("boolean", "bool"):
            neq = int(((a.astype(str)) != (b.astype(str))).sum())
            cmp.append(dict(site=site, col=c, n_nonnull_new=int(a.notna().sum()), n_nonnull_old=int(b.notna().sum()),
                            n_changed=neq, max_abs_diff=np.nan)); continue
        a, b = pd.to_numeric(a, errors="coerce").astype(float), pd.to_numeric(b, errors="coerce").astype(float)
        both_ = a.notna() & b.notna(); nulldiff = int((a.isna() != b.isna()).sum())
        dif = (a[both_] - b[both_]).abs()
        cmp.append(dict(site=site, col=c, n_nonnull_new=int(a.notna().sum()), n_nonnull_old=int(b.notna().sum()),
                        n_changed=int((dif > 1e-9).sum()) + nulldiff, max_abs_diff=float(dif.max()) if len(dif) else np.nan))
    log(f"  {site:9s} n={len(df)} distinct={r['n_distinct_ts']} cols={df.shape[1]} d_h1={d_h1:.2e} d_mean={d_mean:.2e} "
        f"meas2025={r['test_measured_frac']} ({time.time()-t1:.0f}s)")
    assert r["n"] == r["n_distinct_ts"] == 210384 and d_h1 < 1e-9

Q = pd.DataFrame(qc); Q.to_csv(os.path.join(OUT, "qc_build.csv"), index=False)
C = pd.DataFrame(cmp); C.to_csv(os.path.join(OUT, "qc_vs_old.csv"), index=False)
ch = C[C.n_changed > 0].sort_values(["site", "n_changed"], ascending=[True, False])
log("\n== Kolom yang berubah vs solar_new.duckdb (n_changed>0) ==")
log(ch.to_string(index=False, max_rows=400))
assert os.path.getmtime(DB) == mtime0, "DB termodifikasi!"
json.dump(dict(db=DB, sha256=sha, mtime=mtime0, mask_clp=MASK_CLP, clp_harmonised=HARMONISE, clp_cloud_flag="recomputed: clp_cot >= 1 (all sites; M6 2026-10-12)",
               clp_time_convention=("Himawari file nominal time T-10 min used at origin T (all sites)" if HARMONISE else "mixed: label T (5 sites), T-10 (kalbar)"),
               built=time.strftime("%Y-%m-%d %H:%M:%S"),
               duckdb=duckdb.__version__), open(os.path.join(OUT, "provenance.json"), "w"), indent=1)
log("SELESAI Tahap 00")
