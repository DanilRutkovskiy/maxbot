import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger

from app.utils.request_context import get_request_id, get_task_id


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        record.task_id = get_task_id() or "-"
        return True


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "%(request_id)s %(task_id)s",
        rename_fields={"levelname": "level", "asctime": "timestamp"},
    )
    handler.setFormatter(formatter)
    handler.addFilter(ContextFilter())
    root.addHandler(handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_extra(**kwargs: Any) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    if rid := get_request_id():
        extra["request_id"] = rid
    if tid := get_task_id():
        extra["task_id"] = tid
    extra.update(kwargs)
    return extra
