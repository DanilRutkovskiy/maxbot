import re
from typing import Optional

from app.config.settings import get_settings
from app.models.task import ParsedImageMessage
from app.schemas.max_webhook import MaxAttachment, MaxUpdate
from app.utils.logging import get_logger

logger = get_logger(__name__)

PRESET_PATTERN = re.compile(r"(?:/preset|preset:)\s*(smile|nod|hello)", re.IGNORECASE)


def parse_update(update: MaxUpdate) -> Optional[ParsedImageMessage]:
    if update.update_type != "message_created":
        return None

    message = update.message
    if not message or not message.body:
        return None

    sender = message.sender
    if not sender or sender.is_bot:
        return None

    image_url = _extract_image_url(message.body.attachments)
    if not image_url:
        return None

    preset = _extract_preset(message.body.text)
    chat_id = _resolve_chat_id(message.recipient, sender.user_id)

    return ParsedImageMessage(
        user_id=sender.user_id,
        chat_id=chat_id,
        image_url=image_url,
        preset=preset,
        message_id=message.body.mid,
        update_type=update.update_type,
    )


def _extract_image_url(attachments: list[MaxAttachment]) -> Optional[str]:
    for attachment in attachments:
        if attachment.type != "image":
            continue
        payload = attachment.payload or {}
        url = payload.get("url")
        if isinstance(url, str) and url.startswith("http"):
            return url
    return None


def _extract_preset(text: Optional[str]) -> str:
    settings = get_settings()
    if not text:
        return settings.default_preset
    match = PRESET_PATTERN.search(text)
    if match:
        return match.group(1).lower()
    lowered = text.strip().lower()
    if lowered in ("smile", "nod", "hello"):
        return lowered
    return settings.default_preset


def _resolve_chat_id(recipient, fallback_user_id: int) -> Optional[int]:
    if not recipient:
        return None
    if recipient.chat_type == "dialog":
        return recipient.user_id or fallback_user_id
    return recipient.chat_id
