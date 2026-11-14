# Quick test runner for ShiftLens backend
Write-Host "Running backend tests with pytest..." -ForegroundColor Cyan
Set-Location "$PSScriptRoot\..\backend"
python -m pytest -v
Set-Location $PSScriptRoot
