# Manuskrip V6: dibuat oleh analisis/00c_siapkan_gambar_v6.py dari C:\Users\ariff\Documents\_Arsip_Balai_v5\solardata_new_v2\Manusrip_versi4\analisis\08_gambar_alur_kerja.py (sha256 6b1ad78e1769a23b…); jangan disunting langsung.
# -*- coding: utf-8 -*-
"""Naskah v4, analisis 08 — Fig. 2 alur kerja dan arsitektur model (2026-10-23).

Salinan paper_v2_clpbanten/make_fig2_workflow.py (gambar alur v3), dipertahankan atas keputusan penulis 2026-10-23:
panel (b) dengan keluarga model tetap. Satu-satunya perubahan mengikuti alur v4 dan dibuat lebih ringkas: isi kotak
"Evaluation" di panel (a) menjadi "skill, source ablation, / where and why" (v3: "skill vs reference / forecasts /
source ablation"). Skrip asli dan Fig2_workflow.* v3 tidak disentuh.
Keluaran: ../gambar/Fig2_alur_kerja.{pdf,png} (lebar 174 mm). Jalankan: FEATSET=P2 python -u 08_gambar_alur_kerja.py
"""
import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(_HERE)), "paper_v2_clpbanten"))
import _common                                             # himpunan prediktor aktif (FEATSET; v3 = 43)
_F = _common.P2_AKTIF if _common.FEATSET == "P2F" else None   # Manuskrip V6: 44 prediktor
assert _F is not None and len(_F) == 44, "Fig. 2 V6 menggambarkan himpunan 44 prediktor (FEATSET=P2F)"
NG = {"CLP": sum(f.startswith("clp_") for f in _F), "SYN": sum(f.startswith("synop_") for f in _F),
      "AWS": sum(f.startswith("aws_") for f in _F)}; NG["core"] = len(_F) - sum(NG.values()); NF = len(_F)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch
plt.rcParams.update({"font.family": "sans-serif",
                     "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
                     "font.size": 6.5, "mathtext.default": "regular",
                     "pdf.fonttype": 42, "ps.fonttype": 42})
BT = 84.0                                  # puncak panel (b)
W, H = 174.0, BT + 40.0                    # mm
fig = plt.figure(figsize=(W / 25.4, H / 25.4))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

INK = "#222222"
FLAT_FC, FLAT_EC = "#DDEAF6", "#2F5F8A"     # flat predictor vector
SEQ_FC, SEQ_EC = "#FBE6CF", "#B0621C"       # sequence window
MOD_FC, MOD_EC = "#F1F1F1", "#4A4A4A"       # model blocks / stages
OUT_FC, OUT_EC = "#E6F2E7", "#3A7D44"       # output

def box(x, y, w, h, text="", fc=MOD_FC, ec=MOD_EC, fs=6.5, lw=0.8, ls="-", r=1.2, title=None, tfs=6.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=2))
    if title and text:
        ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center", fontsize=tfs, fontweight="bold", color=INK, zorder=3)
        ax.text(x + w / 2, y + h * 0.30, text, ha="center", va="center", fontsize=fs, color=INK, zorder=3, linespacing=1.25)
    else:
        ax.text(x + w / 2, y + h / 2, title or text, ha="center", va="center", fontsize=tfs if title else fs,
                fontweight="bold" if title else "normal", color=INK, zorder=3, linespacing=1.25)

def arrow(x1, y1, x2, y2, ls="-", c=INK, lw=0.8):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=6,
                                 lw=lw, color=c, ls=ls, zorder=4, shrinkA=0, shrinkB=0))

def line(xs, ys, c=INK, lw=0.8, ls="-", z=2.6):
    ax.plot(xs, ys, color=c, lw=lw, ls=ls, zorder=z, solid_capstyle="butt")

def panel(x, y, letter, heading):
    ax.text(x, y, letter, fontsize=9, fontweight="bold", va="top", ha="left", color=INK)
    ax.text(x + 5, y - 0.3, heading, fontsize=7.5, va="top", ha="left", color=INK)

# ============================ (a) workflow ============================
panel(2, H - 2, "a", "Workflow")
TOP = H - 10
bh, bg = 5.4, 1.4                                      # tinggi kotak & jarak dalam tumpukan
stack_h = 4 * bh + 3 * bg
mid = TOP - stack_h / 2
# -- sumber data
srcs = ["Radiation (pyranometer)", "Himawari-8/9 cloud (CLP)", "Surface meteorology (AWS)", "SYNOP reports"]
sx, sw = 3, 38
ax.text(sx + sw / 2, TOP + 1.2, "Data sources", ha="center", va="bottom", fontsize=6.8, fontweight="bold", color=INK)
for i, t in enumerate(srcs):
    box(sx, TOP - (i + 1) * bh - i * bg, sw, bh, t, fs=6.2, r=0.8)
