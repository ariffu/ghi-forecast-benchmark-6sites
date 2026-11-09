# -*- coding: utf-8 -*-
"""Tahap 101 (salinan uji tahap 98 untuk V6.4) uji baru V6.2 (hanya membaca):
H1 fisis fraksi awan (k_c per kelas fraksi, siklus harian, hubungan dengan COT) — tahun latih 2022–2023 saja;
H2 piksel CLP tanpa COT (retrieval 'Failed' menurut FAQ JAXA) dari hitungan CLTT/CLTH/CLTYPE lawan CLOT;
H3 simetri k_c cerah Bengkulu, clear-sky V6.1 lawan V6.2;
H4 kebocoran waktu 44 prediktor P2F (korelasi dengan k_c pada t−30 … t+60);
H5 kelengkapan dan pergeseran sebaran prediktor latih/validasi/uji."""
import os, re, io, sys, zipfile, numpy as np, pandas as pd
from scipy.stats import spearmanr
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); V1 = r"C:\Users\ariff\Documents\Balai_data_v6_3"; V2 = r"C:\Users\ariff\Documents\Balai_data_v6_6"
os.environ.update(DATA_DIR=os.path.join(V2, "00_data"), CLEARSKY_DIR=os.path.join(V2, "clearsky"), FEATSET="P2F", CLP_EKSTRA_DIR=os.path.join(V2, "clp_ekstra"))
sys.path.insert(0, B); import _common
ZIP = r"C:\Users\ariff\Documents\6lokasi_output_chips.zip"; LOK = {"banten": "sta6016_banten", "bengkulu": "sta6009_bengkulu", "jambi": "sta6007_jambi", "jogja": "sta6010_jogja", "kalbar": "sta6003_kalbar", "semarang": "sta6018_jateng"}
def corr(a, b):
    m = np.isfinite(a) & np.isfinite(b); return float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() > 200 and np.nanstd(a[m]) > 0 else np.nan
O = {k: [] for k in ("H1", "H1b", "H2", "H3", "H4", "H5")}; z = zipfile.ZipFile(ZIP); NM = z.namelist()
for s in _common.SITES:
    df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean"); assert len(feats) == 44
    ts = pd.DatetimeIndex(df.ts_wib); el = df.solar_elev_deg.to_numpy(float); kc = df.kt.to_numpy(float); fr = df.clp_cloud_frac.to_numpy(float); cot = df.clp_cot.to_numpy(float)
    e = pd.read_parquet(os.path.join(V2, "clp_ekstra", f"{s}_clp_ekstra.parquet")); q = e.qc_clp_sza.to_numpy()
    lat = (ts.year <= 2023) & (el > 30) & np.isfinite(kc) & np.isfinite(fr) & (q == 0)
    # H1 k_c per kelas fraksi
    b = pd.cut(fr[lat], [-0.001, 0.05, 0.2, 0.4, 0.6, 0.8, 0.95, 1.0]); g = pd.Series(kc[lat]).groupby(b, observed=True).median()
    O["H1"].append(dict(stasiun=s, n=int(lat.sum()), **{f"kc|f{k}": round(v, 3) for k, v in g.items()}, monoton_turun=bool(np.all(np.diff(g.to_numpy()) < 0.02)),
                        spearman_kc_frac=round(spearmanr(kc[lat], fr[lat]).correlation, 3), spearman_kc_cot=round(spearmanr(kc[lat & np.isfinite(cot)], cot[lat & np.isfinite(cot)]).correlation, 3),
                        spearman_kc_fracxcot=round(spearmanr(kc[lat], fr[lat] * np.nan_to_num(cot[lat], nan=0.0)).correlation, 3), r_frac_cot=round(spearmanr(fr[lat & np.isfinite(cot)], cot[lat & np.isfinite(cot)]).correlation, 3)))
    hh = pd.Series(fr[(ts.year <= 2023) & (q == 0)]).groupby(ts[(ts.year <= 2023) & (q == 0)].hour).median().round(2)
    O["H1b"].append(dict(stasiun=s, **{f"jam{h:02d}": v for h, v in hh.items()}))
    # H2 piksel tanpa COT
    F = sorted(n for n in NM if re.search(rf"{LOK[s]}/CLP_{LOK[s]}_\d{{4}}-\d\d-\d\d\.csv$", n))
    C = pd.concat([pd.read_csv(io.BytesIO(z.read(n))).reindex(columns=["source_file", "total_pixels", "CLOT_count", "CLTT_count", "CLTH_count", "CLER_23_count", "CLTYPE_count", "CLTYPE_median"]) for n in F], ignore_index=True)
    C = C[C.source_file.notna()]; c0 = C.CLOT_count.fillna(0); r2 = dict(stasiun=s, berkas=len(C))
    for v in ("CLTT", "CLTH", "CLER_23", "CLTYPE"):
        cv = C[f"{v}_count"].fillna(0); r2[f"{v}>CLOT_slot_%"] = round(100 * float((cv > c0).mean()), 2); r2[f"{v}<CLOT_slot_%"] = round(100 * float((cv < c0).mean()), 2); r2[f"{v}-CLOT_rerata_piksel"] = round(float((cv - c0).mean()), 2)
    r2["CLTYPE_median_nilai"] = str(C.CLTYPE_median.dropna().round().value_counts().sort_index().astype(int).to_dict()); O["H2"].append(r2)
    # H4 kebocoran waktu
    m15 = el > 15
    for f in feats:
        x = pd.to_numeric(df[f], errors="coerce").to_numpy(float); rr = {}
        for k in range(-3, 7):
            y = pd.Series(kc).shift(-k).to_numpy(); rr[k * 10] = corr(x[m15], y[m15])
        if all(not np.isfinite(v) for v in rr.values()): continue
        pk = max(rr, key=lambda a: abs(rr[a]) if np.isfinite(rr[a]) else -1)
        O["H4"].append(dict(stasiun=s, prediktor=f, puncak_mnt=pk, r_puncak=round(rr[pk], 3), r_tmin10=round(rr[-10], 3), r_t0=round(rr[0], 3), r_t10=round(rr[10], 3), r_t60=round(rr[60], 3)))
    # H5 kelengkapan dan pergeseran
    for f in feats:
        x = pd.to_numeric(df[f], errors="coerce").to_numpy(float)
        a, v, t = x[tr], x[va], x[te]; iqr = np.nanpercentile(a, 75) - np.nanpercentile(a, 25) if np.isfinite(a).any() else np.nan
        O["H5"].append(dict(stasiun=s, prediktor=f, kosong_latih=round(float(np.isnan(a).mean()), 3), kosong_val=round(float(np.isnan(v).mean()), 3), kosong_uji=round(float(np.isnan(t).mean()), 3),
                            geser_median_uji_per_IQR=round(float((np.nanmedian(t) - np.nanmedian(a)) / iqr), 3) if iqr and np.isfinite(iqr) and iqr > 0 else np.nan, unik_latih=int(len(np.unique(a[np.isfinite(a)])))))
    print(s, "selesai", flush=True)
