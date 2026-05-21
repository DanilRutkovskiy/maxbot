from typing import Any, Optional

from pydantic import BaseModel, Field


class MaxUser(BaseModel):
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    is_bot: bool = False
    name: Optional[str] = None


class MaxRecipient(BaseModel):
    chat_id: Optional[int] = None
    chat_type: Optional[str] = None
    user_id: Optional[int] = None


class ImageAttachmentPayload(BaseModel):
    url: Optional[str] = None
    token: Optional[str] = None
    photo_id: Optional[int] = None


class MaxAttachment(BaseModel):
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)


class MaxMessageBody(BaseModel):
    mid: Optional[str] = None
    seq: Optional[int] = None
    text: Optional[str] = None
    attachments: list[MaxAttachment] = Field(default_factory=list)


class MaxMessage(BaseModel):
    sender: Optional[MaxUser] = None
    recipient: Optional[MaxRecipient] = None
    timestamp: Optional[int] = None
    body: Optional[MaxMessageBody] = None


class MaxCallback(BaseModel):
    callback_id: Optional[str] = None
    payload: Optional[str] = None
    user: Optional[MaxUser] = None
    timestamp: Optional[int] = None


class MaxUpdate(BaseModel):
    update_type: str
    timestamp: Optional[int] = None
    message: Optional[MaxMessage] = None
    callback: Optional[MaxCallback] = None
    user_locale: Optional[str] = None
