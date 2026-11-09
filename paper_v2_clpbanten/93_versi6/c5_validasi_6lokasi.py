# -*- coding: utf-8 -*-
"""Tahap 93: validasi ekstraksi ulang CLP enam lokasi (6lokasi_output_chips.zip): koordinat, timestamp, skala ganda, fisis, kecocokan dengan
piksel chips 71 hari, kesamaan CSV lama dengan V5, dan perbandingan kotak baru lawan V5. Hanya membaca."""
import zipfile, io, re, os, math, json, numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
HERE = os.path.dirname(os.path.abspath(__file__)); Z = zipfile.ZipFile(r"C:\Users\ariff\Documents\6lokasi_output_chips.zip"); NM = Z.namelist()
V5 = r"C:\Users\ariff\Documents\Balai_data_v5_final87\00_data"; KUB = r"C:\Users\ariff\Documents\chips\chips_asrs_audit\kubus"
LOK = {"banten": "sta6016_banten", "bengkulu": "sta6009_bengkulu", "jambi": "sta6007_jambi", "jogja": "sta6010_jogja", "kalbar": "sta6003_kalbar", "semarang": "sta6018_jateng"}
T1 = dict(banten=(-6.26147, 106.7509), bengkulu=(-3.8607, 102.3381), jambi=(-1.5833, 103.6667), jogja=(-7.731064, 110.353578), kalbar=(0.07489, 109.1905), semarang=(-6.9847, 110.3812))
ASRS_JAMBI = (-1.60111, 103.4944); SK = {"CLOT": (0.01, 0.0), "CLTT": (0.01, 150.0), "CLTH": (0.001, 0.0), "CLER_23": (0.01, 0.0)}
def km(a, b): la = math.radians((a[0] + b[0]) / 2); return 111.2 * math.hypot(a[0] - b[0], (a[1] - b[1]) * math.cos(la))
def baca(site, station):
    pat = rf"{site}/CLP_{site}_{'station_' if station else ''}\d{{4}}-\d\d-\d\d\.csv$"; L = [pd.read_csv(io.BytesIO(Z.read(n))) for n in sorted(NM) if re.search(pat, n)]
    d = pd.concat(L, ignore_index=True); d["tt"] = pd.to_datetime(d.timestamp); return d, len(L)
def balik(C):
    dm = C.groupby(C.tt.dt.date).CLTT_mean.median(); gh = set(dm[dm < 160].index); g = C.tt.dt.date.isin(gh).to_numpy()
    for v, (sc, of) in SK.items():
        for st in ("mean", "median", "min", "max"):
            c = f"{v}_{st}"
            if c in C: C.loc[g, c] = (C.loc[g, c] - of) / sc
        if f"{v}_std" in C: C.loc[g, f"{v}_std"] = C.loc[g, f"{v}_std"] / sc
    return C, gh
