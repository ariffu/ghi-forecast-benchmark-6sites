# -*- coding: utf-8 -*-
"""Manuskrip V6 — membuat skrip Fig. 1 (peta) dan Fig. 2 (alur kerja) dari skrip naskah v4 (arsip _Arsip_Balai_v5) dengan penggantian tercatat.
  v6_13_gambar_peta.py   : koordinat Bengkulu (pengguna, 2026-11-08: −3,864930; 102,311998) dan Jambi ASRS (pengguna, 2026-11-06: −1,60111; 103,4944).
  v6_08_gambar_alur_kerja.py : himpunan prediktor aktif P2F (44; CLP 9).
Jalankan sekali: python 00c_siapkan_gambar_v6.py"""
import os, hashlib, json
HERE = os.path.dirname(os.path.abspath(__file__)); V6 = os.path.dirname(HERE)
ARS = r"C:\Users\ariff\Documents\_Arsip_Balai_v5\solardata_new_v2\Manusrip_versi4\analisis"; LOG = {}
def buat(src, dst, ganti):
    s = open(src, encoding="utf-8").read(); h = hashlib.sha256(s.encode()).hexdigest()
    for a, b in ganti:
        assert s.count(a) == 1, (dst, a); s = s.replace(a, b)
    s = f"# Manuskrip V6: dibuat oleh analisis/00c_siapkan_gambar_v6.py dari {src} (sha256 {h[:16]}…); jangan disunting langsung.\n" + s
    compile(s, dst, "exec"); open(os.path.join(HERE, dst), "w", encoding="utf-8", newline="").write(s); LOG[dst] = dict(sumber=src, sha256=h, ganti=ganti)
buat(os.path.join(ARS, "13_gambar_peta.py"), "v6_13_gambar_peta.py", [
    ('"Bengkulu": (-3.861, 102.338), "Jambi": (-1.583, 103.667)', '"Bengkulu": (-3.865, 102.312), "Jambi": (-1.601, 103.494)')])
buat(os.path.join(ARS, "08_gambar_alur_kerja.py"), "v6_08_gambar_alur_kerja.py", [
    ('_F = _common.P2 if _common.FEATSET == "P2" else None', '_F = _common.P2_AKTIF if _common.FEATSET == "P2F" else None   # Manuskrip V6: 44 prediktor'),
    ('assert _F is not None, "Fig. 2 v3 menggambarkan himpunan 43 prediktor (FEATSET=P2)"', 'assert _F is not None and len(_F) == 44, "Fig. 2 V6 menggambarkan himpunan 44 prediktor (FEATSET=P2F)"')])
json.dump(LOG, open(os.path.join(HERE, "asal_gambar.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False); print("ok", list(LOG))
