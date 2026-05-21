from pathlib import Path

from app.config.settings import Settings
from app.utils.exceptions import AppError

PRESET_FILES: dict[str, str] = {
    "smile": "smile.mp4",
    "nod": "nod.mp4",
    "hello": "hello.mp4",
}

PRESET_REPLICATE_INPUTS: dict[str, dict[str, float | int | bool]] = {
    "smile": {
        "live_portrait_dsize": 512,
        "live_portrait_scale": 2.3,
        "video_frame_load_cap": 128,
        "video_select_every_n_frames": 1,
    },
    "nod": {
        "live_portrait_dsize": 512,
        "live_portrait_scale": 2.3,
        "video_frame_load_cap": 96,
        "video_select_every_n_frames": 1,
    },
    "hello": {
        "live_portrait_dsize": 512,
        "live_portrait_scale": 2.3,
        "video_frame_load_cap": 128,
        "video_select_every_n_frames": 2,
    },
}


def resolve_driving_video(settings: Settings, preset: str) -> Path:
    filename = PRESET_FILES.get(preset)
    if not filename:
        raise AppError(f"Unknown preset: {preset}", code="unknown_preset")
    path = settings.driving_assets_dir / filename
    if not path.is_file():
        raise AppError(
            f"Driving video for preset '{preset}' not found: {path}",
            code="preset_asset_missing",
        )
    return path


def get_replicate_extra_inputs(preset: str) -> dict[str, float | int | bool]:
    return PRESET_REPLICATE_INPUTS.get(preset, PRESET_REPLICATE_INPUTS["smile"])
