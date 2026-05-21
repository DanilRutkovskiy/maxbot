#!/usr/bin/env python3
"""Download LivePortrait driving videos for animation presets."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

BASE = (
    "https://raw.githubusercontent.com/KlingAIResearch/LivePortrait/main"
    "/assets/examples/driving"
)

MAPPING = {
    "smile.mp4": f"{BASE}/d0.mp4",
    "nod.mp4": f"{BASE}/d6.mp4",
    "hello.mp4": f"{BASE}/d3.mp4",
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    dest_dir = root / "assets" / "driving"
    dest_dir.mkdir(parents=True, exist_ok=True)

    for filename, url in MAPPING.items():
        dest = dest_dir / filename
        print(f"Downloading {filename} from {url}")
        urllib.request.urlretrieve(url, dest)
        print(f"  -> {dest} ({dest.stat().st_size} bytes)")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
