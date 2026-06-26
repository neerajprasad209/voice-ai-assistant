import json
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv


SARVAM_MODEL = "saaras:v3"
SARVAM_MODE = "transcribe"
SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".aac",
    ".flac",
    ".ogg",
    ".webm",
    ".mp4",
    ".m4a",
}


def _get_client():
    load_dotenv()
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise ValueError("Missing SARVAM_API_KEY")

    try:
        from sarvamai import SarvamAI
    except ModuleNotFoundError as exc:
        if exc.name == "sarvamai":
            raise ModuleNotFoundError(
                "Sarvam SDK is not installed in this Python environment. Run `uv sync` and launch Streamlit from `.venv`."
            ) from exc
        raise

    return SarvamAI(api_subscription_key=api_key)


def _normalize_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return suffix if suffix else ".wav"


def _validate_audio(filename: str, audio_bytes: bytes) -> str:
    if not audio_bytes:
        raise ValueError("No audio data was provided for transcription.")

    suffix = _normalize_extension(filename)
    if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
        raise ValueError(f"Unsupported audio format `{suffix}`. Supported formats: {supported}.")

    return suffix


def _extract_transcript(response) -> str:
    transcript = getattr(response, "transcript", "")
    if not transcript and isinstance(response, dict):
        transcript = response.get("transcript", "")

    transcript = transcript.strip()
    if not transcript:
        raise RuntimeError("Sarvam STT returned an empty transcript.")

    return transcript


def _should_fallback_to_batch(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    body = getattr(exc, "body", "")
    body_text = str(body).lower()
    error_text = str(exc).lower()

    return status_code == 422 and (
        "30 seconds" in body_text
        or "30 seconds" in error_text
        or "longer files" in body_text
        or "batch api" in body_text
        or "file too large" in body_text
    )


def _transcribe_rest(audio_path: str, *, language: str | None = None) -> str:
    client = _get_client()
    params = {
        "file": open(audio_path, "rb"),
        "model": SARVAM_MODEL,
        "mode": SARVAM_MODE,
    }
    if language:
        params["language_code"] = language

    file_handle = params["file"]
    try:
        response = client.speech_to_text.transcribe(**params)
    finally:
        file_handle.close()

    return _extract_transcript(response)


def _parse_batch_output(output_dir: str) -> str:
    output_path = Path(output_dir)
    for json_file in sorted(output_path.rglob("*.json")):
        with json_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        transcript = str(payload.get("transcript", "")).strip()
        if transcript:
            return transcript

    raise RuntimeError("Sarvam batch transcription completed, but no transcript output was found.")


def _transcribe_batch(audio_path: str, *, language: str | None = None) -> str:
    client = _get_client()
    create_params = {
        "model": SARVAM_MODEL,
        "mode": SARVAM_MODE,
    }
    if language:
        create_params["language_code"] = language

    job = client.speech_to_text_job.create_job(**create_params)
    job.upload_files(file_paths=[audio_path])
    job.start()
    job.wait_until_complete()

    file_results = job.get_file_results()
    failed_files = file_results.get("failed", [])
    if failed_files:
        first_error = failed_files[0]
        raise RuntimeError(
            f"Sarvam batch transcription failed for {first_error.get('file_name', 'the uploaded file')}: "
            f"{first_error.get('error_message', 'Unknown batch error')}"
        )

    with tempfile.TemporaryDirectory() as output_dir:
        job.download_outputs(output_dir=output_dir)
        return _parse_batch_output(output_dir)


def transcribe_audio(audio_bytes: bytes, *, filename: str = "recording.wav", language: str | None = None) -> str:
    """Transcribe audio with Sarvam STT using REST and batch fallback."""
    suffix = _validate_audio(filename, audio_bytes)

    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = os.path.join(temp_dir, f"input{suffix}")
        with open(audio_path, "wb") as handle:
            handle.write(audio_bytes)

        try:
            return _transcribe_rest(audio_path, language=language)
        except Exception as exc:
            if not _should_fallback_to_batch(exc):
                raise
            return _transcribe_batch(audio_path, language=language)
