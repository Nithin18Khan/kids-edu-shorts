# Laptop quality factory: render here, then GitHub only uploads.
# Never publishes a GitHub CPU Blender stub.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "main.py"))) {
    $Root = (Get-Location).Path
}
Set-Location $Root

Write-Host "=== Kids Edu Shorts — PC gold ==="
python main.py --daily --no-pre-render
if ($LASTEXITCODE -ne 0) {
    throw "PC render failed"
}

$gold = Get-ChildItem -Path (Join-Path $Root "approved") -Filter "*_short.mp4" -ErrorAction SilentlyContinue
if (-not $gold) {
    throw "No approved/*_short.mp4 after render"
}

git add approved/*_short.mp4 approved/*_thumb.jpg
git add data/factory_state.json
if (git diff --staged --quiet) {
    Write-Host "No new gold to push"
} else {
    git -c user.name="Nithin18Khan" -c user.email="Nithin18Khan@users.noreply.github.com" commit -m "Add PC gold Short for YouTube (no CPU Blender)."
    git push origin HEAD
}

gh workflow run "Daily kids Short" --ref github-actions --repo Nithin18Khan/kids-edu-shorts
Write-Host "GitHub will upload the PC gold if the next unpublished day has approved/*.mp4"
