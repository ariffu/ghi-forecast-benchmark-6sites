# -*- coding: utf-8 -*-
"""Tahap 100: bangun Balai_data_v6_4 dari Balai_data_v6_3 (hanya dibaca) — meteorologi AWS beracuan SYNOP (DESAIN_100.md)."""
import os, json, shutil, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); V3 = r"C:\Users\ariff\Documents\Balai_data_v6_3"; V4 = r"C:\Users\ariff\Documents\Balai_data_v6_4"
S_ = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; ALT = dict(banten=27, bengkulu=9, jambi=24, jogja=182, kalbar=2, semarang=6)
KT = 0.514444; W7 = "7D"; MINR = 20
MET = ["aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_wind_dir_deg", "aws_wind_dir_sin", "aws_wind_dir_cos", "aws_temp_lag_10m", "aws_temp_lag_30m", "aws_temp_lag_60m",
       "aws_temp_delta_60m", "aws_temp_roll_180m_mean", "aws_rh_lag_60m", "aws_rh_delta_60m", "aws_rh_roll_180m_mean", "aws_pressure_lag_60m", "aws_pressure_delta_60m", "aws_wind_speed_roll_180m_mean"]

def bersih(x, lo, hi):
    x = x.astype(float).copy(); x[(x < lo) | (x > hi)] = np.nan; return x
def ke_semua(est, t, netral):
    """estimasi di jam laporan -> semua slot, kausal (nilai terakhir <= t)."""
    e = np.array(est.reindex(t).ffill().to_numpy(float), dtype=float, copy=True); e[~np.isfinite(e)] = netral; return e
def klim(a_lat, t, lat_ok):
    md = t.hour * 60 + t.minute; return pd.Series(a_lat[lat_ok]).groupby([t.month[lat_ok], md[lat_ok]]).mean()
def isi_kausal(ref, cl, t, umur=180):
    md = t.hour * 60 + t.minute
    last = pd.Series(ref, index=t).ffill().to_numpy(); t0 = pd.DatetimeIndex(pd.Series(np.where(np.isfinite(ref), t, pd.NaT), index=t).ffill())
    age = ((t - t0).total_seconds() / 60).to_numpy(); md0 = np.nan_to_num(t0.hour * 60 + t0.minute, nan=0).astype(int)
    x = last + cl.reindex(list(zip(t.month, md))).to_numpy() - cl.reindex(list(zip(t0.month.fillna(1).astype(int), md0))).to_numpy(); x[~(age <= umur)] = np.nan; return x

