def test_health_check(client):
    res = client.get("/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "ai_mode" in data

def test_login_success(client):
    res = client.post("/v1/auth/login", json={
        "username_or_email": "emp_a",
        "password": "ShiftLens@2026"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "employee"
    assert data["user"]["tenant_id"] == "tenant-cafe-a"

def test_login_invalid_password(client):
    res = client.post("/v1/auth/login", json={
        "username_or_email": "emp_a",
        "password": "WrongPassword"
    })
    assert res.status_code == 401

def test_get_me(client, auth_headers_emp_a):
    res = client.get("/v1/auth/me", headers=auth_headers_emp_a)
    assert res.status_code == 200
    assert res.json()["username"] == "emp_a"
