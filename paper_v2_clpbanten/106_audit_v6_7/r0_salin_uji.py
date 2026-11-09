# -*- coding: utf-8 -*-
"""Tahap 106: salin seluruh rangkaian uji (tahap 104 untuk V6.6; n3/n4/n5 tahap 103; o1 tahap 104) dengan sasaran Balai_data_v6_7. Logika uji tidak diubah."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE)
SRC = [(os.path.join(B, "104_audit_v6_6", f), f) for f in ("e1_struktur.py", "e2_radiasi.py", "e2b_rinci.py", "e3_satelit.py", "e4_meteo.py", "e4b_rinci.py", "h2_sensor_macet.py", "k1_meteo_v66.py", "o1_khusus_v66.py")]
SRC += [(os.path.join(B, "103_meteo_mulus", f), f) for f in ("n3_audit_v66.py", "n4_banding_v66.py", "n5_h1_cek.py")]
for src, f in SRC:
    s = open(src, encoding="utf-8").read()
    s = s.replace("Balai_data_v6_6", "Balai_data_v6_7").replace("Balai_data_v6_5", "Balai_data_v6_6")   # pembanding = versi sebelumnya (V6.6)
    s = s.replace("Tahap 104 (salinan untuk V6.6)", "Tahap 106 (salinan untuk V6.7)")
    dst = f.replace("v66", "v67").replace("n3_", "r3_").replace("n4_", "r4_").replace("n5_", "r5_").replace("o1_", "r1_")
    open(os.path.join(HERE, dst), "w", encoding="utf-8", newline="").write(s); print(dst)
