# After 10:00 PM every day, check and make one Short.
# Works while the PC stays on (you rarely shut down).
#
#   powershell -ExecutionPolicy Bypass -File scripts\install_daily_task.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Watch = Join-Path $PSScriptRoot "pc_watch.ps1"
$TaskName = "KidsEduShortsOnLogon"

if (-not (Test-Path $Watch)) {
    Write-Host "Missing $Watch"
    exit 1
}

$prev = $ErrorActionPreference
$ErrorActionPreference = "Continue"
foreach ($old in @("KidsEduShortsDaily", "KidsEduShortsPCDaily", $TaskName)) {
    schtasks /Delete /TN $old /F 2>$null | Out-Null
}
$ErrorActionPreference = $prev

$startup = [Environment]::GetFolderPath("Startup")
$lnkPath = Join-Path $startup "KidsEduShortsOnLogon.lnk"
$w = New-Object -ComObject WScript.Shell
$s = $w.CreateShortcut($lnkPath)
$s.TargetPath = "powershell.exe"
$s.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$Watch`""
$s.WorkingDirectory = $Root
$s.WindowStyle = 7
$s.Description = "Kids Edu Shorts - check after 10 PM every day"
$s.Save()

Write-Host "Installed 10:00 PM watcher."
Write-Host "Shortcut: $lnkPath"
Write-Host "Every night after 10 PM it checks. If today's film is done, it skips."
Write-Host "Log: $Root\output\pc_watch.log"
Write-Host "Leave the PC on (sleep off is best). You do not need to shut down."
