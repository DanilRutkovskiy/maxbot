from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ParsedImageMessage:
    user_id: int
    chat_id: Optional[int]
    image_url: str
    preset: str
    message_id: Optional[str] = None
    update_type: str = "message_created"


@dataclass
class TaskMeta:
    status: str
    request_id: str
    user_id: int
    preset: str
    stage: str = "queued"
    error: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)
