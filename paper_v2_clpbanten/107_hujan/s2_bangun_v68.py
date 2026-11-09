# -*- coding: utf-8 -*-
"""Tahap 107: bangun Balai_data_v6_8 dari Balai_data_v6_7 (hanya dibaca) — hujan: hitung ganda 07.00 dibuang, isian SYNOP mundur diganti isian kausal maju (DESAIN_107.md)."""
import os, sys, json, shutil, subprocess, duckdb, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); V7 = r"C:\Users\ariff\Documents\Balai_data_v6_7"; V8 = r"C:\Users\ariff\Documents\Balai_data_v6_8"
DB = r"C:\Users\ariff\Documents\Balai Obsidian\Balai\solardata_new_v2\solar_harmonised_clpbanten_v2.duckdb"
SRC = dict(jogja=("jogja.aws_jogja_quality_final", "ts_wib", "jogja.synop_jogja", "timestamp_wib", "synop_rainfall_last_mm", "synop_rainfall_6h_mm"),
           semarang=("semarang.aws_semarang_quality_final", "ts_wib", "semarang.synop_semarang", "data_timestamp_wib", "synop_rainfall_last_mm", "synop_rainfall_6h_mm"))
def isi_maju(t, rr3, rr6):
    """laju periode laporan SYNOP terakhir T <= t (kausal): RR3/18 untuk t-T<180 menit, kalau tidak RR6/36 untuk t-T<360 menit."""
    out = np.full(len(t), np.nan)
    for rr, n, w in ((rr6, 36, 360), (rr3, 18, 180)):                 # RR3 menimpa RR6 bila ada
        s = pd.Series(np.where(np.isfinite(rr), rr / n, np.nan), index=t); last = s.ffill().to_numpy()
        t0 = pd.Series(np.where(np.isfinite(rr), t, np.datetime64("NaT")), index=t).ffill().to_numpy(); age = (t.to_numpy() - t0) / np.timedelta64(1, "m")
        ok = age < w; out = np.where(ok & np.isfinite(last), last, out)
    return out
def bangun(s, d, c, syn=None):
    t = pd.DatetimeIndex(d.ts_wib); r = d.aws_rain_mm.to_numpy(float).copy(); L = {}
    # 1. hitung ganda 07.00 — amandemen 2: pembanding = jumlah slot yang diukur logger (pencacah AWS tidak menghitung isian SYNOP)
    logger = np.ones(len(r), bool)
    if s in SRC:
        A0 = c.execute(f"select {SRC[s][1]} as t, rr_src from {SRC[s][0]}").df(); A0["t"] = pd.to_datetime(A0.t)
        logger = A0.drop_duplicates("t").set_index("t").rr_src.reindex(t).astype(str).to_numpy() == "ok"
    cs = np.nancumsum(np.where(logger, np.nan_to_num(r), 0.0)); i7 = np.where((t.hour == 7) & (t.minute == 0))[0]; kor = np.zeros(len(r), bool)
    for i in i7:
        j = i - 144
        if j < 0: continue
        S = cs[i - 1] - cs[j]
        if S > 0.5 and np.isfinite(r[i]) and 0.8 * S <= r[i] <= 1.2 * S + 0.2: r[i] = max(r[i] - S, 0.0); kor[i] = True   # amandemen 1: hanya bila v(07.00) ≈ jumlah 24 jam (hitung ganda)
    if s == "jogja":   # amandemen 3: residu pencacah 07.00 tidak dapat direkonstruksi -> nilai slot 06.50 (persistensi kausal) di semua hari
        for i in i7:
            if i > 0: r[i] = r[i - 1]; kor[i] = True
    L["koreksi_0700"] = int(kor.sum()); L["mm_dibuang_0700"] = round(float(d.aws_rain_mm.to_numpy(float)[kor].sum() - r[kor].sum()), 1)
    # 2. isian mundur -> isian maju (kausal)
    maju = np.zeros(len(r), bool)
    if s in SRC:
        at, atc, st, stc, c3, c6 = SRC[s]
        A = c.execute(f"select {atc} as t, rr_src from {at}").df(); A["t"] = pd.to_datetime(A.t); src = A.drop_duplicates("t").set_index("t").rr_src.reindex(t).astype(str).to_numpy()
        if syn is None:
            S_ = c.execute(f"select {stc} as t, {c3} as rr3, {c6} as rr6 from {st}").df(); S_["t"] = pd.to_datetime(S_.t); S_ = S_.drop_duplicates("t").set_index("t").reindex(t)
            syn = (S_.rr3.where((S_.rr3 >= 0) & (S_.rr3 < 300)).to_numpy(float), S_.rr6.where((S_.rr6 >= 0) & (S_.rr6 < 400)).to_numpy(float))
        f = isi_maju(t, *syn); dis = np.isin(src, ["synop_disagg", "synop_disagg_capped"])
        L["isi_mundur_mm_lama"] = round(float(np.nansum(r[dis])), 1); r[dis] = f[dis]; maju = dis
        L["isi_maju_slot"] = int(dis.sum()); L["isi_maju_mm"] = round(float(np.nansum(f[dis])), 1); L["isi_maju_kosong"] = int((dis & ~np.isfinite(f)).sum())
    return r, kor, maju, L, syn
