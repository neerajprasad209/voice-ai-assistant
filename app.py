import streamlit as st

from src.guardrails import apply_guardrails
from src.llm import decide_search_requirement, generate_direct_response, generate_response
from src.search import format_search_context, search_web
from src.speech_to_text import transcribe_audio
from src.tts import synthesize_speech
from src.utils import check_api_connectivity, get_configuration_status


STATE_DEFAULTS = {
    "latest_transcript": "",
    "assistant_query_input": "",
    "assistant_query": "",
    "assistant_answer": "",
    "assistant_audio": None,
    "tts_error": None,
    "search_results": [],
    "search_used": False,
    "search_reason": "",
    "processing_error": "",
}


def initialize_state() -> None:
    """Ensure expected Streamlit session keys exist."""
    for key, value in STATE_DEFAULTS.items():
        st.session_state.setdefault(key, value)


def get_audio_source() -> tuple[object | None, str]:
    """Return recorded or uploaded audio depending on Streamlit capabilities."""
    if hasattr(st, "audio_input"):
        audio_value = st.audio_input(
            "Microphone recording",
            help="Allow microphone access in your browser when prompted.",
        )
        return audio_value, "microphone"

    st.info(
        "This Streamlit version does not support in-browser microphone capture. "
        "Upload a WAV, MP3, M4A, or WebM recording instead, or run the app from `.venv` for microphone input."
    )
    audio_value = st.file_uploader(
        "Audio file",
        type=["wav", "mp3", "m4a", "webm", "ogg", "mp4", "mpeg", "mpga", "flac"],
        help="Upload an audio clip to transcribe with Sarvam STT.",
    )
    return audio_value, "upload"


def render_status(label: str, ok: bool, message: str) -> None:
    if ok:
        st.success(f"{label}: {message}")
    else:
        st.warning(f"{label}: {message}")


def reset_assistant_state() -> None:
    """Clear the interactive assistant state."""
    for key, value in STATE_DEFAULTS.items():
        st.session_state[key] = value


def run_assistant(query: str) -> None:
    """Run guardrails, search decision, reasoning, and text-to-speech for a query."""
    guardrail_result = apply_guardrails(query)
    st.session_state["assistant_query"] = query
    st.session_state["processing_error"] = ""

    if not guardrail_result.allowed:
        st.session_state["assistant_answer"] = guardrail_result.text
        st.session_state["search_results"] = []
        st.session_state["assistant_audio"] = None
        st.session_state["tts_error"] = None
        st.session_state["search_used"] = False
        st.session_state["search_reason"] = "Blocked by guardrails."
        return

    search_decision = decide_search_requirement(guardrail_result.text)
    st.session_state["search_used"] = search_decision.should_search
    st.session_state["search_reason"] = search_decision.reason

    search_results = []
    if search_decision.should_search:
        search_results = search_web(guardrail_result.text)
        answer = generate_response(
            guardrail_result.text,
            format_search_context(search_results),
        )
    else:
        answer = generate_direct_response(guardrail_result.text)

    st.session_state["search_results"] = search_results
    st.session_state["assistant_answer"] = answer

    try:
        st.session_state["assistant_audio"] = synthesize_speech(answer)
        st.session_state["tts_error"] = None
    except Exception as exc:
        st.session_state["assistant_audio"] = None
        st.session_state["tts_error"] = str(exc)


def main() -> None:
    st.set_page_config(page_title="Voice AI Assistant")
    initialize_state()
    st.title("Voice AI Assistant")
    st.caption("Phases 2 to 4: speech input, live web search, Groq reasoning, and ElevenLabs speech output.")

    if st.button("Reset", type="secondary"):
        reset_assistant_state()
        st.rerun()

    st.subheader("API Configuration")
    for status in get_configuration_status():
        render_status(status.provider, status.configured, status.message)

    st.subheader("Voice Input")
    st.write("Capture or upload a question, then transcribe it with Sarvam STT.")

    audio_value, audio_source = get_audio_source()

    if audio_value is not None:
        st.audio(audio_value)

        button_label = "Transcribe Recording" if audio_source == "microphone" else "Transcribe Audio"
        if st.button(button_label, type="primary"):
            with st.spinner("Transcribing audio and preparing a response..."):
                try:
                    transcript = transcribe_audio(
                        audio_value.getvalue(),
                        filename=audio_value.name or "recording.wav",
                    )
                    st.session_state["latest_transcript"] = transcript
                    st.session_state["assistant_query_input"] = transcript
                    run_assistant(transcript)
                except Exception as exc:
                    st.session_state["processing_error"] = str(exc)
                    st.error(f"Transcription or assistant pipeline failed: {exc}")
                else:
                    st.success("Transcription complete with Sarvam STT.")

    transcript = st.session_state.get("latest_transcript")
    if transcript:
        st.subheader("Transcribed Text")
        st.write(transcript)
        # st.text_area("Transcript", value=transcript, height=180, disabled=True)

    # if st.button("Search, Answer, and Speak", type="primary"):
    #     with st.spinner("Searching the web, generating an answer, and creating speech..."):
    #         try:
    #             run_assistant(st.session_state["assistant_query_input"])
    #         except Exception as exc:
    #             st.session_state["processing_error"] = str(exc)
    #             st.error(f"Assistant pipeline failed: {exc}")

    search_reason = st.session_state.get("search_reason")
    if search_reason:
        decision_label = "Web search used" if st.session_state.get("search_used") else "Answered without web search"
        st.caption(f"{decision_label}: {search_reason}")

    answer = st.session_state.get("assistant_answer")
    if answer:
        st.subheader("Assistant Response")
        st.write(answer)

    search_results = st.session_state.get("search_results", [])
    if search_results:
        st.subheader("Sources")
        for index, result in enumerate(search_results, start=1):
            if result.url:
                st.markdown(f"{index}. [{result.title}]({result.url})")
            else:
                st.write(f"{index}. {result.title}")

    audio_bytes = st.session_state.get("assistant_audio")
    if audio_bytes:
        st.subheader("Voice Response")
        st.audio(audio_bytes, format="audio/mp3")

    tts_error = st.session_state.get("tts_error")
    if tts_error:
        st.warning(f"Speech synthesis unavailable: {tts_error}")

    processing_error = st.session_state.get("processing_error")
    if processing_error:
        st.warning(f"Last processing error: {processing_error}")

    # st.subheader("Connectivity")
    # if st.button("Check API Connectivity"):
    #     with st.spinner("Checking API access..."):
    #         for status in check_api_connectivity():
    #             render_status(status.provider, status.configured, status.message)



if __name__ == "__main__":
    main()
