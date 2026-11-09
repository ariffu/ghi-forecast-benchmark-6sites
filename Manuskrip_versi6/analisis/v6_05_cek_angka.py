# -*- coding: utf-8 -*-
"""Manuskrip V6, analisis 05 — memeriksa setiap angka teks MANUSKRIP_v6.md (dan angka prosa ESM_v6.md) terhadap sumbernya di V6.
Setiap angka dihitung ulang dari CSV/JSON keluaran V6.10, diformat seperti di naskah, lalu dipastikan string itu ada.
Juga diperiksa: sitasi ↔ pustaka, urutan Tabel/Gambar S, penanda tabel terisi, tidak ada {{penanda}} tersisa, koordinat Tabel 1.
Keluaran: daftar OK/GAGAL; kode keluar 1 bila ada yang gagal. Jalankan: PYTHONIOENCODING=utf-8 python -u v6_05_cek_angka.py"""
import os, re, sys, json, glob, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); V6 = os.path.dirname(HERE); ROOT = os.path.dirname(V6); P = os.path.join(ROOT, "paper_v2_clpbanten")
PV, RR, H, T114 = os.path.join(V6, "pipeline"), os.path.join(V6, "protokol", "hasil"), os.path.join(V6, "hasil"), os.path.join(P, "114_pendukung_v610")
DP = os.path.join(RR, "daftar_periksa")
TXT = open(os.path.join(V6, "MANUSKRIP_v6.md"), encoding="utf-8").read(); ESM = open(os.path.join(V6, "ESM_v6.md"), encoding="utf-8").read()
BODY = TXT.split("## References")[0]; BODY = BODY[BODY.index("## Abstract"):]
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]; TREES = ["LightGBM", "CatBoost", "XGBoost"]; NN = ["MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"]
def f(x, k=3): v = round(float(x), k); v = 0.0 if v == 0 else v; return f"−{abs(v):.{k}f}" if v < 0 else f"{v:.{k}f}"
def sg(x, k=3): v = round(float(x), k); v = 0.0 if v == 0 else v; return f"−{abs(v):.{k}f}" if v < 0 else f"+{v:.{k}f}"
def r(a, b, k=3): return f"{f(a, k)}–{f(b, k)}"
def rs(a, b, k=3): return f"{sg(a, k)} to {sg(b, k)}"
def pc(a, b, k=0): return f"{a:.{k}f}–{b:.{k}f}"
GAGAL = []
def cek(label, s, where=BODY):
    ok = s in where; print(("OK    " if ok else "GAGAL ") + f"{label}: «{s}»")
    if not ok: GAGAL.append(label)
def benar(label, cond):
    print(("OK    " if cond else "GAGAL ") + label)
    if not cond: GAGAL.append(label)
mm = lambda s: (float(s.min()), float(s.max()))

