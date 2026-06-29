from dataclasses import dataclass


@dataclass(frozen=True)
class AvatarStatus:
    configured: bool
    provider: str
    message: str


@dataclass(frozen=True)
class AvatarJob:
    video_id: str
    status: str
    hosted_url: str | None = None
    download_url: str | None = None
    stream_url: str | None = None
    status_details: str | None = None
    error_details: str | None = None


@dataclass(frozen=True)
class AvatarResult:
    provider: str
    video_id: str
    status: str
    local_path: str | None = None
    hosted_url: str | None = None
    download_url: str | None = None
    stream_url: str | None = None
