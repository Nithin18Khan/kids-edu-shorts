# Stay running while the PC is on. After 10:00 PM each day, check and
# render at most one Short. Safe if you rarely shut down.
#
# Started from Windows Startup. One film per IST day.
# Waits in 1-minute chunks so sleep/wake still fires after 10 PM.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "main.py"))) {
    $Root = (Get-Location).Path
}
Set-Location $Root

$Daily = Join-Path $PSScriptRoot "pc_daily.ps1"
$LogDir = Join-Path $Root "output"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir "pc_watch.log"
$Lock = Join-Path $Root "data\pc_watch.lock"
New-Item -ItemType Directory -Force -Path (Join-Path $Root "data") | Out-Null

function Write-Watch([string]$msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Write-Host $line
    Add-Content -Path $Log -Value $line
}

function Get-TodayTenPm {
    return Get-Date -Hour 22 -Minute 0 -Second 0
}

function Wait-UntilTenPm {
    $lastNote = $null
    while ($true) {
        $now = Get-Date
        $todayAt = Get-TodayTenPm
        if ($now -ge $todayAt) {
            return
        }
        $leftMin = [int][Math]::Ceiling(($todayAt - $now).TotalMinutes)
        if ($lastNote -ne $leftMin -and ($leftMin % 15 -eq 0 -or $leftMin -le 5)) {
            Write-Watch "Waiting until 10:00 PM ($leftMin min)."
            $lastNote = $leftMin
        }
        $chunk = 60
        if (($todayAt - $now).TotalSeconds -lt 60) {
            $chunk = [Math]::Max(1, [int]($todayAt - $now).TotalSeconds)
        }
        Start-Sleep -Seconds $chunk
    }
}

function Wait-UntilNextTenPm {
    $next = (Get-TodayTenPm).AddDays(1)
    $lastNote = $null
    while ($true) {
        $now = Get-Date
        if ($now -ge $next) {
            return
        }
        $leftMin = [int][Math]::Ceiling(($next - $now).TotalMinutes)
        if ($lastNote -ne $leftMin -and ($leftMin % 60 -eq 0 -or $leftMin -le 5)) {
            Write-Watch "Next check $($next.ToString('yyyy-MM-dd HH:mm')). Sleep $leftMin min."
            $lastNote = $leftMin
        }
        $chunk = 60
        if (($next - $now).TotalSeconds -lt 60) {
            $chunk = [Math]::Max(1, [int]($next - $now).TotalSeconds)
        }
        Start-Sleep -Seconds $chunk
    }
}

if (Test-Path $Lock) {
    try {
        $old = [int]((Get-Content $Lock -Raw).Trim())
        if ($old -gt 0 -and $old -ne $PID) {
            $alive = Get-Process -Id $old -ErrorAction SilentlyContinue
            if ($alive) {
                Write-Watch "Stopping stuck watcher pid $old so this one can run."
                Stop-Process -Id $old -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
            }
        }
    } catch {}
}
Set-Content -Path $Lock -Value $PID

try {
    Write-Watch "Kids Edu Shorts watcher started. Check every day after 10:00 PM."
    while ($true) {
        Wait-UntilTenPm
        Write-Watch "10:00 PM window - checking today's film."
        try {
            powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Daily
            Write-Watch "Daily check finished (exit $LASTEXITCODE)."
        } catch {
            Write-Watch "Daily check error: $_"
        }
        Wait-UntilNextTenPm
    }
} finally {
    if ((Test-Path $Lock) -and ((Get-Content $Lock -Raw).Trim() -eq "$PID")) {
        Remove-Item $Lock -Force -ErrorAction SilentlyContinue
    }
}
