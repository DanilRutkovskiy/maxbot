import uuid
from pathlib import Path

import httpx

from app.config.settings import Settings, get_settings
from app.utils.exceptions import (
    FileTooLargeError,
    InvalidImageError,
    UnsupportedFormatError,
)
from app.utils.logging import get_logger, log_extra

logger = get_logger(__name__)

MIME_TO_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/bmp": ".bmp",
    "image/heic": ".heic",
}


class ImageDownloader:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def download_image(self, url: str) -> Path:
        timeout = httpx.Timeout(self._settings.download_timeout_sec)
        filename = f"{uuid.uuid4().hex}"

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            logger.info("Downloading image", extra=log_extra(url=url))
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                content_type = (
                    response.headers.get("content-type", "").split(";")[0].strip().lower()
                )
                if content_type and content_type not in self._settings.allowed_image_mime_types:
                    raise UnsupportedFormatError(
                        f"Unsupported content type: {content_type}"
                    )

                ext = MIME_TO_EXT.get(content_type, ".jpg")
                dest = self._settings.temp_path / f"{filename}{ext}"
                dest.parent.mkdir(parents=True, exist_ok=True)

                total = 0
                max_bytes = self._settings.max_image_bytes
                with dest.open("wb") as fh:
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        total += len(chunk)
                        if total > max_bytes:
                            dest.unlink(missing_ok=True)
                            raise FileTooLargeError(
                                f"Image exceeds {max_bytes} bytes limit"
                            )
                        fh.write(chunk)

        if dest.stat().st_size == 0:
            dest.unlink(missing_ok=True)
            raise InvalidImageError("Downloaded image is empty")

        await self._validate_image(dest, content_type)
        logger.info(
            "Image downloaded",
            extra=log_extra(path=str(dest), size=dest.stat().st_size),
        )
        return dest

    async def _validate_image(self, path: Path, content_type: str) -> None:
        try:
            from PIL import Image

            with Image.open(path) as img:
                img.verify()
            with Image.open(path) as img:
                width, height = img.size
                if width < 64 or height < 64:
                    raise InvalidImageError("Image resolution is too small")
                if max(width, height) > 8192:
                    raise InvalidImageError("Image resolution is too large")
        except InvalidImageError:
            path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            path.unlink(missing_ok=True)
            if content_type in self._settings.allowed_image_mime_types:
                return
            raise InvalidImageError(f"Invalid image file: {exc}") from exc
