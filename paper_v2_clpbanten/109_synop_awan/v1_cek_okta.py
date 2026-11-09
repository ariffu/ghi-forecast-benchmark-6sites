# -*- coding: utf-8 -*-
"""Tahap 109 v1: cek okta (N), CL, CM, CH SYNOP Jambi dan Yogyakarta (Mlati) dari berkas pengguna terhadap database V6.8. Hanya membaca.
Argumen: <csv jambi> <csv mlati>. Kolom nama pengamat tidak dibaca. Juga dekode sandi SYNOP mentah (Nddff dan 8NhCLCMCH) sebagai cek silang."""
import os, re, sys, numpy as np, pandas as pd
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_8"
K = ["data_timestamp", "cloud_cover_oktas_m", "cloud_low_type_cl", "cloud_low_cover_oktas", "cloud_med_type_cm", "cloud_high_type_ch", "present_weather_ww", "visibility_vv", "encoded_synop"]
def dekode(s):
    """N dari kelompok Nddff (kelompok ketiga sesudah IIiii) dan Nh/CL/CM/CH dari kelompok 8NhCLCMCH di seksi 1."""
    if not isinstance(s, str): return (np.nan,) * 5
    g = re.findall(r"\b[0-9/]{5}\b", s.replace("\n", " "))
    try:
        i = next(k for k, x in enumerate(g) if re.fullmatch(r"9\d{4}", x) and k + 2 < len(g))    # IIiii (9xxxx)
    except StopIteration: return (np.nan,) * 5
    sec = g[i + 1:]; N = sec[1][0] if len(sec) > 1 else "/"
    try: k8 = next(x for x in sec[2:] if x.startswith("8") and not x.startswith("8/")) if any(x.startswith("8") for x in sec[2:]) else None
    except StopIteration: k8 = None
    for x in sec[2:]:
        if x.startswith("333") or x.startswith("555"): break
    v = lambda ch: float(ch) if ch.isdigit() else np.nan
    if k8 is None: return (v(N), np.nan, np.nan, np.nan, np.nan)
    return (v(N), v(k8[1]), v(k8[2]), v(k8[3]), v(k8[4]))
R = {}
for s, f in (("jambi", sys.argv[1]), ("jogja", sys.argv[2])):
    F = pd.read_csv(f, usecols=K, engine="python"); F["t"] = pd.to_datetime(F.data_timestamp) + pd.Timedelta(hours=7); F = F.drop_duplicates("t").set_index("t").sort_index()
    for c in K[1:-1]: F[c] = pd.to_numeric(F[c], errors="coerce"); F.loc[F[c] > 99, c] = np.nan
    dec = pd.DataFrame([dekode(x) for x in F.encoded_synop], index=F.index, columns=["N_sandi", "Nh_sandi", "CL_sandi", "CM_sandi", "CH_sandi"]); F = F.join(dec)
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "synop_cloud_cover_oktas", "synop_cl", "synop_cm", "synop_ch", "synop_present_weather_ww"]).set_index("ts_wib")
    A = d.reindex(F.index); yr = F.index.year
    print(f"===== {s}: laporan {len(F)} ({F.index.min()} – {F.index.max()}), jam WIB: {sorted(set(F.index.hour))}")
    for c_f, c_s, c_d in (("cloud_cover_oktas_m", "N_sandi", "synop_cloud_cover_oktas"), ("cloud_low_type_cl", "CL_sandi", "synop_cl"), ("cloud_med_type_cm", "CM_sandi", "synop_cm"), ("cloud_high_type_ch", "CH_sandi", "synop_ch")):
        x, y, z = F[c_f], F[c_s], A[c_d]
        isi = x.notna().groupby(yr).mean().round(3).to_dict(); isi_db = z.notna().groupby(yr).mean().round(3).to_dict()
        m = x.notna() & z.notna(); sama = float((x[m] == z[m]).mean()) if m.any() else np.nan; m2 = x.notna() & y.notna()
        print(f"  {c_f:22s} isi berkas/thn {isi} | isi DB/thn {isi_db} | berkas==DB {sama:.3f} (n {int(m.sum())}) | berkas==sandi {float((x[m2] == y[m2]).mean()) if m2.any() else np.nan:.3f}")
    # okta: sebaran dan siklus harian
    N = F.cloud_cover_oktas_m; print("  sebaran N berkas:", N.value_counts().sort_index().astype(int).to_dict()); print("  sebaran N DB    :", A.synop_cloud_cover_oktas.value_counts().sort_index().astype(int).to_dict())
    print("  N rata-rata per jam WIB (berkas):", N[N <= 8].groupby(N[N <= 8].index.hour).mean().round(2).to_dict()); print("  N rata-rata per jam WIB (DB)    :", A.synop_cloud_cover_oktas[A.synop_cloud_cover_oktas <= 8].groupby(A.index[A.synop_cloud_cover_oktas <= 8].hour).mean().round(2).to_dict())
    # beda per tahun dan jam
    m = N.notna() & A.synop_cloud_cover_oktas.notna(); bd = (N != A.synop_cloud_cover_oktas) & m
    print("  N beda berkas–DB per tahun:", bd.groupby(yr).sum().astype(int).to_dict(), "| per jam (terbanyak):", bd.groupby(F.index.hour).sum().sort_values(ascending=False).head(4).astype(int).to_dict())
    R[s] = F
    F.drop(columns=["encoded_synop"]).to_parquet(os.path.join(HERE, f"v1_synop_awan_{s}.parquet"))
