# -*- coding: utf-8 -*-
"""Tahap 112: salin seluruh rangkaian uji tahap 110 (untuk V6.9) dengan sasaran Balai_data_v6_10; pembanding = V6.9. Logika uji tidak diubah."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(HERE), "110_audit_v6_9")
for f in ("e1_struktur.py", "e2_radiasi.py", "e2b_rinci.py", "e3_satelit.py", "e4_meteo.py", "e4b_rinci.py", "h2_sensor_macet.py", "k1_meteo_v69.py", "r1_khusus_v69.py", "r3_audit_v69.py",
          "r4_banding_v69.py", "r5_h1_cek.py", "p1_diurnal.py", "u1_hujan_fisis.py", "w1_synop_awan_jogja.py"):
    s = open(os.path.join(SRC, f), encoding="utf-8").read()
    s = s.replace("Balai_data_v6_9", "Balai_data_v6_10").replace("Balai_data_v6_8", "Balai_data_v6_9").replace("Tahap 110 (salinan untuk V6.9)", "Tahap 112 (salinan untuk V6.10)")
    open(os.path.join(HERE, f.replace("v69", "v610")), "w", encoding="utf-8", newline="").write(s)
print("ok")
