# -*- coding: utf-8 -*-
"""Tahap 98 (salinan uji tahap 95 untuk V6.2) C1–C7: uji satelit CLP. Membaca 6lokasi_output_chips.zip (sumber V6) dan Balai_data_v6_2 (hanya membaca)."""
import os, re, io, zipfile, numpy as np, pandas as pd, pvlib
from scipy.stats import spearmanr
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 60); pd.set_option("display.max_colwidth", 120)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_2"; ZIP = r"C:\Users\ariff\Documents\6lokasi_output_chips.zip"
LOK = {"banten": "sta6016_banten", "bengkulu": "sta6009_bengkulu", "jambi": "sta6007_jambi", "jogja": "sta6010_jogja", "kalbar": "sta6003_kalbar", "semarang": "sta6018_jateng"}
META = dict(banten=(-6.26147, 106.7509, 27), bengkulu=(-3.86493, 102.311998, 9), jambi=(-1.60111, 103.4944, 24), jogja=(-7.731064, 110.353578, 182), kalbar=(0.07489, 109.1905, 2), semarang=(-6.9847, 110.3812, 6))
SK = {"CLOT": (0.01, 0.0), "CLTT": (0.01, 150.0), "CLTH": (0.001, 0.0), "CLER_23": (0.01, 0.0)}
JMA = [(pd.Timestamp("2000-01-01"), "H08"), (pd.Timestamp("2022-12-13 05:00"), "H09"), (pd.Timestamp("2025-10-12 13:00"), "H08"), (pd.Timestamp("2025-11-26 05:00"), "H09")]
def harap(t):
    out = np.empty(len(t), object)
    for a, lab in JMA: out[t >= a] = lab
    return out
def vza(la, lo, slon=140.7):
    g = np.arccos(np.cos(np.radians(la)) * np.cos(np.radians(lo - slon))); r = 6378.137 / 42164.0
    return np.degrees(np.arctan2(np.sin(g), np.cos(g) - r))
