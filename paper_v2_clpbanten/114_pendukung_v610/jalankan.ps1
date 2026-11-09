# Tahap 114: peluncur. Pemakaian: pwsh -File jalankan.ps1 <a1|a2|a3|a4> ; bisa dijalankan ulang (a4 melanjutkan dari preds/).
param([Parameter(Mandatory=$true)][ValidateSet("a1","a2","a3","a4","a5")][string]$kode)
$V = "C:\Users\ariff\Documents\Balai_data_v6_10"
$env:DATA_DIR = "$V\00_data"; $env:CLEARSKY_DIR = "$V\clearsky"; $env:CLP_EKSTRA_DIR = "$V\clp_ekstra"
$env:FEATSET = "P2F"; $env:PYTHONIOENCODING = "utf-8"; $env:PYTHONUNBUFFERED = "1"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$skrip = @{ a1 = "a1_walkforward.py"; a2 = "a2_shap_bengkulu.py"; a3 = "a3_sinyal_sintetis.py"; a4 = "a4_tuning.py"; a5 = "a5_seleksi.py" }[$kode]
Set-Location $here
python (Join-Path $here $skrip)
exit $LASTEXITCODE
