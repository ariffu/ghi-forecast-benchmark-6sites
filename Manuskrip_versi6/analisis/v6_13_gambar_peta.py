# Manuskrip V6: dibuat oleh analisis/00c_siapkan_gambar_v6.py dari C:\Users\ariff\Documents\_Arsip_Balai_v5\solardata_new_v2\Manusrip_versi4\analisis\13_gambar_peta.py (sha256 5bbeba84742fd361…); jangan disunting langsung.
# -*- coding: utf-8 -*-
"""Naskah v4, analisis 13 — Fig. 1 peta enam stasiun, dibuat ulang dengan Python (2026-10-25; pengganti peta QGIS).

Garis pantai: Natural Earth 1:10 m (ne_10m_land, ne_10m_minor_islands; domain publik), dibaca langsung dari berkas .shp lokal
dengan pembaca shapefile minimal (tipe poligon), tanpa pustaka peta. Koordinat stasiun = Tabel 1 naskah.
Perbaikan terhadap peta lama: label Bengkulu tidak lagi menutupi angka 4°S, font sans-serif seperti gambar lain, kata "Station"
tidak diulang, ruang kosong di bawah dipangkas, nama pulau ditambahkan.
Keluaran: ../gambar/Fig1_peta_stasiun.png/.pdf. Jalankan: python -u 13_gambar_peta.py [folder natural_earth_vector]
"""
import os, sys, struct, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Polygon, Rectangle
HERE = os.path.dirname(os.path.abspath(__file__)); V4 = os.path.dirname(HERE); G = os.path.join(V4, "gambar")
NE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "Documents", "natural_earth_vector")
ST = {"Banten": (-6.261, 106.751), "Bengkulu": (-3.865, 102.312), "Jambi": (-1.601, 103.494),
      "Yogyakarta": (-7.731, 110.354), "West Kalimantan": (0.075, 109.191), "Central Java": (-6.985, 110.381)}
# posisi label (bujur, lintang, ha, va): di laut bila memungkinkan, tidak menutupi sumbu
LBL = {"Banten": (106.75, -5.72, "center", "bottom"), "Central Java": (110.38, -6.52, "center", "bottom"),
       "Yogyakarta": (110.35, -8.12, "center", "top"), "Jambi": (104.0, -1.42, "left", "center"),
       "Bengkulu": (101.95, -4.1, "right", "top"), "West Kalimantan": (108.8, 0.3, "right", "center")}
LON, LAT = (100.0, 118.0), (-8.6, 2.6)
LAND, COAST, SEA, INK, INK2 = "#ecebe7", "#4a4945", "#f3f7fa", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "savefig.dpi": 300,
                     "axes.edgecolor": INK2, "xtick.color": INK2, "ytick.color": INK2})

def baca_poligon(path, bbox):
    """bagian-bagian poligon/polyline (tipe 5/3) dari .shp yang kotak batasnya beririsan dengan bbox (bujur min, maks, lintang min, maks)."""
    b = open(path, "rb").read(); off, out = 100, []
    while off < len(b):
        _, clen = struct.unpack_from(">ii", b, off); off += 8; st = struct.unpack_from("<i", b, off)[0]
        if st in (3, 5):
            x0, y0, x1, y1 = struct.unpack_from("<4d", b, off + 4)
            if not (x1 < bbox[0] or x0 > bbox[1] or y1 < bbox[2] or y0 > bbox[3]):
                npart, npt = struct.unpack_from("<ii", b, off + 36)
                parts = list(np.frombuffer(b, "<i4", npart, off + 44)) + [npt]
                pts = np.frombuffer(b, "<f8", 2 * npt, off + 44 + 4 * npart).reshape(-1, 2)
                out += [pts[parts[i]:parts[i + 1]] for i in range(npart)]
        off += clen * 2
    return out

