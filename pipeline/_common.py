# -*- coding: utf-8 -*-
"""_common.py — persiapan data & target (lead h1..h6 = per jam) + helper plot.

RERUN v2 (2026-10-03): sumber data = solar_harmonised_clpbanten_v2.duckdb (D21) melalui
00_build_data.py -> 00_data/{site}_full.parquet (124 kolom, skema identik view lama
std.model_base_10min_full; CLP dimask dengan clp_retrieval_ok). Logika target, mask,
dan split TIDAK berubah dari pipeline solar_new.duckdb. Daftar fitur: lihat FEATSET di bawah (default P2 = 43).
Override folder data: env DATA_DIR (mis. 00_data_rawfill untuk uji sensitivitas).
"""
import os, numpy as np, pandas as pd, duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, os.environ.get("DATA_DIR", "00_data"))
PLOTS = os.path.join(BASE, "plots"); os.makedirs(PLOTS, exist_ok=True)
PARQUET = os.path.join(DATA, "bengkulu_full.parquet")
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
LEADS = [f"ghi_actual_h{i}" for i in range(1, 7)]
SP = [f"smart_persist_h{i}" for i in range(1, 7)]
# Himpunan prediktor (2026-10-06): P2 = 43 prediktor hasil tahap 50 (50_prediktor/DESAIN_TERKUNCI_50.md, RINGKASAN_50.md),
# diadopsi untuk naskah; P0 = 104 prediktor lama (arsip _arsip_P0_104prediktor/). Pilih dengan env FEATSET=P0|P2.
FEATSET = os.environ.get("FEATSET", "P2")
assert FEATSET in ("P0", "P2"), FEATSET
P2 = ["ghi_wm2", "dhi_wm2", "dni_wm2", "reflected_wm2", "aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_wind_dir_sin",
      "aws_wind_dir_cos", "aws_rain_mm", "clp_cot", "clp_cth_km", "clp_cer_um", "clp_cloud_present_int", "decl_noaa_deg", "eot_min", "clear_sky_ghi",
      "kt", "clear_sky_ghi_h1", "kt_delta_10m", "kt_delta_20m", "kt_delta_30m", "kt_delta_60m", "kt_roll_30m_mean", "kt_roll_30m_std",
      "kt_roll_60m_mean", "kt_roll_60m_std", "kt_std_3h", "synop_visibility_km", "synop_cloud_cover_oktas", "synop_cl", "synop_cm", "synop_ch",
      "synop_present_weather_ww", "aws_temp_delta_60m", "aws_rh_delta_60m", "aws_pressure_delta_60m", "aws_rain_sum_180m", "clp_cot_delta_60m",
      "clp_cot_roll_180m_mean", "clp_cth_lag_60m", "clp_cth_roll_180m_mean"]
def featset(feats):
    """Saring daftar 104 kandidat menjadi himpunan aktif (urutan kolom data dipertahankan)."""
    if FEATSET == "P0": return list(feats)
    out = [f for f in feats if f in P2]; assert len(out) == len(P2) == 43, f"P2 tidak lengkap: {len(out)}"
    return out

# Model langit cerah (2026-10-07; 55_clearsky/DESAIN_CLEARSKY_55.md): IP = Ineichen–Perez (pvlib, Linke Remund 2003; cache 00_clearsky/),
# k_c = GHI/GHI_cs dan smart persistence indeks langit cerah; SIMPLE = definisi database lama (GHI_cs = 1100·sin h, k_t = GHI/(1100·sin h)).
# Nama kolom tetap ("kt", "kt_*", "clear_sky_ghi*", "smart_persist_h*"); pada mode IP isinya k_c dan GHI_cs Ineichen–Perez.
# "kt_clearness" = indeks kecerahan lama, HANYA untuk kelas kondisi langit (ambang 0,30/0,65), bukan prediktor.
CLEARSKY = os.environ.get("CLEARSKY", "IP")
assert CLEARSKY in ("IP", "SIMPLE"), CLEARSKY
CS_DIR = os.path.join(BASE, "00_clearsky"); KC_MAX = 2.0
def derive_kt(df, k):
    """Kolom turunan k dengan definisi database (direproduksi eksak, tahap 55): shift; rolling(n, min_periods=1); std ddof=1."""
    for m, n in [(10, 1), (20, 2), (30, 3), (60, 6)]: df[f"kt_lag_{m}m"] = k.shift(n); df[f"kt_delta_{m}m"] = k - k.shift(n)
    for w, n in [(30, 3), (60, 6)]:
        df[f"kt_roll_{w}m_mean"] = k.rolling(n, min_periods=1).mean(); df[f"kt_roll_{w}m_std"] = k.rolling(n, min_periods=1).std(ddof=1)
    df["kt_std_1h"] = k.rolling(6, min_periods=1).std(ddof=1); df["kt_std_3h"] = k.rolling(18, min_periods=1).std(ddof=1)
    df["accel_kt_20m"] = k - 2 * k.shift(1) + k.shift(2)
    return df
