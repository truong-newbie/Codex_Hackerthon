import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "ShiftLens API"
    VERSION: str = "1.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # AI settings
    AI_MODE: str = os.getenv("AI_MODE", "stub").lower()  # "live" or "stub"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # DB settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./shiftlens.db")
    
    # Auth settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "shiftlens-default-secret-hackathon-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days for demo ease

settings = Settings()
