import ast
p = "c1_bangun_v6.py"; t = open(p, encoding="utf-8").read()
R = [
 ("def blok(a):\n    n = len(a);", "def resolusi(a):\n    x = a[np.isfinite(a)][:200000]\n    for r in (1.0, 0.1, 0.01):\n        if np.mean(np.abs(x / r - np.round(x / r)) < 1e-6) > 0.95: return r\n    return 0.0\ndef blok(a, TOL=TOL):\n    n = len(a);"),
 ("def kausal(a, idx, ct=None):\n    obs, interp = blok(a);", "def kausal(a, idx, ct=None):\n    tol = max(0.006, resolusi(a) / 2 + 0.001); obs, interp = blok(a, tol);"),
]
for a, b in R:
    assert t.count(a) == 1, a[:40]; t = t.replace(a, b)
ast.parse(t); open(p, "w", encoding="utf-8").write(t); print("ok")
