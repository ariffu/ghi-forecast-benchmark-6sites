# -*- coding: utf-8 -*-
"""Tahap 104: salin rangkaian uji (e1–e4b, h2 dari tahap 101; k1 dari tahap 101) dengan sasaran Balai_data_v6_6. Logika uji tidak diubah.
h1 (fraksi awan, kebocoran, kelengkapan) sudah dijalankan untuk V6.6 di tahap 103 (n5_h1_cek.py)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(HERE), "101_audit_v6_4")
for f in ("e1_struktur.py", "e2_radiasi.py", "e2b_rinci.py", "e3_satelit.py", "e4_meteo.py", "e4b_rinci.py", "h2_sensor_macet.py", "k1_meteo_v64.py"):
    s = open(os.path.join(SRC, f), encoding="utf-8").read(); n = s.count("Balai_data_v6_4")
    s = s.replace("Balai_data_v6_4", "Balai_data_v6_6").replace("Tahap 101", "Tahap 104 (salinan untuk V6.6)")
    if f == "k1_meteo_v64.py": s = s.replace("Balai_data_v6_3", "Balai_data_v6_5").replace("V6.3", "V6.5").replace("V6.4", "V6.6"); f = "k1_meteo_v66.py"
    open(os.path.join(HERE, f), "w", encoding="utf-8", newline="").write(s); print(f, n)