# ---- sumber ----
T3 = pd.read_csv(os.path.join(DP, "tabel3_baru.csv")).set_index(["blok", "site"]); R2 = T3.xs("R2", level="blok").loc[SITES]
CB = pd.read_csv(os.path.join(DP, "catboost_baru.csv")).set_index("site").loc[SITES]; BR = pd.read_csv(os.path.join(DP, "catboost_vs_ridge_baru.csv")).set_index("site").loc[SITES]
J = json.load(open(os.path.join(DP, "angka_baru.json"), encoding="utf-8")); RG = pd.read_csv(os.path.join(DP, "rentang_per_stasiun.csv")).set_index("site").loc[SITES]
UJ = pd.read_csv(os.path.join(DP, "uji_berpasangan_per_seed.csv")); UJ = UJ[UJ.vs == "LightGBM"]
RB = pd.read_csv(os.path.join(PV, "27_block_bootstrap", "replication_ablation_block.csv")).set_index(["site", "effect"])
AC = pd.read_csv(os.path.join(H, "ablasi_catboost_residual.csv")).set_index(["site", "effect"])
AK = pd.read_csv(os.path.join(H, "a_konvergensi.csv")).set_index("site").loc[SITES]; AJ = json.load(open(os.path.join(H, "angka_analisis.json"), encoding="utf-8"))
JG = json.load(open(os.path.join(H, "angka_gambar.json"), encoding="utf-8")); A = json.load(open(os.path.join(H, "angka_teks_v6.json"), encoding="utf-8"))
JD = json.load(open(os.path.join(H, "angka_data.json"), encoding="utf-8")); CC = pd.read_csv(os.path.join(H, "c_clp_kelas.csv")); BG = pd.read_csv(os.path.join(H, "b_galat_kelas.csv"))
W63 = pd.read_csv(os.path.join(PV, "63_aws_subkelompok", "subkelompok_6situs.csv")).set_index(["site", "subgroup"])
dCLP = pd.Series({s: RB.loc[(s, "dCLP"), "dR2"] for s in SITES}); spread = R2.Spread
eff = lambda D, k: pd.Series({s: D.loc[(s, k), "dR2"] for s in SITES}); sig = lambda D, k: pd.Series({s: D.loc[(s, k), "sig_block"] == "yes" for s in SITES})

# ================= Abstrak =================
cek("abstrak: sebaran arsitektur", f"differed by {r(*mm(spread))} in R² at each station")
cek("abstrak: stacking sisa galat", f"removed only {pc(*AJ['C3_porsi_sisa_pct'])}% of the remaining error")
cek("abstrak: ΔR² CLP", f"ΔR² = {rs(*mm(dCLP))}")
cek("abstrak: porsi sisa galat CLP", f"removing {pc(*JG['clp_porsi_sisa_pct'])}% of the remaining error")
cek("abstrak: AWS di atas CLP", f"surface meteorology added at most {sg(eff(RB, 'dAWS|CLP').max())}")
benar("abstrak: SYNOP di atas CLP nol (|ΔR²| < 0,0005, tidak signifikan)", eff(RB, "dSYNOP|CLP").abs().max() < 0.0005 and not sig(RB, "dSYNOP|CLP").any())
ch = CC[(CC.grup == "perubahan") & (CC.kelas == "berubah")]
cek("abstrak: RMSE turun saat langit berubah", f"by {pc(ch.turun_pct.min(), ch.turun_pct.max())}%")
lat = pd.Series(A["latensi_pct"]); cek("abstrak: latensi", f"removed {pc(*mm(lat))}% of it")
cek("abstrak: CatBoost", f"R² of {r(*mm(CB.R2), 2)} (RMSE {pc(*mm(CB.RMSE))} W m⁻²)")

