# ShiftLens One-Click Demo Launcher (Auto-detects LAN IP for Real Android Phone)
param([string]$PythonExe = "python")
$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $rootDir "backend"

# Detect active IPv4 LAN address
$lanIp = "localhost"
try {
    $ips = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
        $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" -and $_.PrefixOrigin -ne "WellKnown"
    }
    if ($ips) {
        $lanIp = $ips[0].IPAddress
    }
} catch {}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   SHIFTLENS — HACKATHON LIVE DEMO LAUNCHER                     " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " [1] Manager Studio Web UI : http://localhost:8000/studio" -ForegroundColor Green
Write-Host " [2] Swagger OpenAPI Docs  : http://localhost:8000/docs" -ForegroundColor Green
Write-Host " [3] Health Check Endpoint : http://localhost:8000/v1/health" -ForegroundColor Green
Write-Host " [4] URL nhập vào App Android thật (cùng Wi-Fi/Hotspot):" -ForegroundColor Yellow
Write-Host "     👉 http://$($lanIp):8000" -ForegroundColor Magenta
Write-Host "================================================================" -ForegroundColor Cyan

$previousDemoMode = $env:DEMO_MODE
$env:DEMO_MODE = "true"
Push-Location $backendDir
try {
    & $PythonExe -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Database migration failed (exit code $LASTEXITCODE)" }
    & $PythonExe -m app.seed
    if ($LASTEXITCODE -ne 0) { throw "Demo seed failed (exit code $LASTEXITCODE)" }
    & $PythonExe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    if ($LASTEXITCODE -ne 0) { throw "Uvicorn failed (exit code $LASTEXITCODE)" }
} finally {
    Pop-Location
    $env:DEMO_MODE = $previousDemoMode
}
