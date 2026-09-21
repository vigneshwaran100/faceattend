from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routers.attendance import router as attendance_router
from app.api.routers.audit_log import router as audit_log_router
from app.api.routers.auth import router as auth_router
from app.api.routers.department import router as department_router
from app.api.routers.employee import router as employee_router
from app.api.routers.health import router as health_router
from app.api.routers.team import router as team_router
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.database.session import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Startup phase
    configure_logging()
    logger.info(
        "Application starting | app_name=%s | environment=%s",
        settings.app_name,
        settings.environment,
    )

    # Lightweight database connectivity verification (does not run auto-migrations)
    try:
        with engine.connect() as connection:
            connection.execution_options(timeout=2).execute(text("SELECT 1"))
        logger.info("Database connection verified successfully on startup")
    except Exception as exc:
        logger.error("Database connection verification failed on startup: %s", exc)
        if settings.environment == "production":
            raise RuntimeError(
                "Fatal: Cannot establish database connectivity during production startup"
            ) from exc

    # Pre-initialize FaceEngine model once on application startup
    try:
        from app.api.dependencies import get_face_engine
        get_face_engine()
        logger.info("FaceEngine vision model pre-loaded successfully on startup")
    except Exception as exc:
        logger.warning("Could not pre-load FaceEngine model during startup: %s", exc)

    yield

    # Shutdown phase
    logger.info("Application shutting down; disposing database connection pool")
    try:
        engine.dispose()
        logger.info("Database engine resources released cleanly")
    except Exception as exc:
        logger.warning("Error disposing database engine on shutdown: %s", exc)


app = FastAPI(
    title="Face Recognition Attendance API",
    version="1.0.0",
    debug=(settings.environment == "development"),
    lifespan=lifespan,
)

# CORS Configuration
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Global Exception Handler (sanitizes unhandled internal exceptions)
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled server exception during request %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(attendance_router)
app.include_router(audit_log_router)
app.include_router(employee_router)
app.include_router(department_router)
app.include_router(team_router)