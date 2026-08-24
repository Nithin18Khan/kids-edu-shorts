# Install a Windows daily task: 06:30 local, one unique kids Short.
# Run in PowerShell (can request admin if Task Scheduler requires it):
#   powershell -ExecutionPolicy Bypass -File scripts\install_daily_task.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $PSScriptRoot "daily.ps1"
$TaskName = "KidsEduShortsDaily"
$Stamp = "06:30"

$tr = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$Runner`""
schtasks /Create /TN $TaskName /TR $tr /SC DAILY /ST $Stamp /F /RL LIMITED
if ($LASTEXITCODE -ne 0) {
    Write-Host "schtasks failed. Open Task Scheduler and point a daily 06:30 task at:"
    Write-Host $Runner
    exit $LASTEXITCODE
}
Write-Host "Installed $TaskName at $Stamp every day."
Write-Host "Working folder: $Root"
Write-Host "Log: $Root\output\daily.log"
Write-Host "Need credentials/kids/client_secret.json before uploads succeed."
Write-Host "Leave this PC on, with Blender + Python available."
