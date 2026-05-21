from typing import Any

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import bind_request_id, verify_max_webhook_secret
from app.bot.handlers import handle_max_update
from app.schemas.api import WebhookResponse
from app.schemas.max_webhook import MaxUpdate
from app.utils.logging import get_logger, log_extra

router = APIRouter(tags=["webhook"])
logger = get_logger(__name__)


@router.post("/webhook/max", response_model=WebhookResponse)
async def max_webhook(
    request: Request,
    _: None = Depends(verify_max_webhook_secret),
    request_id: str = Depends(bind_request_id),
) -> WebhookResponse:
    body: dict[str, Any] = await request.json()
    logger.info(
        "MAX webhook received",
        extra=log_extra(
            request_id=request_id,
            update_type=body.get("update_type"),
        ),
    )

    update = MaxUpdate.model_validate(body)
    result = await handle_max_update(update, request_id)

    return WebhookResponse(
        ok=True,
        task_id=result.get("task_id"),
        message=result.get("message", "accepted"),
    )
