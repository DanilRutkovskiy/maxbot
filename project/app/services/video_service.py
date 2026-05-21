import subprocess
import uuid
from pathlib import Path
from typing import Optional

from app.config.settings import Settings, get_settings
from app.utils.exceptions import AppError
from app.utils.logging import get_logger, log_extra

logger = get_logger(__name__)


class VideoService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def compress_mp4(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        output = output_path or (
            self._settings.temp_path / f"compressed_{uuid.uuid4().hex}.mp4"
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        scale = f"scale='min({self._settings.video_max_width},iw)':-2"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vf",
            scale,
            "-t",
            str(self._settings.video_max_duration_sec),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output),
        ]
        self._run_ffmpeg(cmd, "compress_mp4")
        logger.info("Video compressed", extra=log_extra(output=str(output)))
        return output

    def extract_thumbnail(self, video_path: Path, output_path: Optional[Path] = None) -> Path:
        output = output_path or (
            self._settings.temp_path / f"thumb_{uuid.uuid4().hex}.jpg"
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-ss",
            "00:00:00.500",
            "-vframes",
            "1",
            "-q:v",
            "2",
            str(output),
        ]
        self._run_ffmpeg(cmd, "extract_thumbnail")
        return output

    def create_gif_preview(
        self,
        video_path: Path,
        output_path: Optional[Path] = None,
    ) -> Path:
        output = output_path or (
            self._settings.temp_path / f"preview_{uuid.uuid4().hex}.gif"
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-t",
            "3",
            "-vf",
            "fps=10,scale=320:-1:flags=lanczos",
            "-loop",
            "0",
            str(output),
        ]
        self._run_ffmpeg(cmd, "create_gif_preview")
        return output

    def limit_duration(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        output = output_path or (
            self._settings.temp_path / f"trimmed_{uuid.uuid4().hex}.mp4"
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-t",
            str(self._settings.video_max_duration_sec),
            "-c",
            "copy",
            str(output),
        ]
        self._run_ffmpeg(cmd, "limit_duration", allow_copy_fail=True)
        if not output.exists() or output.stat().st_size == 0:
            return self.compress_mp4(input_path, output)
        return output

    def frames_to_video(self, frame_paths: list[Path], output_path: Path) -> Path:
        if not frame_paths:
            raise AppError("No frames to encode", code="no_frames")
        list_file = output_path.parent / f"frames_list_{uuid.uuid4().hex}.txt"
        with list_file.open("w", encoding="utf-8") as fh:
            for frame in frame_paths:
                fh.write(f"file '{frame.as_posix()}'\n")
                fh.write("duration 0.04\n")
            fh.write(f"file '{frame_paths[-1].as_posix()}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-vf",
            f"scale='min({self._settings.video_max_width},iw)':-2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        try:
            self._run_ffmpeg(cmd, "frames_to_video")
        finally:
            list_file.unlink(missing_ok=True)
        return output_path

    def _run_ffmpeg(
        self,
        cmd: list[str],
        operation: str,
        allow_copy_fail: bool = False,
    ) -> None:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 and not allow_copy_fail:
            logger.error(
                "FFmpeg failed",
                extra=log_extra(
                    operation=operation,
                    stderr=result.stderr[-2000:],
                ),
            )
            raise AppError(
                f"FFmpeg {operation} failed: {result.stderr[-500:]}",
                code="ffmpeg_error",
            )
