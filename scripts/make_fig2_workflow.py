# -*- coding: utf-8 -*-
"""Fig. 2 — benchmark workflow (a) and model architectures (b).
Layout follows the priority-corpus convention (Al-Hilfi et al. 2026 Fig. 2 flowchart;
Zang et al. 2024 Fig. 4 stage-wise pipeline; Liu 2021 / Zang 2024 layer-level model schematics).
All architecture details are taken from scripts/04_arch_mean.py and 04b_seq_6situs_mean.py.
Output: Fig2_workflow.{pdf,eps,png}  (174 mm width, Springer double column)."""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch
plt.rcParams.update({"font.family": "sans-serif",
                     "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
                     "font.size": 6.5, "mathtext.default": "regular",
                     "pdf.fonttype": 42, "ps.fonttype": 42})
W, H = 174.0, 200.0                       # mm
fig = plt.figure(figsize=(W / 25.4, H / 25.4))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

INK = "#222222"
FLAT_FC, FLAT_EC = "#DDEAF6", "#2F5F8A"     # flat predictor vector
SEQ_FC, SEQ_EC = "#FBE6CF", "#B0621C"       # sequence window
MOD_FC, MOD_EC = "#F1F1F1", "#4A4A4A"       # model blocks / stages
RES_FC, RES_EC = "#E6F2E7", "#3A7D44"       # residual / probabilistic

def box(x, y, w, h, text="", fc=MOD_FC, ec=MOD_EC, fs=6.5, lw=0.8, ls="-", r=1.2,
        title=None, tfs=6.8, va="center", pad_top=2.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=2))
    if title and text:
        ax.text(x + w / 2, y + h - pad_top, title, ha="center", va="top", fontsize=tfs,
                fontweight="bold", color=INK, zorder=3)
        ax.text(x + w / 2, y + (h - pad_top - 2.6) / 2, text, ha="center", va="center",
                fontsize=fs, color=INK, zorder=3, linespacing=1.25)
    elif title:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=tfs,
                fontweight="bold", color=INK, zorder=3)
    else:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                color=INK, zorder=3, linespacing=1.25)

def arrow(x1, y1, x2, y2, ls="-", c=INK, lw=0.8, cs="arc3,rad=0"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=6,
                                 lw=lw, color=c, ls=ls, connectionstyle=cs, zorder=4,
                                 shrinkA=0, shrinkB=0))

def line(xs, ys, c=INK, lw=0.8, ls="-", z=2.6):
    ax.plot(xs, ys, color=c, lw=lw, ls=ls, zorder=z, solid_capstyle="butt")

def panel(x, y, letter, heading):
    ax.text(x, y, letter, fontsize=9, fontweight="bold", va="top", ha="left", color=INK)
    ax.text(x + 5, y - 0.3, heading, fontsize=7.5, va="top", ha="left", color=INK)

# ============================ (a) workflow ============================
panel(2, H - 2, "a", "Benchmark workflow")
TOP = H - 12
# -- data sources
src = [("ASRS radiation (BMKG)", "pyranometer · pyrheliometer"),
       ("Himawari-8/9 cloud (CLP)", "COT · CTH · CTT · CER"),
       ("AWS surface meteorology", "T · RH · p · wind · rain"),
       ("SYNOP reports", "cloud (okta, types) · met.")]
sx, sw, sh, sg = 3, 38, 8.6, 2.2
for i, (t, s) in enumerate(src):
    y = TOP - (i + 1) * sh - i * sg
    box(sx, y, sw, sh, s, title=t, tfs=6.5, fs=6.2, pad_top=1.6)
src_mid = [TOP - (i + 1) * sh - i * sg + sh / 2 for i in range(4)]
src_bot = TOP - 4 * sh - 3 * sg
# -- harmonisation
hx, hw = 49, 30
hy, hh = src_bot + 6, TOP - src_bot - 12
box(hx, hy, hw, hh, "10-min grid\n6 stations\n2022–2025\nQC + provenance\nflag per slot",
    title="Harmonisation", fs=6.2, pad_top=4)
