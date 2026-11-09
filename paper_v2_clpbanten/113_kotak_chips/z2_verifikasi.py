# -*- coding: utf-8 -*-
"""Tahap 113 Z2: verifikasi menyeluruh chips_supplement_6 (1.390 hari x 6 stasiun) terhadap CSV kotak V6, memakai jendela dari Z1.
Per baris CSV yang punya berkas: CLOT_count = jumlah piksel COT sah di chip; chip = bilangan bulat terpotong dari nilai fisis
(cek: floor(CSV min/max) = min/max chip untuk CLOT dan CLTH, dengan koreksi hari skala ganda seperti c6_clp_6lokasi.py).
Juga mencatat hari skala ganda CSV dan jumlah slot berkas."""
import io, zipfile, json, os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
ZC = zipfile.ZipFile(r"C:\Users\ariff\Documents\chips_supplement_6.zip"); ZS = zipfile.ZipFile(r"C:\Users\ariff\Documents\6lokasi_output_chips.zip")
LOK = {"banten": "sta6016_banten", "bengkulu": "sta6009_bengkulu", "jambi": "sta6007_jambi", "jogja": "sta6010_jogja", "kalbar": "sta6003_kalbar", "semarang": "sta6018_jateng"}
W = {s: (v["terbaik"][0]["baris"], v["terbaik"][0]["kolom"]) for s, v in json.load(open(os.path.join(HERE, "z1_cocok.json"))).items()}
SK = {"CLOT": (0.01, 0.0), "CLTT": (0.01, 150.0), "CLTH": (0.001, 0.0), "CLER_23": (0.01, 0.0)}
HARI = sorted(n.split("_")[-1][:10] for n in ZC.namelist() if n.endswith(".npz"))
R = {s: dict(baris=0, kunci_ada=0, count_sama=0, cot_minmax_floor=0, cth_minmax_floor=0, n_awan=0, hari_skala_ganda=0) for s in LOK}
for h, day in enumerate(HARI):
    D = np.load(io.BytesIO(ZC.read(f"chips_supplement_6/CHIPS_SUPPLEMENT_{day}.npz")), allow_pickle=False); F = set(D.files)
    for s, site in LOK.items():
        C = pd.read_csv(io.BytesIO(ZS.read(f"{site}/CLP_{site}_{day}.csv"))); C = C[C.source_file.notna()].reindex(columns=list(dict.fromkeys(list(C.columns) + [f"{v}_{st}" for v in SK for st in ("mean", "std", "min", "max", "median", "count")])))
        nr, nc = map(int, str(C.grid_size.iloc[0]).split("x")) if len(C) else (11, 11); i, j = W[s]
        g = len(C) and C.CLTT_mean.median() < 160
        if g:
            R[s]["hari_skala_ganda"] += 1
            for v, (sc, of) in SK.items():
                for st in ("min", "max"): C[f"{v}_{st}"] = (C[f"{v}_{st}"] - of) / sc
        for _, r in C.iterrows():
            R[s]["baris"] += 1; k = pd.Timestamp(r.timestamp).strftime("%H%M")
            if f"{k}__{site}__CLOT" not in F: continue
            R[s]["kunci_ada"] += 1
            a = D[f"{k}__{site}__CLOT"][i:i + nr, j:j + nc]; b = D[f"{k}__{site}__CLTH"][i:i + nr, j:j + nc]; x = a[a >= 0]; y = b[b >= 0]
            cn = int(r.CLOT_count) if np.isfinite(r.CLOT_count) else 0; R[s]["count_sama"] += x.size == cn
            if cn > 0 and x.size:
                R[s]["n_awan"] += 1
                R[s]["cot_minmax_floor"] += (x.min() == np.floor(r.CLOT_min + 1e-6)) and (x.max() == np.floor(r.CLOT_max + 1e-6))
                if y.size and np.isfinite(r.CLTH_min): R[s]["cth_minmax_floor"] += (y.min() == np.floor(r.CLTH_min + 1e-6)) and (y.max() == np.floor(r.CLTH_max + 1e-6))
    if h % 100 == 0: print(day, {s: (R[s]["count_sama"], R[s]["kunci_ada"]) for s in LOK}, flush=True)
for s in R: R[s].update(hari_chip=len(HARI), hari_pertama=HARI[0], hari_terakhir=HARI[-1])
R = json.loads(json.dumps(R, default=int)); print(json.dumps(R, indent=1)); json.dump(R, open(os.path.join(HERE, "z2_verifikasi.json"), "w"), indent=1)