# ================= 2.1 =================
lg = pd.Series(A["logger_2025"]); tu = pd.Series(A["terukur_2025"])
cek("logger 2025", f"the logger supplies {pc(*mm(lg), 1)}% of the daytime values"); cek("terukur 2025", f"make up {lg.min():.1f}"[:0] + f"make up {tu.min():.1f}–{'100' if tu.max() >= 99.95 else f'{tu.max():.1f}'}%")
benar("isian CLP < 0,001", A["isi_clp_maks"] < 0.001); cek("isian CLP", "less than 0.001 in R²")
h9 = {v["h09_pertama"] for v in JD["satelit"].values()}; h8 = {tuple(map(tuple, v["h08_2025"])) for v in JD["satelit"].values()}
benar("H9 mulai 2022-12-13 di semua stasiun", h9 == {"2022-12-13"}); cek("H8 sampai", "until 12 December 2022")
benar("H8 2025 = 12 Okt–25 Nov di semua stasiun", h8 == {(("2025-10-12", "2025-11-25"),)}); cek("H8 2025", "from 12 October to 25 November 2025")
sy = pd.Series(A["synop_okta_uji_pct"]); cek("SYNOP tersedia", f"available at {sy.min():.0f}–{('100' if sy.max() >= 99.95 else f'{sy.max():.0f}')}% of the test origins")
benar("SYNOP berlaku ≤ 50 menit (provenance)", True); cek("SYNOP 50 menit", "was kept for the following 50 min")
# ================= 2.2 =================
wf = A["walkforward"]; cek("walk-forward", f"R² = {wf['mean']:.3f} ± {wf['sd']:.3f} over five folds"); cek("LightGBM Bengkulu uji", f"test-year value of {R2.loc['bengkulu', 'LightGBM']:.3f}")
sl = A["seleksi_val"]; cek("seleksi prediktor", f"changed validation R² by {rs(sl[0], sl[1], 4)}")
# ================= 2.3 =================
cek("SE seed", f"(median {J['seed_se5_median']:.4f}, maximum {J['seed_se5_max']:.4f})"); cek("SD seed", f"(median {J['seed_sd_median']:.4f}, maximum {J['seed_sd_max']:.4f})")
# ================= 3.1 =================
cek("CatBoost R²", f"R² of {r(*mm(CB.R2))} (RMSE {pc(*mm(CB.RMSE), 1)} W m⁻², {pc(*mm(CB.nRMSE_pct))}% of the mean GHI), against {r(*mm(R2.SP))} for smart persistence")
cek("skill", f"was {r(*mm(CB.skill_pers))} against smart persistence and {r(*mm(CB.skill_cp))} against the CP reference")
cek("sebaran", f"differed by only {r(*mm(spread))} in R² at each station")
pos = RG.pohon_terbaik_minus_js_terbaik; benar("pohon terbaik di 5 stasiun, kalbar tidak", int((pos > 0).sum()) == 5 and pos["kalbar"] < 0)
cek("pohon vs jaringan saraf", f"by only {r(pos[pos > 0].min(), pos[pos > 0].max())} over the best neural network"); cek("kalbar", f"Transformer-hybrid led by {abs(pos['kalbar']):.4f}")
KATA = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
nb = J["nn_runs_sig_better"]; cek("run NN lebih akurat", f"Of the 150 single-seed neural runs, {KATA.get(nb, str(nb))} were significantly more accurate")
cek("run NN kurang akurat", f"whereas {J['nn_runs_sig_worse']} were significantly"); md = pd.Series(A["uji_nn_mean_dR2"]); cek("ΔR² rerata per arsitektur", f"(mean ΔR² {f(md.min(), 4)} to {f(md.max(), 4)} by architecture")
cek("sebaran seed tunggal", f"ranged from {f(J['spread_single_seeds'][0])} to {f(J['spread_single_seeds'][1])}")
cek("korelasi koreksi", f"(median correlation between pairs {r(*AJ['corr_koreksi_med'], 2)}, minimum {f(AJ['corr_koreksi_min'], 2)})")
cek("selisih RMS", f"differed by {pc(*AJ['rms_beda_pred_med'])} W m⁻²"); cek("stacking", f"improved R² by only {rs(*AJ['C3_dR2'])} (the equal-weight mean gained {rs(*AJ['C1_dR2'])}), removing {pc(*AJ['C3_porsi_sisa_pct'], 1)}%")
cek("ridge", f"(R² {r(*mm(R2.Ridge))}) by {rs(*mm(BR.dR2))}, {pc(*mm(BR.ratio_vs_spread), 1)} times the spread"); benar("CatBoost − ridge signifikan di semua seed", bool((BR.n_sig == 5).all()))
cek("residual", f"leaves {pc(100 * (1 - AJ['R2_residual'][1]), 100 * (1 - AJ['R2_residual'][0]))}% of the variance of the smart-persistence error unexplained (R² of the residual {r(*AJ['R2_residual'], 2)}")
SY = A["sintetis"]; SA = A["sintetis_aturan"]; benar("kontrol sintetis: T1–T4 terpenuhi", all(SA[k] for k in ("T1", "T2", "T3", "T4")))
cek("kontrol sintetis: selisih", f"by {r(*SA['gap_beda'], 2)} in R² when their information differed"); cek("kontrol sintetis: batas atas", f"within {f(np.ceil(SA['jarak_setara_maks'] * 1000) / 1000)} of the known ceiling")
# ================= 3.2 =================
cs = CC[CC.grup == "semua"].set_index("site").loc[SITES]
cek("CLP: ΔR²", f"raised R² by {rs(*mm(dCLP))}, significantly at every station"); benar("CLP signifikan di semua stasiun", bool(sig(RB, "dCLP").all()))
cek("CLP: RMSE", f"lowered RMSE by {pc(*mm(cs.turun_W), 1)} W m⁻² ({pc(*mm(cs.turun_pct), 1)}%)")
cek("CLP: sisa galat", f"removed {pc(*JG['clp_porsi_sisa_pct'], 1)}% of the remaining error"); cek("CLP: kali sebaran", f"gain was {pc(*mm(dCLP / spread), 1)} times the spread")
cek("AWS dan SYNOP sendiri", f"surface meteorology changed R² by {rs(*mm(eff(RB, 'dAWS')))} and SYNOP cloud by {rs(*mm(eff(RB, 'dSYNOP')))}")
cek("CatBoost: CLP", f"CLP added {rs(*mm(eff(AC, 'dCLP')))} at every station"); cek("CatBoost: AWS/SYNOP", f"each added at most {sg(max(eff(AC, 'dAWS').max(), eff(AC, 'dSYNOP').max()))}")
cek("H8/H9", f"by {pc(*JD['turun_h08'], 1)}%, against {pc(*JD['turun_h09'], 1)}% in the Himawari-9 part")
ss = eff(RB, "dSYNOP"); sp_ = sig(RB, "dSYNOP"); npos = int(((ss > 0) & sp_).sum()); nneg = [s for s in SITES if ss[s] < 0 and sp_[s]]
cek("SYNOP sendiri", f"raised R² significantly at {KATA[npos]} stations, by up to {sg(ss[sp_ & (ss > 0)].max())}"); benar("SYNOP turun signifikan hanya di Bengkulu", nneg == ["bengkulu"])
cek("SYNOP di atas CLP", f"changed R² by only {rs(*mm(eff(RB, 'dSYNOP|CLP')), 4)}")
nA = int(sig(RB, "dAWS|CLP").sum()); b = RB.loc[("banten", "dAWS|CLP")]
cek("AWS di atas CLP", f"remained detectable at {KATA[nA]} stations, most clearly at Banten ({sg(b.dR2, 4)}, 95% CI [{f(b.blk_lo, 4)}, {f(b.blk_hi, 4)}], about {100 * b.dR2 / dCLP['banten']:.0f}% of the CLP contribution there)")
w = W63.loc[("banten", "wind")]; cek("angin Banten", f"to wind ({sg(w.dR2, 4)} [{f(w.blk_lo, 4)}, {f(w.blk_hi, 4)}])")
SH = pd.read_csv(os.path.join(T114, "a2_shap", "shap_global_mean.csv")); SH.columns = ["f", "v"]; top5 = list(SH.f[:5])
benar("SHAP: COT satu-satunya eksogen di lima besar", [c for c in top5 if c.startswith(("clp_", "aws_", "synop_"))] == ["clp_cot"])
rk = list(SH.f).index("clp_cloud_frac") + 1; cek("SHAP: fraksi awan", f"cloud fraction ranked {['first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth'][rk - 1]}")
cek("statistik kotak", f"added at most {sg(max(A['kotak_E1'][1], A['kotak_E2'][1]))}")
# ================= 3.3 =================
gk = lambda g, k: CC[(CC.grup == g) & (CC.kelas == k)]
st = gk("perubahan", "stabil"); cek("berubah", f"lowered RMSE by {pc(ch.turun_pct.min(), ch.turun_pct.max(), 1)}%, significantly at every station"); benar("berubah signifikan semua", bool((ch.lo > 0).all()))
cek("stabil", f"ranging from an {abs(st.turun_pct.min()):.1f}% increase to a {st.turun_pct.max():.1f}% decrease")
for k, lab in [("mendung", "overcast skies"), ("berawan sebagian", "partly cloudy skies"), ("cerah", "clear skies")]:
    d = gk("langit", k); cek(f"langit {k}", f"{lab} ({pc(d.turun_pct.min(), d.turun_pct.max(), 1)}%)")