for ym in src_mid:
    arrow(sx + sw, ym, hx, hy + hh / 2, cs="arc3,rad=0")
# -- predictor tiers
tiers = [("T1 core: radiation, geometry, lags", 55), ("T2 satellite cloud (CLP)", 10),
         ("T3 SYNOP: cloud 4 + met. 10", 14), ("T4 surface meteorology", 21), ("T5 experimental", 4)]
px, pw = 87, 44
th, tg = 5.4, 1.2
for i, (t, n) in enumerate(tiers):
    y = TOP - (i + 1) * th - i * tg
    box(px, y, pw, th, f"{t}  ({n})", fc=FLAT_FC, ec=FLAT_EC, fs=6.0, r=0.8)
tb = TOP - 5 * th - 4 * tg
ax.text(px + pw / 2, tb - 1.6, "104 predictors", ha="center", va="top", fontsize=6.5,
        fontweight="bold", color=FLAT_EC)
ax.text(px + pw / 2, tb - 5.0, "excluded: GHI(t+1 h), smart persistence,\nprovenance flags (anti-leakage)",
        ha="center", va="top", fontsize=5.6, color="#555555", style="italic", linespacing=1.2)
arrow(hx + hw, hy + hh / 2, px, hy + hh / 2)
# -- chronological split
cx, cw = 139, 32
cy = hy + hh / 2 - 5
ax.text(cx + cw / 2, cy + 14, "Chronological split", ha="center", va="bottom",
        fontsize=6.8, fontweight="bold", color=INK)
segs = [("Train\n2022–23", 16, "#E3E3E3"), ("Val.\n2024", 8, "#C9C9C9"), ("Test\n2025", 8, "#9E9E9E")]
xx = cx
for lab, w, c in segs:
    ax.add_patch(Rectangle((xx, cy), w, 10, fc=c, ec=MOD_EC, lw=0.7, zorder=2))
    ax.text(xx + w / 2, cy + 5, lab, ha="center", va="center", fontsize=5.9, color=INK,
            zorder=3, linespacing=1.15)
    xx += w
ax.text(cx + cw / 2, cy - 1.8, "no shuffling; ranking on\ntraining years only", ha="center",
        va="top", fontsize=5.6, color="#555555", style="italic", linespacing=1.2)
arrow(px + pw, hy + hh / 2, cx, hy + hh / 2)

# -- row 2
R2Y, R2H = 112, 24
link_y = R2Y + R2H + 6
line([cx + cw / 2, cx + cw / 2], [cy - 9, link_y], z=1.5)
line([cx + cw / 2, 21], [link_y, link_y], z=1.5)
arrow(21, link_y, 21, R2Y + R2H)
row2 = [(3, 36, "Targets (t + 1 h)",
         "hourly mean (headline)\npoint value (companion)\nbaseline: smart\npersistence $\\hat{y}_{SP}$", MOD_FC, MOD_EC),
        (47, 36, "8 architectures",
         "× 6 sites\nsame features, split\nand protocol\n(panel b)", MOD_FC, MOD_EC),
        (91, 40, "Evaluation (test 2025)",
         "masks A · B · C\nR², MAE, RMSE, skill vs SP\nand CP-optimal reference\nbootstrap ΔR², source ablation", MOD_FC, MOD_EC),
        (139, 32, "Probabilistic layer",
         "quantile / Gaussian\n→ conformal (CQR),\ncalibrated on 2024\nPICP · PINAW · CRPS", RES_FC, RES_EC)]
for i, (x, w, t, s, fc, ec) in enumerate(row2):
    box(x, R2Y, w, R2H, s, title=t, fc=fc, ec=ec, fs=6.1, tfs=6.6)
    if i:
        px_, pw_ = row2[i - 1][0], row2[i - 1][1]
        arrow(px_ + pw_, R2Y + R2H / 2, x, R2Y + R2H / 2)
