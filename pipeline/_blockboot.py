# -*- coding: utf-8 -*-
"""_blockboot.py — uji ΔR² berpasangan dengan BLOCK BOOTSTRAP HARIAN (tahap 27+).

Galat ramalan 10-menit berkorelasi serial dalam satu hari; bootstrap per-record (dipakai pipeline asli)
menghasilkan CI terlalu sempit. Di sini yang diresampel adalah HARI (tanggal WIB origin) dengan pengembalian;
R² tiap resampel dihitung eksak dari statistik cukup harian (n, Σy, Σy², SSE_a, SSE_b).
ΔR² = R²(a) − R²(b). Juga mengembalikan CI per-record (metode lama) untuk pembanding.
"""
import numpy as np

def r2(y, p):
    y = np.asarray(y, float); p = np.asarray(p, float)
    return 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()

def delta_r2(y, pa, pb, day, nb=2000, seed=11, record=True):
    y, pa, pb = (np.asarray(v, float) for v in (y, pa, pb))
    days, inv = np.unique(np.asarray(day), return_inverse=True); D = len(days)
    n_d = np.bincount(inv, minlength=D).astype(float)
    sy, syy = np.bincount(inv, y, D), np.bincount(inv, y * y, D)
    ea, eb = np.bincount(inv, (y - pa) ** 2, D), np.bincount(inv, (y - pb) ** 2, D)
    rng = np.random.default_rng(seed)
    C = np.empty((nb, D))
    for i in range(nb): C[i] = np.bincount(rng.integers(0, D, D), minlength=D)
    N, SY, SYY = C @ n_d, C @ sy, C @ syy
    d_block = (C @ eb - C @ ea) / (SYY - SY ** 2 / N)
    out = dict(dR2=r2(y, pa) - r2(y, pb), n=len(y), n_days=D,
               blk_lo=float(np.percentile(d_block, 2.5)), blk_hi=float(np.percentile(d_block, 97.5)))
    if record:                                            # metode lama (per-record), utk pembanding
        n = len(y); rr = np.random.default_rng(seed); dr = np.empty(nb)
        for i in range(nb):
            ii = rr.integers(0, n, n); yy = y[ii]; v = ((yy - yy.mean()) ** 2).sum()
            dr[i] = (((yy - pb[ii]) ** 2).sum() - ((yy - pa[ii]) ** 2).sum()) / v
        out.update(rec_lo=float(np.percentile(dr, 2.5)), rec_hi=float(np.percentile(dr, 97.5)))
    out["sig_block"] = "yes" if (out["blk_lo"] > 0 or out["blk_hi"] < 0) else "no"
    if record: out["sig_record"] = "yes" if (out["rec_lo"] > 0 or out["rec_hi"] < 0) else "no"
    return out
