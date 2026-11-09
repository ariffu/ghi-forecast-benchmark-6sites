# -*- coding: utf-8 -*-
"""Tahap 108: salin seluruh rangkaian uji tahap 106 (untuk V6.7) dengan sasaran Balai_data_v6_8; pembanding = V6.7. Logika uji tidak diubah."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(HERE), "106_audit_v6_7")
for f in ("e1_struktur.py", "e2_radiasi.py", "e2b_rinci.py", "e3_satelit.py", "e4_meteo.py", "e4b_rinci.py", "h2_sensor_macet.py", "k1_meteo_v67.py", "r1_khusus_v67.py", "r3_audit_v67.py", "r4_banding_v67.py", "r5_h1_cek.py", "p1_diurnal.py"):
    s = open(os.path.join(SRC, f), encoding="utf-8").read()
    s = s.replace("Balai_data_v6_7", "Balai_data_v6_8").replace("Balai_data_v6_6", "Balai_data_v6_7").replace("Tahap 106 (salinan untuk V6.7)", "Tahap 108 (salinan untuk V6.8)")
    open(os.path.join(HERE, f.replace("v67", "v68")), "w", encoding="utf-8", newline="").write(s); print(f.replace("v67", "v68"))