def proses(d, s, gagal=None, tetap=None, prov=None):
    """d: DataFrame V6.3 satu stasiun. gagal: dict variabel -> himpunan minggu gagal (None = tentukan sendiri). Kembalikan (kolom baru, provenance, gagal, laporan)."""
    t = pd.DatetimeIndex(d.ts_wib); lat = t.year <= 2023; L = {}; PV = {}
    sT, sH = bersih(d.synop_temp_c, 0, 45).to_numpy(), bersih(d.synop_rh_pct, 1, 100).to_numpy()
    sP = bersih(d.synop_pressure_hpa, 900, 1050).to_numpy(); sW = (bersih(d.synop_wind_speed_kt, 0, 199) * KT).to_numpy(); sD = bersih(d.synop_wind_dir_deg, 0, 360).to_numpy()
    aT, aH, aP, aW, aD = (d[c].to_numpy(float).copy() for c in ("aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms", "aws_wind_dir_deg"))
    # deret yang sudah berasal dari SYNOP (rekonstruksi kausal V6, isian V6.3): tidak dikoreksi dan tidak dipakai menaksir bias
    fl = lambda *cs: np.logical_or.reduce([prov[c].to_numpy(bool) for c in cs if c in prov]) if any(c in prov for c in cs) else np.zeros(len(d), bool)
    kT, kH = fl("aws_kausal_suhu"), fl("aws_kausal_rh"); kP = fl("aws_kausal_tekanan", "aws_isi_synop_tekanan", "aws_isi_synop_tekanan_datar"); kW = fl("aws_kausal_angin", "aws_isi_synop_angin")
    if s == "jambi": kP = np.zeros(len(d), bool)   # Jambi: seluruh deret di level QFF, digeser ke level sensor
    # 0. satuan dan konvensi
    kt = d.synop_wind_speed_kt.to_numpy(float); rep_w = np.isfinite(sW)
    sis_w_kt = rep_w & (kt >= 1) & (np.abs(aW - kt) < 0.02) & (np.abs(aW - kt * KT) > 0.05); aW[sis_w_kt] = kt[sis_w_kt] * KT
    sis_w = sis_w_kt | (rep_w & (np.abs(aW - sW) < 0.02))
    if s == "jambi":
        c = -sP * (1 - np.exp(-9.80665 * ALT[s] / (287.05 * (np.nan_to_num(sT, nan=27.0) + 273.15)))); L["c_tekanan"] = "hipsometrik, median %.3f" % float(np.nanmedian(c))
    else:
        rep_p = np.isfinite(sP) & np.isfinite(aP); exact = rep_p & (np.abs(aP - sP) < 0.05)
        c0 = tetap["c"] if tetap else float(np.median((aP - sP)[lat & rep_p & ~exact])); c = np.full(len(t), c0); L["c_tekanan"] = round(float(c0), 3)
    sPs = sP + c; rep_p = np.isfinite(sPs)
    sis_p = rep_p & (np.abs(aP - sP) < 0.05)
    if s != "jambi" and abs(np.nanmedian(c)) > 0.3: aP[sis_p] = sPs[sis_p]
    sis_T = np.isfinite(sT) & (np.abs(aT - sT) < 0.005); sis_H = np.isfinite(sH) & (np.abs(aH - sH) < 0.005)
    L["sisipan"] = dict(angin_knot=int(sis_w_kt.sum()), angin=int(sis_w.sum()), tekanan=int(sis_p.sum()), suhu=int(sis_T.sum()), rh=int(sis_H.sum()))
    # 1. koreksi bias kausal
    def med7(e, ok):
        r = pd.Series(np.where(ok, e, np.nan), index=t)[ok | False]; r = r[np.isfinite(r.to_numpy())]
        return r.rolling(W7, min_periods=MINR).median() if len(r) else pd.Series(dtype=float)
    bT = ke_semua(med7(aT - sT, np.isfinite(sT) & np.isfinite(aT) & ~sis_T & ~kT), t, 0.0); bH = ke_semua(med7(aH - sH, np.isfinite(sH) & np.isfinite(aH) & ~sis_H & ~kH), t, 0.0)
    bP = ke_semua(med7(aP - sPs, (rep_p & np.isfinite(aP) & ~sis_p & ~kP) | ((s == "jambi") & rep_p & np.isfinite(aP))), t, 0.0)
    okw = rep_w & np.isfinite(aW) & (sW >= 1) & ~sis_w & ~kW; R = pd.DataFrame({"s": sW, "a": aW}, index=t)[okw]
    k = (R.s.rolling(W7, min_periods=MINR).sum() / R.a.rolling(W7, min_periods=MINR).sum()).clip(0.5, 2.5) if len(R) else pd.Series(dtype=float); kW_ = ke_semua(k, t, 1.0)
    okd = rep_w & (sW >= 2) & (aW >= 0.5) & np.isfinite(aD) & np.isfinite(sD) & (sD > 0) & ~kW
    if okd.sum() > MINR:
        dd = np.radians(sD - aD); Dd = pd.DataFrame({"s": np.sin(dd), "c": np.cos(dd)}, index=t)[okd]
        dl = np.degrees(np.arctan2(Dd.s.rolling(W7, min_periods=MINR).mean(), Dd.c.rolling(W7, min_periods=MINR).mean())); dD = ke_semua(dl, t, 0.0)
    else: dD = np.zeros(len(t))
    # slot sisipan = SYNOP itu sendiri (acuan), tidak dikoreksi; Jambi: seluruh deret tekanan (QFF) digeser ke level sensor
    kT, kH, kW = kT | sis_T, kH | sis_H, kW | sis_w; kP = (kP | sis_p) if s != "jambi" else kP
    cT = np.where(kT, aT, aT - bT); cH = np.clip(np.where(kH, aH, aH - bH), 0, 100); cP = np.where(kP, aP, aP - bP); cW = np.clip(np.where(kW, aW, aW * kW_), 0, None)
    cD = np.where(np.isfinite(aD), np.where(kW, aD, (aD + dD) % 360), np.nan)
    for v, b in (("suhu", np.where(kT, 0, bT)), ("rh", np.where(kH, 0, bH)), ("tekanan", np.where(kP, 0, bP)), ("angin", np.where(kW, 1, kW_)), ("arah", np.where(kW, 0, dD))): PV[f"met_bias_{v}"] = b.astype("float32")
    # 2. kerusakan per minggu -> isian kausal SYNOP
    wk = t.isocalendar().week.to_numpy(); yr = t.isocalendar().year.to_numpy(); kun = yr * 100 + wk
    ref = dict(suhu=sT, rh=sH, tekanan=sPs, angin=sW); cor = dict(suhu=cT, rh=cH, tekanan=cP, angin=cW); sis = dict(suhu=sis_T, rh=sis_H, tekanan=sis_p, angin=sis_w)
    if gagal is None:
        gagal = {}
        for v, thr in (("suhu", 1.5), ("rh", 10.0), ("tekanan", 1.0)):
            m = np.isfinite(ref[v]) & np.isfinite(cor[v]) & ~sis[v]; f = pd.Series(np.abs(cor[v] - ref[v])[m] > thr).groupby(kun[m]).agg(["mean", "size"])
            gagal[v] = set(f.index[(f["mean"] > 0.2) & (f["size"] >= 20)])
        m = rep_w & np.isfinite(d.aws_wind_speed_ms.to_numpy(float)); raw = d.aws_wind_speed_ms.to_numpy(float)
        g = pd.DataFrame({"z": ((raw == 0) & (sW >= 2))[m], "s2": (sW >= 2)[m], "a": raw[m], "s": sW[m], "k": kun[m]}).groupby("k")
        z = g.z.sum() / g.s2.sum().clip(lower=1); r = g.apply(lambda q: q.a.corr(q.s) if len(q) >= 20 and q.a.std() > 0 and q.s.std() > 0 else np.nan, include_groups=False)
        gagal["angin"] = set(z.index[(z > 0.05)]) | set(r.index[r < 0.4])
        if "aws_isi_synop_angin" in prov: gagal["angin"] |= set(np.unique(kun[prov.aws_isi_synop_angin.to_numpy(bool)]))   # isian V6.3 dihitung ulang di level SYNOP
        m = okd; dd = (np.abs((sD - cD) + 180) % 360 - 180)
        gd = pd.Series(np.abs(dd[m])).groupby(kun[m]).agg(["median", "size"]); gagal["arah"] = set(gd.index[(gd["median"] > 45) & (gd["size"] >= 20)])
    out = {}; TT = dict(c=float(np.nanmedian(c)) if s != "jambi" else None, klim={})
    for v in ("suhu", "rh", "tekanan", "angin"):
        gm = np.isin(kun, list(gagal[v])); okc = lat & ~gm & np.isfinite(cor[v]); x = cor[v].copy()
        if gm.any():
            cl = tetap["klim"][v] if tetap else klim(cor[v], t, okc); TT["klim"][v] = cl; f = isi_kausal(ref[v], cl, t)
            if v == "rh": f = np.clip(f, 0, 100)
            if v == "angin": f = np.clip(f, 0, None)
            x[gm] = f[gm]
        out[v] = x; PV[f"met_isi_{v}"] = gm; PV[f"met_sisipan_{v}"] = sis[v]
    gm = np.isin(kun, list(gagal["arah"])); cD = np.where(gm, np.nan, cD); PV["met_isi_arah"] = gm
    L["minggu_gagal"] = {v: sorted(int(a) for a in g_) for v, g_ in gagal.items()}
    return dict(T=out["suhu"], H=out["rh"], P=out["tekanan"], W=out["angin"], D=cD), PV, gagal, L, ref, TT

