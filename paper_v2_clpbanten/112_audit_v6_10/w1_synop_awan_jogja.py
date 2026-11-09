# -*- coding: utf-8 -*-
"""Tahap 110 W1: kolom SYNOP awan Yogyakarta V6.9 — homogenitas antartahun (2022–2023 dari berkas lawan 2025 dari database), konsistensi dengan k_c dan CLP,
dan pembanding stasiun lain. Hanya membaca; jam laporan saja (menit 00)."""
import os, numpy as np, pandas as pd
from scipy.stats import spearmanr
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_10"; R = []
for s in ("jogja", "banten", "bengkulu", "jambi", "kalbar", "semarang"):
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet")); e = pd.read_parquet(os.path.join(V, "clp_ekstra", f"{s}_clp_ekstra.parquet"))
    cs = pd.read_parquet(os.path.join(V, "clearsky", f"{s}_ineichen.parquet")).ghi_cs.to_numpy(); t = pd.DatetimeIndex(d.ts_wib); el = d.solar_elev_deg.to_numpy(float)
    with np.errstate(all="ignore"): kc = np.where((el > 20) & (cs > 50), d.ghi_wm2.to_numpy(float) / cs, np.nan)
    N = d.synop_cloud_cover_oktas.where(d.synop_cloud_cover_oktas <= 8).to_numpy(float); CH = d.synop_ch.to_numpy(float); CM = d.synop_cm.to_numpy(float); fr = e.clp_cloud_frac.to_numpy(); cth = d.clp_cth_km.to_numpy(float)
    jam = (t.minute == 0)
    for y in range(2022, 2026):
        m = jam & (t.year == y) & np.isfinite(N)
        r = dict(stasiun=s, tahun=y, n=int(m.sum()), okta_rata=round(float(N[m].mean()), 2) if m.any() else np.nan, okta8_pct=round(100 * float((N[m] == 8).mean()), 1) if m.any() else np.nan)
        mk = m & np.isfinite(kc); r["rho_okta_kc"] = round(float(spearmanr(N[mk], kc[mk]).correlation), 3) if mk.sum() > 100 else np.nan
        mf = m & np.isfinite(fr) & (e.qc_clp_sza.to_numpy() == 0); r["rho_okta_fraksiCLP"] = round(float(spearmanr(N[mf], fr[mf]).correlation), 3) if mf.sum() > 100 else np.nan
        mh = jam & (t.year == y) & np.isfinite(CH) & np.isfinite(cth); r["CTH_saat_CH>0"] = round(float(np.nanmedian(cth[mh & (CH > 0)])), 2) if (mh & (CH > 0)).sum() > 30 else np.nan; r["CTH_saat_CH=0"] = round(float(np.nanmedian(cth[mh & (CH == 0)])), 2) if (mh & (CH == 0)).sum() > 30 else np.nan
        r["CM_kode_terbanyak"] = str(pd.Series(CM[jam & (t.year == y)]).value_counts().head(3).astype(int).to_dict()); R.append(r)
T = pd.DataFrame(R); T.to_csv(os.path.join(HERE, "W1_synop_awan.csv"), index=False); print(T.to_string(index=False))
