from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from app.schemas.task import TaskStatusResponse
from app.workers.celery_app import celery_app

router = APIRouter(tags=["tasks"])


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    result = AsyncResult(task_id, app=celery_app)
    state = result.state
    meta = result.info if isinstance(result.info, dict) else {}
    error: str | None = None

    if result.failed():
        error = str(result.result) if result.result else "Task failed"
    elif isinstance(result.info, Exception):
        error = str(result.info)

    return TaskStatusResponse(
        task_id=task_id,
        status=state,
        ready=result.ready(),
        successful=result.successful() if result.ready() else None,
        result=result.result if result.successful() else None,
        error=error,
        meta=meta if isinstance(meta, dict) else {},
    )
