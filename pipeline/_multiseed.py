# -*- coding: utf-8 -*-
"""_multiseed.py — angka & tabel sensitivitas seed model neural untuk builder naskah/SI/ESM/email (sumber: 36_multiseed/, tahap 36–37).

Dipakai oleh 23_build_supplementary (SI Table S8), 24_build_esm (ESM Table S3), 32_build_manuskrip, 34_build_manuskrip_submission,
35_build_cover_email. Semua nilai dihitung dari CSV keluaran 37_multiseed_analysis.py; tidak ada angka tertulis tetap.
"""
import os, math, pandas as pd
B = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(B, "36_multiseed")
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
NN6 = ["MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transformer_hybrid"]
NNB = ["MLP", "LSTM", "Transformer", "LSTM_hybrid", "Transf_hybrid"]
SEQB = ["LSTM", "Transformer", "LSTM_hybrid", "Transf_hybrid"]
TAB = ["LightGBM", "CatBoost", "XGBoost"]
NAME = {"MLP": "MLP", "LSTM": "LSTM", "Transformer": "Transformer", "LSTM_hybrid": "LSTM-hybrid", "Transformer_hybrid": "Transformer-hybrid",
        "Transf_hybrid": "Transformer-hybrid"}
NUMW = ["no", "one", "two", "three", "four", "five", "six"]
def sg(x, k=4):
    v = round(float(x), k); v = 0.0 if v == 0 else v; return f"−{abs(v):.{k}f}" if v < 0 else f"+{v:.{k}f}"
def num(x, k=4):
    v = round(float(x), k); v = 0.0 if v == 0 else v; return f"−{abs(v):.{k}f}" if v < 0 else f"{v:.{k}f}"
def cnum(x):                                                         # batas CI: 5 desimal bila 4 desimal akan membulat ke 0 (tanda tetap terbaca)
    return num(x, 5) if x != 0 and abs(x) < 0.00005 else num(x)
def ci(lo, hi): return f"[{cnum(lo)}, {cnum(hi)}]"
def up3(x): return math.ceil(round(x, 6) * 1000) / 1000           # batas "within" dibulatkan ke atas (seperti builder naskah)
def andjoin(xs): xs = list(xs); return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]

def load():
    S = pd.read_csv(os.path.join(D, "r2_ringkas.csv")); BK = pd.read_csv(os.path.join(D, "bkl_block.csv"))
    SP = pd.read_csv(os.path.join(D, "spread_6situs.csv")).set_index("site").loc[SITES]
    x6 = pd.read_csv(os.path.join(B, "04c_mean_6situs", "baseline_mean_6situs_xgb_mlp.csv")).set_index("site").XGB_R2
    six = S[S.exp == "six"]; bkl = S[S.exp == "bkl"].set_index("model")
    assert (six[six.model.isin(NN6)].n_real == 5).all() and len(six[six.model.isin(NN6)]) == 30, "multi-seed 6 situs belum lengkap"
    assert all(bkl.loc[m, "n_real"] == 5 for m in NNB), "multi-seed Bengkulu belum lengkap"
    assert SP.MLP_R0_reproduced.all(), "R0 MLP 6 situs tidak tereproduksi"
    M = {s: {m: float(six[(six.site == s) & (six.model == m)].R2_mean.iloc[0]) for m in NN6} for s in SITES}
    for s in SITES:
        for m in ["LightGBM", "CatBoost"]: M[s][m] = float(six[(six.site == s) & (six.model == m)].R2_pipe.iloc[0])
        M[s]["XGBoost"] = float(x6[s])
    M = pd.DataFrame(M).T.loc[SITES, TAB + NN6]                      # matriks R² rata-rata-seed (tabular deterministik)
    SD = pd.DataFrame({s: {m: float(six[(six.site == s) & (six.model == m)].R2_sd.iloc[0]) for m in NN6} for s in SITES}).T.loc[SITES, NN6]
    best = M.max(axis=1); spread_sm = M.max(axis=1) - M.min(axis=1); weakest = M.idxmin(axis=1)
    per = BK[BK.real != "ens"]; ens = BK[BK.real == "ens"].set_index("model")
    seq = per[per.model.isin(SEQB)]; mlp = per[per.model == "MLP"]
    seq_mean = seq.groupby("model").dR2.mean()
    ens_seq = ens.loc[SEQB]
    v_b = pd.Series({m: (bkl.loc[m, "R2_mean"] if m in NNB else bkl.loc[m, "R2_pipe"]) for m in TAB + NNB})
    v0 = pd.Series({m: bkl.loc[m, "R2_pipe"] for m in TAB + NNB})
    top4_sm = v_b.sort_values(ascending=False); top4_0 = v0.sort_values(ascending=False)
    R = dict(M=M, SD=SD, SP=SP, BK=BK, bkl=bkl, best=best, spread_sm=spread_sm, weakest=weakest,
             mlp_gap=float((best - M.MLP).max()),
             n_recur_weak=int(weakest.isin(["LSTM", "LSTM_hybrid"]).sum()),
             other_weak={s: w for s, w in weakest.items() if w not in ("LSTM", "LSTM_hybrid")},
             spread_sm_rng=(float(spread_sm.min()), float(spread_sm.max())),
             spread_real_rng=(float(SP.spread_real_min.min()), float(SP.spread_real_max.max())),
             spread_rep_rng=(float(SP.spread_reported.min()), float(SP.spread_reported.max())),
             sd_med=float(SD.stack().median()), sd_max=float(SD.stack().max()), sd_argmax=SD.stack().idxmax(),
             arch_spread_med=float(SP.spread_reported.median()),
             n_seq_sig=int(((seq.sig_block == "yes") & (seq.dR2 < 0)).sum()), n_seq=len(seq),
             seq_rng=(float(seq.dR2.max()), float(seq.dR2.min())), seq_mean_rng=(float(seq_mean.max()), float(seq_mean.min())),
             n_mlp_sig=int((mlp.sig_block == "yes").sum()),
             ens_seq_rng=(float(ens_seq.dR2.max()), float(ens_seq.dR2.min())),
             ens_ns=[m for m in SEQB if ens.loc[m, "sig_block"] == "no"],
             ens_subres=[m for m in SEQB if ens.loc[m, "sig_block"] == "yes" and abs(ens.loc[m, "dR2"]) < 0.002],
             ens=ens, top4_same=set(top4_sm.index[:4]) == set(top4_0.index[:4]),
             top4_sm=float(top4_sm.iloc[0] - top4_sm.iloc[3]), lgb_bkl=float(bkl.loc["LightGBM", "R2_pipe"]))
    return R

