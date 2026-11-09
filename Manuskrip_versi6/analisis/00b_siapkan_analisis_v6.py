# -*- coding: utf-8 -*-
"""Manuskrip V6 — menyalin skrip rangkuman dan analisis V5 ke V6 dengan penggantian teks tercatat (asal_analisis.json).
  protokol/04_daftar_periksa.py  ← Manuskrip_versi5/protokol/04_daftar_periksa.py (jalur relatif; tanpa perubahan logika)
  analisis/v6_01_analisis_tanpa_latih.py ← Manuskrip_versi5/analisis/v4_01_analisis_tanpa_latih.py (assert P2F)
Jalankan sekali: python 00b_siapkan_analisis_v6.py"""
import os, hashlib, json
HERE = os.path.dirname(os.path.abspath(__file__)); V6 = os.path.dirname(HERE); ROOT = os.path.dirname(V6); V5 = os.path.join(ROOT, "Manuskrip_versi5")
LOG = {}
def buat(src, dst, ganti):
    s = open(src, encoding="utf-8").read(); h = hashlib.sha256(s.encode()).hexdigest()
    for a, b in ganti:
        assert s.count(a) == 1, (dst, a); s = s.replace(a, b)
    s = f"# Manuskrip V6: dibuat oleh analisis/00b_siapkan_analisis_v6.py dari {os.path.relpath(src, ROOT)} (sha256 {h[:16]}…); jangan disunting langsung.\n" + s
    compile(s, dst, "exec"); open(dst, "w", encoding="utf-8", newline="").write(s); LOG[os.path.relpath(dst, V6)] = dict(sumber=os.path.relpath(src, ROOT), sha256=h, ganti=ganti)
buat(os.path.join(V5, "protokol", "04_daftar_periksa.py"), os.path.join(V6, "protokol", "04_daftar_periksa.py"), [])
buat(os.path.join(V5, "analisis", "v4_01_analisis_tanpa_latih.py"), os.path.join(HERE, "v6_01_analisis_tanpa_latih.py"),
     [('assert _common.FEATSET == "P2" and _common.CLEARSKY == "IP"', 'assert _common.FEATSET == "P2F" and _common.CLEARSKY == "IP" and len(_common.P2_AKTIF) == 44   # Manuskrip V6')])
json.dump(LOG, open(os.path.join(HERE, "asal_analisis.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False); print("ok", list(LOG))
