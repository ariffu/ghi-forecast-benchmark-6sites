# -*- coding: utf-8 -*-
"""Tahap 102: bangun Balai_data_v6_5 dari Balai_data_v6_3 (hanya dibaca) — meteorologi AWS beracuan SYNOP dengan logika diperbaiki (DESAIN_102.md)."""
import os, sys, json, shutil, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); V3 = r"C:\Users\ariff\Documents\Balai_data_v6_3"; V5 = r"C:\Users\ariff\Documents\Balai_data_v6_5"
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "100_meteo_synop"))
from j2_bangun_v64 import MET, bersih, ke_semua, isi_kausal, turunan
S_ = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; ALT = dict(banten=27, bengkulu=9, jambi=24, jogja=182, kalbar=2, semarang=6)
KT = 0.514444; W7 = "7D"; MINR = 20; LIM = dict(tekanan=2.0, suhu=4.0, rh=25.0)

def qc_synop(s_, a_):
    """kausal: buang laporan yang menyimpang dari laporan sebelumnya (<= 3 jam) DAN dari AWS mentah pada saat sama melebihi batas."""
    def f(S, A, lim, t):
        S = S.copy(); i = np.where(np.isfinite(S))[0]; buang = np.zeros(len(S), bool)
        for a, b in zip(i[:-1], i[1:]):
            if (t[b] - t[a]) <= np.timedelta64(180, "m") and abs(S[b] - S[a]) > lim and np.isfinite(A[b]) and abs(S[b] - A[b]) > lim: buang[b] = True
        S[buang] = np.nan; return S, buang
    return f

