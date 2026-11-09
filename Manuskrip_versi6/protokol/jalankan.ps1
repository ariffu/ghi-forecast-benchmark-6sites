# Manuskrip V6: peluncur pelatihan protokol baku dari Balai_data_v6_10 (P2F, 44 prediktor).
# Pemakaian: pwsh -File jalankan.ps1 <pohon|nn> [argumen skrip...]   contoh: jalankan.ps1 nn --situs banten jambi --threads 3
# Bisa dijalankan ulang kapan saja: skrip melewati model x seed yang sudah ada di metrik_*.csv.
param([Parameter(Mandatory=$true)][ValidateSet("pohon","nn")][string]$jenis, [Parameter(ValueFromRemainingArguments=$true)]$sisa)
$V = "C:\Users\ariff\Documents\Balai_data_v6_10"
$env:DATA_DIR = "$V\00_data"; $env:CLEARSKY_DIR = "$V\clearsky"; $env:CLP_EKSTRA_DIR = "$V\clp_ekstra"
$env:FEATSET = "P2F"; $env:PYTHONIOENCODING = "utf-8"; $env:PYTHONUNBUFFERED = "1"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$skrip = if ($jenis -eq "pohon") { "02_rerun_pohon.py" } else { "01_rerun_jaringan_saraf.py" }
Set-Location $here
python (Join-Path $here $skrip) @sisa
exit $LASTEXITCODE
