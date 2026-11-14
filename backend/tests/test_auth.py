import hashlib

from app.auth import hash_password, verify_password
from app.config import settings
from app.database import SessionLocal
from app.models import Account


def test_password_hash_uses_unique_salts():
    first = hash_password("same-password")
    second = hash_password("same-password")
    assert first != second
    assert verify_password("same-password", first)
    assert not verify_password("wrong-password", first)


def test_legacy_hash_upgraded_after_login(client):
    legacy = hashlib.pbkdf2_hmac("sha256", b"ShiftLens@2026", b"shiftlens_salt_2026", 100000).hex()
    with SessionLocal() as db:
        account = db.query(Account).filter(Account.username == "emp_a").one()
        account.password_hash = legacy
        db.commit()
    response = client.post("/v1/auth/login", json={"username_or_email": "emp_a", "password": "ShiftLens@2026"})
    assert response.status_code == 200
    with SessionLocal() as db:
        account = db.query(Account).filter(Account.username == "emp_a").one()
        assert account.password_hash.startswith("pbkdf2_sha256$")
        assert account.password_hash != legacy


def test_health_check(client):
    res = client.get("/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "ai_mode" in data


def test_validation_error_excludes_input_and_has_request_id(client):
    response = client.post("/v1/auth/login", json={"username_or_email": "x", "password": ["sensitive-password"]})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert "sensitive-password" not in response.text


def test_studio_hides_demo_credentials_when_demo_mode_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    response = client.get("/studio")
    assert response.status_code == 200
    assert "ShiftLens@2026" not in response.text
    assert "quickLogin('manager_a')" not in response.text
    assert "Nạp Mẫu Demo SOP v2" not in response.text

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
