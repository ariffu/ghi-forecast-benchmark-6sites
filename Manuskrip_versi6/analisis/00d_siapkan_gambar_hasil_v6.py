# -*- coding: utf-8 -*-
"""Manuskrip V6 — membuat v6_03_gambar.py (Fig. 3–5, S1, S2) dari Manuskrip_versi5/analisis/v4_03_gambar.py dengan penggantian tercatat:
sumber kontrol sinyal sintetis dan SHAP dari tahap 114 (V6.10); label 44 prediktor; nama tampilan fraksi awan. Jalankan sekali."""
import os, hashlib, json
HERE = os.path.dirname(os.path.abspath(__file__)); V6 = os.path.dirname(HERE); ROOT = os.path.dirname(V6)
src = os.path.join(ROOT, "Manuskrip_versi5", "analisis", "v4_03_gambar.py"); s = open(src, encoding="utf-8").read(); h = hashlib.sha256(s.encode()).hexdigest()
G = [('SY = pd.read_csv(os.path.join(ROOT, "training mirip", "hasil", "sinyal_sintetis.csv"))', 'SY = pd.read_csv(os.path.join(P, "114_pendukung_v610", "a3_sintetis", "sinyal_sintetis.csv"))   # Manuskrip V6: V6.10'),
     ('mods = [("LightGBM, 43 fitur", "LightGBM (43 predictors)", "#2e7d32", "o")', 'mods = [("LightGBM, 43 fitur", "LightGBM (44 predictors)", "#2e7d32", "o")'),
     ('"clp_cloud_present_int": "Cloud flag",', '"clp_cloud_present_int": "Cloud flag", "clp_cloud_frac": "Cloud fraction",'),
     ('SH = pd.read_csv(os.path.join(P, "02_feature_ranking_mean", "shap_global_mean.csv"))', 'SH = pd.read_csv(os.path.join(P, "114_pendukung_v610", "a2_shap", "shap_global_mean.csv"))'),
     ('SS = pd.read_csv(os.path.join(P, "02_feature_ranking_mean", "selection_sweep_mean.csv")).dropna()', 'SS = pd.read_csv(os.path.join(P, "114_pendukung_v610", "a2_shap", "selection_sweep_mean.csv")).dropna()'),
     ('J["shap_seleksi_uji_43"] = float(SS.loc[SS.K == 43, "test_R2"].iloc[0])', 'J["shap_seleksi_uji_44"] = float(SS.loc[SS.K == 44, "test_R2"].iloc[0])'),
     ('a2.set_ylim(-12, 25)', 'a2.set_ylim(-14, 25)'),
     ('a2.set_xlabel("Number of predictors retained (by SHAP rank)")', 'a2.set_xlabel("Number of predictors retained (by importance rank)")')]
for a, b in G:
    assert s.count(a) == 1, a; s = s.replace(a, b)
s = f"# Manuskrip V6: dibuat oleh analisis/00d_siapkan_gambar_hasil_v6.py dari Manuskrip_versi5/analisis/v4_03_gambar.py (sha256 {h[:16]}…); jangan disunting langsung.\n" + s
compile(s, "v6_03_gambar.py", "exec"); open(os.path.join(HERE, "v6_03_gambar.py"), "w", encoding="utf-8", newline="").write(s)
L = json.load(open(os.path.join(HERE, "asal_gambar.json"), encoding="utf-8")); L["v6_03_gambar.py"] = dict(sumber=src, sha256=h, ganti=G)
json.dump(L, open(os.path.join(HERE, "asal_gambar.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False); print("ok")
