from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_bot_token: str = Field(alias="MAX_BOT_TOKEN")
    max_api_url: str = Field(
        default="https://platform-api.max.ru",
        alias="MAX_API_URL",
    )
    max_webhook_secret: str = Field(default="", alias="MAX_WEBHOOK_SECRET")

    replicate_api_token: str = Field(alias="REPLICATE_API_TOKEN")
    replicate_model: str = Field(
        default="fofr/live-portrait",
        alias="REPLICATE_MODEL",
    )

    animation_provider: Literal["replicate", "fal", "liveportrait"] = Field(
        default="replicate",
        alias="ANIMATION_PROVIDER",
    )

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
    )

    storage_path: Path = Field(default=Path("./storage"), alias="STORAGE_PATH")
    temp_path: Path = Field(default=Path("./temp"), alias="TEMP_PATH")
    assets_path: Path = Field(default=Path("./assets"), alias="ASSETS_PATH")

    default_preset: str = Field(default="smile", alias="DEFAULT_PRESET")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    max_image_bytes: int = Field(default=10_485_760, alias="MAX_IMAGE_BYTES")
    download_timeout_sec: float = Field(default=30.0, alias="DOWNLOAD_TIMEOUT_SEC")
    replicate_poll_interval_sec: float = Field(
        default=2.0,
        alias="REPLICATE_POLL_INTERVAL_SEC",
    )
    replicate_poll_timeout_sec: float = Field(
        default=600.0,
        alias="REPLICATE_POLL_TIMEOUT_SEC",
    )
    video_max_duration_sec: float = Field(
        default=15.0,
        alias="VIDEO_MAX_DURATION_SEC",
    )
    video_max_width: int = Field(default=720, alias="VIDEO_MAX_WIDTH")
    generate_gif_preview: bool = Field(default=False, alias="GENERATE_GIF_PREVIEW")

    allowed_image_mime_types: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/bmp",
        "image/heic",
    )

    @property
    def driving_assets_dir(self) -> Path:
        return self.assets_path / "driving"

    def ensure_directories(self) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        self.driving_assets_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()  # type: ignore[call-arg]
    settings.ensure_directories()
    return settings
