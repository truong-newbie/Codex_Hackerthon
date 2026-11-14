# ShiftLens Pre-Flight Readiness Check Script (Hackathon Stage Gate Verification)
$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $rootDir "backend"
$mobileDir = Join-Path $rootDir "mobile"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   SHIFTLENS PRE-FLIGHT STAGE READINESS CHECK (G1 - G6)     " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Detect LAN IP for Real Android Device
$lanIp = (
    Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
    Select-Object -ExpandProperty IPAddress -First 1
)
if (-not $lanIp) { $lanIp = "localhost" }
Write-Host "[1/5] Network & LAN IP Check:" -ForegroundColor Yellow
Write-Host "      -> Local LAN API URL for Android Phone: http://${lanIp}:8000" -ForegroundColor Green
Write-Host "      -> Emulator API URL                   : http://10.0.2.2:8000" -ForegroundColor Green
Write-Host "      -> Built-in Manager Studio Web UI     : http://localhost:8000/studio" -ForegroundColor Green

# 2. Check Android Native Gradle Project & Cleartext Config
Write-Host "`n[2/5] Android Studio Native Project (mobile/android) Check:" -ForegroundColor Yellow
$gradlewPath = Join-Path $mobileDir "android\gradlew.bat"
$manifestPath = Join-Path $mobileDir "android\app\src\main\AndroidManifest.xml"
$storagePath = Join-Path $mobileDir "src\utils\storage.ts"

if (Test-Path $gradlewPath) {
    Write-Host "      -> [OK] mobile/android/gradlew.bat present" -ForegroundColor Green
} else {
    throw "Missing mobile/android/gradlew.bat! Run 'npx expo prebuild --platform android' inside mobile/"
}

$manifestContent = Get-Content $manifestPath -Raw
if ($manifestContent -match 'android:usesCleartextTraffic="true"') {
    Write-Host "      -> [OK] android:usesCleartextTraffic='true' enabled in AndroidManifest.xml" -ForegroundColor Green
} else {
    throw "Missing android:usesCleartextTraffic='true' in AndroidManifest.xml!"
}

$storageContent = Get-Content $storagePath -Raw
if ($storageContent -match '@react-native-async-storage/async-storage') {
    Write-Host "      -> [OK] Native AsyncStorage persistence integrated in mobile/src/utils/storage.ts" -ForegroundColor Green
} else {
    throw "Missing AsyncStorage in storage.ts!"
}

# 3. Check OpenAPI Specification Export
Write-Host "`n[3/5] OpenAPI 3.0 Contract (admin-appsmith/openapi.json) Check:" -ForegroundColor Yellow
$openApiPath = Join-Path $rootDir "admin-appsmith\openapi.json"
if (Test-Path $openApiPath) {
    Write-Host "      -> [OK] admin-appsmith/openapi.json present" -ForegroundColor Green
} else {
    throw "Missing admin-appsmith/openapi.json!"
}

# 4. Seed Database & Verify Café A / Café B Fixtures
Write-Host "`n[4/5] Seeding Database Fixtures (Cafe A & Cafe B):" -ForegroundColor Yellow
Push-Location $backendDir
try {
    python -m app.seed
    Write-Host "      -> [OK] Seeded Cafe A (strict policy) & Cafe B (flexible policy)" -ForegroundColor Green

    # 5. Run Full Pytest Suite (AT-01..AT-16 & Gates G1..G6)
    Write-Host "`n[5/5] Running Automated Acceptance & Governance Test Suite:" -ForegroundColor Yellow
    python -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "Backend pytest suite failed!"
    }
    Write-Host "      -> [OK] All automated tests passed!" -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "   ALL PRE-FLIGHT CHECKS PASSED! READY FOR LIVE DEMO        " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