def turunan(d):
    T, H, P, W = (pd.to_numeric(d[c]) for c in ("aws_temp_c", "aws_rh_pct", "aws_pressure_hpa", "aws_wind_speed_ms")); D = pd.to_numeric(d.aws_wind_dir_deg)
    for m, k in ((10, 1), (30, 3), (60, 6)): d[f"aws_temp_lag_{m}m"] = T.shift(k).to_numpy()
    d["aws_temp_delta_60m"] = (T - T.shift(6)).to_numpy(); d["aws_temp_roll_180m_mean"] = T.rolling(18, min_periods=1).mean().to_numpy()
    d["aws_rh_lag_60m"] = H.shift(6).to_numpy(); d["aws_rh_delta_60m"] = (H - H.shift(6)).to_numpy(); d["aws_rh_roll_180m_mean"] = H.rolling(18, min_periods=1).mean().to_numpy()
    d["aws_pressure_lag_60m"] = P.shift(6).to_numpy(); d["aws_pressure_delta_60m"] = (P - P.shift(6)).to_numpy(); d["aws_wind_speed_roll_180m_mean"] = W.rolling(18, min_periods=1).mean().to_numpy()
    d["aws_wind_dir_sin"] = np.sin(np.radians(D)).to_numpy(); d["aws_wind_dir_cos"] = np.cos(np.radians(D)).to_numpy(); return d

