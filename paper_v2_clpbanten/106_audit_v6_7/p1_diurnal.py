# -*- coding: utf-8 -*-
"""Tahap 106 P1: audit siklus harian semua variabel V6.7 terhadap literatur (hanya membaca). Waktu = waktu matahari semu (AST) = WIB + (bujur − 105)·4 menit + EoT.
Jendela harapan (literatur):
- GHI puncak 11.15–12.45 AST (simetri geometris; awan siang menggeser sedikit lebih pagi); GHI > 5 W m-2 mulai ≤ 30 menit dari terbit hitungan.
- k_c: rezim konvektif darat tropis — rata-rata pagi (08–11) > sore (13–16) (Yang & Slingo 2001; Mori et al. 2004; Qian 2008).
- k_d (fraksi difus): minimum dekat siang (10–14 AST); sore ≥ pagi pada rezim konvektif.
- Fraksi awan/COT CLP dan okta SYNOP: maksimum siang–sore (12–17 AST) di darat; pesisir barat Sumatra boleh pagi (sirkulasi darat–laut).
- CTH: sore > pagi (konveksi dalam).
- Hujan: puncak 13–21 AST di darat Jawa/Sumatra/Kalimantan (Mori 2004; Qian 2008; Yamanaka 2016); pesisir boleh malam–pagi.
- Suhu: maksimum 12–15 AST, minimum 04–07 AST, amplitudo 4–10 °C. RH: kebalikannya.
- Tekanan: S2 puncak 09–11 dan 21–23 AST, lembah 03–05 dan 15–17, amplitudo 0,9–1,7 hPa (Dai & Wang 1999).
- Kecepatan angin: maksimum 11–17 AST, minimum malam (pencampuran batas, angin laut).
- Visibilitas: minimum pagi (05–08), meningkat siang.
"""
import os, numpy as np, pandas as pd
pd.set_option("display.width", 280); pd.set_option("display.max_columns", 60); pd.set_option("display.max_rows", 300)
HERE = os.path.dirname(os.path.abspath(__file__)); V = r"C:\Users\ariff\Documents\Balai_data_v6_7"
LON = dict(banten=106.7509, bengkulu=102.311998, jambi=103.4944, jogja=110.353578, kalbar=109.1905, semarang=110.3812)
def jam(prof, f=np.argmax): return float(prof.index[f(prof.to_numpy())])
def dalam(h, a, b): return a <= h <= b if a <= b else (h >= a or h <= b)
R, PROF = [], {}
for s, lo in LON.items():
    d = pd.read_parquet(os.path.join(V, "00_data", f"{s}_full.parquet")); cs = pd.read_parquet(os.path.join(V, "clearsky", f"{s}_ineichen.parquet")).ghi_cs.to_numpy()
    e = pd.read_parquet(os.path.join(V, "clp_ekstra", f"{s}_clp_ekstra.parquet")); t = pd.DatetimeIndex(d.ts_wib)
    ast = (t.hour * 60 + t.minute + 5 + (lo - 105) * 4 + d.eot_min.to_numpy(float)) % 1440 / 60.0      # tengah slot
    hb = np.floor(ast * 2) / 2                                                                          # kelas 30 menit
    G = d.ghi_wm2.to_numpy(float); el = d.solar_elev_deg.to_numpy(float)
    with np.errstate(all="ignore"): kc = np.where((el > 10) & (cs > 50), G / cs, np.nan); kd = np.where((el > 10) & (G > 50), d.dhi_wm2.to_numpy(float) / G, np.nan)
    X = pd.DataFrame(dict(G=G, kc=kc, kd=kd, frac=np.where(e.qc_clp_sza.to_numpy() == 0, e.clp_cloud_frac.to_numpy(), np.nan), cot=np.where(e.qc_clp_sza.to_numpy() == 0, d.clp_cot.to_numpy(float), np.nan),
                          cth=np.where(e.qc_clp_sza.to_numpy() == 0, d.clp_cth_km.to_numpy(float), np.nan), okta=d.synop_cloud_cover_oktas.where(d.synop_cloud_cover_oktas <= 8).to_numpy(float),
                          hujan=d.aws_rain_mm.to_numpy(float), T=d.aws_temp_c.to_numpy(float), H=d.aws_rh_pct.to_numpy(float), P=d.aws_pressure_hpa.to_numpy(float), W=d.aws_wind_speed_ms.to_numpy(float),
                          vis=d.synop_visibility_km.to_numpy(float)))
    X["P"] = X.P - pd.Series(X.P).rolling(144, center=True, min_periods=60).mean()
    pr = X.groupby(hb).mean(); PROF[s] = pr
    r = dict(stasiun=s)
    r["GHI_puncak_AST"] = jam(pr.G); r["GHI_ok"] = dalam(r["GHI_puncak_AST"], 11.25, 12.75)
    r["GHI_pagi/sore(±3j)"] = round(float(pr.G.loc[9.0:9.5].mean() / pr.G.loc[14.5:15.0].mean()), 3)
    sr = pd.Series(el).groupby(t.date).apply(lambda z: np.nan) if False else None
    day = pd.DataFrame({"d": t.date, "ast": ast, "G": G, "el": el})
    terbit_G = day[day.G > 5].groupby("d").ast.min(); terbit_el = day[day.el > 0].groupby("d").ast.min(); r["GHI_mulai_minus_terbit_mnt"] = round(float((terbit_G - terbit_el).median() * 60), 0)
    pag, sor = pr.kc.loc[8.0:10.5].mean(), pr.kc.loc[13.0:15.5].mean(); r["kc_pagi"], r["kc_sore"] = round(float(pag), 3), round(float(sor), 3); r["kc_ok"] = bool(pag > sor)
    r["kd_min_AST"] = jam(pr.kd.loc[7:17], np.argmin); r["kd_sore≥pagi"] = bool(pr.kd.loc[13.0:15.5].mean() >= pr.kd.loc[8.0:10.5].mean()); r["kd_ok"] = dalam(r["kd_min_AST"], 9.5, 14.0)
    for v in ("frac", "cot", "okta"): r[f"{v}_puncak_AST"] = jam(pr[v].loc[7:17])
    r["awan_ok"] = dalam(r["frac_puncak_AST"], 11.5, 17.5) or s == "bengkulu"
    r["cth_sore>pagi"] = bool(pr.cth.loc[13.0:16.0].mean() > pr.cth.loc[8.0:11.0].mean())
    hj = X.hujan.groupby(np.floor(ast)).mean(); r["hujan_puncak_AST"] = float(hj.idxmax()); r["hujan_ok"] = dalam(r["hujan_puncak_AST"], 13, 21)
    r["T_maks_AST"], r["T_min_AST"] = jam(pr["T"]), jam(pr["T"], np.argmin); r["T_amp"] = round(float(pr["T"].max() - pr["T"].min()), 2); r["T_ok"] = dalam(r["T_maks_AST"], 12, 15) and dalam(r["T_min_AST"], 4, 7.5) and 4 <= r["T_amp"] <= 10
    r["RH_maks_AST"], r["RH_min_AST"] = jam(pr.H), jam(pr.H, np.argmin); r["RH_ok"] = dalam(r["RH_min_AST"], 12, 15.5) and dalam(r["RH_maks_AST"], 3, 8)
    p = pr.P; r["P_puncak1_AST"], r["P_puncak2_AST"] = jam(p.loc[6:13]), jam(p.loc[18:23.5]); r["P_lembah1_AST"], r["P_lembah2_AST"] = jam(p.loc[0:7], np.argmin), jam(p.loc[12:19], np.argmin)
    r["P_amp_puncak_lembah"] = round(float(p.max() - p.min()) / 2, 2)
    r["P_ok"] = dalam(r["P_puncak1_AST"], 9, 11) and dalam(r["P_puncak2_AST"], 20.5, 23.5) and dalam(r["P_lembah2_AST"], 14.5, 17.5)
    r["W_maks_AST"], r["W_min_AST"] = jam(pr.W), jam(pr.W, np.argmin); r["W_ok"] = dalam(r["W_maks_AST"], 11, 17) and not dalam(r["W_min_AST"], 9, 17)
    r["vis_min_AST"] = jam(pr.vis.loc[5:18], np.argmin); r["vis_ok"] = dalam(r["vis_min_AST"], 5, 8.5)
    # arah: rata-rata vektor (berbobot kecepatan) siang 13–16 lawan malam 00–05, hanya slot berarah
    W = d.aws_wind_speed_ms.to_numpy(float); sn, cn = d.aws_wind_dir_sin.to_numpy(float), d.aws_wind_dir_cos.to_numpy(float); ok = (sn ** 2 + cn ** 2) > 0.5
    def arah(m):
        m = m & ok; return float((np.degrees(np.arctan2(np.nansum((W * sn)[m]), np.nansum((W * cn)[m]))) + 360) % 360) if m.sum() > 100 else np.nan
    r["arah_siang_13_16"] = round(arah((ast >= 13) & (ast < 16)), 0); r["arah_malam_00_05"] = round(arah(ast < 5), 0)
    r["putaran_siang_malam_deg"] = round(float(abs((r["arah_siang_13_16"] - r["arah_malam_00_05"] + 180) % 360 - 180)), 0) if np.isfinite(r["arah_malam_00_05"]) else np.nan
    R.append(r); print(s, "selesai", flush=True)
T = pd.DataFrame(R); T.to_csv(os.path.join(HERE, "P1_diurnal.csv"), index=False); print(T.T.to_string())
pd.concat({s: p for s, p in PROF.items()}).to_csv(os.path.join(HERE, "P1_profil_30mnt.csv"))
ok = [c for c in T.columns if c.endswith("_ok")]; print("== ringkas lolos:"); print(T[["stasiun"] + ok].to_string(index=False))