def sentence_bkl(R, table, the=lambda m: "the " + NAME[m]):
    """Kalimat §3.4 (Bengkulu standalone)."""
    t = (f"Retraining the five neural architectures with four further seeds ({table}) leaves this picture largely intact: "
         + ("the same four models lead" if R["top4_same"] else "the leading four models change") + f" and lie within {R['top4_sm']:.4f} of one another, "
         f"the MLP differs significantly from LightGBM in {NUMW[R['n_mlp_sig']]} of five runs, and {R['n_seq_sig']} of the {R['n_seq']} sequence-model runs are "
         f"significantly lower (ΔR² across all {R['n_seq']} runs {sg(R['seq_rng'][0])} to {sg(R['seq_rng'][1])}; seed means {sg(R['seq_mean_rng'][0])} to {sg(R['seq_mean_rng'][1])}). "
         f"Averaging the predictions of the five seeds narrows the sequence-model deficit to {sg(R['ens_seq_rng'][0])} to {sg(R['ens_seq_rng'][1])}")
    q = []
    if R["ens_ns"]:
        e = R["ens"]; q.append("it is no longer significant for " + andjoin(f"{the(m)} ({sg(e.loc[m,'dR2'])}, 95% CI {ci(e.loc[m,'blk_lo'], e.loc[m,'blk_hi'])})" for m in R["ens_ns"]))
    if R["ens_subres"]: e = R["ens"]; q.append("it falls below the resolution treated as meaningful for " + andjoin(f"{the(m)} ({sg(e.loc[m,'dR2'])})" for m in R["ens_subres"]))
    t += ("; " + " and ".join(q) if q else "") + (", so part of the single-seed deficit reflects training variance rather than architecture." if (R["ens_ns"] or R["ens_subres"]) else ".")
    return t

def weak_txt(R, lab):
    o = R["other_weak"]; g = {}
    for s, w in o.items(): g.setdefault(w, []).append(lab[s])
    if R["n_recur_weak"] == 0 and len(g) == 1: return f"the {NAME[next(iter(g))]} is the weakest model at all six sites"
    return (f"a recurrent model (the LSTM or the LSTM-hybrid) is the weakest at {NUMW[R['n_recur_weak']]} of the six sites"
            + (f" (the {'; the '.join(f'{NAME[w]} at {andjoin(v)}' for w, v in g.items())})" if o else ""))

def sentence_limit(R, table, ordinal="Seventh"):
    s, m = R["sd_argmax"]
    return (f"{ordinal}, each neural network in the main tables was trained once (seed 42); across four further seeds its test R² varies with a median "
            f"standard deviation of {R['sd_med']:.4f} (at most {R['sd_max']:.4f}), which leaves the convergence of the architectures unchanged but is "
            f"comparable to several of the pairwise differences between them ({table}).")

def table_bkl():
    R = load(); bkl, BK, e = R["bkl"], R["BK"], R["ens"]
    L = ["| Model | R², seed 42 | R², mean ± SD | ΔR² vs LightGBM, seed 42 | ΔR², range over seeds | Significant runs | ΔR², five-seed ensemble [95% CI] |",
         "|---|---:|---:|---:|---:|---:|---|"]
    for m in NNB:
        g = BK[(BK.model == m) & (BK.real != "ens")]; g0 = g[g.real == "pipe"].iloc[0]
        L.append(f"| {NAME[m]} | {bkl.loc[m,'R2_pipe']:.4f} | {bkl.loc[m,'R2_mean']:.4f} ± {bkl.loc[m,'R2_sd']:.4f} | {sg(g0.dR2)} | "
                 f"{sg(g.dR2.min())} to {sg(g.dR2.max())} | {int((g.sig_block == 'yes').sum())} of 5 | {sg(e.loc[m,'dR2'])} {ci(e.loc[m,'blk_lo'], e.loc[m,'blk_hi'])} |")
    return "\n".join(L)

def table_six(lab):
    R = load(); S = pd.read_csv(os.path.join(D, "r2_ringkas.csv")); six = S[S.exp == "six"]; SP = R["SP"]
    H = ["MLP", "LSTM", "Transformer", "LSTM-hyb", "Transf-hyb"]
    L = ["| Site | " + " | ".join(H) + " | Spread, seed 42 | Spread, seed means | Spread, range over seeds |", "|---|" + "---:|" * 8]
    for s in SITES:
        c = []
        for m in NN6:
            r = six[(six.site == s) & (six.model == m)].iloc[0]; c.append(f"{r.R2_mean:.4f} ± {r.R2_sd:.4f}")
        L.append(f"| {lab[s]} | " + " | ".join(c) + f" | {SP.loc[s,'spread_reported']:.4f} | {R['spread_sm'][s]:.4f} | "
                 f"{SP.loc[s,'spread_real_min']:.4f}–{SP.loc[s,'spread_real_max']:.4f} |")
    return "\n".join(L)
