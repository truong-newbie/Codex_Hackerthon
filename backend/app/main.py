import logging
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import has_live_key, settings
from .services.ai_service import ai_service
from .services.operation_service import OperationError
from .routers import auth_router, sops_router, admin_router, training_router, studio_router, operations_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="ShiftLens API: AI Workforce Training & Simulation Platform (Codex Community Hackathon Hanoi)"
)

logger = logging.getLogger(__name__)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    request_id = request.state.request_id
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": f"HTTP_{exc.status_code}", "request_id": request_id},
        headers={**(exc.headers or {}), "X-Request-ID": request_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    details = [{"loc": error["loc"], "msg": error["msg"], "type": error["type"]} for error in exc.errors()]
    request_id = request.state.request_id
    return JSONResponse(
        status_code=422,
        content={"detail": details, "code": "VALIDATION_ERROR", "request_id": request_id},
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(OperationError)
async def operation_error(request: Request, exc: OperationError):
    request_id = request.state.request_id
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc), "code": exc.code, "request_id": request_id,
            "operation_id": exc.operation_id,
            "retryable": exc.code in {"OPERATION_IN_PROGRESS", "SESSION_BUSY", "STALE_SESSION"},
        },
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(Exception)
async def internal_error(request: Request, exc: Exception):
    request_id = request.state.request_id
    logger.error("Unhandled request error: %s request_id=%s", type(exc).__name__, request_id)
    return JSONResponse(
        status_code=500,
        content={"detail": "Lỗi máy chủ. Vui lòng thử lại sau.", "code": "INTERNAL_ERROR", "request_id": request_id},
        headers={"X-Request-ID": request_id},
    )

# CORS setup for Mobile Expo APK and Appsmith Web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=bool(settings.CORS_ORIGINS),
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
        "live_configured": settings.AI_MODE == "live" and has_live_key(),
        "ai_status": "stub" if settings.AI_MODE == "stub" else ("unverified" if has_live_key() else "unavailable"),
        "gemini_model": settings.GEMINI_MODEL,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

# Register Routers
app.include_router(auth_router.router)
app.include_router(sops_router.router)
app.include_router(admin_router.router)
app.include_router(training_router.router)
app.include_router(operations_router.router)
app.include_router(studio_router.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