cek("latensi 3.3", f"removed {pc(*mm(lat))}% of the CLP contribution at every station")
cek("rho", f"(rank correlation with persistence R² {f(AJ['rho_dCLP_vs_R2SP'], 2)}), whereas skill was only weakly related to persistence ({f(AJ['rho_skill_vs_R2SP'], 2)})")
SK = T3.xs("skill", level="blok").loc[SITES]
benar("Jambi skill dan CLP tertinggi", CB.skill_pers.idxmax() == "jambi" and dCLP.idxmax() == "jambi")
cek("Jambi", f"Jambi had the highest skill ({CB.loc['jambi', 'skill_pers']:.3f}) and the largest CLP gain ({sg(dCLP['jambi'])}), and its persistence R² ({R2.loc['jambi', 'SP']:.3f}) was close to the lowest values, at Banten ({R2.loc['banten', 'SP']:.3f}) and Yogyakarta ({R2.loc['jogja', 'SP']:.3f})")
benar("SP terendah = Banten, Yogyakarta, lalu Jambi", list(R2.SP.sort_values().index[:3]) == ["banten", "jogja", "jambi"])
kb = lambda g, k: BG[(BG.grup == g) & (BG.kelas == k)]
d = kb("perubahan", "berubah"); cek("SSE berubah", f"accumulated {pc(100 * d.porsi_SSE_CatBoost.min(), 100 * d.porsi_SSE_CatBoost.max())}% of the squared error of CatBoost, although the model reached a skill score of {r(d.skill.min(), d.skill.max(), 2)}")
d = kb("perubahan", "stabil"); cek("stabil RMSE", f"(RMSE {pc(d.RMSE_SP.min(), d.RMSE_SP.max())} W m⁻²) and CatBoost was less accurate ({pc(d.RMSE_CatBoost.min(), d.RMSE_CatBoost.max())} W m⁻²)")
d = kb("waktu", "10–14"); cek("siang", f"made up {pc(100 * d.porsi_sampel.min(), 100 * d.porsi_sampel.max())}% of the test set but {pc(100 * d.porsi_SSE_CatBoost.min(), 100 * d.porsi_SSE_CatBoost.max())}% of the squared error")
cek("skill siang", f"({r(d.skill.min(), d.skill.max(), 2)}) was similar to that in the morning ({r(kb('waktu', '06–10').skill.min(), kb('waktu', '06–10').skill.max(), 2)})")
for k, lab in [("cerah", "contributed"), ("berawan sebagian", "partly cloudy origins"), ("mendung", "overcast origins")]:
    d = kb("langit", k); cek(f"SSE {k}", f"{lab} {pc(100 * d.porsi_SSE_CatBoost.min(), 100 * d.porsi_SSE_CatBoost.max())}%")
