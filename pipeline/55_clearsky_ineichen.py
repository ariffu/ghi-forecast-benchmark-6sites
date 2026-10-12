# -*- coding: utf-8 -*-
"""Tahap 55 — GHI langit cerah Ineichen–Perez (pvlib) per situs + diagnostik. Desain: 55_clearsky/DESAIN_CLEARSKY_55.md (ditulis sebelum hasil).

Keluaran:
  00_clearsky/{situs}_ineichen.parquet   ts_wib, ghi_cs (W m⁻²) pada label waktu (WIB = UTC+7), grid identik 00_data
  00_clearsky/provenance.json            pvlib, ketinggian, sumber kekeruhan Linke, konvensi waktu
  55_clearsky/diagnostik_clearsky.csv     per situs: k_c pada hari cerah, kerataan diurnal k_c vs k_t, fraksi terpotong, R² SP lama vs baru
Juga memeriksa bahwa fungsi turunan _common.apply_clearsky (mode SIMPLE) mereproduksi kolom database secara eksak.
Jalankan: PYTHONIOENCODING=utf-8 python -u 55_clearsky_ineichen.py
"""
import os, sys, json, warnings, datetime as dt
import numpy as np, pandas as pd, duckdb, pvlib
warnings.filterwarnings("ignore")
B = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, B)
CS = os.path.join(B, "00_clearsky"); D = os.path.join(B, "55_clearsky"); os.makedirs(CS, exist_ok=True); os.makedirs(D, exist_ok=True)
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
DB = os.environ.get("GHI_DB", "")
if not DB: raise SystemExit("Set env var GHI_DB to the path of the harmonised DuckDB database (std.* schema).")
con = duckdb.connect(DB, read_only=True)
META = con.execute("SELECT site_id, latitude, longitude FROM std.dim_site").df().set_index("site_id")
def r2(y, p): return 1 - np.nansum((y - p) ** 2) / np.nansum((y - np.nanmean(y)) ** 2)
prov, rows = {}, []
for s in SITES:
    df = duckdb.connect().execute("SELECT * FROM read_parquet(?) ORDER BY ts_wib", [os.path.join(B, "00_data", f"{s}_full.parquet")]).df()
    lat, lon = float(META.loc[s, "latitude"]), float(META.loc[s, "longitude"])
    alt = max(0.0, float(pvlib.location.lookup_altitude(lat, lon)))
    t = pd.DatetimeIndex(df.ts_wib).tz_localize("Etc/GMT-7")                 # WIB = UTC+7, tanpa DST
    loc = pvlib.location.Location(lat, lon, tz="Etc/GMT-7", altitude=alt)
    lt = pvlib.clearsky.lookup_linke_turbidity(t, lat, lon, interp_turbidity=True)
    cs = loc.get_clearsky(t, model="ineichen", linke_turbidity=lt)["ghi"].to_numpy()
    sp = pvlib.solarposition.get_solarposition(t, lat, lon, altitude=alt)
    _out = pd.DataFrame({"ts_wib": df.ts_wib.values, "ghi_cs": cs}); _w = duckdb.connect(); _w.register("cs_tbl", _out)
    _w.execute(f"COPY (SELECT * FROM cs_tbl ORDER BY ts_wib) TO '{os.path.join(CS, s + '_ineichen.parquet').replace(chr(92), '/')}' (FORMAT PARQUET)"); _w.close()
    prov[s] = dict(latitude=lat, longitude=lon, altitude_m=alt, linke_min=float(lt.min()), linke_max=float(lt.max()),
                   elev_median_abs_diff_vs_db=float(np.median(np.abs(sp.elevation.values - df.solar_elev_deg.values)[df.solar_elev_deg.values > 5])))
    # ---- diagnostik
    el = df.solar_elev_deg.to_numpy(float); ghi = df.ghi_wm2.to_numpy(float); kt_old = df.kt.to_numpy(float)
    with np.errstate(all="ignore"): kc_raw = np.where(~np.isnan(kt_old) & (cs > 0), ghi / cs, np.nan)
    clip_frac = float(np.nanmean(kc_raw > 2)); kc = np.clip(kc_raw, 0, 2)
    d = df.assign(date=df.ts_wib.dt.date, kc=kc)
    day = d[d.solar_elev_deg > 20].groupby("date").kt.agg(["median", "std", "count"])
    clear = day[(day["median"] > 0.70) & (day["std"] < 0.06) & (day["count"] >= 40)].index
    cd = d[d.date.isin(clear) & (d.solar_elev_deg > 10)]
    bins = pd.cut(cd.solar_elev_deg, [10, 20, 30, 45, 60, 90])
    kc_by, kt_by = cd.groupby(bins, observed=True).kc.median(), cd.groupby(bins, observed=True).kt.median()
    # SP lama vs baru (target rata-rata jam, uji 2025, protokol A) — dihitung di sini dari definisi, independen dari _common
    G = np.column_stack([np.r_[ghi[k:], [np.nan] * k] for k in range(1, 7)])
    C_old = np.column_stack([np.r_[(1100 * np.sin(np.radians(el)))[k:], [np.nan] * k] for k in range(1, 7)])
    C_new = np.column_stack([np.r_[cs[k:], [np.nan] * k] for k in range(1, 7)])
    y = np.nanmean(G, 1); valid = ~np.isnan(G).any(1) & ~np.isnan(C_new).any(1)
    m = (el > 5) & valid & ~np.isnan(kt_old) & (df.ts_wib.dt.year == 2025).to_numpy()
    b_old = kt_old * C_old.mean(1); b_new = kc * C_new.mean(1)
    hr = df.ts_wib.dt.hour.to_numpy()
    edge = m & ((hr < 9) | (hr >= 15))
    rows.append(dict(site=s, altitude_m=alt, clear_days=len(clear), kc_clear_median=float(cd.kc.median()),
                     kc_clear_range_by_elev=float(kc_by.max() - kc_by.min()), kt_clear_range_by_elev=float(kt_by.max() - kt_by.min()),
                     cs_over_1100sin_at_noon=float(np.nanmedian((cs / (1100 * np.sin(np.radians(el))))[el > 70])) if (el > 70).any() else np.nan,
                     kc_clip_frac=clip_frac, R2_SP_old=r2(y[m], b_old[m]), R2_SP_new=r2(y[m], b_new[m]),
                     RMSE_SP_old=float(np.sqrt(np.nanmean((y[m] - b_old[m]) ** 2))), RMSE_SP_new=float(np.sqrt(np.nanmean((y[m] - b_new[m]) ** 2))),
                     RMSE_SP_old_edges=float(np.sqrt(np.nanmean((y[edge] - b_old[edge]) ** 2))), RMSE_SP_new_edges=float(np.sqrt(np.nanmean((y[edge] - b_new[edge]) ** 2)))))
    print(f"{s}: alt={alt:.0f} m, Linke {lt.min():.2f}–{lt.max():.2f}, clear days={len(clear)}, kc_clear_median={rows[-1]['kc_clear_median']:.3f}, "
          f"R2_SP {rows[-1]['R2_SP_old']:.4f} -> {rows[-1]['R2_SP_new']:.4f}, clip={clip_frac:.5f}", flush=True)
