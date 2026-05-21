import asyncio
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import replicate

from app.config.settings import Settings, get_settings
from app.providers.base import AnimationProvider
from app.providers.presets import get_replicate_extra_inputs, resolve_driving_video
from app.utils.exceptions import (
    GenerationFailedError,
    NoFaceDetectedError,
    ProviderTimeoutError,
)
from app.utils.logging import get_logger, log_extra

logger = get_logger(__name__)

FACE_ERROR_MARKERS = (
    "no face",
    "face not found",
    "failed to detect",
    "insightface",
    "face detection",
)


class ReplicateProvider(AnimationProvider):
    name = "replicate"

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = replicate.Client(api_token=self._settings.replicate_api_token)

    async def generate_animation(self, image_path: str, preset: str) -> str:
        driving_path = resolve_driving_video(self._settings, preset)
        output_path = (
            self._settings.temp_path / f"replicate_{uuid.uuid4().hex}.mp4"
        )
        return await asyncio.to_thread(
            self._run_prediction_sync,
            image_path,
            str(driving_path),
            preset,
            str(output_path),
        )

    def _run_prediction_sync(
        self,
        image_path: str,
        driving_path: str,
        preset: str,
        output_path: str,
    ) -> str:
        extra = get_replicate_extra_inputs(preset)
        model = self._settings.replicate_model

        with open(image_path, "rb") as face_file, open(driving_path, "rb") as drive_file:
            inputs: dict[str, Any] = {
                "face_image": face_file,
                "driving_video": drive_file,
                **extra,
            }
            logger.info(
                "Starting Replicate prediction",
                extra=log_extra(model=model, preset=preset),
            )
            prediction = self._client.predictions.create(
                model=model,
                input=inputs,
            )

        prediction = self._poll_prediction(prediction.id)
        if prediction.status == "failed":
            error_text = str(prediction.error or "unknown error")
            self._raise_mapped_error(error_text)

        output = prediction.output
        return self._download_output_sync(output, output_path)

    def _poll_prediction(self, prediction_id: str) -> Any:
        deadline = time.monotonic() + self._settings.replicate_poll_timeout_sec
        interval = self._settings.replicate_poll_interval_sec

        while time.monotonic() < deadline:
            prediction = self._client.predictions.get(prediction_id)
            if prediction.status in ("succeeded", "failed", "canceled"):
                return prediction
            time.sleep(interval)

        raise ProviderTimeoutError(
            f"Replicate prediction {prediction_id} timed out after "
            f"{self._settings.replicate_poll_timeout_sec}s"
        )

    def _raise_mapped_error(self, error_text: str) -> None:
        lowered = error_text.lower()
        if any(marker in lowered for marker in FACE_ERROR_MARKERS):
            raise NoFaceDetectedError(error_text)
        raise GenerationFailedError(error_text)

    def _download_output_sync(self, output: Any, output_path: str) -> str:
        urls = self._extract_output_urls(output)
        if not urls:
            raise GenerationFailedError("Replicate returned empty output")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if len(urls) == 1 and self._looks_like_video(urls[0]):
            self._download_url_sync(urls[0], path)
            return str(path)

        frames_dir = path.parent / f"frames_{uuid.uuid4().hex}"
        frames_dir.mkdir(parents=True, exist_ok=True)
        frame_paths: list[Path] = []
        for idx, url in enumerate(urls):
            frame_path = frames_dir / f"frame_{idx:05d}.png"
            self._download_url_sync(url, frame_path)
            frame_paths.append(frame_path)

        from app.services.video_service import VideoService

        video_service = VideoService(self._settings)
        video_service.frames_to_video(frame_paths, path)
        for fp in frame_paths:
            fp.unlink(missing_ok=True)
        frames_dir.rmdir()
        return str(path)

    @staticmethod
    def _looks_like_video(url: str) -> bool:
        lowered = url.lower()
        return lowered.endswith(".mp4") or lowered.endswith(".webm") or "/video" in lowered

    def _extract_output_urls(self, output: Any) -> list[str]:
        if output is None:
            return []
        if isinstance(output, str):
            return [output]
        if isinstance(output, (list, tuple)):
            urls: list[str] = []
            for item in output:
                urls.extend(self._extract_output_urls(item))
            return urls
        if hasattr(output, "url"):
            return [str(getattr(output, "url"))]
        return [str(output)]

    def _download_url_sync(self, url: str, dest: Path) -> None:
        with httpx.Client(timeout=self._settings.download_timeout_sec) as client:
            response = client.get(url)
            response.raise_for_status()
            dest.write_bytes(response.content)
