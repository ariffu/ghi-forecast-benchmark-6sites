# -*- coding: utf-8 -*-
"""Tahap 103: bangun Balai_data_v6_6 dari Balai_data_v6_5 (hanya dibaca) — penaksir kausal mulus dan lengkap untuk meteorologi AWS (DESAIN_103.md)."""
import os, sys, json, shutil, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE)
V3 = r"C:\Users\ariff\Documents\Balai_data_v6_3"; V5 = r"C:\Users\ariff\Documents\Balai_data_v6_5"; V6 = r"C:\Users\ariff\Documents\Balai_data_v6_6"
sys.path.insert(0, os.path.join(B, "102_v6_5")); sys.path.insert(0, os.path.join(B, "100_meteo_synop"))
import l1_bangun_v65 as L1
from j2_bangun_v64 import MET, turunan
S_ = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
VAR = dict(suhu=("aws_temp_c", 1.5, None, None), rh=("aws_rh_pct", 7.5, 0.0, 100.0), tekanan=("aws_pressure_hpa", 0.5, None, None), angin=("aws_wind_speed_ms", 3.0, 0.0, None))
ISI3 = dict(suhu=[], rh=[], tekanan=["aws_isi_synop_tekanan", "aws_isi_synop_tekanan_datar"], angin=["aws_isi_synop_angin"])
SYN_PRED = ["synop_visibility_km", "synop_cloud_cover_oktas", "synop_cl", "synop_cm", "synop_ch", "synop_present_weather_ww"]

def penaksir(Lg, S, cl, lim, lo, hi, n_ramp=6):
    """Penaksir kausal: ikuti logger (bobot naik 1/6..1), atau rambat dengan klimatologi + koreksi SYNOP disebar 6 slot; batas laju per slot."""
    n = len(Lg); out = np.full(n, np.nan); mode = np.full(n, -1, np.int8); dib = np.zeros(n, bool)
    dcl = np.nan_to_num(np.diff(cl, prepend=cl[0]), nan=0.0)
    x = np.nan; w = 0; rem = 0.0; nrem = 0
    for i in range(n):
        Li, Si = Lg[i], S[i]
        if x != x:                                                   # belum ada keadaan
            if Li == Li: x = Li; w = n_ramp; out[i] = x; mode[i] = 0
            elif Si == Si: x = Si; out[i] = x; mode[i] = 1
            continue
        xp = x + dcl[i]
        if Li == Li:
            w = min(w + 1, n_ramp); tgt = xp + (w / n_ramp) * (Li - xp); rem = 0.0; nrem = 0; m = 0
        else:
            w = 0
            if Si == Si: rem = Si - xp; nrem = n_ramp
            if nrem > 0 or abs(rem) > 1e-9:
                tgt = xp + rem / max(nrem, 1); m = 1
            else: tgt = xp; m = 2
        step = tgt - x                                               # amandemen 1: batas laju pada perubahan total per slot
        if abs(step) > lim: step = np.sign(step) * lim; dib[i] = True
        xn = x + step
        if m == 1: rem -= (xn - xp); nrem = max(nrem - 1, 1) if abs(rem) > 1e-9 else 0
        x = xn
        if lo is not None and x < lo: x = lo
        if hi is not None and x > hi: x = hi
        out[i] = x; mode[i] = m
    return out, mode, dib

def asof(val, rep, t, menit=60):
    """nilai laporan terakhir (pada slot laporan) berlaku sampai 'menit' sesudahnya; laporan yang kolomnya kosong tidak mewarisi laporan lama."""
    g = np.cumsum(rep); v = np.array(pd.Series(np.where(rep, val, np.nan)).groupby(g).transform("first").to_numpy(float), dtype=float, copy=True)
    t0 = pd.Series(np.where(rep, t, np.datetime64("NaT"))).ffill().to_numpy(); umur = (t - t0) / np.timedelta64(1, "m")
    v[(g == 0) | ~(umur < menit)] = np.nan; return v, umur