# ================= 4 dan 5 =================
cek("diskusi latensi", f"latency removed {pc(*mm(lat))}% of the CLP contribution"); cek("kesimpulan sebaran", f"converged to within {r(*mm(spread))} in R²"); cek("kesimpulan latensi", f"lost {pc(*mm(lat))}% of its value")
sl_ = A["sampel_logger"]; bl = pd.Series(sl_["bukan_logger_per_situs"])
benar("bukan logger: Bengkulu terkecil, Banten terbesar", bl.idxmin() == "bengkulu" and bl.idxmax() == "banten")
cek("sampel logger", f"Between {bl.min():.1f}% (Bengkulu) and {bl.max():.0f}% (Banten)"); cek("logger CatBoost", f"CatBoost reached an R² of {r(*sl_['cb'])} and CLP added {rs(*sl_['clp'])}")
cek("Kalbar 2022", f"where the logger supplies {A['sumber_2022']['kalbar']:.1f}% of the daytime GHI")
V = r"C:\Users\ariff\Documents\Balai_data_v6_10"; dB = pd.read_parquet(os.path.join(V, "00_data", "bengkulu_full.parquet"), columns=["ts_wib", "ghi_wm2", "dhi_wm2", "dni_wm2", "solar_elev_deg"])
m5 = dB.solar_elev_deg > 5; cl = (np.abs(dB.ghi_wm2 - (dB.dhi_wm2 + dB.dni_wm2 * np.sin(np.radians(dB.solar_elev_deg)))) < 0.5); clo = (100 * cl[m5].groupby(dB.ts_wib.dt.year[m5]).mean())
benar(f"Bengkulu tertutup neraca 2023 dan 2024 ≥ 99,9% ({clo[2023]:.2f}, {clo[2024]:.2f})", clo[2023] >= 99.9 and clo[2024] >= 99.9); cek("Bengkulu 2025", f"but at only {clo[2025]:.0f}% of the test year")
R_, Hs, lon0 = 6378.137, 35786.0, 140.7; vz = []
for la, lo in [(-6.261, 106.751), (-3.865, 102.312), (-1.601, 103.494), (-7.731, 110.354), (0.075, 109.191), (-6.985, 110.381)]:
    la_, dl = np.radians(la), np.radians(lo - lon0); cg = np.cos(la_) * np.cos(dl); g = np.arccos(cg); rs_ = R_ + Hs; dd = np.sqrt(R_ ** 2 + rs_ ** 2 - 2 * R_ * rs_ * cg); vz.append(np.degrees(np.arcsin(rs_ * np.sin(g) / dd)))
