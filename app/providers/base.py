from abc import ABC, abstractmethod
from typing import Any


class AnimationProvider(ABC):
    """Abstract animation provider (Replicate, Fal.ai, local LivePortrait)."""

    name: str = "base"

    @abstractmethod
    async def generate_animation(
        self,
        image_path: str,
        preset: str,
    ) -> str:
        """
        Generate animated video from a portrait image.

        Args:
            image_path: Local path to source portrait image.
            preset: Animation preset name (smile, nod, hello).

        Returns:
            Local path to generated MP4 video.
        """
        raise NotImplementedError

    def map_preset_inputs(self, preset: str, driving_video_path: str) -> dict[str, Any]:
        """Map preset to provider-specific input parameters."""
        return {
            "face_image": None,
            "driving_video": driving_video_path,
            "preset": preset,
        }
