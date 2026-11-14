param(
    [string]$PythonExe
)

$ErrorActionPreference = "Stop"
$backendDir = Join-Path (Split-Path -Parent $PSScriptRoot) "backend"

if (-not $PythonExe) {
    foreach ($candidate in @("python", "py")) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            $PythonExe = $command.Source
            break
        }
    }
}

if (-not $PythonExe -or -not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python executable not found. Pass -PythonExe with the absolute path to python.exe."
}

Push-Location $backendDir
try {
    & $PythonExe -m pytest -v
    if ($LASTEXITCODE -ne 0) {
        throw "Backend tests failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}