def apply_clearsky(df, site):
    """Ganti definisi langit cerah sesuai CLEARSKY. df harus terurut ts_wib dan bertipe float pada kolom kt/ghi."""
    df["kt_clearness"] = pd.to_numeric(df["kt"], errors="coerce").astype("float64")
    if CLEARSKY == "SIMPLE": return df
    c = duckdb.connect().execute("SELECT ts_wib, ghi_cs FROM read_parquet(?) ORDER BY ts_wib", [os.path.join(CS_DIR, f"{site}_ineichen.parquet")]).df()
    assert len(c) == len(df) and (c.ts_wib.to_numpy() == df.ts_wib.to_numpy()).all(), f"{site}: grid langit cerah tidak cocok"
    cs = pd.Series(c.ghi_cs.to_numpy(float), index=df.index); ghi = pd.to_numeric(df["ghi_wm2"], errors="coerce").astype("float64")
    with np.errstate(all="ignore"): kc = (ghi / cs).where(df["kt_clearness"].notna() & (cs > 0)).clip(0, KC_MAX)
    df["kt"] = kc; df["clear_sky_ghi"] = cs
    for h in range(1, 7):
        df[f"clear_sky_ghi_h{h}"] = cs.shift(-6 * h); df[f"smart_persist_h{h}"] = kc * df[f"clear_sky_ghi_h{h}"]
    if "ghi_cs_t60" in df: df["ghi_cs_t60"] = df["clear_sky_ghi_h1"]   # di DB duplikat persis clear_sky_ghi_h1 (hanya ada di 104 kandidat, P0)
    return derive_kt(df, kc)
def cs_for_baseline(df):
    """GHI cerah untuk smart persistence: IP = Ineichen–Perez; SIMPLE = rumus lama 1100·sin h apa adanya (reproduksi arsip)."""
    return df["clear_sky_ghi"].to_numpy(float) if CLEARSKY == "IP" else 1100.0 * np.sin(np.radians(df["solar_elev_deg"].to_numpy(float)))

def prepare(site="bengkulu", l_filter=5):
    p = os.path.join(DATA, f"{site}_full.parquet")
    df = duckdb.connect().execute("SELECT * FROM read_parquet(?)", [p]).df()
    df = df.sort_values("ts_wib").reset_index(drop=True)
    DROP = set(["site_id","ts_wib","ghi_origin","has_source_row","aod_500nm","angstrom_exp",
                "smart_persist","smart_persist_avg","kt_clearness"]) | set(LEADS) | set(SP)
    feats = [c for c in df.columns if c not in DROP]
    for c in feats:
        if str(df[c].dtype) in ("boolean", "bool"): df[c] = df[c].astype("boolean").fillna(False).astype(int)
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    assert len(feats) == 104, f"kandidat prediktor {len(feats)} ≠ 104"
    feats = featset(feats)                       # semua 104 kolom tetap ada di df (mask, kanal sequence); model hanya memakai himpunan aktif
    df = apply_clearsky(df, site)                # CLEARSKY=IP: k_c, GHI_cs Ineichen–Perez, turunan, smart persistence standar
    # target: h1 = t+1 jam
    df["y_point"] = df["ghi_actual_h1"];       df["base_point"] = df["smart_persist_h1"]
    # rata-rata jam: mean ghi pada t+10..t+60 (grid 10-menit)
    ghi = df["ghi_wm2"].to_numpy(float)
    # IP: Ineichen–Perez (≥ 0). SIMPLE: rumus lama apa adanya, 1100·sin h yang NEGATIF setelah matahari terbenam (bug kecil baseline lama,
    # 5,8 % origin; LAPORAN §25) — dipertahankan hanya agar arsip dapat direproduksi persis.
    cs = cs_for_baseline(df)
    def fwd(a):
        M = np.full((len(a), 6), np.nan)
        for k in range(1, 7): M[:-k, k-1] = a[k:]
        return M
    G, C = fwd(ghi), fwd(cs)
    with np.errstate(all="ignore"):
        df["y_mean"] = np.nanmean(G, axis=1)
        df["base_mean"] = df["kt"].to_numpy() * np.nanmean(C, axis=1)
    df.loc[df["kt"].isna(), "base_mean"] = np.nan
    df["valid_mean"] = (~np.isnan(G).any(axis=1)) & (~np.isnan(C).any(axis=1))
    yr = df["ts_wib"].dt.year
    return df, feats, yr

def split_idx(df, yr, tgt="point"):
    yc = f"y_{tgt}"; bc = f"base_{tgt}"
    m = (df["solar_elev_deg"] > 5) & df[yc].notna() & df[bc].notna()
    if tgt == "mean": m &= df["valid_mean"]
    idx = np.where(m.to_numpy())[0]
    return idx[yr[idx] <= 2023], idx[yr[idx] == 2024], idx[yr[idx] == 2025]

def savefig(fig, name):
    p = os.path.join(PLOTS, name)
    fig.tight_layout(); fig.savefig(p, dpi=140); plt.close(fig)
    print(f"    plot -> {name}", flush=True)
    return p

def fig_scatter(y, p, title, xlabel="Observed GHI (W/m²)", ylabel="Predicted GHI (W/m²)"):
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    ax.scatter(y, p, s=5, alpha=0.25, color="steelblue")
    lim = [0, max(y.max(), p.max()) * 1.02]
    ax.plot(lim, lim, "r--", lw=1)
    ax.set_xlim(lim); ax.set_ylim(lim); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.set_title(title)
    return fig
