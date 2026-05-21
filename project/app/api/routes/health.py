import redis
from fastapi import APIRouter

from app import __version__
from app.config.settings import get_settings
from app.schemas.api import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    redis_ok = False
    try:
        client = redis.from_url(settings.redis_url, socket_connect_timeout=2)
        redis_ok = bool(client.ping())
    except redis.RedisError:
        redis_ok = False

    status = "ok" if redis_ok else "degraded"
    return HealthResponse(status=status, version=__version__, redis=redis_ok)
