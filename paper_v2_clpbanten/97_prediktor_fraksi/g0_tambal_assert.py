# -*- coding: utf-8 -*-
"""Tahap 97: pemeriksaan FEATSET == "P2" di skrip analisis diganti FEATSET in ("P2", "P2F"). Builder V3 (49, 52) tidak disentuh. Cadangan .bak97."""
import os, re, shutil
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = ["60_skill_linear.py", "61_tuning_bengkulu.py", "62_scatter_6situs.py", "63_aws_subkelompok.py", "69_timeseries_contoh.py", "70_ablation_catboost.py",
     "77_seri_logger.py", "80c_protokol_baku.py", "make_fig2_workflow.py", os.path.join("93_versi6", "c4_pratinjau.py"), os.path.join("92_aws_kausal", "b2_latih.py")]
for f in F:
    p = os.path.join(B, f); s = open(p, encoding="utf-8").read(); o = s
    s = s.replace('_common.FEATSET == "P2"', '_common.FEATSET in ("P2", "P2F")')
    s = s.replace("assert len(feats) == 43", "assert len(feats) == len(_common.P2_AKTIF)")
    s = s.replace('_F = _common.P2 if _common.FEATSET in ("P2", "P2F") else None', '_F = _common.P2_AKTIF')
    n = sum(a != b for a, b in zip(o.splitlines(), s.splitlines()))
    if s != o:
        shutil.copyfile(p, p + ".bak97"); open(p, "w", encoding="utf-8", newline="").write(s)
    print(f, "baris diubah:", n)
