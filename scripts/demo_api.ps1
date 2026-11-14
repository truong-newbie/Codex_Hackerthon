# ShiftLens E2E API Verification Script (PowerShell)
$baseUrl = "http://localhost:8000"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   SHIFTLENS E2E API VERIFICATION SCRIPT  " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Health Check
Write-Host "`n[1] Checking /v1/health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/v1/health" -Method Get
    Write-Host "OK: Status=$($health.status), AI_Mode=$($health.ai_mode), LiveReady=$($health.live_ready)" -ForegroundColor Green
} catch {
    Write-Host "Failed to connect to $baseUrl. Is the server running?" -ForegroundColor Red
    exit 1
}

# 2. Login as Employee Café A
Write-Host "`n[2] Logging in as Employee Café A (emp_a)..." -ForegroundColor Yellow
$loginBody = @{
    username_or_email = "emp_a"
    password = "ShiftLens@2026"
} | ConvertTo-Json

$loginRes = Invoke-RestMethod -Uri "$baseUrl/v1/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
$token = $loginRes.access_token
$headers = @{ Authorization = "Bearer $token" }
Write-Host "OK: Logged in! User=$($loginRes.user.full_name), Tenant=$($loginRes.user.tenant_name)" -ForegroundColor Green

# 3. Get Active SOPs
Write-Host "`n[3] Fetching SOP list for Café A..." -ForegroundColor Yellow
$sops = Invoke-RestMethod -Uri "$baseUrl/v1/sops" -Method Get -Headers $headers
$sop = $sops[0]
Write-Host "OK: Found SOP: '$($sop.title)', Active Version=v$($sop.active_version.version_no)" -ForegroundColor Green

# 4. Start Training Session (AI Compiler)
Write-Host "`n[4] Starting Training Session (AI Compiler)..." -ForegroundColor Yellow
$startBody = @{ sop_id = $sop.id } | ConvertTo-Json
$session = Invoke-RestMethod -Uri "$baseUrl/v1/training/start" -Method Post -Headers $headers -Body $startBody -ContentType "application/json"
$sessionId = $session.session_id
Write-Host "OK: Session Created ($sessionId)" -ForegroundColor Green
Write-Host "Situation: $($session.module.situation)" -ForegroundColor Gray
Write-Host "Customer Opening: '$($session.module.opening_message)'" -ForegroundColor Magenta

# 5. Send Turn 1
Write-Host "`n[5] Sending Employee Turn 1..." -ForegroundColor Yellow
$turn1Body = @{
    message = "Dạ em chào anh ạ, em rất xin lỗi anh vì sự bất tiện của ly cà phê này! Em xin phép kiểm tra lại ngay ạ."
} | ConvertTo-Json
$turn1 = Invoke-RestMethod -Uri "$baseUrl/v1/training/$sessionId/turn" -Method Post -Headers $headers -Body $turn1Body -ContentType "application/json"
Write-Host "Employee: $($turn1.employee_text)" -ForegroundColor Gray
Write-Host "Customer Reply: '$($turn1.customer_text)'" -ForegroundColor Magenta

# 6. Send Turn 2
Write-Host "`n[6] Sending Employee Turn 2..." -ForegroundColor Yellow
$turn2Body = @{
    message = "Dạ em đã báo bạn bar trưởng pha lại ngay một ly mới theo đúng chuẩn cho anh, anh đợi em 2 phút nhé!"
} | ConvertTo-Json
$turn2 = Invoke-RestMethod -Uri "$baseUrl/v1/training/$sessionId/turn" -Method Post -Headers $headers -Body $turn2Body -ContentType "application/json"
Write-Host "Employee: $($turn2.employee_text)" -ForegroundColor Gray
Write-Host "Customer Reply: '$($turn2.customer_text)'" -ForegroundColor Magenta

# 7. Evaluate Session (Deterministic Scoring + Evidence)
Write-Host "`n[7] Requesting Evaluation (Evidence + Deterministic Scoring)..." -ForegroundColor Yellow
$eval = Invoke-RestMethod -Uri "$baseUrl/v1/training/$sessionId/evaluate" -Method Post -Headers $headers
Write-Host "OK: Evaluation Result Received!" -ForegroundColor Green
Write-Host "Score: $($eval.score)/100 | Passed: $($eval.passed) | Critical Failure: $($eval.critical_failure)" -ForegroundColor ($eval.passed ? "Green" : "Red")
Write-Host "Coaching Tip: $($eval.coaching_tip)" -ForegroundColor Cyan
Write-Host "`nEvidence details:"
foreach ($ev in $eval.evidence) {
    $stat = if ($ev.passed) { "PASSED" } else { "FAILED" }
    Write-Host " - [$stat] $($ev.label) ($($ev.weight)đ): quote='$($ev.exact_quote)' (verified: $($ev.quote_verified))"
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "   E2E DEMO COMPLETED SUCCESSFULLY!       " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