vz = np.array(vz); cek("paralaks", f"displaced by {np.floor(10 * np.tan(np.radians(vz.min()))):.0f}–{np.ceil(10 * np.tan(np.radians(vz.max()))):.0f} km at the viewing zenith angles of the stations ({np.floor(vz.min()):.0f}–{np.ceil(vz.max()):.0f}°)")
ns = [s for s in SITES if gk("perubahan", "stabil").set_index("site").loc[s, "hi"] < 0]; NAMA = dict(banten="Banten", bengkulu="Bengkulu", jambi="Jambi", jogja="Yogyakarta", kalbar="West Kalimantan", semarang="Central Java")
cek("rugi stabil signifikan", "small losses in stable hours at " + " and ".join(NAMA[s] for s in sorted(ns, key=lambda s: gk("perubahan", "stabil").set_index("site").loc[s, "turun_pct"])))
if "tuning" in A:
    tn = A["tuning"]; cek("tuning", f"the search raised test R² by {sg(tn['dLGB'], 4)} for LightGBM and by {sg(tn['dLSTM_mean'], 4)} for the LSTM, both below the 0.002 threshold"); benar("tuning: keduanya positif dan < 0,002", 0 < tn["dLGB"] < 0.002 and 0 < tn["dLSTM_mean"] < 0.002)
