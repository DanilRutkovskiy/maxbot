import asyncio
from typing import Any, Callable, Coroutine

from celery import Task
from app.schemas.task import AnimationJobPayload, TaskStatus
from app.services.animation_service import AnimationPipeline
from app.utils.exceptions import AppError
from app.utils.logging import get_logger, log_extra
from app.utils.request_context import set_request_id, set_task_id
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


class AnimationTask(Task):
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True
    max_retries = 3


def _run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    return asyncio.run(coro)


@celery_app.task(
    bind=True,
    base=AnimationTask,
    name="animation.process",
    acks_late=True,
)
def process_animation_task(self: AnimationTask, payload_dict: dict[str, Any]) -> dict[str, Any]:
    payload = AnimationJobPayload.model_validate(payload_dict)
    set_request_id(payload.request_id)
    set_task_id(self.request.id)

    pipeline = AnimationPipeline()

    async def on_stage(stage: str) -> None:
        self.update_state(
            state=TaskStatus.STARTED.value,
            meta={
                "stage": stage,
                "request_id": payload.request_id,
                "user_id": payload.user_id,
                "preset": payload.preset,
            },
        )

    try:
        self.update_state(
            state=TaskStatus.STARTED.value,
            meta={"stage": "queued", "request_id": payload.request_id},
        )
        result = _run_async(
            pipeline.run(
                user_id=payload.user_id,
                image_url=payload.image_url,
                preset=payload.preset,
                chat_id=payload.chat_id,
                on_stage=on_stage,
            )
        )
        logger.info(
            "Animation task completed",
            extra=log_extra(task_id=self.request.id, result=result),
        )
        return result
    except Exception as exc:
        logger.error(
            "Animation task failed",
            extra=log_extra(task_id=self.request.id, error=str(exc)),
            exc_info=True,
        )
        _run_async(
            pipeline.notify_error(
                payload.user_id,
                exc,
                chat_id=payload.chat_id,
            )
        )
        if self.request.retries < self.max_retries and _is_retryable(exc):
            raise self.retry(exc=exc)
        raise


def _is_retryable(exc: Exception) -> bool:
    code = getattr(exc, "code", "")
    return code in ("provider_timeout", "max_api_error", "generation_failed")


@celery_app.task(name="animation.ping")
def ping() -> str:
    return "pong"