if __name__ == "__main__":
    assert not os.path.exists(os.path.join(V8, "SHA256.txt")), "V6.8 sudah beku"
    if os.path.exists(V8): shutil.rmtree(V8)
    shutil.copytree(V7, V8, copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("SHA256.txt", "README.md"))
    c = duckdb.connect(DB, read_only=True); LAP = {}
    for s in ("banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"):
        d0 = pd.read_parquet(os.path.join(V8, "00_data", f"{s}_full.parquet")); r, kor, maju, L, syn = bangun(s, d0, c); t = pd.DatetimeIndex(d0.ts_wib)
        if syn is not None:   # kausalitas isian maju
            for cut in ("2022-09-14 10:05", "2024-03-03 15:35", "2025-11-29 08:15"):
                cc = np.asarray(t > pd.Timestamp(cut)); s2 = tuple(np.where(cc, np.nan, x) for x in syn); r2 = bangun(s, d0, c, s2)[0]
                assert np.allclose(r2[~cc], r[~cc], equal_nan=True), (s, cut)
        for var in ("00_data", "00_data_rawfill"):
            f = os.path.join(V8, var, f"{s}_full.parquet"); d = pd.read_parquet(f); dt = d.dtypes; old = d.copy()
            assert np.array_equal(np.nan_to_num(old.aws_rain_mm.to_numpy(float), nan=-1), np.nan_to_num(d0.aws_rain_mm.to_numpy(float), nan=-1))
            d["aws_rain_mm"] = r; d["aws_rain_sum_180m"] = pd.Series(r).rolling(18, min_periods=1).sum().to_numpy()
            for col in d.columns:
                if str(dt[col]) != str(d[col].dtype): d[col] = d[col].astype(dt[col])
            beda = {col for col in d.columns if not d[col].equals(old[col])}; assert beda <= {"aws_rain_mm", "aws_rain_sum_180m"}, beda
            d.to_parquet(f, index=False)
        pv = os.path.join(V8, "provenance", f"{s}_provenance.parquet"); P_ = pd.read_parquet(pv); P_["hujan_koreksi_0700"] = kor; P_["hujan_isi_maju"] = maju; P_.to_parquet(pv, index=False)
        L["kosong_total"] = int(np.isnan(r).sum()); L["total_mm_lama"] = round(float(np.nansum(d0.aws_rain_mm)), 0); L["total_mm_baru"] = round(float(np.nansum(r)), 0)
        LAP[s] = L; print(s, L, flush=True)
    json.dump(LAP, open(os.path.join(HERE, "s2_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    kode = r'''
import sys, numpy as np; sys.path.insert(0, r"%s"); import _common
for s in _common.SITES:
    df, feats, yr = _common.prepare(s); tr, va, te = _common.split_idx(df, yr, "mean"); d = df.iloc[te]
    print(s, len(feats), len(te), round(float(np.nanmean(d.base_mean)), 3), "hujan kosong uji", round(float(d.aws_rain_mm.isna().mean()), 4), "sum180 kosong", round(float(d.aws_rain_sum_180m.isna().mean()), 4))
''' % B
    env = dict(os.environ, DATA_DIR=os.path.join(V8, "00_data"), CLEARSKY_DIR=os.path.join(V8, "clearsky"), CLP_EKSTRA_DIR=os.path.join(V8, "clp_ekstra"), FEATSET="P2F", PYTHONIOENCODING="utf-8")
    o = subprocess.run([sys.executable, "-c", kode], capture_output=True, text=True, env=env, cwd=B); print(o.stdout); print(o.stderr[-400:] if o.returncode else "")