if __name__ == "__main__":
    assert not os.path.exists(os.path.join(V4, "SHA256.txt")), "V6.4 sudah beku"
    if os.path.exists(V4): shutil.rmtree(V4)
    shutil.copytree(V3, V4, copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("SHA256.txt", "README.md")); LAP = {}
    for s in S_:
        d0 = pd.read_parquet(os.path.join(V3, "00_data", f"{s}_full.parquet")); dr = pd.read_parquet(os.path.join(V3, "00_data_rawfill", f"{s}_full.parquet"))
        assert all(np.array_equal(np.nan_to_num(d0[c].to_numpy(float), nan=-9e9), np.nan_to_num(dr[c].to_numpy(float), nan=-9e9)) for c in MET + [c for c in d0.columns if c.startswith("synop_")]), s
        pv3 = pd.read_parquet(os.path.join(V3, "provenance", f"{s}_provenance.parquet")); X, PV, gagal, L, ref, TT = proses(d0, s, prov=pv3)
        # kausalitas: hapus SYNOP sesudah titik potong, keputusan minggu gagal tetap
        t = pd.DatetimeIndex(d0.ts_wib)
        for cut in ("2022-09-14 10:05", "2024-03-03 15:35", "2025-11-29 08:15"):
            dc = d0.copy(); cc = t > pd.Timestamp(cut)
            for c in [c for c in d0.columns if c.startswith("synop_")]: dc.loc[cc, c] = np.nan
            Xc = proses(dc, s, gagal, TT, pv3)[0]
            for k_ in X: assert np.allclose(np.asarray(Xc[k_])[~cc], np.asarray(X[k_])[~cc], equal_nan=True, atol=1e-9), (s, cut, k_)
        for var, d in (("00_data", d0), ("00_data_rawfill", dr)):
            dt = d.dtypes; old = d.copy()
            d["aws_temp_c"], d["aws_rh_pct"], d["aws_pressure_hpa"], d["aws_wind_speed_ms"] = X["T"], X["H"], X["P"], X["W"]
            if np.isfinite(old.aws_wind_dir_deg.to_numpy(float)).any(): d["aws_wind_dir_deg"] = X["D"]
            d = turunan(d)
            if not np.isfinite(old.aws_wind_dir_deg.to_numpy(float)).any(): d["aws_wind_dir_sin"], d["aws_wind_dir_cos"] = old.aws_wind_dir_sin, old.aws_wind_dir_cos
            for c in d.columns:
                if str(dt[c]) != str(d[c].dtype): d[c] = d[c].astype(dt[c])
            beda = sorted(c for c in d.columns if not d[c].equals(old[c])); assert set(beda) <= set(MET), (s, var, set(beda) - set(MET))
            d.to_parquet(os.path.join(V4, var, f"{s}_full.parquet"), index=False)
        pv = os.path.join(V4, "provenance", f"{s}_provenance.parquet"); P_ = pd.read_parquet(pv)
        for k_, v in PV.items(): P_[k_] = v
        P_.to_parquet(pv, index=False)
        # ringkasan residu bulanan sesudah perbaikan (jam laporan, bukan sisipan)
        m_ = t.to_period("M").astype(str); rs = {}
        for v, x in (("suhu", X["T"]), ("rh", X["H"]), ("tekanan", X["P"])):
            e = pd.Series(x - ref[v]); ok = np.isfinite(e.to_numpy()) & ~PV[f"met_sisipan_{v}"]; mm = e[ok].groupby(m_[ok]).median()
            rs[v] = dict(median_abs_bulanan_maks=round(float(mm.abs().max()), 2), median_bulanan=round(float(mm.median()), 3))
        ok = np.isfinite(ref["angin"]) & (ref["angin"] >= 1) & np.isfinite(X["W"]) & ~PV["met_sisipan_angin"]
        rr = pd.DataFrame({"a": X["W"][ok], "s": ref["angin"][ok], "m": m_[ok]}).groupby("m").sum(); q = rr.a / rr.s
        rs["angin_rasio"] = dict(min=round(float(q.min()), 2), maks=round(float(q.max()), 2))
        L["residu_sesudah"] = rs; L["isi_slot"] = {k_: int(np.asarray(v).sum()) for k_, v in PV.items() if k_.startswith("met_isi")}
        LAP[s] = L; print(s, json.dumps(L, ensure_ascii=False, default=str), flush=True)
    json.dump(LAP, open(os.path.join(HERE, "j2_laporan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str); print("SELESAI")
