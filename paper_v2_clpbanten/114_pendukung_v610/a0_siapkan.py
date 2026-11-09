# -*- coding: utf-8 -*-
"""Tahap 114 a0: membuat a1–a3 dari skrip asal dengan penggantian teks tercatat (DESAIN_114.md). Jalankan sekali: python a0_siapkan.py"""
import os, hashlib, json
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(HERE); ROOT = os.path.dirname(B)
CEK = ('import os as _os\n_V = r"C:\\Users\\ariff\\Documents\\Balai_data_v6_10"\n'
       'assert _os.environ.get("FEATSET") == "P2F"\n'
       'for _k, _d in (("DATA_DIR", "00_data"), ("CLEARSKY_DIR", "clearsky"), ("CLP_EKSTRA_DIR", "clp_ekstra")): assert _os.path.normcase(_os.environ.get(_k, "")) == _os.path.normcase(_os.path.join(_V, _d)), _k\n')
LOG = {}
def buat(src, dst, ganti):
    s = open(src, encoding="utf-8").read(); h = hashlib.sha256(s.encode()).hexdigest()
    for a, b in ganti:
        assert s.count(a) == 1, (dst, a); s = s.replace(a, b)
    s = f"# Tahap 114: dibuat oleh a0_siapkan.py dari {os.path.relpath(src, ROOT)} (sha256 {h[:16]}…); jangan disunting langsung.\n" + s
    compile(s, dst, "exec"); open(os.path.join(HERE, dst), "w", encoding="utf-8", newline="").write(s); LOG[dst] = dict(sumber=os.path.relpath(src, ROOT), sha256=h, ganti=ganti)
# a1 walk-forward
buat(os.path.join(B, "01b_walkforward_mean.py"), "a1_walkforward.py", [
    ("sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))", CEK + 'sys.path.insert(0, r"%s")' % B),
    ('df, feats, yr = prepare("bengkulu")', 'df, feats, yr = prepare("bengkulu"); import _common as _c; assert len(feats) == 44 and _c.FEATSET == "P2F"'),
    ('out = os.path.join(BASE, "01_baseline", "bengkulu_walkforward_mean.csv")', 'out = os.path.join(r"%s", "a1_walkforward_bengkulu.csv")' % HERE)])
# a2 peringkat fitur dan SHAP
buat(os.path.join(B, "02b_feature_ranking_mean.py"), "a2_shap_bengkulu.py", [
    ("sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))", CEK + 'sys.path.insert(0, r"%s")' % B),
    ('OUT = os.path.join(BASE, "02_feature_ranking_mean"); os.makedirs(OUT, exist_ok=True)', 'OUT = os.path.join(r"%s", "a2_shap"); os.makedirs(OUT, exist_ok=True)' % HERE),
    ("df, feats, yr = prepare()", 'df, feats, yr = prepare("bengkulu"); import _common as _c; assert len(feats) == 44 and _c.FEATSET == "P2F"')])
# a3 sinyal sintetis
buat(os.path.join(ROOT, "training mirip", "07_sinyal_sintetis.py"), "a3_sinyal_sintetis.py", [
    ('PAPER = os.path.join(os.path.dirname(HERE), "paper_v2_clpbanten"); sys.path.insert(0, PAPER)', CEK + 'PAPER = r"%s"; sys.path.insert(0, PAPER)' % B),
    ('assert _common.FEATSET == "P2"', 'assert _common.FEATSET == "P2F"'),
    ('OUT = os.path.join(HERE, "hasil"); t0 = time.time(); torch.set_num_threads(max(1, (os.cpu_count() or 4) - 1))',
     'OUT = os.path.join(HERE, "a3_sintetis"); os.makedirs(OUT, exist_ok=True); t0 = time.time(); torch.set_num_threads(4)'),
    ("assert len(ite) == 24714 and len(feats) == 43", "assert len(feats) == 44; print('uji', len(ite), flush=True)")])
json.dump(LOG, open(os.path.join(HERE, "asal_skrip_114.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False); print("ok", list(LOG))
