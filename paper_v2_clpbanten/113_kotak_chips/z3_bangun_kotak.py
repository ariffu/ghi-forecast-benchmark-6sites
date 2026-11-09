# -*- coding: utf-8 -*-
"""Tahap 113 Z3: membangun statistik kotak CLP V6 (pengganti 28_clp_spatial/data yang berasal dari ekstraksi lama) -> Balai_kotak_v6_10 (beku).
Sumber nilai: CSV kotak 11x11 (Kalbar 10x11) di 6lokasi_output_chips.zip, sumber yang SAMA dengan clp_cot V6.10. Kotak dan waktunya
diverifikasi piksel demi piksel dengan chips_supplement_6.zip (Z1/Z2: CLOT_count = jumlah piksel COT sah, geseran 0). Nilai chip tidak
dipakai karena tersimpan sebagai bilangan bulat terpotong (COT, CTH km), sehingga simpangan baku CTH (~1 km) tidak terukur.
Konvensi V6 (c6_clp_6lokasi.py): t = T + 10; koreksi hari skala ganda (median CLTT < 160 K) untuk mean/median/min/max dan std (/skala).
Kosong bila tidak ada berkas; statistik COT/CTH kosong bila kotak tanpa piksel berawan (sama dengan clp_cot).
Fitur (definisi tahap 28): clps_cot_std, clps_cot_min, clps_cot_max, clps_cth_std, clps_cloud_frac (= clp_cloud_frac V6.10, tidak dipakai
sebagai SPAT karena sudah prediktor ke-44), clps_cloud_frac_lag_60m (= clp_cloud_frac digeser 6 slot), clps_cot_std_lag_60m."""
import io, re, os, json, stat, hashlib, zipfile, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_10"; OUT = r"C:\Users\ariff\Documents\Balai_kotak_v6_10"
assert not os.path.exists(OUT), "Balai_kotak_v6_10 sudah ada (beku); buat versi baru bila perlu mengubah"
os.makedirs(OUT + "_tmp", exist_ok=True); T = OUT + "_tmp"
ZS = zipfile.ZipFile(r"C:\Users\ariff\Documents\6lokasi_output_chips.zip"); NM = ZS.namelist()
LOK = {"banten": "sta6016_banten", "bengkulu": "sta6009_bengkulu", "jambi": "sta6007_jambi", "jogja": "sta6010_jogja", "kalbar": "sta6003_kalbar", "semarang": "sta6018_jateng"}
SK = {"CLOT": (0.01, 0.0), "CLTT": (0.01, 150.0), "CLTH": (0.001, 0.0), "CLER_23": (0.01, 0.0)}
LAP = {}
for s, site in LOK.items():
    F = sorted(n for n in NM if re.search(rf"{site}/CLP_{site}_\d{{4}}-\d\d-\d\d\.csv$", n)); assert len(F) == 1461, (s, len(F))
    C = pd.concat([pd.read_csv(io.BytesIO(ZS.read(n))) for n in F], ignore_index=True); C["tt"] = pd.to_datetime(C.timestamp); assert not C.tt.duplicated().any()
    dm = C.groupby(C.tt.dt.date).CLTT_mean.median(); gh = set(dm[dm < 160].index); g = C.tt.dt.date.isin(gh).to_numpy()
    sd_lama = {v: float(C.loc[g, f"{v}_std"].median()) if g.any() else None for v in ("CLOT", "CLTH")}
    for v, (sc, of) in SK.items():
        for st in ("mean", "median", "min", "max"): C.loc[g, f"{v}_{st}"] = (C.loc[g, f"{v}_{st}"] - of) / sc
        C.loc[g, f"{v}_std"] = C.loc[g, f"{v}_std"] / sc
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "clp_cot", "clp_cth_km"]); t = pd.DatetimeIndex(d.ts_wib)
    X = C.set_index(C.tt + pd.Timedelta(minutes=10)).reindex(t); ada = X.source_file.notna().to_numpy()
    cot = X.CLOT_mean.to_numpy(float); c6 = d.clp_cot.to_numpy(float)
    sama = np.array_equal(np.isfinite(cot), np.isfinite(c6)) and np.allclose(cot[np.isfinite(c6)], c6[np.isfinite(c6)], atol=1e-9)
    assert sama, (s, "CLOT_mean CSV tidak sama dengan clp_cot V6.10")
    assert np.allclose(X.CLTH_mean.to_numpy(float)[np.isfinite(c6)], d.clp_cth_km.to_numpy(float)[np.isfinite(c6)], atol=1e-9, equal_nan=True)
    e = pd.read_parquet(os.path.join(V, "clp_ekstra", f"{s}_clp_ekstra.parquet"), columns=["ts_wib", "clp_cloud_frac"]); assert (e.ts_wib.to_numpy() == d.ts_wib.to_numpy()).all()
    awan = np.isfinite(c6)
    out = pd.DataFrame({"ts_wib": d.ts_wib.values,
                        "clps_cot_std": np.where(awan, X.CLOT_std.to_numpy(float), np.nan), "clps_cot_min": np.where(awan, X.CLOT_min.to_numpy(float), np.nan),
                        "clps_cot_max": np.where(awan, X.CLOT_max.to_numpy(float), np.nan), "clps_cloud_frac": e.clp_cloud_frac.to_numpy(float),
                        "clps_cth_std": np.where(awan, X.CLTH_std.to_numpy(float), np.nan)})
    out["clps_cloud_frac_lag_60m"] = out.clps_cloud_frac.shift(6); out["clps_cot_std_lag_60m"] = out.clps_cot_std.shift(6)
    for c, lo, hi in (("clps_cot_std", 0, 100), ("clps_cot_min", 0, 150), ("clps_cot_max", 0, 150), ("clps_cth_std", 0, 10), ("clps_cloud_frac", 0, 1)):
        x = out[c].dropna(); assert ((x >= -1e-9) & (x <= hi + 1e-9)).all(), (s, c, x.min(), x.max())
    m = np.isfinite(out.clps_cot_min) & np.isfinite(out.clps_cot_max); assert (out.clps_cot_min[m] <= c6[m] + 1e-6).all() and (c6[m] <= out.clps_cot_max[m] + 1e-6).all()
    out.to_parquet(os.path.join(T, f"{s}_clp_kotak.parquet"), index=False)
    LAP[s] = dict(pusat=[float(C.station_lat.iloc[0]), float(C.station_lon.iloc[0])], grid=str(C.grid_size.iloc[0]), slot_berkas=int(ada.sum()), slot_berawan=int(awan.sum()),
                  hari_skala_ganda=len(gh), std_cot_hari_ganda_sebelum_koreksi=sd_lama["CLOT"], isi={c: int(out[c].notna().sum()) for c in out.columns[1:]},
                  median={c: round(float(out[c].median()), 4) for c in out.columns[1:]}, clot_mean_sama_clp_cot=bool(sama))
    print(s, json.dumps(LAP[s], ensure_ascii=False), flush=True)
