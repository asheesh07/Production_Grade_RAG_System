# health.py
"""
Service health and readiness checks.

Responsibilities:
- Liveness probe (is the service running?)
- Readiness probe (can it serve traffic?)
- Dependency diagnostics (cache, vector DB, LLM)

NO business logic lives here.
"""

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from typing import Dict

from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# -------------------------------------------------
# Helper checks
# -------------------------------------------------
def _check_cache(request: Request) -> bool:
    cache = getattr(request.app.state, "cache", None)
    if not cache:
        return False
    return cache.ping()


def _check_rag_pipeline(request: Request) -> bool:
    """
    Lightweight sanity check that the RAG pipeline is initialized.
    NO heavy calls allowed here.
    """
    return hasattr(request.app.state, "rag_pipeline")


# -------------------------------------------------
# Liveness Probe
# -------------------------------------------------
@router.get(
    "/live",
    summary="Liveness probe",
    response_description="Service is alive",
)
async def liveness() -> Dict[str, str]:
    """
    Liveness check.

    Used by:
    - load balancers
    - container orchestrators

    This should NEVER fail unless the process is dead.
    """
    return {"status": "alive"}


# -------------------------------------------------
# Readiness Probe
# -------------------------------------------------
@router.get(
    "/ready",
    summary="Readiness probe",
    response_description="Service is ready to receive traffic",
)
async def readiness(request: Request):
    """
    Readiness check.

    Used by:
    - Kubernetes
    - autoscalers
    - deployment pipelines

    Fails if critical dependencies are unavailable.
    """

    checks = {
        "cache": _check_cache(request),
        "rag_pipeline": _check_rag_pipeline(request),
    }

    all_ready = all(checks.values())

    if not all_ready:
        logger.warning("Readiness check failed", extra={"checks": checks})
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "checks": checks,
            },
        )

    return {
        "status": "ready",
        "checks": checks,
    }


# -------------------------------------------------
# Dependency Diagnostics
# -------------------------------------------------
@router.get(
    "/dependencies",
    summary="Dependency diagnostics",
    response_description="Detailed dependency status",
)
async def dependencies(request: Request):
    """
    Detailed dependency health.

    Used by:
    - on-call engineers
    - debugging production issues
    - dashboards
    """

    results = {
        "cache": False,
        "rag_pipeline": False,
    }

    try:
        results["cache"] = _check_cache(request)
    except Exception as e:
        logger.error("Cache health check failed", extra={"error": str(e)})

    try:
        results["rag_pipeline"] = _check_rag_pipeline(request)
    except Exception as e:
        logger.error("RAG pipeline check failed", extra={"error": str(e)})

    return {
        "status": "ok" if all(results.values()) else "degraded",
        "dependencies": results,
    }
