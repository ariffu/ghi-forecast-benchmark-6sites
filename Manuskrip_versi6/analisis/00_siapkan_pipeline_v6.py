# -*- coding: utf-8 -*-
"""Manuskrip V6 — membuat 01_pipeline_v6.py dari Manuskrip_versi5/analisis/01_pipeline_v5.py dengan penggantian teks yang tercatat.
Logika analisis, hiperparameter, dan seed TIDAK diubah. Yang diganti:
 (1) assert FEATSET P2 -> P2F (44 prediktor);
 (2) data: folder kerja SCR_V5 -> Balai_data_v6_10 (00_data, 00_data_rawfill), beku hanya-baca;
 (3) tahap 18b: pemuat tahap 18b ditambah clp_cloud_frac (add_clp_ekstra), karena P2F menambah prediktor itu;
 (4) tahap 28 (statistik kotak, keputusan pengguna 2026-11-08 "bangun ulang dari chips"): data kotak dari Balai_kotak_v6_10 (tahap 113,
     kotak dan waktu = clp_cot V6.10, diverifikasi dengan chips_supplement_6.zip), menggantikan 28_clp_spatial/data (ekstraksi lama).
     SPAT V6 = 6 fitur: clps_cloud_frac dikeluarkan karena sama dengan prediktor ke-44 clp_cloud_frac (sudah di T1+CLP dan FULL).
Jalankan sekali: python 00_siapkan_pipeline_v6.py"""
import os, hashlib, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "Manuskrip_versi5", "analisis", "01_pipeline_v5.py"); s = open(SRC, encoding="utf-8").read(); asal = hashlib.sha256(s.encode()).hexdigest()
def ganti(lama, baru):
    global s; assert s.count(lama) == 1, lama; s = s.replace(lama, baru)
ganti('assert _common.FEATSET == "P2" and _common.CLEARSKY == "IP"',
      'assert _common.FEATSET == "P2F" and _common.CLEARSKY == "IP" and len(_common.P2_AKTIF) == 44   # Manuskrip V6\n'
      '_V610 = r"C:\\Users\\ariff\\Documents\\Balai_data_v6_10"; _KOTAK = r"C:\\Users\\ariff\\Documents\\Balai_kotak_v6_10"\n'
      'for _k, _d in (("DATA_DIR", "00_data"), ("CLEARSKY_DIR", "clearsky"), ("CLP_EKSTRA_DIR", "clp_ekstra")): assert os.path.normcase(os.environ.get(_k, "")) == os.path.normcase(os.path.join(_V610, _d)), _k')
ganti('SCR = os.environ["SCR_V5"]; D0, DR = os.path.join(SCR, "00_data"), os.path.join(SCR, "00_data_rawfill");',
      'D0, DR = os.path.join(_V610, "00_data"), os.path.join(_V610, "00_data_rawfill");')   # variabel V5 di skrip = folder Manuskrip_versi6
ganti('ns18 = {"__file__": os.path.join(B, "18b_synop_asof_6situs.py")}; exec(compile(s18.replace(\'os.environ.get("DATA_DIR", "00_data")\', repr(D0)), "18b", "exec"), ns18)',
      's18 = s18.replace("X = apply_clearsky(X, site)", "X = apply_clearsky(X, site); X = _common.add_clp_ekstra(X, site) if _common.FEATSET == \'P2F\' else X")   # Manuskrip V6: prediktor ke-44\n'
      'ns18 = {"__file__": os.path.join(B, "18b_synop_asof_6situs.py"), "_common": _common}; exec(compile(s18.replace(\'os.environ.get("DATA_DIR", "00_data")\', repr(D0)), "18b", "exec"), ns18)')
ganti('SPAT = ["clps_cot_std", "clps_cot_min", "clps_cot_max", "clps_cloud_frac", "clps_cth_std", "clps_cloud_frac_lag_60m", "clps_cot_std_lag_60m"]',
      'SPAT = ["clps_cot_std", "clps_cot_min", "clps_cot_max", "clps_cth_std", "clps_cloud_frac_lag_60m", "clps_cot_std_lag_60m"]   # Manuskrip V6: clps_cloud_frac = clp_cloud_frac (prediktor ke-44)')
ganti('os.path.join(B, "28_clp_spatial", "data", f"{s}_clp_spatial.parquet")', 'os.path.join(_KOTAK, f"{s}_clp_kotak.parquet")')
ganti('    for c in SPAT: d2[c] = sp[c].to_numpy(float)',
      '    assert np.allclose(sp.clps_cloud_frac.to_numpy(float), df.clp_cloud_frac.to_numpy(float), equal_nan=True)   # Manuskrip V6\n    for c in SPAT: d2[c] = sp[c].to_numpy(float)')
ganti('log("SELESAI analisis 01 v5")', 'log("SELESAI analisis 01 v6")')
s = ('# Manuskrip V6: dibuat oleh 00_siapkan_pipeline_v6.py dari Manuskrip_versi5/analisis/01_pipeline_v5.py (sha256 ' + asal[:16] + '…); jangan disunting langsung.\n'
     '# Jalankan: DATA_DIR, CLEARSKY_DIR, CLP_EKSTRA_DIR = Balai_data_v6_10/…, FEATSET=P2F, PYTHONIOENCODING=utf-8 python -u 01_pipeline_v6.py\n' + s)
compile(s, "01_pipeline_v6.py", "exec")
open(os.path.join(HERE, "01_pipeline_v6.py"), "w", encoding="utf-8", newline="").write(s)
json.dump(dict(sumber="Manuskrip_versi5/analisis/01_pipeline_v5.py", sha256=asal, kotak="Balai_kotak_v6_10"), open(os.path.join(HERE, "asal_pipeline.json"), "w"), indent=1); print("ok", asal[:16])
