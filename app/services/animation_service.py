from pathlib import Path
from typing import Awaitable, Callable, Optional

from app.config.settings import Settings, get_settings
from app.providers.factory import get_animation_provider
from app.services.downloader import ImageDownloader
from app.services.max_client import MaxClient
from app.services.video_service import VideoService
from app.utils.exceptions import AppError
from app.utils.logging import get_logger, log_extra

logger = get_logger(__name__)

USER_MESSAGES: dict[str, str] = {
    "invalid_image": "Не удалось обработать изображение. Пришлите JPG или PNG с чётким лицом.",
    "no_face_detected": "На фото не найдено лицо. Отправьте портрет анфас.",
    "file_too_large": "Файл слишком большой. Максимум 10 МБ.",
    "unsupported_format": "Формат не поддерживается. Используйте JPG, PNG или WEBP.",
    "provider_timeout": "Генерация заняла слишком много времени. Попробуйте позже.",
    "generation_failed": "Не удалось создать анимацию. Попробуйте другое фото.",
    "max_api_error": "Ошибка отправки в MAX. Мы уже разбираемся.",
    "app_error": "Произошла ошибка. Попробуйте ещё раз.",
}


class AnimationPipeline:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._downloader = ImageDownloader(self._settings)
        self._provider = get_animation_provider(self._settings)
        self._video = VideoService(self._settings)
        self._max = MaxClient(self._settings)

    async def run(
        self,
        user_id: int,
        image_url: str,
        preset: str,
        chat_id: int | None = None,
        on_stage: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> dict[str, str]:
        image_path: Path | None = None
        raw_video: Path | None = None
        final_video: Path | None = None

        async def stage(name: str) -> None:
            if on_stage:
                await on_stage(name)

        try:
            await stage("downloading")
            image_path = await self._downloader.download_image(image_url)

            await stage("generating")
            raw_path = await self._provider.generate_animation(
                str(image_path),
                preset,
            )
            raw_video = Path(raw_path)

            await stage("processing")
            final_video = self._video.compress_mp4(raw_video)
            if self._settings.generate_gif_preview:
                self._video.create_gif_preview(final_video)

            await stage("uploading")
            await self._max.send_video(
                user_id=user_id,
                video_path=final_video,
                caption="✨ Ваша анимация готова!",
                chat_id=chat_id,
            )

            stored = self._store_result(final_video, user_id)
            return {"video_path": str(stored), "preset": preset}

        finally:
            for p in (image_path, raw_video):
                if p and p.exists() and p != final_video:
                    p.unlink(missing_ok=True)
            if raw_video and final_video and raw_video != final_video:
                raw_video.unlink(missing_ok=True)

    async def notify_error(
        self,
        user_id: int,
        error: Exception,
        chat_id: int | None = None,
    ) -> None:
        code = getattr(error, "code", "app_error")
        text = USER_MESSAGES.get(code, USER_MESSAGES["app_error"])
        try:
            await self._max.send_text_message(user_id, text, chat_id=chat_id)
        except Exception as send_exc:
            logger.error(
                "Failed to notify user about error",
                extra=log_extra(error=str(send_exc)),
                exc_info=True,
            )

    def _store_result(self, video: Path, user_id: int) -> Path:
        dest_dir = self._settings.storage_path / str(user_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / video.name
        if video.resolve() != dest.resolve():
            dest.write_bytes(video.read_bytes())
        return dest
