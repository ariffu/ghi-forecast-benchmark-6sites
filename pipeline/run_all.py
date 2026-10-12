# -*- coding: utf-8 -*-
"""Runner BERURUTAN rerun manuskrip hourly 6 situs pada solar_harmonised_clpbanten_v2.duckdb.

Urutan mengikuti dependensi artefak (lihat README_RERUN_v2.md). Setiap tahap:
log -> logs/NN_<skrip>.log, penanda selesai -> logs/NN_<skrip>.done (resume aman),
ringkasan -> logs/run_manifest.csv. Berhenti pada kegagalan pertama.
Jalankan: python -u run_all.py      (ulang dari awal: hapus folder logs/)
"""
import os, sys, time, json, platform, subprocess, importlib
BASE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(BASE, "logs"); os.makedirs(LOGS, exist_ok=True)
STEPS = [
    ("00_build_data.py",              "data: integritas DB + frame 124 kolom (CLP dimask)"),
    ("01_baseline_v3.py",             "§3.1 baseline Bengkulu (point + mean)"),
    ("01b_walkforward_v2.py",         "§2.6 walk-forward point"),
    ("01b_walkforward_mean.py",       "§2.6 walk-forward mean"),
    ("02_feature_ranking_v2.py",      "§3.2 ranking fitur (point, pembanding urutan)"),
    ("02b_feature_ranking_mean.py",   "§3.2 SHAP + kurva seleksi (mean)"),
    ("03_ablation_mean.py",           "§3.3 ablasi + bootstrap Bengkulu"),
    ("04_arch_mean.py",               "§3.4 8 arsitektur Bengkulu"),
    ("01b_timeseries_mean.py",        "Fig.3b deret waktu (pakai prediksi 04_arch_mean)"),
    ("06_strat_mean.py",              "§3.5 stratifikasi"),
    ("06_strat_mean_plot.py",         "plot stratifikasi"),
    ("04c_mean_6situs.py",            "§3.7 baseline mean 6 situs (CatBoost, LightGBM)"),
    ("04c_mean_6situs_xgb_mlp.py",    "§3.7 baseline mean 6 situs (XGBoost, MLP)"),
    ("04b_seq_6situs_mean.py",        "§3.7 sequence models mean 6 situs"),
    ("04b_merge_mean.py",             "§3.7 tabel 8x6 mean"),
    ("04b_arch_6situs.py",            "§3.7 tabel 8x6 point"),
    ("04b_arch_6situs_plot.py",       "matriks R2 point + plot"),
    ("07b_replication_ablation_mean.py", "§3.7 ablasi 6 situs + CI"),
    ("09_sens_mean.py",               "§3.6 / Tabel S2 protokol A/B/C"),
    ("13b_reference_skill_6situs.py", "§3.1/§3.7 / Tabel S4 skill vs CP-optimal"),
    ("11_probabilistic_mean.py",      "§3.8 / Tabel S1 kuantil & Gaussian"),
    ("12b_conformal_split_mean.py",   "§3.8 CQR split (mean)"),
    ("12b_conformal_split.py",        "SI CQR split (point companion)"),
    ("S3_target_effect.py",           "Tabel S3 efek target"),
    ("15_final_figs_mean_en.py",      "gambar pendukung (EN)"),
    ("16_final_figs_release_en.py",   "gambar rilis Fig.3-10, S1-S4"),
    ("make_fig2_workflow.py",         "Fig.2 diagram alur (statis)"),
]
env_info = dict(python=sys.version, platform=platform.platform(), started=time.strftime("%Y-%m-%d %H:%M:%S"))
for m in ["numpy", "pandas", "duckdb", "lightgbm", "catboost", "xgboost", "torch", "sklearn", "scipy", "matplotlib"]:
    try: env_info[m] = importlib.import_module(m).__version__
    except Exception as e: env_info[m] = f"ERR {e}"
json.dump(env_info, open(os.path.join(LOGS, "environment.json"), "w"), indent=1)
man = os.path.join(LOGS, "run_manifest.csv")
if not os.path.exists(man): open(man, "w").write("step,script,description,start,end,seconds,exit\n")
t_all = time.time()
for i, (scr, desc) in enumerate(STEPS):
    tag = f"{i:02d}_{os.path.splitext(scr)[0]}"; done = os.path.join(LOGS, tag + ".done")
    if os.path.exists(done): print(f"[skip] {tag}", flush=True); continue
    args = [sys.executable, "-u", scr] + (["plots/final"] if scr == "make_fig2_workflow.py" else [])
    if scr == "make_fig2_workflow.py": os.makedirs(os.path.join(BASE, "plots", "final"), exist_ok=True)
    t0 = time.time(); st = time.strftime("%Y-%m-%d %H:%M:%S"); print(f"[run ] {tag} — {desc}", flush=True)
    with open(os.path.join(LOGS, tag + ".log"), "w", encoding="utf-8") as lf:
        rc = subprocess.call(args, cwd=BASE, stdout=lf, stderr=subprocess.STDOUT,
                             env={**os.environ, "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg"})
    dt = time.time() - t0
    open(man, "a").write(f'{i},{scr},"{desc}",{st},{time.strftime("%Y-%m-%d %H:%M:%S")},{dt:.0f},{rc}\n')
    print(f"       exit={rc} ({dt:.0f}s, total {time.time()-t_all:.0f}s)", flush=True)
    if rc != 0: print(f"GAGAL pada {tag}; lihat logs/{tag}.log", flush=True); sys.exit(rc)
    open(done, "w").write(time.strftime("%Y-%m-%d %H:%M:%S"))
print(f"SEMUA TAHAP SELESAI dalam {time.time()-t_all:.0f}s", flush=True)
