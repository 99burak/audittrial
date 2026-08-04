import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.session import check_database_connection

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    """Report whether the API process is running."""
    return {"status": "ok"}


@app.get("/api/health/ready", tags=["health"])
def readiness() -> JSONResponse:
    """Report whether the API can connect to PostgreSQL."""
    try:
        check_database_connection()
    except SQLAlchemyError:
        logger.warning("Database readiness check failed")
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable"},
        )

    return JSONResponse(content={"status": "ready"})
