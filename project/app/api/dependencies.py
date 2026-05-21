from fastapi import Header, HTTPException, Request

from app.config.settings import Settings, get_settings
from app.utils.request_context import generate_request_id, set_request_id


def get_app_settings() -> Settings:
    return get_settings()


async def bind_request_id(request: Request) -> str:
    incoming = request.headers.get("X-Request-ID")
    request_id = incoming or generate_request_id()
    set_request_id(request_id)
    return request_id


async def verify_max_webhook_secret(
    x_max_bot_api_secret: str | None = Header(default=None),
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    if not settings.max_webhook_secret:
        return
    if x_max_bot_api_secret != settings.max_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
