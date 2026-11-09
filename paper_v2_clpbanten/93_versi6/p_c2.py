import ast
p = "c2_validasi_v6.py"; t = open(p, encoding="utf-8").read()
a = '''        r[f"segaris_{c}_V5"] = round(float(seg(a[c].to_numpy(float), idx)[nh].mean()), 4); r[f"segaris_{c}_V6"] = round(float(seg(b[c].to_numpy(float), idx)[nh].mean()), 4)'''
b = '''        x5, x6 = a[c].to_numpy(float), b[c].to_numpy(float); xx = x5[np.isfinite(x5)][:200000]; res = next((q for q in (1.0, 0.1, 0.01) if np.mean(np.abs(xx / q - np.round(xx / q)) < 1e-6) > 0.95), 0.0); tl = max(0.006, res / 2 + 0.001)
        s5 = seg(x5, idx, tl); s6 = seg(x6, idx, tl); r[f"segaris_{c}_V5"] = round(float(s5[nh].mean()), 4); r[f"bocor_sisa_{c}_V6"] = round(float((s6 & np.isclose(x5, x6))[nh].mean()), 4)'''
assert t.count(a) == 1; t = t.replace(a, b)
a2 = '''    r["flag_cocok"] = round(float(((b.clp_cot >= 1).astype(float).where(b.clp_cot.notna()) == b.clp_cloud_present_int.where(b.clp_cot.notna())).mean()), 4)'''
b2 = '''    q = day & b.clp_cot.notna().to_numpy(); r["flag_cocok_siang"] = round(float(((b.clp_cot[q] >= 1).astype(int) == b.clp_cloud_present_int[q]).mean()), 4)'''
assert t.count(a2) == 1; t = t.replace(a2, b2)
ast.parse(t); open(p, "w", encoding="utf-8").write(t); print("ok")