# models box emphasis
ax.add_patch(FancyBboxPatch((47, R2Y), 36, R2H, boxstyle="round,pad=0,rounding_size=1.2",
                            fc="none", ec=INK, lw=1.4, zorder=3))

# ============================ (b) architectures ============================
BT = 104
panel(2, BT, "b", "Model architectures")
# residual strip
ry = BT - 15
box(3, ry, 168, 8.6, "", fc=RES_FC, ec=RES_EC, r=1.0)
ax.text(87, ry + 5.9, "Residual formulation: $\\Delta = y - \\hat{y}_{SP}$, forecast $\\hat{y} = \\hat{y}_{SP} + \\hat{\\Delta}$ "
        "(all eight models in the Bengkulu benchmark run)", ha="center", va="center", fontsize=6.3, color=INK, zorder=3)
ax.text(87, ry + 2.5, "Six-site replication: LightGBM and the four sequence models use the residual; "
        "CatBoost, XGBoost and the MLP are fitted directly on $y$", ha="center", va="center", fontsize=6.3, color=INK, zorder=3)
cols = [3, 46, 89, 132]; CW = 39
heads = [("Gradient-boosted trees", "LightGBM · CatBoost · XGBoost"),
         ("MLP", "fully connected, non-temporal"),
         ("LSTM (+ hybrid)", "2-layer recurrent"),
         ("Transformer (+ hybrid)", "2-layer encoder")]
hy_ = ry - 3.2
for x, (t, s) in zip(cols, heads):
    ax.text(x + CW / 2, hy_, t, ha="center", va="top", fontsize=6.9, fontweight="bold", color=INK)
    ax.text(x + CW / 2, hy_ - 3.4, s, ha="center", va="top", fontsize=6.0, color="#444444", style="italic")
# thin separators
for x in cols[1:]:
    line([x - 2, x - 2], [2, hy_ - 5], c="#BBBBBB", lw=0.5, ls=(0, (2, 2)), z=1)

IN_Y, IN_H = 66, 7          # input row
OUT_Y = 1.5                   # output row
def out(xc, y=OUT_Y):
    ax.add_patch(Circle((xc, y + 2.6), 2.8, fc=RES_FC, ec=RES_EC, lw=0.8, zorder=3))
    ax.text(xc, y + 2.6, "$\\hat{\\Delta}$", ha="center", va="center", fontsize=7, zorder=4)

def flat_input(x, lab="104 predictors  $x_t$"):
    box(x + 3, IN_Y, CW - 6, IN_H, lab, fc=FLAT_FC, ec=FLAT_EC, fs=6.2, r=0.8)

def seq_input(x):
    gx, gy, cwid, rh = x + 5, IN_Y - 1.5, 2.0, 1.25       # 12 steps × (14 channels shown as 6 rows)
    for i in range(12):
        for j in range(6):
            ax.add_patch(Rectangle((gx + i * cwid, gy + j * rh), cwid, rh, fc=SEQ_FC,
                                   ec=SEQ_EC, lw=0.3, zorder=2))
    ax.text(gx + 12 * cwid + 1.2, gy + 3 * rh, "14 ch.", ha="left", va="center", fontsize=5.6, color=SEQ_EC)
    ax.text(gx + 6 * cwid, gy + 6 * rh + 0.8, "window 12 × 10 min (2 h)", ha="center", va="bottom",
            fontsize=5.8, color=SEQ_EC)
    return gx + 6 * cwid, gy

