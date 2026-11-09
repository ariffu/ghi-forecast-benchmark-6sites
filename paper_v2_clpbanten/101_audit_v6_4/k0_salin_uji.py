# -*- coding: utf-8 -*-
"""Tahap 101: salin rangkaian uji tahap 95/98 ke folder ini dengan sasaran Balai_data_v6_4. Logika uji tidak diubah."""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(HERE), "98_audit_v6_2")
for f in ("e1_struktur.py", "e2_radiasi.py", "e2b_rinci.py", "e3_satelit.py", "e4_meteo.py", "e4b_rinci.py", "h1_v62_cek.py", "h2_sensor_macet.py"):
    s = open(os.path.join(SRC, f), encoding="utf-8").read(); n = s.count("Balai_data_v6_2")
    s = s.replace("Balai_data_v6_2", "Balai_data_v6_4").replace("Tahap 98", "Tahap 101 (salinan uji tahap 98 untuk V6.4)")
    if f == "h1_v62_cek.py":
        s = s.replace("Balai_data_v6_1", "Balai_data_v6_3").replace("V6.1 (Tabel 1)", "V6.3").replace("V6.2 (koordinat pengguna)", "V6.4"); f = "h1_cek.py"
    open(os.path.join(HERE, f), "w", encoding="utf-8", newline="").write(s); print(f, "jalur diganti:", n)
