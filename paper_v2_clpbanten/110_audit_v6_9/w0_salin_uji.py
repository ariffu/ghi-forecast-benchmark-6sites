# -*- coding: utf-8 -*-
"""Tahap 110: salin seluruh rangkaian uji tahap 108 (untuk V6.8) dengan sasaran Balai_data_v6_9; pembanding = V6.8. Logika uji tidak diubah."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(HERE), "108_audit_v6_8")
for f in ("e1_struktur.py", "e2_radiasi.py", "e2b_rinci.py", "e3_satelit.py", "e4_meteo.py", "e4b_rinci.py", "h2_sensor_macet.py", "k1_meteo_v68.py", "r1_khusus_v68.py", "r3_audit_v68.py",
          "r4_banding_v68.py", "r5_h1_cek.py", "p1_diurnal.py", "u1_hujan_fisis.py"):
    s = open(os.path.join(SRC, f), encoding="utf-8").read()
    s = s.replace("Balai_data_v6_8", "Balai_data_v6_9").replace("Balai_data_v6_7", "Balai_data_v6_8").replace("Tahap 108 (salinan untuk V6.8)", "Tahap 110 (salinan untuk V6.9)")
    open(os.path.join(HERE, f.replace("v68", "v69")), "w", encoding="utf-8", newline="").write(s)
print("ok")
