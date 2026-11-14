import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set the database before importing app modules. load_dotenv() does not override it.
# The test suite must never bind to backend/shiftlens.db or a configured live DB.
_test_directory = tempfile.TemporaryDirectory(prefix="shiftlens-tests-")
_test_database_path = Path(_test_directory.name, "test.db").resolve()
os.environ["DATABASE_URL"] = f"sqlite:///{_test_database_path.as_posix()}"
os.environ["AI_MODE"] = "stub"
os.environ["ENVIRONMENT"] = "test"

from app.main import app  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.seed import seed_database  # noqa: E402


def _assert_test_database():
    actual_path = Path(engine.url.database).resolve()
    if actual_path != _test_database_path or actual_path.parent != Path(_test_directory.name).resolve():
        raise RuntimeError("Refusing to reset a database outside the isolated test directory")

@pytest.fixture(autouse=True)
def setup_clean_test_db():
    _assert_test_database()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield

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
