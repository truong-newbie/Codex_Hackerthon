param(
    [switch]$RunTests,
    [string]$PythonExe
)

$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent $PSScriptRoot
$mobileDir = Join-Path $rootDir "mobile"

Write-Host "ShiftLens preflight: local files and optional isolated tests" -ForegroundColor Cyan

try {
    $lanIps = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
        Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
        Select-Object -ExpandProperty IPAddress)
    if ($lanIps.Count -gt 0) {
        Write-Host "Possible LAN API URLs (verify on the device):" -ForegroundColor Yellow
        $lanIps | ForEach-Object { Write-Host "  http://${_}:8000" }
    } else {
        Write-Host "No usable LAN IPv4 address detected. Network: NOT_VERIFIED" -ForegroundColor Yellow
    }
} catch {
    Write-Host "LAN detection unavailable. Network: NOT_VERIFIED" -ForegroundColor Yellow
}

$requiredPaths = @(
    (Join-Path $mobileDir "android\gradlew.bat"),
    (Join-Path $mobileDir "android\app\src\main\AndroidManifest.xml"),
    (Join-Path $mobileDir "src\utils\storage.ts"),
    (Join-Path $rootDir "admin-appsmith\openapi.json")
)
foreach ($path in $requiredPaths) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required project file is missing: $path"
    }
    Write-Host "[PASS] Present: $path" -ForegroundColor Green
}

if ($RunTests) {
    & (Join-Path $PSScriptRoot "run_tests.ps1") -PythonExe $PythonExe
} else {
    Write-Host "Backend tests: SKIPPED (use -RunTests to run on an isolated test database)" -ForegroundColor Yellow
}

Write-Host "Android install/force-stop, API reachability and Gemini Live: NOT_VERIFIED" -ForegroundColor Yellow
