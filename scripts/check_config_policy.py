"""Check startup configuration failures without importing the database or app."""

import os
import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / ".deps"))
sys.path.insert(0, str(ROOT / "backend"))
BASE_ENV = {
    "AI_MODE": "stub",
    "ENVIRONMENT": "test",
    "DEMO_MODE": "false",
    "SECRET_KEY": "shiftlens-default-secret-hackathon-2026",
    "CORS_ORIGINS": "",
}


_previous = {name: os.environ.get(name) for name in BASE_ENV}
os.environ.update(BASE_ENV)
import app.config as config  # noqa: E402


def check(overrides: dict[str, str], should_pass: bool, expected: str = "") -> None:
    os.environ.update({**BASE_ENV, **overrides})
    try:
        importlib.reload(config)
        if not should_pass:
            raise AssertionError(f"Expected config failure containing {expected!r}")
    except RuntimeError as error:
        if should_pass or expected not in str(error):
            raise AssertionError(f"Unexpected config failure: {error}") from error


if __name__ == "__main__":
    try:
        check({}, True)
        check({"AI_MODE": "invalid"}, False, "AI_MODE")
        check({"ENVIRONMENT": "production"}, False, "SECRET_KEY")
        check({
            "ENVIRONMENT": "production", "SECRET_KEY": "a" * 48,
        }, False, "CORS_ORIGINS")
        check({
            "ENVIRONMENT": "production", "SECRET_KEY": "a" * 48,
            "CORS_ORIGINS": "https://studio.example.com",
        }, True)
        check({
            "ENVIRONMENT": "production", "SECRET_KEY": "a" * 48,
            "CORS_ORIGINS": "http://studio.example.com",
        }, False, "HTTPS")
        print("Configuration policy checks passed")
    finally:
        for name, value in _previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
