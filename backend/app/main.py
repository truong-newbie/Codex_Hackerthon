from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .services.ai_service import ai_service
from .routers import auth_router, sops_router, admin_router, training_router

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="ShiftLens API: AI Workforce Training & Simulation Platform (Codex Community Hackathon Hanoi)"
)

# CORS setup for Mobile Expo APK and Appsmith Web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public Health Check
@app.get("/v1/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "ai_mode": settings.AI_MODE,
        "live_ready": ai_service.is_live_ready(),
        "gemini_model": settings.GEMINI_MODEL,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

# Register Routers
app.include_router(auth_router.router)
app.include_router(sops_router.router)
app.include_router(admin_router.router)
app.include_router(training_router.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
