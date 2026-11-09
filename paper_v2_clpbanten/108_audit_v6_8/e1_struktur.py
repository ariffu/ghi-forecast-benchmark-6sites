# -*- coding: utf-8 -*-
"""Tahap 108 (salinan untuk V6.8) (salinan uji tahap 98 untuk V6.4) (salinan uji tahap 95 untuk V6.2) S1–S3: struktur, hash, posisi matahari, koordinat. Hanya membaca Balai_data_v6_8."""
import os, hashlib, json, numpy as np, pandas as pd, pvlib
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_8"
S = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
META = dict(banten=(-6.26147, 106.7509, 27), bengkulu=(-3.864930, 102.311998, 9), jambi=(-1.60111, 103.4944, 24), jogja=(-7.731064, 110.353578, 182), kalbar=(0.07489, 109.1905, 2), semarang=(-6.9847, 110.3812, 6))
CLP = dict(banten=(-6.2615, 106.7508), bengkulu=(-3.86, 102.31), jambi=(-1.602, 103.485), jogja=(-7.731, 110.354), kalbar=(0.075, 109.19), semarang=(-6.9847, 110.3806))
BKL_USER = (-3.864930, 102.311998)
def km(a, b):
    la1, lo1, la2, lo2 = map(np.radians, (a[0], a[1], b[0], b[1]))
    h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2; return 6371.0 * 2 * np.arcsin(np.sqrt(h))
# S1 hash
sha = {}
for ln in open(os.path.join(V, "SHA256.txt"), encoding="utf-8"):
    p = ln.strip().split(None, 1)
    if len(p) == 2: sha[p[1].strip().lstrip("*").replace("\\", "/")] = p[0].lower()
bad = []
for rel, h in sha.items():
    f = os.path.join(V, rel)
    if not os.path.exists(f): bad.append((rel, "hilang")); continue
    m = hashlib.sha256(); fh = open(f, "rb")
    for b in iter(lambda: fh.read(1 << 22), b""): m.update(b)
    if m.hexdigest() != h: bad.append((rel, "beda"))
semua = sorted(os.path.relpath(os.path.join(r, f), V).replace("\\", "/") for r, _, fs in os.walk(V) for f in fs)
print("S1 hash: tercatat", len(sha), "| tidak cocok", bad, "| berkas tak tercatat", [f for f in semua if f not in sha and f != "SHA256.txt"])
full = pd.date_range("2022-01-01", "2025-12-31 23:50", freq="10min"); R1 = []; R2 = []; R3 = []
for s in S:
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet")); r = pd.read_parquet(os.path.join(V, "00_data_rawfill", f"{s}_full.parquet"), columns=["ts_wib"])
    c = pd.read_parquet(os.path.join(V, "clearsky", f"{s}_ineichen.parquet")); q = pd.read_parquet(os.path.join(V, "qc", f"{s}_qc.parquet")); p = pd.read_parquet(os.path.join(V, "provenance", f"{s}_provenance.parquet"), columns=["ts_wib"])
    ts = pd.DatetimeIndex(d.ts_wib)
    R1.append(dict(stasiun=s, baris=len(d), kolom=d.shape[1], grid_lengkap=bool(len(ts) == len(full) and (ts == full).all()), duplikat=int(ts.duplicated().sum()),
                   sejajar_rawfill=bool((r.ts_wib.values == d.ts_wib.values).all()), sejajar_clearsky=bool((c.ts_wib.values == d.ts_wib.values).all()),
                   sejajar_qc=bool((q.ts_wib.values == d.ts_wib.values).all()), sejajar_prov=bool((p.ts_wib.values == d.ts_wib.values).all()), site_id=",".join(map(str, d.site_id.unique()))))
    # S2 posisi matahari: cari geseran waktu dan koordinat yang cocok dengan solar_elev_deg
    el = d.solar_elev_deg.to_numpy(float); m = np.isfinite(el) & (el > 2); k = np.where(m)[0][::13]
    loc = META[s]; best = None
    for lab, (la, lo) in (("Tabel 1", loc[:2]), ("pusat CLP", CLP[s])) + ((("pengguna", BKL_USER),) if s == "bengkulu" else ()):
        for off in range(-10, 11):
            sp = pvlib.solarposition.get_solarposition(ts[k].tz_localize("Etc/GMT-7") + pd.Timedelta(minutes=off), la, lo, altitude=loc[2])
            for kind in ("elevation", "apparent_elevation"):
                e = float(np.sqrt(np.mean((sp[kind].to_numpy() - el[k]) ** 2)))
                R2.append(dict(stasiun=s, koordinat=lab, geser_mnt=off, jenis=kind, rmse_deg=round(e, 4)))
    # S3 koordinat
    a = loc[:2]; R3.append(dict(stasiun=s, tabel1=a, pusat_clp=CLP[s], km_tabel1_clp=round(km(a, CLP[s]), 2), **({"pengguna": BKL_USER, "km_pengguna_tabel1": round(km(BKL_USER, a), 2), "km_pengguna_clp": round(km(BKL_USER, CLP[s]), 2)} if s == "bengkulu" else {})))
    print(s, "selesai", flush=True)
