from __future__ import annotations

from pathlib import Path

import requests

from src.logger import logger


VIDEO_DIR = Path("assets/generated_video")
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def get_video_output_path(video_id: str, suffix: str = ".mp4") -> Path:
    safe_video_id = video_id.strip().replace("/", "_").replace("\\", "_")
    return VIDEO_DIR / f"{safe_video_id}{suffix}"


def download_video_to_cache(video_url: str, video_id: str) -> str:
    output_path = get_video_output_path(video_id)

    logger.info("Caching avatar video {} to {}", video_id, output_path)

    response = requests.get(video_url, timeout=60)
    response.raise_for_status()

    output_path.write_bytes(response.content)

    logger.success("Avatar video cached successfully at {}", output_path)

    return str(output_path)