# -- kelompok prediktor
tiers = [("Core", NG["core"]), ("Satellite cloud (CLP)", NG["CLP"]), ("SYNOP", NG["SYN"]), ("Surface meteorology (AWS)", NG["AWS"])]
px, pw = 52, 38
ax.text(px + pw / 2, TOP + 1.2, f"{NF} predictors", ha="center", va="bottom", fontsize=6.8, fontweight="bold", color=FLAT_EC)
for i, (t, n) in enumerate(tiers):
    box(px, TOP - (i + 1) * bh - i * bg, pw, bh, f"{t} ({n})", fc=FLAT_FC, ec=FLAT_EC, fs=6.2, r=0.8)
arrow(sx + sw, mid, px, mid)
# -- model & evaluasi
mx, mw = 101, 30
box(mx, mid - 9, mw, 18, f"× 6 stations\n(panel b)", title="8 architectures", fs=6.2)
ax.add_patch(FancyBboxPatch((mx, mid - 9), mw, 18, boxstyle="round,pad=0,rounding_size=1.2", fc="none", ec=INK, lw=1.4, zorder=3))
arrow(px + pw, mid, mx, mid)
ex, ew = 141, 30
box(ex, mid - 9, ew, 18, "skill, source ablation,\nwhere and why", title="Evaluation", fs=6.2)
arrow(mx + mw, mid, ex, mid)

# ============================ (b) architectures ============================
panel(2, BT, "b", "Model architectures")
cols = [3, 46, 89, 132]; CW = 39
heads = [("Gradient-boosted trees", "LightGBM · CatBoost · XGBoost"),
         ("MLP", "fully connected"),
         ("LSTM (+ hybrid)", "recurrent"),
         ("Transformer (+ hybrid)", "self-attention encoder")]
hy_ = BT - 7
for x, (t, s) in zip(cols, heads):
    ax.text(x + CW / 2, hy_, t, ha="center", va="top", fontsize=6.9, fontweight="bold", color=INK)
    ax.text(x + CW / 2, hy_ - 3.4, s, ha="center", va="top", fontsize=6.0, color="#444444", style="italic")
for x in cols[1:]:
    line([x - 2, x - 2], [2, hy_ - 1], c="#BBBBBB", lw=0.5, ls=(0, (2, 2)), z=1)

IN_Y, IN_H = 63, 6.5
OUT_Y = 1.5
def out(xc, y=OUT_Y):
    ax.add_patch(Circle((xc, y + 2.6), 2.8, fc=OUT_FC, ec=OUT_EC, lw=0.8, zorder=3))
    ax.text(xc, y + 2.6, "$\\hat{y}$", ha="center", va="center", fontsize=7, zorder=4)

def flat_input(x, lab=f"{NF} predictors  $x_t$"):
    box(x + 3, IN_Y, CW - 6, IN_H, lab, fc=FLAT_FC, ec=FLAT_EC, fs=6.2, r=0.8)

def seq_input(x):
    gx, gy, cwid, rh = x + 7.5, IN_Y - 1.0, 2.0, 1.25
    for i in range(12):
        for j in range(6):
            ax.add_patch(Rectangle((gx + i * cwid, gy + j * rh), cwid, rh, fc=SEQ_FC, ec=SEQ_EC, lw=0.3, zorder=2))
    return gx + 6 * cwid, gy

# ---- trees
x = cols[0]; xc = x + CW / 2
flat_input(x)
arrow(xc, IN_Y, xc, 56)
def tree(tx, ty, s=1.0):
    pts = {"r": (tx, ty), "a": (tx - 3.2 * s, ty - 4.5 * s), "b": (tx + 3.2 * s, ty - 4.5 * s),
           "c": (tx - 4.8 * s, ty - 9 * s), "d": (tx - 1.6 * s, ty - 9 * s),
           "e": (tx + 1.6 * s, ty - 9 * s), "f": (tx + 4.8 * s, ty - 9 * s)}
    for p, q in [("r", "a"), ("r", "b"), ("a", "c"), ("a", "d"), ("b", "e"), ("b", "f")]:
        line([pts[p][0], pts[q][0]], [pts[p][1], pts[q][1]], c=MOD_EC, lw=0.6)
    for k, (px_, py_) in pts.items():
        ax.add_patch(Circle((px_, py_), 0.9, fc=(OUT_FC if k in "cdef" else "white"), ec=MOD_EC, lw=0.5, zorder=3))
box(x + 1, 32, CW - 2, 24, "", fc=MOD_FC, ec=MOD_EC)
for tx in [x + 7.0, x + 19.5, x + 32.0]:
    tree(tx, 52.5, 0.9)
ax.text(x + 13.5, 53.0, "+", ha="center", va="center", fontsize=8)
ax.text(x + 25.5, 53.0, "+", ha="center", va="center", fontsize=8)
ax.text(xc, 37.5, "$f_1(x_t) + f_2(x_t) + \\dots + f_M(x_t)$", ha="center", va="center", fontsize=6.2)
arrow(xc, 32, xc, OUT_Y + 5.4)
out(xc)

