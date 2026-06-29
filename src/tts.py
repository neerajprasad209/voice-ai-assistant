import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

from pathlib import Path

AUDIO_DIR = Path("assets/generated_audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
DEFAULT_MODEL_ID = "eleven_v3"


def synthesize_speech(text: str,*,voice_id: str | None = None,save_audio: bool = True,) -> tuple[bytes, str | None]:
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
    
    audio_path = None

    if save_audio:

        audio_path = AUDIO_DIR / "assistant_response.mp3"

        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

    return audio_bytes, str(audio_path)
