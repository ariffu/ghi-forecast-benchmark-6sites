# -*- coding: utf-8 -*-
"""Tahap 113 Z1: mencocokkan piksel chips_supplement_6.zip (24x24, 0,05°) dengan statistik kotak CSV sumber CLP V6 (6lokasi_output_chips.zip).
Untuk tiap stasiun dan sampel hari: cari jendela (baris, kolom) seukuran kotak CSV dan geseran waktu kunci chip yang membuat
CLOT_count dan CLOT_mean piksel = CSV. Hanya membaca kedua zip (tanpa ekstraksi ke disk)."""
import io, re, zipfile, json, numpy as np, pandas as pd, os
HERE = os.path.dirname(os.path.abspath(__file__))
ZC = zipfile.ZipFile(r"C:\Users\ariff\Documents\chips_supplement_6.zip"); ZS = zipfile.ZipFile(r"C:\Users\ariff\Documents\6lokasi_output_chips.zip")
LOK = {"banten": "sta6016_banten", "bengkulu": "sta6009_bengkulu", "jambi": "sta6007_jambi", "jogja": "sta6010_jogja", "kalbar": "sta6003_kalbar", "semarang": "sta6018_jateng"}
HARI = [str(d.date()) for d in pd.date_range("2022-03-20", "2025-12-25", periods=24)]
def chip(day):
    return np.load(io.BytesIO(ZC.read(f"chips_supplement_6/CHIPS_SUPPLEMENT_{day}.npz")), allow_pickle=False)
def csv(site, day):
    C = pd.read_csv(io.BytesIO(ZS.read(f"{site}/CLP_{site}_{day}.csv"))); C["tt"] = pd.to_datetime(C.timestamp); return C
R = {}
for s, site in LOK.items():
    skor = {}; info = None
    for day in HARI:
        D = chip(day); C = csv(site, day)
        if info is None:
            la, lo = D[f"0600__{site}__lat"], D[f"0600__{site}__lon"]; info = dict(lat=[float(la[0]), float(la[-1])], lon=[float(lo[0]), float(lo[-1])], pusat_csv=[float(C.station_lat.iloc[0]), float(C.station_lon.iloc[0])], grid=str(C.grid_size.iloc[0]), total=int(C.total_pixels.iloc[0]))
        nr, nc = map(int, info["grid"].split("x"))
        for _, r in C.iterrows():
            if not np.isfinite(r.CLOT_count) if "CLOT_count" in r else True: pass
            for gz in (-10, 0, 10):
                k = (r.tt + pd.Timedelta(minutes=gz)).strftime("%H%M") + f"__{site}__CLOT"
                if k not in D.files: continue
                a = D[k]
                for i in range(0, 24 - nr + 1):
                    for j in range(0, 24 - nc + 1):
                        w = a[i:i + nr, j:j + nc]; v = w[w >= 0]; n = v.size
                        cn = 0 if not np.isfinite(r.CLOT_count) else int(r.CLOT_count)
                        ok_n = n == cn; ok_m = (n == 0 and not np.isfinite(r.CLOT_mean)) or (n > 0 and np.isfinite(r.CLOT_mean) and (abs(v.mean() * 0.01 - r.CLOT_mean) < 1e-3 or abs(v.mean() - r.CLOT_mean) < 1e-3))
                        key = (gz, i, j); t = skor.setdefault(key, [0, 0, 0]); t[0] += 1; t[1] += ok_n; t[2] += ok_n and ok_m
    best = sorted(skor.items(), key=lambda kv: -kv[1][2] / kv[1][0])[:4]
    R[s] = dict(info, terbaik=[dict(geser_menit=k[0], baris=k[1], kolom=k[2], n=v[0], cocok_count=round(v[1] / v[0], 4), cocok_count_mean=round(v[2] / v[0], 4)) for k, v in best])
    print(s, json.dumps(R[s], ensure_ascii=False), flush=True)
json.dump(R, open(os.path.join(HERE, "z1_cocok.json"), "w"), indent=1)
