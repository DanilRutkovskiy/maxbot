import contextvars
import uuid
from typing import Optional

_request_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id",
    default=None,
)
_task_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "task_id",
    default=None,
)


def generate_request_id() -> str:
    return str(uuid.uuid4())


def set_request_id(request_id: str) -> contextvars.Token[Optional[str]]:
    return _request_id.set(request_id)


def get_request_id() -> Optional[str]:
    return _request_id.get()


def set_task_id(task_id: str) -> contextvars.Token[Optional[str]]:
    return _task_id.set(task_id)


def get_task_id() -> Optional[str]:
    return _task_id.get()


def reset_request_id(token: contextvars.Token[Optional[str]]) -> None:
    _request_id.reset(token)


def reset_task_id(token: contextvars.Token[Optional[str]]) -> None:
    _task_id.reset(token)
