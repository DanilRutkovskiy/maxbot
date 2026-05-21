from app.providers.base import AnimationProvider
from app.utils.exceptions import AppError


class FalProvider(AnimationProvider):
    """Placeholder for future Fal.ai integration."""

    name = "fal"

    async def generate_animation(self, image_path: str, preset: str) -> str:
        raise AppError(
            "Fal.ai provider is not configured. Set ANIMATION_PROVIDER=replicate.",
            code="provider_not_implemented",
        )
