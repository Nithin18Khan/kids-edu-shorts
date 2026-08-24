# Daily kids-channel factory. Run from Task Scheduler.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$LogDir = Join-Path $Root "output"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir "daily.log"
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $Log -Value "`n===== $stamp daily start ====="
& python main.py --daily --upload *>> $Log
$code = $LASTEXITCODE
Add-Content -Path $Log -Value "===== daily exit $code ====="
exit $code
