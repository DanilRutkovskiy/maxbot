from app.providers.base import AnimationProvider
from app.utils.exceptions import AppError


class LivePortraitLocalProvider(AnimationProvider):
    """Placeholder for future on-prem LivePortrait inference."""

    name = "liveportrait"

    async def generate_animation(self, image_path: str, preset: str) -> str:
        raise AppError(
            "Local LivePortrait provider is not configured. "
            "Set ANIMATION_PROVIDER=replicate.",
            code="provider_not_implemented",
        )
