import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers_emp_a(client):
    res = client.post("/v1/auth/login", json={
        "username_or_email": "emp_a",
        "password": "ShiftLens@2026"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_manager_a(client):
    res = client.post("/v1/auth/login", json={
        "username_or_email": "manager_a",
        "password": "ShiftLens@2026"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_emp_b(client):
    res = client.post("/v1/auth/login", json={
        "username_or_email": "emp_b",
        "password": "ShiftLens@2026"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
