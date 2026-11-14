import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "ShiftLens API"
    VERSION: str = "1.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
    CORS_ORIGINS: list[str] = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
    
    # AI settings
    AI_MODE: str = os.getenv("AI_MODE", "stub").lower()  # "live" or "stub"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    OPERATION_LEASE_SECONDS: int = int(os.getenv("OPERATION_LEASE_SECONDS", "90"))
    
    # DB settings
    # Anchor the default database to backend/, independent of the launch cwd.
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'shiftlens.db').as_posix()}")
    
    # Auth settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "shiftlens-default-secret-hackathon-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days for demo ease

settings = Settings()

if settings.AI_MODE not in {"live", "stub"}:
    raise RuntimeError("AI_MODE must be 'live' or 'stub'")
if not 30 <= settings.OPERATION_LEASE_SECONDS <= 600:
    raise RuntimeError("OPERATION_LEASE_SECONDS must be between 30 and 600")

if settings.ENVIRONMENT not in {"development", "test", "staging", "production"}:
    raise RuntimeError("ENVIRONMENT must be development, test, staging, or production")

if settings.ENVIRONMENT == "production":
    if settings.DEMO_MODE:
        raise RuntimeError("DEMO_MODE must be disabled in production")
    if settings.SECRET_KEY == "shiftlens-default-secret-hackathon-2026" or len(settings.SECRET_KEY) < 32:
        raise RuntimeError("Production requires a strong, non-demo SECRET_KEY")
    if not settings.CORS_ORIGINS or "*" in settings.CORS_ORIGINS:
        raise RuntimeError("Production requires an explicit CORS_ORIGINS allowlist")

if settings.ENVIRONMENT in {"staging", "production"}:
    if any(not origin.startswith("https://") for origin in settings.CORS_ORIGINS):
        raise RuntimeError("Staging and production CORS_ORIGINS must use HTTPS")


def has_live_key() -> bool:
    key = settings.GEMINI_API_KEY.strip()
    return bool(key and key.lower() not in {
        "your_gemini_api_key_here", "your-api-key", "replace_me", "changeme"
    })