json.dump(dict(model="Ineichen–Perez (pvlib.clearsky.ineichen via Location.get_clearsky)", pvlib=pvlib.__version__,
               linke="Remund et al. (2003) monthly climatology, pvlib LinkeTurbidities.h5, interp_turbidity=True",
               altitude="pvlib.location.lookup_altitude (negatif -> 0)", time="label time ts_wib, tz Etc/GMT-7 (WIB)", kc="GHI/GHI_cs on DB kt domain, clipped to [0, 2]",
               built=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sites=prov), open(os.path.join(CS, "provenance.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
R = pd.DataFrame(rows); R.to_csv(os.path.join(D, "diagnostik_clearsky.csv"), index=False)
print(R.round(4).to_string(index=False))
# ---- cek desain 1: fungsi turunan _common.derive_kt mereproduksi kolom database bila diberi k_t database
import _common
COLS = [f"kt_lag_{m}m" for m in (10, 20, 30, 60)] + [f"kt_delta_{m}m" for m in (10, 20, 30, 60)] + ["kt_roll_30m_mean", "kt_roll_30m_std", "kt_roll_60m_mean",
        "kt_roll_60m_std", "kt_std_1h", "kt_std_3h", "accel_kt_20m"]
chk = []
for s in SITES:
    df = duckdb.connect().execute("SELECT * FROM read_parquet(?) ORDER BY ts_wib", [os.path.join(B, "00_data", f"{s}_full.parquet")]).df()
    k = pd.to_numeric(df.kt, errors="coerce").astype(float); ref = df[COLS].apply(pd.to_numeric, errors="coerce").astype(float).copy()
    out = _common.derive_kt(pd.DataFrame(index=df.index), k)
    for c in COLS:
        a, b = ref[c], out[c]; both = a.notna() & b.notna()
        chk.append(dict(site=s, col=c, max_abs=float((a[both] - b[both]).abs().max()), nan_mismatch=int((a.isna() != b.isna()).sum())))
C = pd.DataFrame(chk); C.to_csv(os.path.join(D, "cek_derive_kt_vs_db.csv"), index=False)
ok = bool((C.max_abs < 1e-6).all() and (C.nan_mismatch == 0).all())
print(f"cek derive_kt vs database: maks |selisih| = {C.max_abs.max():.2e}, NaN beda = {int(C.nan_mismatch.sum())} -> {'OK' if ok else 'GAGAL'}")
assert ok
