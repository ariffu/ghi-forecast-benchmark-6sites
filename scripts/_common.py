# -*- coding: utf-8 -*-
"""_common.py - shared data preparation and plotting helpers (PORTABLE).
All paths are resolved relative to the repository root, never to the author's
machine. Set the environment variable GHI_DB to the path of solar_new.duckdb
(read-only std.* layer) if you need to re-extract the Bengkulu table.
"""
import os, numpy as np, pandas as pd, duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
BASE = os.path.join(REPO, "results")                                 # per-stage result folders
PLOTS = os.path.join(REPO, "figures"); os.makedirs(PLOTS, exist_ok=True)
DATA = os.path.join(REPO, "data")
PARQUET = os.path.join(DATA, "bengkulu_full.parquet")
DB = os.environ.get("GHI_DB", "")
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
LEADS = [f"ghi_actual_h{i}" for i in range(1, 7)]
SP = [f"smart_persist_h{i}" for i in range(1, 7)]

def prepare(site="bengkulu", l_filter=5):
    if site == "bengkulu" and os.path.exists(PARQUET):
        df = duckdb.connect().execute("SELECT * FROM read_parquet(?)", [PARQUET]).df()
    else:
        if not DB:
            raise SystemExit("Set env var GHI_DB to the path of solar_new.duckdb (read-only std.* layer).")
        df = duckdb.connect(DB, read_only=True).execute(
            "SELECT * FROM std.model_base_10min_full WHERE site_id = ?", [site]).df()
    df = df.sort_values("ts_wib").reset_index(drop=True)
    DROP = set(["site_id", "ts_wib", "ghi_origin", "has_source_row", "aod_500nm", "angstrom_exp",
                "smart_persist", "smart_persist_avg"]) | set(LEADS) | set(SP)
    feats = [c for c in df.columns if c not in DROP]
    for c in feats:
        if str(df[c].dtype) == "boolean":
            df[c] = df[c].fillna(False).astype(int)
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    df["y_point"] = df["ghi_actual_h1"]; df["base_point"] = df["smart_persist_h1"]
    ghi = df["ghi_wm2"].to_numpy(float)
    cs = 1100.0 * np.sin(np.radians(df["solar_elev_deg"].to_numpy(float)))
    def fwd(a):
        M = np.full((len(a), 6), np.nan)
        for k in range(1, 7):
            M[:-k, k - 1] = a[k:]
        return M
    G, C = fwd(ghi), fwd(cs)
    df["y_mean"] = np.nanmean(G, axis=1)
    df["base_mean"] = df["kt"].to_numpy() * np.nanmean(C, axis=1)
    df.loc[df["kt"].isna(), "base_mean"] = np.nan
    df["valid_mean"] = (~np.isnan(G).any(axis=1)) & (~np.isnan(C).any(axis=1))
    yr = df["ts_wib"].dt.year
    return df, feats, yr

def split_idx(df, yr, tgt="point"):
    yc = f"y_{tgt}"; bc = f"base_{tgt}"
    m = (df["solar_elev_deg"] > 5) & df[yc].notna() & df[bc].notna()
    if tgt == "mean":
        m &= df["valid_mean"]
    idx = np.where(m.to_numpy())[0]
    return idx[yr[idx] <= 2023], idx[yr[idx] == 2024], idx[yr[idx] == 2025]

def savefig(fig, name):
    p = os.path.join(PLOTS, name)
    fig.tight_layout(); fig.savefig(p, dpi=140); plt.close(fig)
    print(f"    plot -> {name}", flush=True)
    return p

def fig_scatter(y, p, title, xlabel="Observed GHI (W/m2)", ylabel="Predicted GHI (W/m2)"):
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    ax.scatter(y, p, s=5, alpha=0.25, color="steelblue")
    lim = [0, max(y.max(), p.max()) * 1.02]
    ax.plot(lim, lim, "r--", lw=1)
    ax.set_xlim(lim); ax.set_ylim(lim); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.set_title(title)
    return fig