z = zipfile.ZipFile(ZIP); NM = z.namelist(); O = {k: [] for k in ("C1", "C2", "C3", "C4", "C5", "C6", "C7")}
for s, site in LOK.items():
    la, lo, alt = META[s]
    F = sorted(n for n in NM if re.search(rf"{site}/CLP_{site}_\d{{4}}-\d\d-\d\d\.csv$", n))
    C = pd.concat([pd.read_csv(io.BytesIO(z.read(n))) for n in F], ignore_index=True); C["tt"] = pd.to_datetime(C.timestamp); C["tu"] = pd.to_datetime(C.file_timestamp_utc)
    dm = C.groupby(C.tt.dt.date).CLTT_mean.median(); g = C.tt.dt.date.isin(set(dm[dm < 160].index)).to_numpy()
    for v, (sc, of) in SK.items():
        for st in ("mean", "median", "min", "max"):
            if f"{v}_{st}" in C: C.loc[g, f"{v}_{st}"] = (C.loc[g, f"{v}_{st}"] - of) / sc
    # C1 satelit dan versi
    sat_f = C.source_file.str.extract(r"NC_(H0\d)_")[0]; ver = C.source_file.str.extract(r"_(L2CLP\d+)_")[0]; suf = C.source_file.str.extract(r"FLDK\.(\d+_\d+)\.nc")[0]
    e = harap(C.tu.to_numpy()); O["C1"].append(dict(stasiun=s, berkas=int(C.source_file.notna().sum()), satelit_berkas=str(sat_f.value_counts().to_dict()), tak_sesuai_jadwal_JMA=int((sat_f.notna() & (sat_f != e)).sum()),
                                                    kolom_satellite_beda_nama=int((C.satellite != sat_f).sum()), versi=str(ver.value_counts().to_dict()), sufiks=str(suf.value_counts().head(3).to_dict())))
    # C2 ketersediaan per jam UTC (siang lokal 22–11 UTC)
    hm = C.tu.dt.strftime("%H:%M"); days = C.tt.dt.date.nunique(); cnt = hm[C.source_file.notna()].value_counts()
    full = pd.date_range("2022-01-01", periods=144, freq="10min").strftime("%H:%M"); miss = {h: round(1 - cnt.get(h, 0) / days, 3) for h in full}
    O["C2"].append(dict(stasiun=s, hari=days, hilang_0240=miss["02:40"], hilang_1440=miss["14:40"], hilang_median_lain=round(float(np.median([v for k, v in miss.items() if k not in ("02:40", "14:40")])), 4),
                        jam_hilang_gt5pct=str({k: v for k, v in miss.items() if v > 0.05 and k not in ("02:40", "14:40")})))
    # posisi matahari pada waktu pindai (perkiraan T + 5 menit)
    sp = pvlib.solarposition.get_solarposition(pd.DatetimeIndex(C.tu).tz_localize("UTC") + pd.Timedelta(minutes=5), la, lo, altitude=alt); sza = sp.zenith.to_numpy()
    cot, cer, ctt, cth = (C[f"{v}_mean"].to_numpy(float) for v in ("CLOT", "CLER_23", "CLTT", "CLTH")); n_ = C.CLOT_count.to_numpy(float); tot = C.total_pixels.to_numpy(float); ada = C.source_file.notna().to_numpy()
    # C3 rentang dan laju CTT–CTH
    w = np.isfinite(ctt) & np.isfinite(cth) & (cth > 1) & (cth < 14)
    sl = np.polyfit(cth[w], ctt[w], 1)
    O["C3"].append(dict(stasiun=s, cot_min=np.nanmin(cot), cot_maks=np.nanmax(cot), cot_eq150=int((cot >= 149.99).sum()), ctt_min=round(np.nanmin(ctt), 1), ctt_maks=round(np.nanmax(ctt), 1), cth_maks=round(np.nanmax(cth), 2),
                        cer_min=round(np.nanmin(cer), 2), cer_maks=round(np.nanmax(cer), 2), cer_nol=int((cer == 0).sum()), laju_K_per_km=round(-sl[0], 2), ctt_pada_0km=round(sl[1], 1),
                        malam_sza_gt90_cot=int((ada & (sza > 90) & np.isfinite(cot)).sum()), malam_sza_gt90_cth=int((ada & (sza > 90) & np.isfinite(cth)).sum())))
    # C4 agregasi kotak: COT = rata-rata piksel berawan; fraksi berawan = count/total
    fr = np.where(ada, np.nan_to_num(n_, nan=0.0) / tot, np.nan); dayv = ada & (sza < 70)
    cm = dayv & np.isfinite(cot)
    O["C4"].append(dict(stasiun=s, slot_siang_sza70=int(dayv.sum()), cot_ada=int(cm.sum()), fraksi_median_saat_cot_ada=round(float(np.median(fr[cm])), 3), fraksi_lt_0_5=round(float((fr[cm] < 0.5).mean()), 3),
                        fraksi_lt_0_1=round(float((fr[cm] < 0.1).mean()), 3), cot_median_fraksi_lt0_1=round(float(np.median(cot[cm & (fr < 0.1)])), 2), cot_median_fraksi_gt0_9=round(float(np.median(cot[cm & (fr > 0.9)])), 2),
                        mean_x_count_cek=round(float(np.nanmedian(C.CLOT_coverage.to_numpy(float)[cm] - fr[cm])), 4), cltype_ada=int(np.isfinite(C.CLTYPE_mean.to_numpy(float)).sum())))
    # C5 retrieval dan zenit matahari
    for a, b in ((0, 30), (30, 50), (50, 60), (60, 70), (70, 80), (80, 90)):
        m = ada & (sza >= a) & (sza < b)
        O["C5"].append(dict(stasiun=s, sza=f"{a}-{b}", slot=int(m.sum()), cot_ada=round(float(np.isfinite(cot[m]).mean()), 3), fraksi_awan_median=round(float(np.nanmedian(fr[m])), 3),
                            cot_median=round(float(np.nanmedian(cot[m])), 2), cer_median=round(float(np.nanmedian(cer[m])), 2), cth_median=round(float(np.nanmedian(cth[m])), 2)))
    # C6 geometri pandang
    v = vza(la, lo); cthd = cth[np.isfinite(cth) & (sza < 70)]
    O["C6"].append(dict(stasiun=s, vza_deg=round(float(v), 1), cth_median=round(float(np.median(cthd)), 2), cth_p90=round(float(np.percentile(cthd, 90)), 2),
                        paralaks_km_median=round(float(np.median(cthd) * np.tan(np.radians(v))), 1), paralaks_km_p90=round(float(np.percentile(cthd, 90) * np.tan(np.radians(v))), 1), arah="menjauhi titik subsatelit (tampak ke barat; awan sebenarnya di timur)"))
    # C7 silang dengan SYNOP (pada slot V6.1)
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "clp_cth_km", "clp_cot", "synop_cl", "synop_cm", "synop_ch", "synop_cloud_cover_oktas", "ghi_wm2", "solar_elev_deg"])
    X = C.set_index(C.tt + pd.Timedelta(minutes=10)).reindex(pd.DatetimeIndex(d.ts_wib)); frd = X.CLOT_count.fillna(0).to_numpy() / 121.0; frd[X.source_file.isna().to_numpy()] = np.nan
    if s == "kalbar": frd = X.CLOT_count.fillna(0).to_numpy() / 110.0; frd[X.source_file.isna().to_numpy()] = np.nan
    syn = d.synop_cloud_cover_oktas.notna().to_numpy() & (d.solar_elev_deg.to_numpy() > 15)
    cl, cmi, ch = (pd.to_numeric(d[c], errors="coerce").to_numpy() for c in ("synop_cl", "synop_cm", "synop_ch")); ct = d.clp_cth_km.to_numpy(float); ok = (d.clp_cot.to_numpy(float) > 0)
    hanya_ch = syn & (cl == 0) & (cmi == 0) & (ch > 0); hanya_cl = syn & (cl > 0) & (cmi == 0) & (ch == 0)
    ok_ = syn & np.isfinite(frd)
    rho = spearmanr(frd[ok_], d.synop_cloud_cover_oktas.to_numpy()[ok_]).correlation if ok_.sum() > 100 else np.nan
    okt = pd.Series(frd[ok_]).groupby(d.synop_cloud_cover_oktas.to_numpy()[ok_]).median().round(2).to_dict()
    O["C7"].append(dict(stasiun=s, n_hanya_CH=int((hanya_ch & ok).sum()), cth_median_hanya_CH=round(float(np.nanmedian(ct[hanya_ch & ok])), 2) if (hanya_ch & ok).sum() else np.nan,
                        n_hanya_CL=int((hanya_cl & ok).sum()), cth_median_hanya_CL=round(float(np.nanmedian(ct[hanya_cl & ok])), 2) if (hanya_cl & ok).sum() else np.nan,
                        spearman_fraksi_okta=round(float(rho), 3), fraksi_median_per_okta=str(okt)))
    print(s, "selesai", flush=True)
for k, L in O.items():
    T = pd.DataFrame(L); T.to_csv(os.path.join(HERE, f"{k}.csv"), index=False); print("==", k); print(T.to_string(index=False))
