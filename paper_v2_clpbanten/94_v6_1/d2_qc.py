# -*- coding: utf-8 -*-
"""Tahap 94 A2: bendera QC per slot gaya BSRN untuk GHI, DHI, DNI, reflected (kode asal) + bit uji fisis Long & Shi (2008) pada nilai akhir.
Membaca V6 (00_data, provenance) hanya-baca; menulis Balai_data_v6_1/qc/{s}_qc.parquet. Nilai radiasi tidak diubah."""
import os, json, numpy as np, pandas as pd, pvlib
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
HERE = os.path.dirname(os.path.abspath(__file__)); V6 = r"C:\Users\ariff\Documents\Balai_data_v6"; OUT = r"C:\Users\ariff\Documents\Balai_data_v6_1\qc"; os.makedirs(OUT, exist_ok=True)
META = dict(banten=(-6.26147, 106.7509, 27), bengkulu=(-3.8607, 102.3381, 9), jambi=(-1.60111, 103.4944, 24), jogja=(-7.731064, 110.353578, 182), kalbar=(0.07489, 109.1905, 2), semarang=(-6.9847, 110.3812, 6))
SEK = {"portal", "db", "db_trapesium", "tabel_10min", "lainnya"}; DB_UKUR = {"measured", "measured_qc_corrected"}
L = {}
for s, (la, lo, alt) in META.items():
    d = pd.read_parquet(os.path.join(V6, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "ghi_wm2", "dhi_wm2", "dni_wm2", "reflected_wm2"])
    p = pd.read_parquet(os.path.join(V6, "provenance", f"{s}_provenance.parquet"), columns=["ts_wib", "ghi_sumber", "ghi_origin_v2", "dhi_status", "dni_status", "refl_status"])
    assert (d.ts_wib.values == p.ts_wib.values).all()
    idx = pd.DatetimeIndex(d.ts_wib).tz_localize("Etc/GMT-7"); sp = pvlib.solarposition.get_solarposition(idx + pd.Timedelta(minutes=5), la, lo, altitude=alt)   # titik tengah interval
    Z = sp.apparent_zenith.to_numpy(); mu = np.cos(np.radians(Z)); el = 90 - Z; Sa = 1361.0 * (1 + 0.033 * np.cos(2 * np.pi * idx.dayofyear.to_numpy() / 365.0))
    G, Dh, Dn, Rf = (d[c].to_numpy(float) for c in ("ghi_wm2", "dhi_wm2", "dni_wm2", "reflected_wm2"))
    gs, g2, ds, ns, rs = (p[c].astype(str).to_numpy() for c in ("ghi_sumber", "ghi_origin_v2", "dhi_status", "dni_status", "refl_status"))
    # kode asal GHI
    qg = np.full(len(d), 9, np.int8)
    qg[gs == "logger"] = 0
    sek = np.isin(gs, list(SEK)); qg[sek] = 1; qg[sek & (gs == "db") & ~np.isin(g2, list(DB_UKUR))] = 3
    qg[gs == "batas_fisis"] = 2; qg[gs == "estimasi_aws"] = 3; qg[gs == "malam"] = 8
    # DHI, DNI, reflected: 'asli' mengikuti sumber GHI baris itu
    def kode(st, base):
        q = np.full(len(d), 9, np.int8); a = (st == "asli") | (st == "logger_2022"); q[a] = np.where(st[a] == "logger_2022", 0, base[a])
        q[st == "diperbaiki_tahap85"] = 2; q[np.isin(st, ["model_isi", "hitung_neraca", "albedo"])] = 3; return q
    qd, qn, qr = kode(ds, np.where(qg == 2, 1, qg)), kode(ns, np.where(qg == 2, 1, qg)), kode(rs, np.where(qg == 2, 1, qg))
    # neraca tertutup persis pada status 'asli' = dimodelkan di sumber (misalnya DHI/DNI Bengkulu tahun latih)
    mu_t = np.sin(np.radians(pd.read_parquet(os.path.join(V6, "00_data", f"{s}_full.parquet"), columns=["solar_elev_deg"]).solar_elev_deg.to_numpy(float)))   # elevasi awal slot (konvensi DB v2 dan tahap 85)
    with np.errstate(all="ignore"): tutup = (G > 50) & ((np.abs(G - (Dh + Dn * mu)) < 0.5) | (np.abs(G - (Dh + Dn * mu_t)) < 0.5)) & np.isin(ds, ["asli"]) & np.isin(ns, ["asli"])
    qd[tutup & (qd < 3)] = 3; qn[tutup & (qn < 3)] = 3
    malam = el <= 0
    for q, x in ((qg, G), (qd, Dh), (qn, Dn), (qr, Rf)):
        q[malam & np.isfinite(x)] = 8; q[~np.isfinite(x)] = 9
    # bit uji BSRN pada nilai akhir (siang)
    u = np.zeros(len(d), np.uint8); dy = mu > 0
    with np.errstate(all="ignore"):
        m12 = np.where(dy, mu, 0) ** 1.2; m02 = np.where(dy, mu, 0) ** 0.2
        tests = [(G < -4) | (G > Sa * 1.5 * m12 + 100), (Dh < -4) | (Dh > Sa * 0.95 * m12 + 50), (Dn < -4) | (Dn > Sa), (G > Sa * 1.2 * m12 + 50), (Dh > Sa * 0.75 * m12 + 30), (Dn > Sa * 0.95 * m02 + 10)]
        ratio = G / (Dh + Dn * mu); cmp = (G > 50) & (((Z < 75) & (np.abs(ratio - 1) > 0.08)) | ((Z >= 75) & (Z < 93) & (np.abs(ratio - 1) > 0.15)))
        dif = (G > 50) & (((Z < 75) & (Dh / G > 1.05)) | ((Z >= 75) & (Z < 93) & (Dh / G > 1.10)))
    for b, t in enumerate(tests + [cmp, dif]): u[dy & np.nan_to_num(t, nan=False).astype(bool)] |= np.uint8(1 << b)
    Q = pd.DataFrame({"ts_wib": d.ts_wib.values, "qc_ghi": qg, "qc_dhi": qd, "qc_dni": qn, "qc_refl": qr, "qc_uji": u})
    Q.to_parquet(os.path.join(OUT, f"{s}_qc.parquet"), index=False)
    siang = el > 5
    L[s] = {k: Q.loc[siang, k].value_counts().sort_index().to_dict() for k in ("qc_ghi", "qc_dhi", "qc_dni", "qc_refl")} | {"uji_gagal_siang": {f"bit{b}": int(((u >> b) & 1)[siang].sum()) for b in range(8)}, "neraca_tutup_persis": int(tutup.sum()),
             "sumber_tak_terpetakan": sorted(set(gs[qg == 9][np.isfinite(G[qg == 9])]))}
    print(s, json.dumps({k: {str(a): int(b) for a, b in v.items()} if isinstance(v, dict) else v for k, v in L[s].items()}, ensure_ascii=False), flush=True)
json.dump({s: {k: ({str(a): int(b) for a, b in v.items()} if isinstance(v, dict) else v) for k, v in x.items()} for s, x in L.items()}, open(os.path.join(HERE, "d2_qc_ringkas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