# ---- MLP
x = cols[1]; xc = x + CW / 2
flat_input(x)
arrow(xc, IN_Y, xc, 56)
box(x + 1, 32, CW - 2, 24, "", fc=MOD_FC, ec=MOD_EC)
lx = [x + 7, x + 15.5, x + 24, x + 32]
nodes = []
for n, X in zip([5, 6, 5, 1], lx):
    nodes.append([(X, 44 + (k - (n - 1) / 2) * 3.0) for k in range(n)])
for A, B in zip(nodes[:-1], nodes[1:]):
    for (x1, y1) in A:
        for (x2, y2) in B:
            line([x1, x2], [y1, y2], c="#9A9A9A", lw=0.25)
for L_ in nodes:
    for (X, Y) in L_:
        ax.add_patch(Circle((X, Y), 0.95, fc="white", ec=MOD_EC, lw=0.5, zorder=3))
arrow(xc, 32, xc, OUT_Y + 5.4)
out(xc)

# ---- sequence models (shared parts)
def hybrid_and_head(x, top_y):
    xc = x + CW / 2
    ax.add_patch(Circle((xc, 20.5), 2.0, fc="white", ec=INK, lw=0.7, zorder=3))
    ax.text(xc, 20.5, "$\\oplus$", ha="center", va="center", fontsize=8, zorder=4)
    arrow(xc, top_y, xc, 22.5)
    hx0 = x + CW - 4.5
    box(hx0 - 4.5, 17.8, 8.5, 5.4, f"{NF}\n$x_t$", fc=FLAT_FC, ec=FLAT_EC, fs=5.4, r=0.6, ls="--")
    arrow(hx0 - 4.5, 20.5, xc + 2.0, 20.5, ls="--")
    ax.text(x + 2.2, 20.5, "hybrid\nonly", ha="left", va="center", fontsize=5.4, color="#555555", style="italic", linespacing=1.1)
    box(x + 9, 10.0, CW - 18, 5.4, "dense", fs=5.9, r=0.6)
    arrow(xc, 18.5, xc, 15.4)
    arrow(xc, 10.0, xc, OUT_Y + 5.4)
    out(xc)

# ---- LSTM
x = cols[2]; xc = x + CW / 2
wx, wy = seq_input(x)
arrow(xc, wy, xc, 53.5)
for y0, lab in [(46.5, "LSTM layer"), (36.5, "LSTM layer")]:
    box(x + 7, y0, CW - 14, 7, lab, fs=6.0)
    ax.add_patch(FancyArrowPatch((x + CW - 7, y0 + 5.5), (x + CW - 7, y0 + 1.5), arrowstyle="-|>", mutation_scale=5,
                                 lw=0.6, color=INK, zorder=4, connectionstyle="arc3,rad=-1.6"))
arrow(xc, 46.5, xc, 43.5)
arrow(xc, 36.5, xc, 31.8)
ax.text(xc, 29.8, "last hidden state", ha="center", va="center", fontsize=5.9)
hybrid_and_head(x, 28.2)

# ---- Transformer
x = cols[3]; xc = x + CW / 2
wx, wy = seq_input(x)
arrow(xc, wy, xc, 56.5)
box(x + 6, 51.5, CW - 12, 5.0, "input embedding", fs=5.9, r=0.6)
arrow(xc, 51.5, xc, 48.6)
ex_, ew_, ey_, eh_ = x + 5, CW - 10, 34.0, 14.6
ax.add_patch(FancyBboxPatch((ex_, ey_), ew_, eh_, boxstyle="round,pad=0,rounding_size=1.2", fc=MOD_FC, ec=MOD_EC, lw=0.8, zorder=2))
for lab, yy in [("multi-head attention", 44.3), ("feed-forward", 38.3)]:
    ax.add_patch(Rectangle((ex_ + 2, yy - 1.9), ew_ - 4, 3.8, fc="white", ec="#8A8A8A", lw=0.45, zorder=3))
    ax.text(ex_ + ew_ / 2, yy, lab, ha="center", va="center", fontsize=5.6, zorder=4)
arrow(xc, ey_, xc, 31.8)
ax.text(xc, 29.8, "last token", ha="center", va="center", fontsize=5.9)
hybrid_and_head(x, 28.2)

# legend (inputs)
lg_y = BT - 3.6
for lx0, fc, ec, lab in [(82, FLAT_FC, FLAT_EC, f"flat predictor vector ({NF})"),
                         (126, SEQ_FC, SEQ_EC, "2-h sequence window")]:
    ax.add_patch(Rectangle((lx0, lg_y), 4, 2.4, fc=fc, ec=ec, lw=0.6))
    ax.text(lx0 + 5.5, lg_y + 1.2, lab, ha="left", va="center", fontsize=5.9)

out_dir = os.path.join(os.path.dirname(_HERE), "gambar")
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(out_dir, f"Fig2_alur_kerja.{ext}"), dpi=600 if ext == "png" else None)
print("saved")
