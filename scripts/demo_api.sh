#!/usr/bin/env bash
set -e

BASE_URL="http://localhost:8000"

echo "=== ShiftLens API Sanity Demo ==="

# 1. Health
echo "[1] Checking health..."
curl -s "$BASE_URL/v1/health" | python3 -m json.tool

# 2. Login
echo -e "\n[2] Logging in as emp_a..."
TOKEN_RES=$(curl -s -X POST "$BASE_URL/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"emp_a","password":"ShiftLens@2026"}')
TOKEN=$(echo "$TOKEN_RES" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 3. List SOPs
echo -e "\n[3] Getting SOPs..."
SOP_RES=$(curl -s -X GET "$BASE_URL/v1/sops" -H "Authorization: Bearer $TOKEN")
SOP_ID=$(echo "$SOP_RES" | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")

# 4. Start training
echo -e "\n[4] Starting training session..."
SESSION_RES=$(curl -s -X POST "$BASE_URL/v1/training/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"sop_id\":\"$SOP_ID\"}")
SESSION_ID=$(echo "$SESSION_RES" | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")

# 5. Turn 1
echo -e "\n[5] Sending Turn 1..."
curl -s -X POST "$BASE_URL/v1/training/$SESSION_ID/turn" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Dạ em rất xin lỗi anh vì sự cố đồ uống này ạ, em kiểm tra ngay cho anh."}' | python3 -m json.tool

# 6. Evaluate
echo -e "\n[6] Evaluating session..."
curl -s -X POST "$BASE_URL/v1/training/$SESSION_ID/evaluate" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n=== Demo Completed ==="