json.dump(LAP, open(os.path.join(T, "laporan_z3.json"), "w"), indent=1, ensure_ascii=False)
open(os.path.join(T, "README.md"), "w", encoding="utf-8").write(
    "# Balai_kotak_v6_10 — statistik kotak CLP untuk Manuskrip V6 (tahap 28)\n\nDibangun 2026-11-08 oleh `solardata_new_v2/paper_v2_clpbanten/113_kotak_chips/z3_bangun_kotak.py`. Beku, hanya-baca.\n\n"
    "Sumber nilai: CSV kotak 11×11 piksel (Kalbar 10×11), buffer 30 km, di `6lokasi_output_chips.zip`, sama dengan `clp_cot` V6.10 (CLOT_mean = clp_cot persis). "
    "Kotak dan waktu diverifikasi piksel demi piksel dengan `chips_supplement_6.zip` (tahap 113 Z1/Z2). Nilai chip tidak dipakai karena tersimpan sebagai bilangan bulat terpotong.\n\n"
    "Konvensi: grid 10 menit WIB V6.10, t = T + 10; kosong bila tidak ada berkas; statistik COT/CTH kosong bila kotak tanpa piksel berawan. "
    "`clps_cloud_frac` = `clp_cloud_frac` V6.10 (prediktor ke-44); untuk uji tahap 28 V6 dipakai enam fitur lain.\n")
with open(os.path.join(T, "SHA256.txt"), "w") as f:
    for n in sorted(os.listdir(T)):
        if n != "SHA256.txt": f.write(hashlib.sha256(open(os.path.join(T, n), "rb").read()).hexdigest() + "  " + n + "\n")
os.rename(T, OUT)
for n in os.listdir(OUT): os.chmod(os.path.join(OUT, n), stat.S_IREAD)
print("BEKU", OUT)
