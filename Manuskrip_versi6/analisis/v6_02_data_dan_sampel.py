# -*- coding: utf-8 -*-
"""Manuskrip V6, analisis 02 — angka data dari V6.10 (hanya membaca): pengganti 04b_tabel_banten_v5.py dan v4_21_satelit_dan_radiasi.py.
  A. Sumber GHI (provenance `ghi_sumber`, label DB v2 `ghi_origin_v2`) per stasiun dan tahun, siang (elevasi > 5°): porsi logger, porsi terukur.
     Terukur = logger, portal, tabel 10 menit logger, atau nilai database berlabel measured.
  B. Sampel evaluasi: origin yang slot origin dan keenam slot targetnya (t … t + 60 menit) semua dari logger; Banten juga logger atau portal.
     CatBoost (rerata 5 seed, protokol baku V6), smart persistence, ΔR²(CLP) ablasi CatBoost (hasil/preds_ablasi_cb) dan LightGBM (pipeline/27).
  C. Asal satelit CLP menurut nama berkas sumber CSV V6 (6lokasi_output_chips.zip, NC_H08_/NC_H09_), mayoritas per hari 07–17 WIB;
     ΔRMSE oleh CLP (LightGBM inti vs inti + CLP, pipeline/27) pada hari uji Himawari-8 dan Himawari-9.
  D. Status DHI/DNI (provenance) per stasiun dan tahun: porsi asli, dari logger 2022, diperbaiki (uji neraca), dimodelkan.
Keluaran: ../hasil/angka_data.json, ../hasil/sumber_ghi.csv, ../hasil/sampel_logger.csv.
Jalankan: DATA_DIR/CLEARSKY_DIR/CLP_EKSTRA_DIR = V6.10, FEATSET=P2F, PYTHONIOENCODING=utf-8 python -u v6_02_data_dan_sampel.py"""
import os, sys, io, re, json, zipfile, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); V6 = os.path.dirname(HERE); ROOT = os.path.dirname(V6); P = os.path.join(ROOT, "paper_v2_clpbanten"); sys.path.insert(0, P)
import _common
from _common import prepare, split_idx
assert _common.FEATSET == "P2F" and len(_common.P2_AKTIF) == 44
V = r"C:\Users\ariff\Documents\Balai_data_v6_10"; assert os.path.normcase(_common.DATA) == os.path.normcase(os.path.join(V, "00_data"))
H = os.path.join(V6, "hasil"); RR = os.path.join(V6, "protokol", "hasil"); PV = os.path.join(V6, "pipeline")
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; SEEDS = [42, 1, 2, 3, 4]
def r2(y, p): return 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
def rmse(y, p): return float(np.sqrt(((y - p) ** 2).mean()))
J = {"sumber": {}, "sampel": {}, "satelit": {}, "dhi_dni": {}}; rowsA, rowsB = [], []
TERUKUR_SUMBER = {"logger", "portal", "tabel_10min"}
for s in SITES:
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet"), columns=["ts_wib", "solar_elev_deg"])
    pv = pd.read_parquet(os.path.join(V, "provenance", f"{s}_provenance.parquet"), columns=["ts_wib", "ghi_sumber", "ghi_origin_v2", "dhi_status", "dni_status"])
    assert (d.ts_wib.to_numpy() == pv.ts_wib.to_numpy()).all()
    src = pv.ghi_sumber.astype(str).to_numpy(); v2 = pv.ghi_origin_v2.astype(str).to_numpy()
    terukur = np.isin(src, list(TERUKUR_SUMBER)) | (np.isin(src, ["db", "db_trapesium"]) & (v2 == "measured"))
    siang = d.solar_elev_deg.to_numpy() > 5; th = d.ts_wib.dt.year.to_numpy()
    J["sumber"][s] = {}
    for y_ in (2022, 2023, 2024, 2025):
        m = siang & (th == y_); vc = pd.Series(src[m]).value_counts(normalize=True).mul(100)
        J["sumber"][s][y_] = dict(logger=float(vc.get("logger", 0.0)), terukur=float(100 * terukur[m].mean()), komposisi={k: round(float(v), 2) for k, v in vc.items()})
        rowsA.append(dict(site=s, tahun=y_, logger_pct=float(vc.get("logger", 0.0)), terukur_pct=float(100 * terukur[m].mean()), **{f"pct_{k}": float(v) for k, v in vc.items()}))
        dh = pd.Series(pv.dhi_status.astype(str).to_numpy()[m]).value_counts(normalize=True).mul(100).round(2).to_dict()
        dn = pd.Series(pv.dni_status.astype(str).to_numpy()[m]).value_counts(normalize=True).mul(100).round(2).to_dict()
        J["dhi_dni"].setdefault(s, {})[y_] = dict(dhi=dh, dni=dn)
    # ---- B. sampel evaluasi ----
    df, feats, yr = prepare(s, l_filter=5); tr, va, te = split_idx(df, yr, tgt="mean"); assert len(feats) == 44
    y, b = df.y_mean.to_numpy(float)[te], df.base_mean.to_numpy(float)[te]; day = df.ts_wib.dt.date.astype(str).to_numpy()[te]
    Y = np.load(os.path.join(RR, "nn", f"yb_{s}.npz"), allow_pickle=True); assert np.allclose(Y["y"], y) and np.allclose(Y["b"], b)
    pos = pd.Series(np.arange(len(d)), index=pd.DatetimeIndex(d.ts_wib)); ts = pd.DatetimeIndex(df.ts_wib.to_numpy()[te]); ip = pos.reindex(ts).to_numpy(); assert not np.isnan(ip).any(); ip = ip.astype(int)
    def semua(lbl):
        ok = np.ones(len(ip), bool)
        for k in range(7): j = np.clip(ip + k, 0, len(src) - 1); ok &= np.isin(src[j], list(lbl) + ["malam"]) & (ip + k < len(src))   # slot malam (GHI = 0) bukan isian
        return ok
    S_ = {"penuh": np.ones(len(ip), bool), "logger": semua(["logger"])}
    if s == "banten": S_["logger_portal"] = semua(["logger", "portal"])
    PCB = [np.load(os.path.join(RR, "pohon", f"pred_{s}_CatBoost_s{sd}.npy")).astype(float) for sd in SEEDS]
    ZC = np.load(os.path.join(H, f"preds_ablasi_cb_{s}.npz"), allow_pickle=True); assert np.allclose(ZC["y"], y)
    ZL = np.load(os.path.join(PV, "27_block_bootstrap", f"preds_replication_{s}.npz"), allow_pickle=True); assert np.allclose(ZL["y"], y)
    for k, m in S_.items():
        rowsB.append(dict(site=s, sampel=k, n=int(m.sum()), porsi=float(m.mean()), SP=r2(y[m], b[m]), CatBoost=float(np.mean([r2(y[m], p[m]) for p in PCB])),
                          RMSE=float(np.mean([rmse(y[m], p[m]) for p in PCB])), skill=1 - float(np.mean([rmse(y[m], p[m]) for p in PCB])) / rmse(y[m], b[m]),
                          dCLP_CB=r2(y[m], ZC["T1+CLP"][m]) - r2(y[m], ZC["T1"][m]), dCLP_LGB=r2(y[m], ZL["T1+CLP"][m]) - r2(y[m], ZL["T1"][m])))
    print(s, "sumber dan sampel selesai", flush=True)
