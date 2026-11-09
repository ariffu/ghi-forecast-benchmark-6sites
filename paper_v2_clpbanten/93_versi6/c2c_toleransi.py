# -*- coding: utf-8 -*-
"""Tahap 93: kalibrasi toleransi deteksi segaris menurut resolusi data. Laju 'positif palsu' diukur di stasiun/kolom yang datanya 10 menit asli. Hanya membaca."""
import numpy as np, pandas as pd
V5 = r"C:\Users\ariff\Documents\Balai_data_v5_final87\00_data"
def blok(a, tol):
    n = len(a); H = np.arange(0, n - 6, 6); v0, v1 = a[H], a[H + 6]; seg = np.stack([a[H + k] for k in range(1, 6)], 1); lin = np.stack([v0 + (v1 - v0) * k / 6 for k in range(1, 6)], 1)
    ok = np.isfinite(v0) & np.isfinite(v1) & np.isfinite(seg).all(1) & (np.abs(v1 - v0) > 2 * tol)
    return ok, ok & (np.abs(seg - lin) < tol).all(1)
def resolusi(a):
    x = a[np.isfinite(a)]; x = x[:200000]
    for r in (1.0, 0.1, 0.01):
        if np.mean(np.abs(x / r - np.round(x / r)) < 1e-6) > 0.95: return r
    return 0.0
for s in ("bengkulu", "jogja", "kalbar", "semarang", "banten", "jambi"):
    d = pd.read_parquet(f"{V5}\\{s}_full.parquet", columns=["ts_wib", "aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "solar_elev_deg"]); day = (d.solar_elev_deg > 5).to_numpy()[np.arange(0, len(d) - 6, 6) + 3]
    for c in ("aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms"):
        a = d[c].to_numpy(float); r = resolusi(a); out = [f"{s:9s} {c:18s} resolusi {r:<5}"]
        for tol in (0.006, 0.051, 0.501):
            ok, on = blok(a, tol); out.append(f"tol {tol}: {on[day].sum() / max(ok[day].sum(), 1):.4f} (n {int(ok[day].sum())})")
        print(" | ".join(out))