def klim(a_lat, t, lat_ok):
    """amandemen 2: klimatologi bulan × menit-hari dihaluskan melingkar ±30 menit (7 slot), berbobot jumlah data; lengkap 12 × 144 sel."""
    md = (t.hour * 6 + t.minute // 10).to_numpy(); mo = t.month.to_numpy(); ok = lat_ok & np.isfinite(a_lat)
    S_ = np.zeros((13, 144)); N_ = np.zeros((13, 144)); np.add.at(S_, (mo[ok], md[ok]), a_lat[ok]); np.add.at(N_, (mo[ok], md[ok]), 1)
    k = np.ones(7); Sh = np.zeros_like(S_); Nh = np.zeros_like(N_)
    for j, w in zip(range(-3, 4), k): Sh += np.roll(S_, j, axis=1) * w; Nh += np.roll(N_, j, axis=1) * w
    M = np.where(Nh > 0, Sh / np.where(Nh > 0, Nh, 1), np.nan)
    idx = pd.MultiIndex.from_product([range(1, 13), range(0, 1440, 10)]); return pd.Series(M[1:, :].ravel(), index=idx)
def tetangga(x):
    return np.nanmean(np.c_[np.r_[np.nan, x[:-1]], np.r_[x[1:], np.nan]], axis=1)

def proses(d, s, gagal=None, tetap=None, prov=None):
    t = pd.DatetimeIndex(d.ts_wib); tn = t.to_numpy(); lat = t.year <= 2023; L = {}; PV = {}
    sT, sH = bersih(d.synop_temp_c, 0, 45).to_numpy(), bersih(d.synop_rh_pct, 1, 100).to_numpy()
    sP = bersih(d.synop_pressure_hpa, 900, 1050).to_numpy(); sW = (bersih(d.synop_wind_speed_kt, 0, 199) * KT).to_numpy(); sD = bersih(d.synop_wind_dir_deg, 0, 360).to_numpy()
    aT, aH, aP, aW, aD = (d[c].to_numpy(float).copy() for c in ("aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_wind_dir_deg"))
    fl = lambda *cs: np.logical_or.reduce([prov[c].to_numpy(bool) for c in cs if c in prov]) if any(c in prov for c in cs) else np.zeros(len(d), bool)
    kaus = dict(suhu=fl("aws_kausal_suhu"), rh=fl("aws_kausal_rh"), tekanan=fl("aws_kausal_tekanan"), angin=fl("aws_kausal_angin"))
    isi3 = dict(suhu=np.zeros(len(d), bool), rh=np.zeros(len(d), bool), tekanan=fl("aws_isi_synop_tekanan", "aws_isi_synop_tekanan_datar"), angin=fl("aws_isi_synop_angin"))
    # konvensi tekanan
    if s == "jambi": c = -sP * (1 - np.exp(-9.80665 * ALT[s] / (287.05 * (np.nan_to_num(sT, nan=27.0) + 273.15)))); L["c_tekanan"] = "hipsometrik %.3f" % float(np.nanmedian(c))
    else:
        rp = np.isfinite(sP) & np.isfinite(aP); ex = rp & (np.abs(aP - sP) < 0.05)
        c0 = tetap["c"] if tetap else float(np.median((aP - sP)[lat & rp & ~ex])); c = np.full(len(t), c0); L["c_tekanan"] = round(float(c0), 3)
    # 4. QC laporan SYNOP (kausal)
    q = qc_synop(None, None)
    sPs, bP_ = q(sP + c, aP if s != "jambi" else aP + np.nanmedian(c), LIM["tekanan"], tn); sT, bT_ = q(sT, aT, LIM["suhu"], tn); sH, bH_ = q(sH, aH, LIM["rh"], tn)
    L["synop_dibuang"] = dict(tekanan=int(bP_.sum()), suhu=int(bT_.sum()), rh=int(bH_.sum()))
    # 3. sisipan sebagai lonjakan
    kt = d.synop_wind_speed_kt.to_numpy(float); rep_w = np.isfinite(sW); nbW = tetangga(aW)
    sis_w_kt = rep_w & (kt >= 1) & (np.abs(aW - kt) < 0.02) & (np.abs(aW - kt * KT) > 0.05) & (np.abs(aW - nbW) > 0.3 * np.abs(aW)); aW[sis_w_kt] = kt[sis_w_kt] * KT
    sis_w = sis_w_kt | (rep_w & (np.abs(aW - sW) < 0.02))
    sPraw = sPs - c; nbP = tetangga(aP); sis_p = np.isfinite(sPs) & (np.abs(aP - sPraw) < 0.05)
    lonj_p = sis_p & (np.abs(aP - nbP) >= 0.5 * np.abs(c))
    if s != "jambi" and abs(np.nanmedian(c)) > 0.3: aP[lonj_p] = sPs[lonj_p]; sis_p = lonj_p
    sis_T = np.isfinite(sT) & (np.abs(aT - sT) < 0.005); sis_H = np.isfinite(sH) & (np.abs(aH - sH) < 0.005)
    sis = dict(suhu=sis_T, rh=sis_H, tekanan=sis_p, angin=sis_w)
    L["sisipan"] = {k: int(v.sum()) for k, v in sis.items()} | dict(angin_knot=int(sis_w_kt.sum()))
    # 5. lonjakan angin logger satu slot
    lw = (aW > 8) & (aW > 3 * nbW) & (np.r_[np.nan, aW[:-1]] < aW / 2) & (np.r_[aW[1:], np.nan] < aW / 2) & ~sis_w & ~isi3["angin"] & ~kaus["angin"]
    aW[lw] = np.nan; L["lonjakan_angin_dibuang"] = int(lw.sum())
    A = dict(suhu=aT, rh=aH, tekanan=aP, angin=aW); ref = dict(suhu=sT, rh=sH, tekanan=sPs, angin=sW)
    # 1. deret mayoritas-SYNOP -> bangun ulang
    rep = {v: np.isfinite(ref[v]) for v in ref}
    siang = lat & (d.solar_elev_deg.to_numpy(float) > 5)   # amandemen 1: semua slot siang tahun latih, bukan hanya jam laporan
    frac = {v: float(((sis[v] | kaus[v]) & siang).sum() / max(siang.sum(), 1)) for v in ref}
    RB = {v for v in ("suhu", "rh", "angin") if frac[v] >= 0.5} | ({"tekanan"} if s == "jambi" else set()); L["fraksi_dari_synop_latih"] = {k: round(v, 3) for k, v in frac.items()}; L["bangun_ulang"] = sorted(RB)
    TT = dict(c=float(np.nanmedian(c)) if s != "jambi" else None, klim={}, klim_rb={})
    out = {}
    for v in RB:
        # amandemen 3: bentuk siklus harian dari semua slot tahun latih (offset level logger saling meniadakan dalam x̄(t) − x̄(t0))
        cl = tetap["klim_rb"][v] if tetap else klim(A[v], t, lat & np.isfinite(A[v])); TT["klim_rb"][v] = cl
        x = isi_kausal(ref[v], cl, t); x = np.clip(x, 0, 100) if v == "rh" else (np.clip(x, 0, None) if v == "angin" else x); out[v] = x
        PV[f"met_bangun_ulang_{v}"] = np.ones(len(t), bool)
    # 2. koreksi bias kausal untuk deret logger (rekonstruksi V6 ikut dikoreksi; isian V6.3 dan sisipan tidak)
    def med7(e, ok):
        r = pd.Series(np.where(ok, e, np.nan), index=t); r = r[np.isfinite(r.to_numpy())]
        return r.rolling(W7, min_periods=MINR).median() if len(r) else pd.Series(dtype=float)
    beku = {v: sis[v] | isi3[v] for v in ref}
    b = {}
    for v in ("suhu", "rh", "tekanan"):
        b[v] = ke_semua(med7(A[v] - ref[v], rep[v] & np.isfinite(A[v]) & ~beku[v]), t, 0.0)
    okw = rep_w & np.isfinite(aW) & (sW >= 1) & ~beku["angin"]; R = pd.DataFrame({"s": sW, "a": aW}, index=t)[okw]
    kk = (R.s.rolling(W7, min_periods=MINR).sum() / R.a.rolling(W7, min_periods=MINR).sum()).clip(0.5, 2.0) if len(R) else pd.Series(dtype=float); kW_ = ke_semua(kk, t, 1.0)
    okd = rep_w & (sW >= 2) & (aW >= 0.5) & np.isfinite(aD) & np.isfinite(sD) & (sD > 0) & ~beku["angin"] & ("angin" not in RB)
    if okd.sum() > MINR:
        dd = np.radians(sD - aD); Dd = pd.DataFrame({"s": np.sin(dd), "c": np.cos(dd)}, index=t)[okd]
        dD = ke_semua(np.degrees(np.arctan2(Dd.s.rolling(W7, min_periods=MINR).mean(), Dd.c.rolling(W7, min_periods=MINR).mean())), t, 0.0)
    else: dD = np.zeros(len(t))
    cor = dict(suhu=np.where(beku["suhu"], aT, aT - b["suhu"]), rh=np.clip(np.where(beku["rh"], aH, aH - b["rh"]), 0, 100), tekanan=np.where(beku["tekanan"], aP, aP - b["tekanan"]), angin=np.clip(np.where(beku["angin"], aW, aW * kW_), 0, None))
    cD = np.where(np.isfinite(aD), np.where(beku["angin"], aD, (aD + dD) % 360), np.nan)
    for v in ("suhu", "rh", "tekanan"): PV[f"met_bias_{v}"] = np.where(beku[v] | (v in RB), 0, b[v]).astype("float32")
    PV["met_bias_angin"] = np.where(beku["angin"] | ("angin" in RB), 1, kW_).astype("float32"); PV["met_bias_arah"] = np.where(beku["angin"] | ("angin" in RB), 0, dD).astype("float32")
    # 3. minggu rusak -> isian kausal (deret logger saja)
    kun = t.isocalendar().year.to_numpy() * 100 + t.isocalendar().week.to_numpy()
    if gagal is None:
        gagal = {}
        for v, thr in (("suhu", 1.5), ("rh", 10.0), ("tekanan", 1.0)):
            m = rep[v] & np.isfinite(cor[v]) & ~sis[v]; f = pd.Series(np.abs(cor[v] - ref[v])[m] > thr).groupby(kun[m]).agg(["mean", "size"])
            gagal[v] = set(f.index[(f["mean"] > 0.2) & (f["size"] >= 20)]) if v not in RB else set()
        raw = d.aws_wind_speed_ms.to_numpy(float); m = rep_w & np.isfinite(raw)
        g = pd.DataFrame({"z": ((raw == 0) & (sW >= 2))[m], "s2": (sW >= 2)[m], "a": raw[m], "s": sW[m], "k": kun[m]}).groupby("k")
        z = g.z.sum() / g.s2.sum().clip(lower=1); r = g.apply(lambda q_: q_.a.corr(q_.s) if len(q_) >= 20 and q_.a.std() > 0 and q_.s.std() > 0 else np.nan, include_groups=False)
        gagal["angin"] = (set(z.index[z > 0.05]) | set(r.index[r < 0.4]) | set(np.unique(kun[isi3["angin"]]))) if "angin" not in RB else set()
        dd = np.abs((sD - cD) + 180) % 360 - 180; gd = pd.Series(np.abs(dd[okd])).groupby(kun[okd]).agg(["median", "size"]); gagal["arah"] = set(gd.index[(gd["median"] > 45) & (gd["size"] >= 20)])
    for v in ("suhu", "rh", "tekanan", "angin"):
        if v in RB: PV[f"met_isi_{v}"] = np.zeros(len(t), bool); PV[f"met_sisipan_{v}"] = sis[v]; continue
        gm = np.isin(kun, list(gagal[v])); x = cor[v].copy()
        if gm.any():
            cl = tetap["klim"][v] if tetap else klim(cor[v], t, lat & ~gm & np.isfinite(cor[v])); TT["klim"][v] = cl; f = isi_kausal(ref[v], cl, t)
            x[gm] = (np.clip(f, 0, 100) if v == "rh" else (np.clip(f, 0, None) if v == "angin" else f))[gm]
        out[v] = x; PV[f"met_isi_{v}"] = gm; PV[f"met_sisipan_{v}"] = sis[v]
        if f"met_bangun_ulang_{v}" not in PV: PV[f"met_bangun_ulang_{v}"] = np.zeros(len(t), bool)
    gm = np.isin(kun, list(gagal["arah"])); cD = np.where(gm, np.nan, cD); PV["met_isi_arah"] = gm; PV["met_lonjakan_angin"] = lw
    PV["met_synop_dibuang_tekanan"], PV["met_synop_dibuang_suhu"], PV["met_synop_dibuang_rh"] = bP_, bT_, bH_
    L["minggu_gagal"] = {v: len(g_) for v, g_ in gagal.items()}
    return dict(T=out["suhu"], H=out["rh"], P=out["tekanan"], W=out["angin"], D=cD), PV, gagal, L, ref, TT

if __name__ == "__main__":
    assert not os.path.exists(os.path.join(V5, "SHA256.txt")), "V6.5 sudah beku"
    if os.path.exists(V5): shutil.rmtree(V5)
    shutil.copytree(V3, V5, copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("SHA256.txt", "README.md")); LAP = {}
    for s in S_:
        d0 = pd.read_parquet(os.path.join(V3, "00_data", f"{s}_full.parquet")); dr = pd.read_parquet(os.path.join(V3, "00_data_rawfill", f"{s}_full.parquet"))
        pv3 = pd.read_parquet(os.path.join(V3, "provenance", f"{s}_provenance.parquet")); X, PV, gagal, L, ref, TT = proses(d0, s, prov=pv3); t = pd.DatetimeIndex(d0.ts_wib)
        for cut in ("2022-09-14 10:05", "2024-03-03 15:35", "2025-11-29 08:15"):
            dc = d0.copy(); cc = t > pd.Timestamp(cut)
            for c in [c for c in d0.columns if c.startswith("synop_")]: dc.loc[cc, c] = np.nan
            Xc = proses(dc, s, gagal, TT, pv3)[0]
            for k_ in X: assert np.allclose(np.asarray(Xc[k_])[~cc], np.asarray(X[k_])[~cc], equal_nan=True, atol=1e-9), (s, cut, k_)
        for var, d in (("00_data", d0), ("00_data_rawfill", dr)):
            dt = d.dtypes; old = d.copy()
            d["aws_temp_c"], d["aws_rh_pct"], d["aws_pressure_hpa"], d["aws_wind_speed_ms"] = X["T"], X["H"], X["P"], X["W"]
            ada_arah = np.isfinite(old.aws_wind_dir_deg.to_numpy(float)).any()
            if ada_arah: d["aws_wind_dir_deg"] = X["D"]
            d = turunan(d)
            if not ada_arah: d["aws_wind_dir_sin"], d["aws_wind_dir_cos"] = old.aws_wind_dir_sin, old.aws_wind_dir_cos
            for c in d.columns:
                if str(dt[c]) != str(d[c].dtype): d[c] = d[c].astype(dt[c])
            beda = sorted(c for c in d.columns if not d[c].equals(old[c])); assert set(beda) <= set(MET), (s, var, set(beda) - set(MET))
            d.to_parquet(os.path.join(V5, var, f"{s}_full.parquet"), index=False)
        pv = os.path.join(V5, "provenance", f"{s}_provenance.parquet"); P_ = pd.read_parquet(pv)
        for k_ in sorted(PV): P_[k_] = PV[k_]
        P_.to_parquet(pv, index=False)
        L["isi_slot"] = {k_: int(np.asarray(v).sum()) for k_, v in PV.items() if k_.startswith("met_isi")}; LAP[s] = L; print(s, json.dumps(L, ensure_ascii=False, default=str), flush=True)
    json.dump(LAP, open(os.path.join(HERE, "l1_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str); print("SELESAI")
