# Voice AI Assistant

Voice AI assistant built with Streamlit, Sarvam speech-to-text, Tavily search, Groq LLMs, and ElevenLabs text-to-speech.

## Files

- `app.py`: Entry point
- `requirements.txt`: Python dependencies
- `.env`: Environment variables
- `src/`: Source modules
- `assets/`: Static or media assets

## Run

Install dependencies into the project virtual environment, then launch Streamlit with that interpreter:

```powershell
uv sync
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Phases 2 to 4 are now wired up:

* Record audio with the browser microphone input
* Send the captured audio to Sarvam STT
* Search the web with Tavily
* Generate an answer with Groq
* Convert the answer to speech with ElevenLabs
* Display the transcript, sources, answer, and playable audio in the app

If you launch the app from an older global Streamlit install, the app falls back to audio file upload because `st.audio_input` is only available in newer Streamlit releases.

If Tavily reports `No module named 'tavily'`, Streamlit is running from a different Python environment. Use the command above from this project directory.

If ElevenLabs reports `Unauthorized`, update `ELEVENLABS_API_KEY` in `.env` with a valid active API key from your ElevenLabs account.