A = pd.DataFrame(rowsA); A.to_csv(os.path.join(H, "sumber_ghi.csv"), index=False)
Bs = pd.DataFrame(rowsB); Bs.to_csv(os.path.join(H, "sampel_logger.csv"), index=False)
J["sampel"] = {f"{r.site}|{r.sampel}": {k: (float(v) if not isinstance(v, str) else v) for k, v in r._asdict().items() if k not in ("Index",)} for r in Bs.itertuples()}
# ---- C. asal satelit CLP dari CSV sumber V6 ----
Z = zipfile.ZipFile(r"C:\Users\ariff\Documents\6lokasi_output_chips.zip"); NM = Z.namelist()
LOK = {"banten": "sta6016_banten", "bengkulu": "sta6009_bengkulu", "jambi": "sta6007_jambi", "jogja": "sta6010_jogja", "kalbar": "sta6003_kalbar", "semarang": "sta6018_jateng"}
for s, site in LOK.items():
    F = sorted(n for n in NM if re.search(rf"{site}/CLP_{site}_\d{{4}}-\d\d-\d\d\.csv$", n)); assert len(F) == 1461
    C = pd.concat([pd.read_csv(io.BytesIO(Z.read(n)), usecols=["timestamp", "source_file"]) for n in F], ignore_index=True)
    C["ts"] = pd.to_datetime(C.timestamp); C["sat"] = C.source_file.astype(str).str.extract(r"NC_(H0[89])_", expand=False)
    C = C[C.sat.notna() & (C.ts.dt.hour >= 7) & (C.ts.dt.hour < 17)]; C["tgl"] = C.ts.dt.date.astype(str)
    hari = C.groupby("tgl").sat.agg(lambda v: v.value_counts().idxmax())
    pertama_h09 = min(hari[(hari == "H09") & (hari.index >= "2022-11-01")].index); h25 = hari[hari.index.str.startswith("2025")]; h08 = sorted(h25[h25 == "H08"].index)
    blok = []
    for dd in h08:
        if blok and (pd.Timestamp(dd) - pd.Timestamp(blok[-1][1])).days == 1: blok[-1][1] = dd
        else: blok.append([dd, dd])
    ZL = np.load(os.path.join(PV, "27_block_bootstrap", f"preds_replication_{s}.npz"), allow_pickle=True); yy, dday = ZL["y"], pd.Series(ZL["day"]).astype(str).to_numpy(); m8 = np.isin(dday, h08)
    red = {k: 100 * (1 - rmse(yy[m], ZL["T1+CLP"][m]) / rmse(yy[m], ZL["T1"][m])) for k, m in [("H08", m8), ("H09", ~m8)]}
    J["satelit"][s] = dict(h09_pertama=pertama_h09, h08_2025=blok, hari_uji_h08=int(len(set(dday[m8]))), hari_uji_h09=int(len(set(dday[~m8]))), turun_rmse_clp_pct=red)
    print(s, J["satelit"][s], flush=True)
S = J["satelit"]
J["turun_h08"] = [min(v["turun_rmse_clp_pct"]["H08"] for v in S.values()), max(v["turun_rmse_clp_pct"]["H08"] for v in S.values())]
J["turun_h09"] = [min(v["turun_rmse_clp_pct"]["H09"] for v in S.values()), max(v["turun_rmse_clp_pct"]["H09"] for v in S.values())]
json.dump(J, open(os.path.join(H, "angka_data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(A.round(1).to_string(index=False)); print(Bs.round(4).to_string(index=False)); print(json.dumps({k: J[k] for k in ("turun_h08", "turun_h09")}))
