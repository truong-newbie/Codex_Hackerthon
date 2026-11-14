import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.seed import seed_database

@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_clean_db():
    # Ensure clean seeded database before tests
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield
    # Restore clean seeded database after tests so demo state is always pristine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()

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