# ---- trees
x = cols[0]; xc = x + CW / 2
flat_input(x)
arrow(xc, IN_Y, xc, 58)
def tree(tx, ty, s=1.0):
    pts = {"r": (tx, ty), "a": (tx - 3.2 * s, ty - 4.5 * s), "b": (tx + 3.2 * s, ty - 4.5 * s),
           "c": (tx - 4.8 * s, ty - 9 * s), "d": (tx - 1.6 * s, ty - 9 * s),
           "e": (tx + 1.6 * s, ty - 9 * s), "f": (tx + 4.8 * s, ty - 9 * s)}
    for p, q in [("r", "a"), ("r", "b"), ("a", "c"), ("a", "d"), ("b", "e"), ("b", "f")]:
        line([pts[p][0], pts[q][0]], [pts[p][1], pts[q][1]], c=MOD_EC, lw=0.6)
    for k, (px_, py_) in pts.items():
        leaf = k in "cdef"
        ax.add_patch(Circle((px_, py_), 0.9, fc=(RES_FC if leaf else "white"), ec=MOD_EC, lw=0.5, zorder=3))
box(x + 1, 30, CW - 2, 28, "", fc=MOD_FC, ec=MOD_EC)
for k, tx in enumerate([x + 7.0, x + 19.5, x + 32.0]):
    tree(tx, 55.5, 0.9)
ax.text(x + 13.5, 56.0, "+", ha="center", va="center", fontsize=8)
ax.text(x + 25.5, 56.0, "+", ha="center", va="center", fontsize=8)
ax.text(xc, 38.5, "$f_1(x_t) + f_2(x_t) + \\dots + f_M(x_t)$", ha="center", va="center", fontsize=6.2)
ax.text(xc, 33.3, "M ≤ 3000, early stopping on 2024", ha="center", va="center", fontsize=5.8, color="#444444")
arrow(xc, 30, xc, OUT_Y + 5.4)
out(xc)

# ---- MLP
x = cols[1]; xc = x + CW / 2
flat_input(x)
arrow(xc, IN_Y, xc, 58)
box(x + 1, 30, CW - 2, 28, "", fc=MOD_FC, ec=MOD_EC)
layers = [(5, "104"), (6, "256"), (5, "128"), (1, "1")]
lx = [x + 6, x + 15, x + 24, x + 33]
nodes = []
for (n, lab), X in zip(layers, lx):
    ys = [44 + (k - (n - 1) / 2) * 3.0 for k in range(n)]
    nodes.append([(X, y) for y in ys])
    ax.text(X, 33.0, lab, ha="center", va="center", fontsize=5.9)
for A, B in zip(nodes[:-1], nodes[1:]):
    for (x1, y1) in A:
        for (x2, y2) in B:
            line([x1, x2], [y1, y2], c="#9A9A9A", lw=0.25)
for L_ in nodes:
    for (X, Y) in L_:
        ax.add_patch(Circle((X, Y), 0.95, fc="white", ec=MOD_EC, lw=0.5, zorder=3))
ax.text(xc, 55.0, "dense · ReLU · dropout 0.2", ha="center", va="center", fontsize=5.8, color="#444444")
arrow(xc, 30, xc, OUT_Y + 5.4)
out(xc)

# ---- sequence models (shared parts)
def hybrid_and_head(x, top_y, dense_lab):
    xc = x + CW / 2
    # hybrid concat
    ax.add_patch(Circle((xc, 22.5), 2.0, fc="white", ec=INK, lw=0.7, zorder=3))
    ax.text(xc, 22.5, "$\\oplus$", ha="center", va="center", fontsize=8, zorder=4)
    arrow(xc, top_y, xc, 24.5)
    hx0 = x + CW - 4.5
    box(hx0 - 4.5, 19.8, 8.5, 5.4, "104\n$x_t$", fc=FLAT_FC, ec=FLAT_EC, fs=5.4, r=0.6, ls="--")
    arrow(hx0 - 4.5, 22.5, xc + 2.0, 22.5, ls="--")
    ax.text(x + 2.2, 22.5, "hybrid\nonly", ha="left", va="center", fontsize=5.4, color="#555555",
            style="italic", linespacing=1.1)
    box(x + 7, 10.3, CW - 14, 7.2, dense_lab, fs=5.8, r=0.6)
    arrow(xc, 20.5, xc, 17.5)
    arrow(xc, 10.3, xc, OUT_Y + 5.4)
    out(xc)

