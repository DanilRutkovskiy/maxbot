from app.bot.parser import parse_update
from app.schemas.max_webhook import MaxUpdate
from app.schemas.task import AnimationJobPayload
from app.services.max_client import MaxClient
from app.utils.logging import get_logger, log_extra
from app.workers.tasks import process_animation_task

logger = get_logger(__name__)


async def handle_max_update(update: MaxUpdate, request_id: str) -> dict[str, str | None]:
    parsed = parse_update(update)
    if not parsed:
        logger.debug(
            "Update ignored",
            extra=log_extra(update_type=update.update_type),
        )
        return {"task_id": None, "message": "ignored"}

    payload = AnimationJobPayload(
        user_id=parsed.user_id,
        chat_id=parsed.chat_id,
        image_url=parsed.image_url,
        preset=parsed.preset,
        request_id=request_id,
        message_id=parsed.message_id,
    )

    max_client = MaxClient()
    try:
        await max_client.send_text_message(
            parsed.user_id,
            f"🎬 Принял фото! Создаю анимацию (пресет: {parsed.preset})…",
            chat_id=parsed.chat_id,
        )
    except Exception as exc:
        logger.warning(
            "Could not send acknowledgment message",
            extra=log_extra(error=str(exc)),
        )

    async_result = process_animation_task.delay(payload.model_dump())
    logger.info(
        "Animation job enqueued",
        extra=log_extra(
            task_id=async_result.id,
            user_id=parsed.user_id,
            preset=parsed.preset,
        ),
    )
    return {"task_id": async_result.id, "message": "enqueued"}