R = {}
for s, site in LOK.items():
    r = {}; B, nb = baca(site, False); O, no = baca(site, True)
    la, lo = float(B.station_lat.iloc[0]), float(B.station_lon.iloc[0]); r["hari_baru"] = nb; r["hari_lama"] = no
    r["pusat_baru"] = (la, lo); r["pusat_unik"] = int(B[["station_lat", "station_lon"]].drop_duplicates().shape[0]); r["grid"] = B.grid_size.unique().tolist(); r["buffer_km"] = B.buffer_km.unique().tolist()
    r["pusat_lama"] = tuple(O[["station_lat", "station_lon"]].iloc[0].round(5)); r["jarak_baru_ke_lama_km"] = round(km((la, lo), r["pusat_lama"]), 2); r["jarak_baru_ke_tabel1_km"] = round(km((la, lo), T1[s]), 2)
    if s == "jambi": r["jarak_baru_ke_ASRS_km"] = round(km((la, lo), ASRS_JAMBI), 2)
    r["duplikat"] = int(B.tt.duplicated().sum()); r["slot_per_hari"] = B.groupby(B.tt.dt.date).size().value_counts().head(3).to_dict()
    ft = pd.to_datetime(B.file_timestamp_utc); r["ts_minus7_eq_berkas"] = float(((B.tt - pd.Timedelta(hours=7)) == ft).mean())
    fn = pd.to_datetime(B.source_file.str.extract(r"_(\d{8}_\d{4})_")[0], format="%Y%m%d_%H%M"); r["nama_berkas_eq_kolom"] = float((fn == ft).mean())
    r["satelit_eq_nama"] = float((B.source_file.str.extract(r"NC_(H0\d)_")[0] == B.satellite).mean())
    B, gh = balik(B); r["hari_skala_ganda"] = len(gh); r["ganda_mulai"] = str(min(gh)) if gh else None; r["ganda_selesai"] = str(max(gh)) if gh else None
    for c, lo_, hi_ in (("CLOT_mean", 0, 150), ("CLTT_mean", 180, 315), ("CLTH_mean", 0, 20), ("CLER_23_mean", 0, 100)):
        x = B[c].dropna(); r[f"{c}_luar"] = int(((x < lo_ - 1e-6) | (x > hi_ + 1e-6)).sum()); r[f"{c}_p50"] = round(float(x.median()), 2)
    q = B.CLTT_mean.notna() & B.CLTH_mean.notna(); r["r_ctt_cth"] = round(float(np.corrcoef(B.CLTT_mean[q], B.CLTH_mean[q])[0, 1]), 3); r["lereng"] = round(float(np.polyfit(B.CLTH_mean[q], B.CLTT_mean[q], 1)[0]), 2)
    # piksel 71 hari
    K = np.load(os.path.join(KUB, f"kubus_{site}.npz"), allow_pickle=False); ts = pd.to_datetime(K["ts"], unit="m").round("min"); lat, lon = K["lat"].astype(float), K["lon"].astype(float); M = K["meta"]
    tau = np.where(K["CLOT"] > -32000, K["CLOT"] * M[0][0], np.nan).astype(float); tau[(tau < 0) | (tau > 150)] = np.nan
    i = int(np.argmin(np.abs(lat - la))); j = int(np.argmin(np.abs(lon - lo))); b = tau[:, i - 5:i + 6, j - 5:j + 6]; n = np.isfinite(b).sum((1, 2)); mpx = np.full(len(b), np.nan); ok = n > 0; mpx[ok] = np.nansum(b[ok], (1, 2)) / n[ok]
    c = B.set_index("tt").CLOT_mean.reindex(ts).to_numpy(); w = np.isfinite(mpx) & np.isfinite(c)
    r["piksel_r"] = round(float(np.corrcoef(mpx[w], c[w])[0, 1]), 5); r["piksel_rmse"] = round(float(np.sqrt(np.mean((mpx[w] - c[w]) ** 2))), 4); r["piksel_n"] = int(w.sum())
    r["piksel_jumlah_sama"] = round(float((n[w] == B.set_index("tt").CLOT_count.reindex(ts).to_numpy()[w]).mean()), 4)
    # V5: CSV lama dan baru pada t = T + 10
    V = pd.read_parquet(os.path.join(V5, f"{s}_full.parquet"), columns=["ts_wib", "clp_cot", "solar_elev_deg"]).set_index("ts_wib").sort_index()
    for lab, X in (("lama", O), ("baru", B)):
        cc = X.set_index("tt").CLOT_mean; v = V.clp_cot.reindex(cc.index + pd.Timedelta(minutes=10)).to_numpy(); ww = cc.notna().to_numpy() & np.isfinite(v)
        r[f"{lab}_lawan_V5_r"] = round(float(np.corrcoef(cc.to_numpy()[ww], v[ww])[0, 1]), 4); r[f"{lab}_lawan_V5_rmse"] = round(float(np.sqrt(np.mean((cc.to_numpy()[ww] - v[ww]) ** 2))), 3); r[f"{lab}_lawan_V5_sama"] = round(float(np.isclose(cc.to_numpy()[ww], v[ww], atol=1e-4).mean()), 4)
    R[s] = r; print(s, "selesai", flush=True)
    B.drop(columns=["tt"]).to_parquet(os.path.join(HERE, f"_csv_baru_dibalik_{s}.parquet"), index=False)
T = pd.DataFrame(R); print(T.to_string()); T.to_csv(os.path.join(HERE, "c5_validasi_6lokasi.csv"))
# Jambi: sama dengan sta6007_jambi.zip pada 876 hari?
z2 = zipfile.ZipFile(r"C:\Users\ariff\Documents\sta6007_jambi.zip"); a = {os.path.basename(i.filename): i.CRC for i in z2.infolist() if re.search(r"CLP_sta6007_jambi_\d{4}", i.filename)}
b = {os.path.basename(i.filename): i.CRC for i in Z.infolist() if re.search(r"CLP_sta6007_jambi_\d{4}", i.filename)}
same = sum(1 for k in a if b.get(k) == a[k]); print(f"Jambi: {len(a)} CSV di sta6007_jambi.zip, {same} identik CRC dengan zip baru; zip baru {len(b)} CSV")
