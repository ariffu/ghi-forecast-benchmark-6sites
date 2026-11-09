# -*- coding: utf-8 -*-
"""Tahap 98: salin skrip uji tahap 95 (e1, e2, e2b, e3, e4, e4b) ke folder ini dengan sasaran Balai_data_v6_2. Logika uji tidak diubah."""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(HERE), "95_audit_v6_1")
for f in ("e1_struktur.py", "e2_radiasi.py", "e2b_rinci.py", "e3_satelit.py", "e4_meteo.py", "e4b_rinci.py"):
    s = open(os.path.join(SRC, f), encoding="utf-8").read()
    n = s.count("Balai_data_v6_1"); s = s.replace("Balai_data_v6_1", "Balai_data_v6_2").replace("Tahap 95", "Tahap 98 (salinan uji tahap 95 untuk V6.2)")
    if f == "e1_struktur.py":   # V6.2: koordinat Bengkulu pengguna dipakai di clear-sky; bandingkan juga dengan Tabel 1
        s = s.replace('bengkulu=(-3.8607, 102.3381, 9)', 'bengkulu=(-3.864930, 102.311998, 9)')
    open(os.path.join(HERE, f), "w", encoding="utf-8", newline="").write(s); print(f, "jalur diganti:", n)
