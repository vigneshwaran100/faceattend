import logging
import socket
from typing import Any
from urllib.parse import urlsplit

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.config import settings
from app.database.session import engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


def _check_database() -> dict[str, Any]:
    try:
        with engine.connect() as connection:
            connection.execution_options(timeout=2).execute(text("SELECT 1"))
        return {"status": "healthy", "critical": True}
    except Exception as exc:
        logger.warning("Readiness check: database unreachable: %s", exc)
        return {"status": "unavailable", "critical": True}


def _check_milvus() -> dict[str, Any]:
    try:
        parsed = urlsplit(settings.milvus_uri)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 19530)
        with socket.create_connection((host, port), timeout=1.5):
            pass
        return {"status": "healthy", "critical": False}
    except Exception as exc:
        logger.warning("Readiness check: milvus unreachable: %s", exc)
        return {
            "status": "unavailable",
            "critical": False,
            "message": "Face enrollment non-operational; core auth & attendance operational",
        }


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> dict[str, str]:
    """Liveness probe: answers whether the application process is running."""
    return {
        "status": "healthy",
    }


@router.get("/ready")
def readiness_check(response: Response) -> dict[str, Any]:
    """
    Readiness probe: answers whether dependencies are ready to receive traffic.

    - PostgreSQL is critical for core API functionality (503 if unreachable).
    - Milvus is non-critical for core attendance/auth (reports 'degraded' 200 if unreachable).
    - Degraded state must NOT be interpreted as Milvus fully operational.
    """
    db_result = _check_database()
    milvus_result = _check_milvus()

    is_db_healthy = db_result["status"] == "healthy"
    is_milvus_healthy = milvus_result["status"] == "healthy"

    if not is_db_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "not_ready"
        is_ready = False
    elif not is_milvus_healthy:
        response.status_code = status.HTTP_200_OK
        overall_status = "degraded"
        is_ready = True
    else:
        response.status_code = status.HTTP_200_OK
        overall_status = "ready"
        is_ready = True

    return {
        "status": overall_status,
        "ready": is_ready,
        "dependencies": {
            "database": db_result,
            "milvus": milvus_result,
        },
    }