# ---- LSTM
x = cols[2]; xc = x + CW / 2
wx, wy = seq_input(x)
arrow(xc, wy, xc, 55.5)
box(x + 5, 47.5, CW - 10, 8, "", fc=MOD_FC, ec=MOD_EC)
box(x + 5, 36.5, CW - 10, 8, "", fc=MOD_FC, ec=MOD_EC)
ax.text(xc, 51.5, "LSTM layer 1 (96 units)", ha="center", va="center", fontsize=6.0)
ax.text(xc, 40.5, "LSTM layer 2 (96 units)", ha="center", va="center", fontsize=6.0)
for yy in (51.5, 40.5):
    ax.add_patch(FancyArrowPatch((x + CW - 5, yy + 2), (x + CW - 5, yy - 2), arrowstyle="-|>",
                                 mutation_scale=5, lw=0.6, color=INK, zorder=4,
                                 connectionstyle="arc3,rad=-1.6"))
ax.text(x + CW - 1.2, 46.0, "$h_{t-1}$", ha="center", va="center", fontsize=5.4, color="#444444")
arrow(xc, 47.5, xc, 44.5)
ax.text(xc, 31.8, "last hidden state $h_t$", ha="center", va="center", fontsize=5.9)
arrow(xc, 36.5, xc, 33.4)
hybrid_and_head(x, 30.2, "dense 64 → 1\n(hybrid: 128 → 1)")

# ---- Transformer
x = cols[3]; xc = x + CW / 2
wx, wy = seq_input(x)
arrow(xc, wy, xc, 58.6)
box(x + 4, 53.2, CW - 8, 5.4, "linear 14 → 64 + positional enc.", fs=5.8, r=0.6)
arrow(xc, 53.2, xc, 50.6)
# encoder block
ex, ew, ey, eh = x + 3, CW - 6, 33.5, 17.1
ax.add_patch(FancyBboxPatch((ex, ey), ew, eh, boxstyle="round,pad=0,rounding_size=1.2",
                            fc=MOD_FC, ec=MOD_EC, lw=0.8, zorder=2))
sub = [("multi-head attention (4 heads)", 46.3), ("add & norm", 43.0),
       ("feed-forward (128)", 39.7), ("add & norm", 36.4)]
for lab, yy in sub:
    ax.add_patch(Rectangle((ex + 2, yy - 1.4), ew - 7.5, 2.9, fc="white", ec="#8A8A8A",
                           lw=0.45, zorder=3))
    ax.text(ex + 2 + (ew - 7.5) / 2, yy + 0.05, lab, ha="center", va="center", fontsize=5.3, zorder=4)
ax.text(ex + ew - 2.6, ey + eh / 2, "×2", ha="center", va="center", fontsize=6.8, fontweight="bold")
ax.text(xc, 30.9, "last token", ha="center", va="center", fontsize=5.9)
arrow(xc, ey, xc, 32.3)
hybrid_and_head(x, 29.5, "dense 64 → 1\n(hybrid: 128 → 1)")

# legend (inputs)
lg_y = BT - 3.6
for lx0, fc, ec, lab in [(82, FLAT_FC, FLAT_EC, "flat predictor vector (104)"),
                         (126, SEQ_FC, SEQ_EC, "raw sequence window (12 × 14)")]:
    ax.add_patch(Rectangle((lx0, lg_y), 4, 2.4, fc=fc, ec=ec, lw=0.6))
    ax.text(lx0 + 5.5, lg_y + 1.2, lab, ha="left", va="center", fontsize=5.9)

out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
for ext in ("pdf", "eps", "png"):
    fig.savefig(os.path.join(out_dir, f"Fig2_workflow.{ext}"), dpi=600 if ext == "png" else None)
print("saved")
