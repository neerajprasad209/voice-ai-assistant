import os
from dataclasses import dataclass
from http import HTTPStatus
from typing import Callable

import requests
from dotenv import load_dotenv


REQUIRED_API_KEYS = {
    "Sarvam STT": "SARVAM_API_KEY",
    "Groq LLM": "GROQ_API_KEY",
    "Tavily": "TAVILY_API_KEY",
    "ElevenLabs": "ELEVENLABS_API_KEY",
    "Avatar": "TAVUS_API_KEY",
}


@dataclass(frozen=True)
class ApiStatus:
    provider: str
    configured: bool
    message: str


def load_config() -> dict[str, str | None]:
    """Load API keys from the local environment."""
    load_dotenv()
    return {env_name: os.getenv(env_name) for env_name in REQUIRED_API_KEYS.values()}


def get_configuration_status() -> list[ApiStatus]:
    """Return whether each required provider key is available."""
    config = load_config()
    statuses: list[ApiStatus] = []

    for provider, env_name in REQUIRED_API_KEYS.items():
        configured = bool(config.get(env_name))
        message = "Configured" if configured else f"Missing {env_name}"
        statuses.append(ApiStatus(provider, configured, message))

    return statuses


def check_groq_connectivity(api_key: str | None) -> ApiStatus:
    if not api_key:
        return ApiStatus("Groq LLM", False, "Missing GROQ_API_KEY")

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        client.models.list()
        return ApiStatus("Groq LLM", True, "Connected")
    except Exception as exc:
        return ApiStatus("Groq LLM", False, f"Connection failed: {exc}")


def check_sarvam_connectivity(api_key: str | None) -> ApiStatus:
    if not api_key:
        return ApiStatus("Sarvam STT", False, "Missing SARVAM_API_KEY")

    try:
        from sarvamai import SarvamAI

        SarvamAI(api_subscription_key=api_key)
        return ApiStatus("Sarvam STT", True, "SDK ready")
    except ModuleNotFoundError as exc:
        if exc.name == "sarvamai":
            return ApiStatus(
                "Sarvam STT",
                False,
                "Sarvam SDK is not installed in this Python environment. Run `uv sync` and launch Streamlit from `.venv`.",
            )
        return ApiStatus("Sarvam STT", False, f"Connection failed: {exc}")
    except Exception as exc:
        status_code = getattr(exc, "status_code", None)
        if status_code == HTTPStatus.FORBIDDEN:
            return ApiStatus(
                "Sarvam STT",
                False,
                "Forbidden: check SARVAM_API_KEY in .env and make sure it is an active Sarvam API key.",
            )
        return ApiStatus("Sarvam STT", False, f"Connection failed: {exc}")


def check_tavily_connectivity(api_key: str | None) -> ApiStatus:
    if not api_key:
        return ApiStatus("Tavily", False, "Missing TAVILY_API_KEY")

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        client.search("health check", max_results=1)
        return ApiStatus("Tavily", True, "Connected")
    except ModuleNotFoundError as exc:
        if exc.name == "tavily":
            return ApiStatus(
                "Tavily",
                False,
                "Package not installed in this Python environment. Run Streamlit with `.venv\\Scripts\\python.exe -m streamlit run app.py`.",
            )
        return ApiStatus("Tavily", False, f"Connection failed: {exc}")
    except Exception as exc:
        return ApiStatus("Tavily", False, f"Connection failed: {exc}")


def check_elevenlabs_connectivity(api_key: str | None) -> ApiStatus:
    if not api_key:
        return ApiStatus("ElevenLabs", False, "Missing ELEVENLABS_API_KEY")

    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": api_key},
            timeout=15,
        )
        response.raise_for_status()
        return ApiStatus("ElevenLabs", True, "Connected")
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code == HTTPStatus.UNAUTHORIZED:
            return ApiStatus(
                "ElevenLabs",
                False,
                "Unauthorized: check ELEVENLABS_API_KEY in .env and make sure it is an active ElevenLabs API key.",
            )
        return ApiStatus("ElevenLabs", False, f"Connection failed: {exc}")
    except Exception as exc:
        return ApiStatus("ElevenLabs", False, f"Connection failed: {exc}")


def check_api_connectivity() -> list[ApiStatus]:
    """Run lightweight authentication checks for all Phase 1 providers."""
    config = load_config()
    checks: list[tuple[str, Callable[[str | None], ApiStatus]]] = [
        ("SARVAM_API_KEY", check_sarvam_connectivity),
        ("GROQ_API_KEY", check_groq_connectivity),
        ("TAVILY_API_KEY", check_tavily_connectivity),
        ("ELEVENLABS_API_KEY", check_elevenlabs_connectivity),
    ]

    return [check(config.get(env_name)) for env_name, check in checks]
