# Laptop quality factory: render here, then GitHub only uploads.
# Triggered at Windows logon (no clock). Safe to run more than once per day.
# Never publishes a GitHub CPU Blender stub.

param(
    [switch]$Boot
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "main.py"))) {
    $Root = (Get-Location).Path
}
Set-Location $Root

$env:Path = @(
    "$env:LOCALAPPDATA\Programs\Python\Python310"
    "$env:LOCALAPPDATA\Programs\Python\Python311"
    "$env:LOCALAPPDATA\Programs\Python\Python312"
    "C:\Program Files\Git\cmd"
    "C:\Program Files\GitHub CLI"
    $env:Path
) -join ";"

$LogDir = Join-Path $Root "output"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir "pc_daily.log"
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $Log -Value "`n===== $stamp PC boot start ====="

function Write-Both([string]$msg) {
    Write-Host $msg
    Add-Content -Path $Log -Value $msg
}

Write-Both "=== Kids Edu Shorts - PC gold (logon) ==="

if ($Boot) {
    Write-Both "Waiting 90 seconds so Wi-Fi / OneDrive can start ..."
    Start-Sleep -Seconds 90
}

$deadline = (Get-Date).AddMinutes(5)
$online = $false
while ((Get-Date) -lt $deadline) {
    try {
        if (Test-Connection -ComputerName github.com -Count 1 -Quiet -ErrorAction SilentlyContinue) {
            $online = $true
            break
        }
    } catch {}
    Write-Both "Waiting for internet ..."
    Start-Sleep -Seconds 10
}
if (-not $online) {
    Write-Both "No internet after 5 minutes. Will retry next time you turn the PC on."
    exit 0
}

try {
    git fetch origin
    if ($LASTEXITCODE -ne 0) { throw "git fetch failed (exit $LASTEXITCODE)" }

    # A dirty tree makes --rebase refuse. Park local edits, rebase, put them back.
    $stashed = $false
    git diff --quiet
    $dirty = ($LASTEXITCODE -ne 0)
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) { $dirty = $true }
    if ($dirty) {
        git stash push -u -m "pc_daily auto-stash" -- . ":!data" ":!approved"
        if ($LASTEXITCODE -ne 0) { throw "git stash failed (exit $LASTEXITCODE)" }
        $stashed = $true
        Write-Both "Parked local edits so the rebase can run."
    }

    git pull --rebase origin github-actions
    $pullCode = $LASTEXITCODE

    if ($stashed) {
        git stash pop
        if ($LASTEXITCODE -ne 0) {
            Write-Both "WARNING: could not restore local edits. See: git stash list"
        }
    }
    if ($pullCode -ne 0) { throw "git pull --rebase failed (exit $pullCode)" }
    Write-Both "Pulled latest factory state from GitHub."
} catch {
    Write-Both "git pull FAILED - factory state may be stale: $_"
}

$py = Join-Path $env:LOCALAPPDATA "Programs\Python\Python310\python.exe"
if (-not (Test-Path $py)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source } else { $py = "python" }
}

$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $py main.py --pc-boot *>> $Log
$code = $LASTEXITCODE
$ErrorActionPreference = $prevEap
Add-Content -Path $Log -Value "===== pc-boot exit $code ====="
Write-Host "pc-boot exit $code"

# 1 = render failed. 2 = already done today. 3 = another run is live.
if ($code -eq 1) {
    throw "PC render failed (see output\pc_daily.log)"
}

$goldDir = Join-Path $Root "approved"
$goldRel = $null
$goldFile = Join-Path $Root "data\pc_last_gold.txt"
if (Test-Path $goldFile) {
    $goldRel = (Get-Content $goldFile -Raw).Trim()
}
$goldPath = if ($goldRel) { Join-Path $Root $goldRel } else { $null }
if (-not $goldPath -or -not (Test-Path $goldPath)) {
    $found = Get-ChildItem -Path $goldDir -Filter "*_short.mp4" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $goldPath = $found.FullName }
}
if (-not $goldPath -or -not (Test-Path $goldPath)) {
    if ($code -eq 0) {
        throw "No approved gold mp4 after render"
    }
    Write-Both "No gold to push this logon."
    exit 0
}
if (-not $goldRel) {
    $goldRel = $goldPath.Substring($Root.Length).TrimStart("\", "/") -replace "\\", "/"
}

git add -- $goldRel
$thumbRel = $goldRel -replace "_short\.mp4$", "_thumb.jpg"
if ($thumbRel -and (Test-Path (Join-Path $Root $thumbRel))) {
    git add -- $thumbRel
}
git add data/factory_state.json
if (git diff --staged --quiet) {
    Write-Both "No new gold to push"
    if ($code -ne 0) {
        exit 0
    }
} else {
    git -c user.name="Nithin18Khan" -c user.email="Nithin18Khan@users.noreply.github.com" commit -m "Add PC gold Short for YouTube (no CPU Blender)."
    git push origin HEAD
}

if ($code -eq 0) {
    gh workflow run "Daily kids Short" --ref github-actions --repo Nithin18Khan/kids-edu-shorts
    Write-Both "GitHub will upload the PC gold if the next unpublished day has approved/*.mp4"
} else {
    Write-Both "Skipped GitHub upload trigger (already handled or still rendering)."
}
exit 0
