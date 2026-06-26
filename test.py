from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv

load_dotenv()

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

try:
    audio = client.text_to_speech.convert(
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        text="Hello",
        model_id="eleven_multilingual_v2",
    )

    print(b"".join(audio))

except Exception as e:
    import traceback
    traceback.print_exc()