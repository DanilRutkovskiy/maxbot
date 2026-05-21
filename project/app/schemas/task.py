from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    DOWNLOADING = "DOWNLOADING"
    GENERATING = "GENERATING"
    PROCESSING = "PROCESSING"
    UPLOADING = "UPLOADING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"


class AnimationJobPayload(BaseModel):
    user_id: int
    chat_id: Optional[int] = None
    image_url: str
    preset: str = "smile"
    request_id: str
    message_id: Optional[str] = None


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    ready: bool
    successful: Optional[bool] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    meta: dict[str, Any] = Field(default_factory=dict)
