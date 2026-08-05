import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes.auth import router as auth_router
from app.core.config import get_settings
from app.db.session import check_database_connection

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret.get_secret_value(),
    session_cookie="audittrail_session",
    max_age=settings.session_max_age_seconds,
    same_site="lax",
    https_only=settings.session_cookie_secure,
)
app.include_router(auth_router, prefix="/api")


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
