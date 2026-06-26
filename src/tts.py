import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs


DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
DEFAULT_MODEL_ID = "eleven_v3"


def synthesize_speech(text: str, *, voice_id: str | None = None) -> bytes:
    """Convert response text to playable MP3 audio with ElevenLabs."""
    cleaned_text = text.strip()
    if not cleaned_text:
        raise ValueError("No text was provided for speech synthesis.")

    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("Missing ELEVENLABS_API_KEY")

    client = ElevenLabs(api_key=api_key)
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id or os.getenv("ELEVENLABS_VOICE_ID") or DEFAULT_VOICE_ID,
        text=cleaned_text,
        model_id=DEFAULT_MODEL_ID,
        output_format="mp3_44100_128",
    )

    audio_bytes = b"".join(audio_stream)
    if not audio_bytes:
        raise RuntimeError("ElevenLabs returned empty audio.")

    return audio_bytes
