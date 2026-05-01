from fastapi import APIRouter

from app.repositories.database_repository import DatabaseRepository

router = APIRouter()
repository = DatabaseRepository()

@router.get("/healthz/live")
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/healthz/ready")
def readiness() -> dict[str, bool | str]:
    checks = repository.readiness()
    status = "ready" if all(checks.values()) else "degraded"
    return {"status": status, **checks}
