from __future__ import annotations

import os
import time
from pathlib import Path
from uuid import uuid4

import requests
from dotenv import load_dotenv

from src.avatar_models import AvatarJob, AvatarResult, AvatarStatus
from src.custom_exception import VoiceAssistantException
from src.logger import logger
from src.video_cache import download_video_to_cache


load_dotenv()


class AvatarConfig:
    PROVIDER = os.getenv("AVATAR_PROVIDER", "tavus")
    API_KEY = os.getenv("TAVUS_API_KEY")
    REPLICA_ID = os.getenv("TAVUS_REPLICA_ID")
    BASE_URL = os.getenv("TAVUS_BASE_URL", "https://tavusapi.com")
    POLL_INTERVAL_SECONDS = int(os.getenv("AVATAR_POLL_INTERVAL_SECONDS", "5"))
    TIMEOUT_SECONDS = int(os.getenv("AVATAR_TIMEOUT_SECONDS", "600"))
    FAST = os.getenv("TAVUS_FAST_MODE", "false").strip().lower() == "true"


def get_avatar_status() -> AvatarStatus:
    if AvatarConfig.PROVIDER.lower() != "tavus":
        return AvatarStatus(False, AvatarConfig.PROVIDER, "Only Tavus is supported in this MVP.")

    if not AvatarConfig.API_KEY:
        return AvatarStatus(False, AvatarConfig.PROVIDER, "Missing TAVUS_API_KEY")

    if not AvatarConfig.REPLICA_ID:
        return AvatarStatus(False, AvatarConfig.PROVIDER, "Missing TAVUS_REPLICA_ID")

    return AvatarStatus(True, AvatarConfig.PROVIDER, "Configured")


def generate_audio_filename() -> Path:
    folder = Path("assets/generated_audio")
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{uuid4()}.mp3"


def _build_headers() -> dict[str, str]:
    return {
        "x-api-key": AvatarConfig.API_KEY or "",
        "Content-Type": "application/json",
    }


def _extract_job(response_payload: dict) -> AvatarJob:
    data = response_payload.get("data")
    if not isinstance(data, dict):
        data = {}

    status = (
        response_payload.get("status")
        or data.get("status")
        or "unknown"
    )

    hosted_url = (
        response_payload.get("hosted_url")
        or data.get("hosted_url")
    )
    download_url = (
        response_payload.get("download_url")
        or data.get("download_url")
    )
    stream_url = (
        response_payload.get("stream_url")
        or data.get("stream_url")
    )
    status_details = (
        response_payload.get("status_details")
        or data.get("status_details")
    )
    error_details = (
        response_payload.get("error_details")
        or response_payload.get("error_message")
        or data.get("error_details")
        or data.get("error_message")
    )

    return AvatarJob(
        video_id=(
            response_payload.get("video_id")
            or response_payload.get("id")
            or data.get("video_id")
            or data.get("id")
            or ""
        ),
        status=status,
        hosted_url=hosted_url,
        download_url=download_url,
        stream_url=stream_url,
        status_details=status_details,
        error_details=error_details,
    )


def create_avatar_video(script: str, video_name: str | None = None) -> AvatarJob:
    status = get_avatar_status()
    if not status.configured:
        raise ValueError(status.message)

    payload = {
        "replica_id": AvatarConfig.REPLICA_ID,
        "script": script,
        "video_name": video_name or f"voice-ai-{uuid4().hex[:8]}",
        "fast": AvatarConfig.FAST,
    }

    logger.info("Creating Tavus avatar video request.")

    response = requests.post(
        f"{AvatarConfig.BASE_URL.rstrip('/')}/v2/videos",
        headers=_build_headers(),
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    job = _extract_job(response.json())

    if not job.video_id:
        raise ValueError("Tavus did not return a video_id.")

    logger.success("Avatar video request created successfully: {}", job.video_id)
    logger.info(
        "Avatar job {} created with initial status: {}",
        job.video_id,
        job.status,
    )

    return job


def get_avatar_video(video_id: str) -> AvatarJob:
    logger.info("Checking Tavus avatar video status for {}", video_id)

    response = requests.get(
        f"{AvatarConfig.BASE_URL.rstrip('/')}/v2/videos/{video_id}",
        headers={"x-api-key": AvatarConfig.API_KEY or ""},
        timeout=60,
    )
    response.raise_for_status()

    response_payload = response.json()
    job = _extract_job(response_payload)

    if job.status.lower() == "unknown":
        logger.warning(
            "Avatar job {} returned an unrecognized response shape: {}",
            video_id,
            response_payload,
        )

    logger.info(
        "Avatar job {} status: {} | details: {}",
        video_id,
        job.status,
        job.status_details or "n/a",
    )

    return job


def wait_for_avatar_video(video_id: str) -> AvatarJob:
    deadline = time.time() + AvatarConfig.TIMEOUT_SECONDS
    last_job = AvatarJob(video_id=video_id, status="queued")
    poll_count = 0

    logger.info(
        "Waiting for avatar job {}. Poll interval: {}s | Timeout: {}s",
        video_id,
        AvatarConfig.POLL_INTERVAL_SECONDS,
        AvatarConfig.TIMEOUT_SECONDS,
    )

    while time.time() < deadline:
        poll_count += 1
        logger.info("Polling avatar job {} attempt {}", video_id, poll_count)
        last_job = get_avatar_video(video_id)

        normalized_status = last_job.status.lower()
        if normalized_status == "ready":
            logger.success(
                "Avatar job {} completed successfully with status: {}",
                video_id,
                last_job.status,
            )
            return last_job

        if normalized_status in {"failed", "error"}:
            details = last_job.error_details or last_job.status_details or "Avatar generation failed."
            logger.error(
                "Avatar job {} failed with status: {} | details: {}",
                video_id,
                last_job.status,
                details,
            )
            raise ValueError(details)

        time.sleep(AvatarConfig.POLL_INTERVAL_SECONDS)

    logger.error(
        "Avatar job {} timed out after {} seconds. Last known status: {}",
        video_id,
        AvatarConfig.TIMEOUT_SECONDS,
        last_job.status,
    )
    raise TimeoutError(
        f"Avatar generation timed out after {AvatarConfig.TIMEOUT_SECONDS} seconds for video {video_id}."
    )


def generate_avatar_response(script: str) -> AvatarResult:
    try:
        job = create_avatar_video(script)
        completed_job = wait_for_avatar_video(job.video_id)

        local_path = None
        if completed_job.download_url:
            logger.info(
                "Avatar job {} is ready. Downloading cached video from {}",
                completed_job.video_id,
                completed_job.download_url,
            )
            local_path = download_video_to_cache(completed_job.download_url, completed_job.video_id)

        return AvatarResult(
            provider=AvatarConfig.PROVIDER,
            video_id=completed_job.video_id,
            status=completed_job.status,
            local_path=local_path,
            hosted_url=completed_job.hosted_url,
            download_url=completed_job.download_url,
            stream_url=completed_job.stream_url,
        )
    except Exception as e:
        logger.exception("Avatar generation failed.")
        raise VoiceAssistantException(e)
