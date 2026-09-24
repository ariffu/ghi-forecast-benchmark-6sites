# -*- coding: utf-8 -*-
"""
Tahap 0 — Rerun GHI h+1 Bengkulu (solar_new.duckdb)
Ekstraksi dari std.model_base_10min_full + sanity check + definisi split.

Kontrak: hanya membaca std.*; kunci (site_id, ts_wib); WIB=UTC+7.
Output: 00_data/bengkulu_full.parquet
"""
import os
import duckdb

DB = os.environ.get("GHI_DB", "solar_new.duckdb")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(OUT, exist_ok=True)
PARQUET = os.path.join(OUT, "bengkulu_full.parquet")

con = duckdb.connect(DB, read_only=True)

print("== Kolom std.model_base_10min_full ==")
cols = [r[0] for r in con.execute(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_schema='std' AND table_name='model_base_10min_full' ORDER BY ordinal_position"
).fetchall()]
print(f"n_cols={len(cols)}")
print(cols)

print("\n== Sanity: cakupan & kunci Bengkulu ==")
q = con.execute("""
    SELECT count(*) AS n,
           min(ts_wib) AS t_min,
           max(ts_wib) AS t_max,
           count(DISTINCT ts_wib) AS n_distinct_ts
    FROM std.model_base_10min_full
    WHERE site_id = 'bengkulu'
""").fetchone()
print("n={} t_min={} t_max={} distinct_ts={}".format(*q))

print("\n== Distribusi ghi_origin (siang, solar_elev_deg>0) ==")
for r in con.execute("""
    SELECT ghi_origin, count(*) AS n
    FROM std.model_base_10min_full
    WHERE site_id='bengkulu' AND solar_elev_deg > 0
    GROUP BY ALL ORDER BY 2 DESC
""").fetchall():
    print(f"  {r[0]:24s} {r[1]}")

print("\n== Distribusi has_source_row ==")
for r in con.execute("""
    SELECT has_source_row, count(*) FROM std.model_base_10min_full
    WHERE site_id='bengkulu' GROUP BY ALL
""").fetchall():
    print(f"  has_source_row={r[0]}  n={r[1]}")

print("\n== Cek non-null kolom kunci (Bengkulu, siang) ==")
key = ["ghi_wm2","kt","clp_cot","clp_cth_km","synop_cloud_cover_oktas",
       "synop_temp_c","aws_temp_c","ghi_actual_h6","smart_persist_h1","aod_500nm"]
for c in key:
    n = con.execute(f"""SELECT count({c}) FROM std.model_base_10min_full
                        WHERE site_id='bengkulu' AND solar_elev_deg>0""").fetchone()[0]
    print(f"  {c:28s} non_null_siang={n}")

print("\n== Ekstraksi ke parquet ==")
con.execute(f"""
    COPY (
        SELECT * FROM std.model_base_10min_full WHERE site_id='bengkulu'
    ) TO '{PARQUET}' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
n = con.execute(f"SELECT count(*) FROM read_parquet('{PARQUET}')").fetchone()[0]
print(f"tersimpan: {PARQUET}  baris={n}  ukuran={os.path.getsize(PARQUET)/1e6:.1f} MB")

con.close()
print("SELESAI Tahap 0.")