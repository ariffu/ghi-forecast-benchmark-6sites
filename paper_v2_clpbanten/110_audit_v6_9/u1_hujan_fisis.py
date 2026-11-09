# -*- coding: utf-8 -*-
"""Tahap 108 U1: konsistensi fisis hujan V6.8 (hanya membaca), per sumber (logger / isian maju):
- intensitas 10 menit (maks, p99,9, kelipatan resolusi penakar 0,2 mm pada slot logger);
- hujan lawan k_c (elevasi > 20°): median k_c saat hujan ≥ 0,5 mm/10 menit, proporsi k_c > 0,9;
- hujan lawan CLP (fraksi awan, COT, CTH) dan RH/suhu;
- hujan lawan kode cuaca SYNOP (ww 50–99 = presipitasi) pada jam laporan: hujan AWS 60 menit terakhir;
- total tahunan."""
import os, numpy as np, pandas as pd
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_9"
R = []
for s in ("banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"):
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet")); p = pd.read_parquet(os.path.join(V, "provenance", f"{s}_provenance.parquet"))
    e = pd.read_parquet(os.path.join(V, "clp_ekstra", f"{s}_clp_ekstra.parquet")); cs = pd.read_parquet(os.path.join(V, "clearsky", f"{s}_ineichen.parquet")).ghi_cs.to_numpy(); t = pd.DatetimeIndex(d.ts_wib)
    r = d.aws_rain_mm.to_numpy(float); maju = p.hujan_isi_maju.to_numpy(bool); el = d.solar_elev_deg.to_numpy(float)
    with np.errstate(all="ignore"): kc = np.where((el > 20) & (cs > 50), d.ghi_wm2.to_numpy(float) / cs, np.nan)
    lg = ~maju & np.isfinite(r)
    rr = dict(stasiun=s, maks_10mnt=float(np.nanmax(r)), p999_hujan=round(float(np.nanpercentile(r[r > 0], 99.9)), 1), negatif=int((r < 0).sum()),
              logger_kelipatan_0_2_pct=round(100 * float(np.isclose((r[lg & (r > 0)] / 0.2) % 1, 0, atol=1e-6).mean() + np.isclose((r[lg & (r > 0)] / 0.2) % 1, 1, atol=1e-6).mean()), 1))
    for lab, m in (("logger", lg), ("isi_maju", maju)):
        h = m & (r >= 0.5) & np.isfinite(kc); rr[f"kc_median_hujan_{lab}"] = round(float(np.median(kc[h])), 3) if h.sum() > 30 else np.nan; rr[f"kc_gt0_9_hujan_{lab}_pct"] = round(100 * float((kc[h] > 0.9).mean()), 1) if h.sum() > 30 else np.nan
    h = lg & (r >= 0.5) & (e.qc_clp_sza.to_numpy() == 0); k = lg & (r == 0) & (e.qc_clp_sza.to_numpy() == 0)
    for c_, nm in ((e.clp_cloud_frac.to_numpy(), "frac"), (d.clp_cot.to_numpy(float), "cot"), (d.clp_cth_km.to_numpy(float), "cth")):
        rr[f"{nm}_hujan"] = round(float(np.nanmedian(c_[h])), 2); rr[f"{nm}_kering"] = round(float(np.nanmedian(c_[k])), 2)
    rr["RH_hujan"] = round(float(np.nanmedian(d.aws_rh_pct.to_numpy(float)[lg & (r >= 0.5)])), 1); rr["RH_kering"] = round(float(np.nanmedian(d.aws_rh_pct.to_numpy(float)[lg & (r == 0)])), 1)
    ww = d.synop_present_weather_ww.to_numpy(float); rep = np.isfinite(ww) & (np.r_[True, np.diff(np.nan_to_num(ww, nan=-1)) != 0] | True)
    h60 = pd.Series(np.nan_to_num(r)).rolling(6, min_periods=1).sum().to_numpy(); jam = (t.minute == 0) & np.isfinite(ww)
    presip = (ww >= 50) & (ww <= 99); rr["ww_presip_aws_hujan60_pct"] = round(100 * float((h60[jam & presip] > 0).mean()), 1); rr["ww_tanpa_presip_aws_gt1mm_pct"] = round(100 * float((h60[jam & ~presip & (ww < 50)] > 1).mean()), 1)
    rr["tahunan_mm"] = str(pd.Series(np.nan_to_num(r)).groupby(t.year).sum().round(0).astype(int).to_dict())
    R.append(rr); print(s, "selesai", flush=True)
T = pd.DataFrame(R); T.to_csv(os.path.join(HERE, "U1_hujan_fisis.csv"), index=False); print(T.T.to_string())