# H3 simetri k_c cerah Bengkulu
for lab, V in (("V6.3", V1), ("V6.4", V2)):
    d = pd.read_parquet(os.path.join(V2, "00_data", "bengkulu_full.parquet"), columns=["ts_wib", "ghi_wm2", "solar_elev_deg", "kt"]); cs = pd.read_parquet(os.path.join(V, "clearsky", "bengkulu_ineichen.parquet")).ghi_cs.to_numpy()
    g = d.ghi_wm2.to_numpy(float); el = d.solar_elev_deg.to_numpy(float); hr = pd.DatetimeIndex(d.ts_wib).hour.to_numpy()
    with np.errstate(all="ignore"): k = np.where(d.kt.notna().to_numpy() & (cs > 50), g / cs, np.nan)
    K = pd.Series(k); cl = ((K.rolling(6, center=True, min_periods=6).std() < 0.03) & K.rolling(6, center=True, min_periods=6).mean().between(0.85, 1.15)).to_numpy()
    r = dict(clear_sky=lab, slot_cerah=int(cl.sum()))
    for lo, hi in ((10, 20), (20, 40), (40, 60)):
        m = cl & (el > lo) & (el <= hi); r[f"pagi−sore el{lo}-{hi}"] = round(float(np.nanmedian(k[m & (hr < 12)]) - np.nanmedian(k[m & (hr >= 12)])), 4)
    O["H3"].append(r)
for k_, L in O.items():
    T = pd.DataFrame(L); T.to_csv(os.path.join(HERE, f"{k_}.csv"), index=False)
    if k_ == "H4":
        f = T[(T.puncak_mnt >= 10) & (T.r_puncak.abs() > T.r_t0.abs() + 0.02)]; print("== H4 prediktor yang paling kuat di masa depan (≥ t+10) dan > |r(t)| + 0,02:"); print(f.to_string(index=False) if len(f) else "  tidak ada")
        print("== H4 CLP:"); print(T[T.prediktor.str.startswith("clp_")].to_string(index=False))
    elif k_ == "H5":
        f = T[((T.kosong_uji - T.kosong_latih).abs() > 0.1) | (T.geser_median_uji_per_IQR.abs() > 0.5) | (T.unik_latih <= 2)]; print("== H5 kelengkapan beda > 10 poin, geser median > 0,5 IQR, atau ≤ 2 nilai unik:"); print(f.to_string(index=False))
    else: print("==", k_); print(T.to_string(index=False))
