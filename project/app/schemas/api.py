from typing import Any, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    redis: bool


class WebhookResponse(BaseModel):
    ok: bool = True
    task_id: Optional[str] = None
    message: str = "accepted"


class ErrorResponse(BaseModel):
    ok: bool = False
    error: str
    code: str
    detail: Optional[Any] = None