def bangun(s, d5, p5, d3, pv3, ref=None):
    t = d5.ts_wib.to_numpy(); ti = pd.DatetimeIndex(d5.ts_wib); lat = ti.year <= 2023; OUT, PV, L = {}, {}, {}
    if ref is None: ref = L1.proses(d3, s, prov=pv3)[4]
    for v, (c, lim, lo, hi) in VAR.items():
        x5 = d5[c].to_numpy(float)
        bad = p5[f"met_bangun_ulang_{v}"].to_numpy(bool) | p5[f"met_isi_{v}"].to_numpy(bool) | p5[f"met_sisipan_{v}"].to_numpy(bool)
        for k in ISI3[v]: bad |= pv3[k].to_numpy(bool)
        x3 = d3[c].to_numpy(float); xs = np.where(np.isfinite(x5), x5, x3)   # amandemen 1: bentuk siklus harian dari V6.5, slot kosong dari V6.3
        Lg = np.where(bad, np.nan, x5); cl = L1.klim(xs, ti, lat & np.isfinite(xs)).reindex(list(zip(ti.month, ti.hour * 60 + ti.minute))).to_numpy()
        x, mode, dib = penaksir(Lg, ref[v], cl, lim, lo, hi)
        OUT[c] = x; PV[f"mulus_mode_{v}"] = mode; PV[f"mulus_dibatasi_{v}"] = dib
        L[v] = dict(logger=round(float((mode == 0).mean()), 3), synop=round(float((mode == 1).mean()), 3), rambat=round(float((mode == 2).mean()), 3), dibatasi=int(dib.sum()), kosong=int(np.isnan(x).sum()))
    # arah angin
    aD = d5.aws_wind_dir_deg.to_numpy(float); sD = d3.synop_wind_dir_deg.to_numpy(float); sD = np.where((sD > 0) & (sD <= 360), sD, np.nan)
    rep_d = np.isfinite(sD); sDa, _ = asof(sD, rep_d, t, 60)
    D = np.where(np.isfinite(aD), aD, sDa); md = np.where(np.isfinite(aD), 0, np.where(np.isfinite(sDa), 1, 2)).astype(np.int8)
    D = pd.Series(D).ffill().to_numpy(); md[np.isnan(D)] = -1; OUT["aws_wind_dir_deg"] = D; PV["mulus_mode_arah"] = md
    L["arah"] = dict(aws=round(float((md == 0).mean()), 3), synop=round(float((md == 1).mean()), 3), tahan=round(float((md == 2).mean()), 3), kosong=int(np.isnan(D).sum()))
    # kolom SYNOP prediktor: as-of 60 menit
    rep = (d3[["synop_temp_c", "synop_pressure_hpa", "synop_visibility_km", "synop_present_weather_ww"]].notna().any(axis=1)).to_numpy()
    for c in SYN_PRED:
        v_, umur = asof(d3[c].to_numpy(float), rep, t, 60); OUT[c] = v_
    PV["synop_asof_umur_mnt"] = np.where(umur < 60, umur, np.nan).astype("float32")
    return OUT, PV, L, ref

if __name__ == "__main__":
    assert not os.path.exists(os.path.join(V6, "SHA256.txt")), "V6.6 sudah beku"
    if os.path.exists(V6): shutil.rmtree(V6)
    shutil.copytree(V5, V6, copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("SHA256.txt", "README.md")); LAP = {}
    for s in S_:
        d5 = pd.read_parquet(os.path.join(V5, "00_data", f"{s}_full.parquet")); p5 = pd.read_parquet(os.path.join(V5, "provenance", f"{s}_provenance.parquet"))
        d3 = pd.read_parquet(os.path.join(V3, "00_data", f"{s}_full.parquet")); pv3 = pd.read_parquet(os.path.join(V3, "provenance", f"{s}_provenance.parquet"))
        OUT, PV, L, ref = bangun(s, d5, p5, d3, pv3); t = pd.DatetimeIndex(d5.ts_wib)
        # kausalitas: SYNOP sesudah titik potong dihapus -> nilai sebelum potongan identik
        for cut in ("2022-09-14 10:05", "2024-03-03 15:35", "2025-11-29 08:15"):
            cc = np.asarray(t > pd.Timestamp(cut)); r2 = {k: np.where(cc, np.nan, v) for k, v in ref.items()}; d3c = d3.copy()
            for c in [c for c in d3.columns if c.startswith("synop_")]: d3c.loc[cc, c] = np.nan
            O2 = bangun(s, d5, p5, d3c, pv3, r2)[0]
            for k in OUT: assert np.allclose(np.asarray(O2[k], float)[~cc], np.asarray(OUT[k], float)[~cc], equal_nan=True, atol=1e-9), (s, cut, k)
        for var in ("00_data", "00_data_rawfill"):
            f = os.path.join(V6, var, f"{s}_full.parquet"); d = pd.read_parquet(f); dt = d.dtypes; old = d.copy(); ada_arah = np.isfinite(old.aws_wind_dir_deg.to_numpy(float)).any() or np.isfinite(OUT["aws_wind_dir_deg"]).any()
            for c, v in OUT.items(): d[c] = v
            d = turunan(d)
            for c in d.columns:
                if str(dt[c]) != str(d[c].dtype): d[c] = d[c].astype(dt[c])
            beda = sorted(c for c in d.columns if not d[c].equals(old[c])); assert set(beda) <= set(MET) | set(SYN_PRED), (s, var, set(beda) - set(MET) - set(SYN_PRED))
            d.to_parquet(f, index=False)
        pv = os.path.join(V6, "provenance", f"{s}_provenance.parquet"); P_ = pd.read_parquet(pv)
        for k in sorted(PV): P_[k] = PV[k]
        P_.to_parquet(pv, index=False); LAP[s] = L; print(s, json.dumps(L, ensure_ascii=False), flush=True)
    json.dump(LAP, open(os.path.join(HERE, "n2_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("SELESAI")
