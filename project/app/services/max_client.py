import asyncio
from pathlib import Path
from typing import Any, Optional

import httpx

from app.config.settings import Settings, get_settings
from app.utils.exceptions import MaxApiError
from app.utils.logging import get_logger, log_extra

logger = get_logger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 1.5


class MaxClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._base_url = self._settings.max_api_url.rstrip("/")
        self._headers = {
            "Authorization": self._settings.max_bot_token,
            "Content-Type": "application/json",
        }

    async def send_text_message(
        self,
        user_id: int,
        text: str,
        chat_id: Optional[int] = None,
        format: Optional[str] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"text": text}
        if format:
            body["format"] = format
        return await self._post_message(body, user_id=user_id, chat_id=chat_id)

    async def send_video(
        self,
        user_id: int,
        video_path: Path,
        caption: Optional[str] = None,
        chat_id: Optional[int] = None,
    ) -> dict[str, Any]:
        token = await self.upload_media(video_path, media_type="video")
        attachments = [
            {
                "type": "video",
                "payload": {"token": token},
            }
        ]
        body: dict[str, Any] = {"attachments": attachments}
        if caption:
            body["text"] = caption
        await self._wait_for_attachment_ready()
        return await self._post_message(body, user_id=user_id, chat_id=chat_id)

    async def upload_media(self, file_path: Path, media_type: str = "video") -> str:
        upload_meta = await self._request(
            "POST",
            "/uploads",
            params={"type": media_type},
        )
        upload_url = upload_meta.get("url")
        if not upload_url:
            raise MaxApiError("MAX /uploads did not return upload URL")

        token = await self._upload_file_multipart(upload_url, file_path)
        if token:
            return token

        if media_type == "image" and "token=" in upload_url:
            return upload_url.split("token=")[-1].split("&")[0]

        raise MaxApiError("Failed to obtain media token after upload")

    async def _upload_file_multipart(self, upload_url: str, file_path: Path) -> Optional[str]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            with file_path.open("rb") as fh:
                files = {"data": (file_path.name, fh, "application/octet-stream")}
                response = await client.post(upload_url, files=files)
        if response.status_code >= 400:
            raise MaxApiError(
                f"File upload failed: {response.status_code} {response.text[:300]}"
            )
        data = response.json() if response.content else {}
        token = data.get("token")
        if isinstance(token, str):
            return token
        retval = data.get("retval")
        if isinstance(retval, str):
            return retval
        return None

    async def _post_message(
        self,
        body: dict[str, Any],
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if user_id is not None:
            params["user_id"] = user_id
        if chat_id is not None:
            params["chat_id"] = chat_id
        return await self._request("POST", "/messages", params=params, json_body=body)

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        json_body: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        last_error: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.request(
                        method,
                        url,
                        headers=self._headers,
                        params=params,
                        json=json_body,
                    )
                if response.status_code == 429:
                    await asyncio.sleep(RETRY_BACKOFF * attempt)
                    continue
                if response.status_code >= 400:
                    raise MaxApiError(
                        f"MAX API {method} {path} -> {response.status_code}: "
                        f"{response.text[:500]}"
                    )
                return response.json() if response.content else {}
            except (httpx.HTTPError, MaxApiError) as exc:
                last_error = exc
                logger.warning(
                    "MAX API request failed, retrying",
                    extra=log_extra(attempt=attempt, path=path, error=str(exc)),
                )
                await asyncio.sleep(RETRY_BACKOFF * attempt)

        raise MaxApiError(str(last_error) if last_error else "MAX API request failed")

    @staticmethod
    async def _wait_for_attachment_ready(delay: float = 2.0) -> None:
        await asyncio.sleep(delay)
