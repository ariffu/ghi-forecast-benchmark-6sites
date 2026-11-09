# -*- coding: utf-8 -*-
"""Tahap 102: salin skrip audit (k1 tahap 101, j1 tahap 100, h1/h2 tahap 101) dengan sasaran Balai_data_v6_5. Logika tidak diubah."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE)
for src, dst, rep in ((os.path.join(B, "101_audit_v6_4", "k1_meteo_v64.py"), "m1_meteo_v65.py", [("Balai_data_v6_4", "Balai_data_v6_5"), ("V6.4", "V6.5")]),
                      (os.path.join(B, "100_meteo_synop", "j1_banding_bulanan.py"), "m2_banding_v65.py", [("Balai_data_v6_3", "Balai_data_v6_5"), ("j1_bulanan.csv", "m2_bulanan_v65.csv"), ("j1_konvensi.csv", "m2_konvensi_v65.csv")]),
                      (os.path.join(B, "101_audit_v6_4", "h1_cek.py"), "m3_h1_cek.py", [("Balai_data_v6_4", "Balai_data_v6_5")]),
                      (os.path.join(B, "101_audit_v6_4", "h2_sensor_macet.py"), "m4_h2_macet.py", [("Balai_data_v6_4", "Balai_data_v6_5")])):
    s = open(src, encoding="utf-8").read()
    for a, b in rep: s = s.replace(a, b)
    open(os.path.join(HERE, dst), "w", encoding="utf-8", newline="").write(s); print(dst)