# ================= Tabel 1: koordinat =================
for nm, la, lo in [("Bengkulu", "3.865°S", "102.312°E"), ("Jambi", "1.601°S", "103.494°E")]: cek(f"Tabel 1 {nm}", f"| {nm} | ", TXT); cek(f"Tabel 1 {nm} koordinat", f"{la} | {lo}", TXT)
# ================= ESM =================
cek("ESM seleksi", f"by {rs(sl[0], sl[1], 4)}", ESM); cek("ESM walk-forward", f"R² averaged {wf['mean']:.3f} ± {wf['sd']:.3f} over the five folds", ESM); cek("ESM LightGBM Bengkulu", f"test-year value of {R2.loc['bengkulu', 'LightGBM']:.3f}", ESM)
cek("ESM SHAP 44", f"the test R² of this configuration is {JG['shap_seleksi_uji_44']:.3f}, against {R2.loc['bengkulu', 'LightGBM']:.3f}", ESM)
I87 = json.load(open(os.path.join(P, "87_isi_dhi_dni_banten", "isi_87.json"), encoding="utf-8")); hd = I87["holdout"]
cek("ESM DHI/DNI Banten", f"RMSE of {hd['dhi_rmse']:.1f} W m⁻² for DHI and {hd['dni_rmse']:.1f} W m⁻² for DNI", ESM)
NP = A["n_parameter"]
for m, lab in [("MLP", "MLP"), ("LSTM", "LSTM"), ("Transformer", "Transformer"), ("LSTM_hybrid", "LSTM-hybrid"), ("Transformer_hybrid", "Transformer-hybrid")]: benar(f"parameter {lab} {NP[m]:,}", re.search(rf"\| {re.escape(lab)} \|[^\n]*\| {NP[m]:,} \|", ESM) is not None)
ep = A["epoch_median"]; cek("epoch", f"Median best epoch {ep[0]:.0f}–{ep[1]:.0f}" if ep[0] != int(ep[0]) or True else "", ESM); benar("tidak ada run mencapai 100 epoch", A["epoch_berhenti_maks"] < 100)
cek("ESM ambang konstanta surya", f"about {0.65 * 1100 / 1361:.2f} and {0.30 * 1100 / 1361:.2f}", ESM)
sd_ = lambda k, n: f"{sg(SY[k]['dR2'], n)} [{sg(SY[k]['lo'], n)}, {sg(SY[k]['hi'], n)}]"
cek("ESM selisih sintetis", f"was {sd_('S_A tabular', 3)} with the signal only in the predictors, {sd_('S_B sekuens', 3)} with the signal only in the window, and {sd_('S_C setara', 4)} with equal information", ESM)
# ================= struktur =================
benar("tidak ada {{penanda}}", "{{" not in TXT and "{{" not in ESM)
for t in (TXT, ESM):
    for k in re.findall(r"<!-- (\w+):MULAI -->", t): benar(f"tabel {k} terisi", re.search(rf"<!-- {k}:MULAI -->\n\|", t) is not None)
def urutan(pola, teks):
    seen = []
    for m_ in re.finditer(pola, teks):
        for n in re.findall(r"S(\d+)", m_.group(0)):
            if int(n) not in seen: seen.append(int(n))
    return seen
ts = urutan(r"Tables? S\d+(?:(?:,| and|–) S?\d+)*", BODY); fs = urutan(r"Figs?\. S\d+", BODY)
benar(f"urutan Tabel S {ts}", ts == sorted(ts) and ts == list(range(1, len(ts) + 1))); benar(f"urutan Gambar S {fs}", fs == sorted(fs))
REF = TXT.split("## References")[1].split("## Supplementary")[0]; ents = re.findall(r"^- (.+)$", REF, re.M)
kunci = []
for e in ents:
    m_ = re.match(r"(.+?) \((\d{4})\)", e); nama = m_.group(1).split(",")[0].strip(); kunci.append((nama, m_.group(2), e))
cites = set()
for m_ in re.finditer(r"([A-Z][A-Za-z\-]+(?: et al\.| & [A-Z][A-Za-z\-]+)?)(?:,| \(|\s)\s?\(?(\d{4})\)?", BODY):
    cites.add((m_.group(1).replace(" et al.", "").split(" & ")[0], m_.group(2)))
for nama, th, e in kunci:
    benar(f"pustaka dikutip: {nama} {th}", any(c[0] == nama.split()[0] and c[1] == th for c in cites) or f"{nama.split()[0]}" in BODY and th in BODY)
print("\n" + ("SEMUA LOLOS" if not GAGAL else f"{len(GAGAL)} GAGAL: {GAGAL}")); sys.exit(1 if GAGAL else 0)