T1 = pd.DataFrame(R1); T1.to_csv(os.path.join(HERE, "S1_struktur.csv"), index=False); print(T1.to_string(index=False))
T2 = pd.DataFrame(R2); T2.to_csv(os.path.join(HERE, "S2_posisi_matahari.csv"), index=False)
print(T2.loc[T2.groupby(["stasiun", "koordinat"]).rmse_deg.idxmin()].to_string(index=False))
T3 = pd.DataFrame(R3); T3.to_csv(os.path.join(HERE, "S3_koordinat.csv"), index=False); print(T3.to_string(index=False))
# dampak koordinat Bengkulu pengguna pada clear-sky interval
t1 = pd.date_range("2022-01-01 00:00", "2026-01-01 00:59", freq="1min", tz="Etc/GMT-7"); out = {}
for lab, (la, lo) in (("Tabel 1", META["bengkulu"][:2]), ("pengguna", BKL_USER)):
    L = pvlib.location.Location(la, lo, tz="Etc/GMT-7", altitude=9); lt = pvlib.clearsky.lookup_linke_turbidity(t1, la, lo, interp_turbidity=True)
    out[lab] = L.get_clearsky(t1, model="ineichen", linke_turbidity=lt).ghi.groupby(t1.floor("10min")).mean(); out[lab + "_linke"] = float(lt.mean())
v61 = pd.read_parquet(os.path.join(V, "clearsky", "bengkulu_ineichen.parquet")).set_index("ts_wib").ghi_cs
a, b = out["Tabel 1"].to_numpy(), out["pengguna"].to_numpy(); n = min(len(a), len(v61)); idx = out["Tabel 1"].index[:n]
ok = a[:n] > 50; rr = b[:n][ok] / a[:n][ok]; hr = idx.hour[ok]
print("S3 Bengkulu clear-sky: reproduksi V6.1 maks |selisih| =", round(float(np.nanmax(np.abs(a[:n] - v61.to_numpy()[:n]))), 4), "W m-2; Linke rerata Tabel 1/pengguna", round(out["Tabel 1_linke"], 4), round(out["pengguna_linke"], 4))
print("  rasio pengguna/Tabel 1 (GHI_cs > 50): median", round(float(np.median(rr)), 5), "pagi < 8 WIB", round(float(np.median(rr[hr < 8])), 5), "sore ≥ 17", round(float(np.median(rr[hr >= 17])), 5), "min", round(float(rr.min()), 4), "maks", round(float(rr.max()), 4))
json.dump(dict(hash_tidak_cocok=bad), open(os.path.join(HERE, "S1_hash.json"), "w"), indent=1)
