# -*- coding: utf-8 -*-
"""Runner rerun 43 prediktor (FEATSET=P2, keputusan 2026-10-06; LAPORAN §21–§22). BERURUTAN, berhenti pada kegagalan, dapat dilanjutkan.

Prasyarat: 51_arsipkan_P0.py sudah dijalankan (hasil 104 prediktor di _arsip_P0_104prediktor/, keluaran resume dan penanda .done dipindah).
Urutan:
 1) run_all.py (tahap 01 dst.; 00_data tidak dibangun ulang karena tidak bergantung pada himpunan prediktor)
 2) 19, 18b (6 situs + summary), 27, 28, 31 (V0 direkonstruksi dari 00_data), 33_verify_B (silang dengan 31)
 3) multi-seed 36 (six_mlp, six_tab, bkl, six_seq) + 37
 4) gambar 15, 16; tabel 20, 21
 5) uji tuning Bengkulu (61; ±1 jam, dapat dilanjutkan; DESAIN_61), skill dan pembanding linear (60, sejak 2026-10-08; DESAIN_60), naskah v3 (49), suplemen v3 = SI + ESM (52), paket submission v3 (53), registri (38)
Builder struktur v2 (23, 24, 34, 35) dipagari sejak 2026-10-06 (LAPORAN §23).
Log: logs/P2_NN_*.log (36: logs/36_<tahap>.log), manifest logs/run_manifest_P2.csv, penanda logs/P2_NN_*.done.
Jalankan (detached): python -u run_rerun_P2.py > logs/run_rerun_P2.out 2>&1
"""
import os, sys, time, subprocess
BASE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(BASE, "logs")
assert os.path.isdir(os.path.join(BASE, "_arsip_P0_104prediktor")), "jalankan 51_arsipkan_P0.py dulu"
man = os.path.join(LOGS, "run_manifest_P2.csv")
if not os.path.exists(man): open(man, "w").write("step,command,start,end,seconds,exit\n")
ENV = {**os.environ, "FEATSET": "P2", "CLEARSKY": "IP", "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg", "PYTHONWARNINGS": "ignore"}
SITES = ["banten", "bengkulu", "jambi", "jogja", "kalbar", "semarang"]
# Sejak 2026-10-12 (rerun flag CLP seragam, tahap 65): token "K=V" di awal langkah = variabel lingkungan khusus langkah itu.
# Ditambahkan: 00_data_rawfill (MASK_CLP=0, untuk 19/27), 50 (FEATSET=P0; setelah 04c/07b), 62, 63, 64 sebelum naskah.
STEPS = ([["run_all.py"], ["MASK_CLP=0", "00_build_data.py"], ["FEATSET=P0", "50_evaluasi_prediktor.py"], ["19_sens_clp_fill.py"]] +
         [["18b_synop_asof_6situs.py", "run", s] for s in SITES] +
         [["18b_synop_asof_6situs.py", "summary"], ["27_block_bootstrap.py"], ["28_clp_spatial.py"], ["31_clp_lag_sensitivity.py"], ["33_verify_B.py"]] +
         [["36_multiseed_neural.py", p] for p in ["six_mlp", "six_tab", "bkl", "six_seq"]] + [["37_multiseed_analysis.py"]] +
         [["15_final_figs_mean_en.py"], ["16_final_figs_release_en.py"], ["20_angka_manuskrip.py"], ["21_tabel_manuskrip.py"],
          ["61_tuning_bengkulu.py"], ["60_skill_linear.py"], ["62_scatter_6situs.py"], ["63_aws_subkelompok.py"], ["64_kt_referensi.py"], ["49_build_manuskrip_v3.py"], ["52_build_esm_v3.py"], ["53_build_submission_v3.py"], ["38_registri_kanonik.py"]])
t_all = time.time()
for i, st in enumerate(STEPS):
    envx = dict(x.split("=", 1) for x in st if "=" in x and not x.endswith(".py")); st = [x for x in st if not ("=" in x and not x.endswith(".py"))]
    tag = f"P2_{i:02d}_" + "_".join(os.path.splitext(x)[0] for x in st) + "".join(f"_{k}{v}" for k, v in envx.items())
    done = os.path.join(LOGS, tag + ".done")
    if os.path.exists(done): print(f"[skip] {tag}", flush=True); continue
    logname = f"36_{st[1]}.log" if st[0] == "36_multiseed_neural.py" else tag + ".log"        # nama log 36 dipakai cek C4 (38)
    t0 = time.time(); s0 = time.strftime("%Y-%m-%d %H:%M:%S"); print(f"[run ] {tag} ({s0})", flush=True)
    with open(os.path.join(LOGS, logname), "w", encoding="utf-8") as lf:
        rc = subprocess.call([sys.executable, "-u"] + st, cwd=BASE, stdout=lf, stderr=subprocess.STDOUT, env={**ENV, **envx})
    dt = time.time() - t0
    open(man, "a").write(f'{i},"{" ".join(st)}",{s0},{time.strftime("%Y-%m-%d %H:%M:%S")},{dt:.0f},{rc}\n')
    print(f"       exit={rc} ({dt:.0f}s, total {time.time()-t_all:.0f}s)", flush=True)
    if rc != 0: print(f"GAGAL pada {tag}", flush=True); sys.exit(rc)
    open(done, "w").write(time.strftime("%Y-%m-%d %H:%M:%S"))
print(f"RERUN P2 SELESAI dalam {time.time()-t_all:.0f}s", flush=True)
