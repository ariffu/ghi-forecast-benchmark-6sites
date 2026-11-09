# -*- coding: utf-8 -*-
"""Manuskrip V6 — menyalin skrip pelatihan protokol baku (rerun protokol baku/01_rerun_jaringan_saraf.py, 02_rerun_pohon.py) ke folder ini.
Logika, hiperparameter, seed, dan arsitektur TIDAK diubah. Yang diubah hanya: folder keluaran ke Manuskrip_versi6/protokol/hasil, dan pemeriksaan
lingkungan (V6.10, FEATSET=P2F, 44 prediktor) sebelum pelatihan. Jalankan sekali: python 00_siapkan_skrip.py"""
import os, hashlib, json
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(os.path.dirname(HERE)), "rerun protokol baku")
CEK = '''
import os as _os
_V = r"C:\\Users\\ariff\\Documents\\Balai_data_v6_10"
assert _os.environ.get("FEATSET") == "P2F", "Manuskrip V6: FEATSET harus P2F"
assert _os.path.normcase(_os.environ.get("DATA_DIR", "")) == _os.path.normcase(_os.path.join(_V, "00_data")), "DATA_DIR harus Balai_data_v6_10/00_data"
assert _os.path.normcase(_os.environ.get("CLEARSKY_DIR", "")) == _os.path.normcase(_os.path.join(_V, "clearsky")), "CLEARSKY_DIR harus Balai_data_v6_10/clearsky"
assert _os.path.normcase(_os.environ.get("CLP_EKSTRA_DIR", "")) == _os.path.normcase(_os.path.join(_V, "clp_ekstra")), "CLP_EKSTRA_DIR harus Balai_data_v6_10/clp_ekstra"
'''
LOG = {}
for f, sub in (("01_rerun_jaringan_saraf.py", "nn"), ("02_rerun_pohon.py", "pohon")):
    s = open(os.path.join(SRC, f), encoding="utf-8").read(); asal = hashlib.sha256(s.encode()).hexdigest()
    lama = f'OUT = os.path.join(HERE, "hasil", "{sub}"); os.makedirs(OUT, exist_ok=True)'; assert s.count(lama) == 1, f
    s = s.replace(lama, f'OUT = os.path.join(HERE, "hasil", "{sub}"); os.makedirs(OUT, exist_ok=True)   # Manuskrip V6: HERE = Manuskrip_versi6/protokol')
    s = s.replace("from _common import prepare, split_idx, SITES", CEK.strip() + "\nfrom _common import prepare, split_idx, SITES\nimport _common as _c; assert len(_c.P2_AKTIF) == 44")
    s = s.replace("ROOT = os.path.dirname(HERE)", "ROOT = os.path.dirname(os.path.dirname(HERE))   # Manuskrip V6: dua tingkat di atas protokol/")
    s = '# Manuskrip V6: salinan dari "rerun protokol baku/' + f + '" (sha256 ' + asal[:16] + '…); hanya folder keluaran dan pemeriksaan lingkungan yang ditambah.\n' + s
    open(os.path.join(HERE, f), "w", encoding="utf-8", newline="").write(s); LOG[f] = asal
json.dump(dict(sumber=LOG, data="Balai_data_v6_10", featset="P2F (44)"), open(os.path.join(HERE, "asal_skrip.json"), "w"), indent=1); print("ok", LOG)