def gambar_daratan(ax, bbox, lw):
    for f in ["ne_10m_land.shp", "ne_10m_minor_islands.shp"]:
        for p in baca_poligon(os.path.join(NE, "10m_physical", f), bbox):
            ax.add_patch(Polygon(p, closed=True, fc=LAND, ec=COAST, lw=lw, zorder=1))

def deg(v, pos, ns):
    a = abs(v); s = f"{a:g}°"
    return s if v == 0 else s + ((("N" if v > 0 else "S")) if ns else ("E" if v > 0 else "W"))

fig, ax = plt.subplots(figsize=(7.0, 4.25))
ax.set_facecolor(SEA); gambar_daratan(ax, (LON[0] - 1, LON[1] + 1, LAT[0] - 1, LAT[1] + 1), 0.4)
ax.set_xlim(*LON); ax.set_ylim(*LAT); ax.set_aspect("equal")
ax.set_xticks(np.arange(100, 119, 4)); ax.set_yticks(np.arange(-8, 3, 2))
ax.set_xticklabels([deg(v, 0, False) for v in ax.get_xticks()]); ax.set_yticklabels([deg(v, 0, True) for v in ax.get_yticks()])
ax.grid(lw=0.3, color="#c9d3db", zorder=0); ax.tick_params(length=2.5)
halo = [pe.withStroke(linewidth=2.2, foreground="white")]
for nm, (la, lo) in ST.items():
    ax.plot(lo, la, "o", ms=5.5, mfc=INK, mec="white", mew=0.8, zorder=5)
    x, y, ha, va = LBL[nm]; ax.text(x, y, nm, ha=ha, va=va, fontsize=7.6, color=INK, zorder=6, path_effects=halo)
for nm, x, y, r in [("Sumatra", 101.2, -0.9, -42), ("Java", 108.4, -7.3, -8), ("Borneo", 113.4, -1.6, 0)]:
    ax.text(x, y, nm, ha="center", va="center", rotation=r, fontsize=8, style="italic", color=INK2, zorder=4, path_effects=halo)
# skala 500 km pada lintang batang skala
ys = -7.95; kmdeg = 111.32 * np.cos(np.radians(abs(ys))); x0 = 100.6; dx = 250 / kmdeg
for i, c in enumerate([INK, "white"]):
    ax.add_patch(Rectangle((x0 + i * dx, ys), dx, 0.13, fc=c, ec=INK, lw=0.6, zorder=6))
for i, t in enumerate(["0", "250", "500 km"]):
    ax.text(x0 + i * dx, ys + 0.22, t, ha="center", va="bottom", fontsize=6.6, color=INK, zorder=6, path_effects=halo)
ax.annotate("", xy=(100.75, 1.75), xytext=(100.75, 0.95), arrowprops=dict(arrowstyle="-|>", lw=1.0, color=INK), zorder=6)
ax.text(100.75, 1.8, "N", ha="center", va="bottom", fontsize=8, fontweight="bold", color=INK, path_effects=halo, zorder=6)
# peta sisipan: posisi area di Indonesia
ia = ax.inset_axes([0.665, 0.655, 0.33, 0.335]); ia.set_facecolor(SEA)
IB = (94.0, 142.0, -11.5, 7.0); gambar_daratan(ia, (IB[0] - 1, IB[1] + 1, IB[2] - 1, IB[3] + 1), 0.25)
ia.set_xlim(IB[0], IB[1]); ia.set_ylim(IB[2], IB[3]); ia.set_aspect("equal"); ia.set_xticks([]); ia.set_yticks([])
ia.add_patch(Rectangle((LON[0], LAT[0]), LON[1] - LON[0], LAT[1] - LAT[0], fill=False, ec="#c62828", lw=1.0, zorder=5))
for s_ in ia.spines.values(): s_.set_edgecolor(INK2); s_.set_linewidth(0.6)
for ext in ["png", "pdf"]: fig.savefig(os.path.join(G, f"Fig1_peta_stasiun.{ext}"), bbox_inches="tight", pad_inches=0.03)
print("ok")
