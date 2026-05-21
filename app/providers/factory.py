from app.config.settings import Settings, get_settings
from app.providers.base import AnimationProvider
from app.providers.fal_provider import FalProvider
from app.providers.liveportrait_provider import LivePortraitLocalProvider
from app.providers.replicate_provider import ReplicateProvider
from app.utils.exceptions import AppError


def get_animation_provider(settings: Settings | None = None) -> AnimationProvider:
    settings = settings or get_settings()
    provider = settings.animation_provider

    if provider == "replicate":
        return ReplicateProvider(settings)
    if provider == "fal":
        return FalProvider()
    if provider == "liveportrait":
        return LivePortraitLocalProvider()

    raise AppError(
        f"Unknown animation provider: {provider}",
        code="unknown_provider",
    )
