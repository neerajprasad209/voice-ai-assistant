import streamlit as st

from src.chat_history import ChatHistoryManager
from src.custom_exception import VoiceAssistantException
from src.guardrails import apply_guardrails
from src.llm import (
    decide_search_requirement,
    generate_direct_response,
    generate_response,
)
from src.logger import logger
from src.search import format_search_context, search_web
from src.speech_to_text import transcribe_audio
from src.tts import synthesize_speech
from src.utils import check_api_connectivity, get_configuration_status


STATE_DEFAULTS = {
    "chat_history": ChatHistoryManager(),
    "assistant_audio": None,
    "tts_error": None,
    "search_results": [],
    "search_used": False,
    "search_reason": "",
    "processing_error": "",
}


def initialize_state() -> None:
    """Ensure expected Streamlit session keys exist."""

    logger.info("Initializing Streamlit session state.")

    try:
        for key, value in STATE_DEFAULTS.items():
            st.session_state.setdefault(key, value)

        logger.success("Session state initialized successfully.")

    except Exception as e:
        logger.exception("Failed to initialize session state.")
        raise VoiceAssistantException(e)


def get_audio_source() -> tuple[object | None, str]:
    """Return recorded or uploaded audio depending on Streamlit capabilities."""

    logger.info("Detecting available audio input source.")

    try:

        if hasattr(st, "audio_input"):

            logger.info("Using Streamlit microphone input.")

            audio_value = st.audio_input(
                "Microphone recording",
                help="Allow microphone access in your browser when prompted.",
            )

            return audio_value, "microphone"

        logger.warning(
            "Streamlit audio_input is unavailable. Falling back to file uploader."
        )

        st.info(
            "This Streamlit version does not support in-browser microphone capture. "
            "Upload a WAV, MP3, M4A, or WebM recording instead, or run the app from `.venv` for microphone input."
        )

        audio_value = st.file_uploader(
            "Audio file",
            type=[
                "wav",
                "mp3",
                "m4a",
                "webm",
                "ogg",
                "mp4",
                "mpeg",
                "mpga",
                "flac",
            ],
            help="Upload an audio clip to transcribe with Sarvam STT.",
        )

        logger.success("Audio source initialized.")

        return audio_value, "upload"

    except Exception as e:
        logger.exception("Failed while initializing audio source.")
        raise VoiceAssistantException(e)


def render_status(label: str, ok: bool, message: str) -> None:

    try:

        if ok:
            logger.info(f"{label}: {message}")
            st.success(f"{label}: {message}")

        else:
            logger.warning(f"{label}: {message}")
            st.warning(f"{label}: {message}")

    except Exception as e:
        logger.exception("Failed while rendering API status.")
        raise VoiceAssistantException(e)


def reset_assistant_state() -> None:

    logger.info("Resetting assistant session state.")

    try:

        st.session_state["chat_history"] = ChatHistoryManager()
        st.session_state["assistant_audio"] = None
        st.session_state["tts_error"] = None
        st.session_state["search_results"] = []
        st.session_state["search_used"] = False
        st.session_state["search_reason"] = ""
        st.session_state["processing_error"] = ""

        logger.success("Assistant session state reset successfully.")

    except Exception as e:
        logger.exception("Failed to reset assistant state.")
        raise VoiceAssistantException(e)


def run_assistant(query: str) -> None:

    logger.info("Starting assistant pipeline.")

    try:

        history = st.session_state["chat_history"]

        logger.info("Applying guardrails.")

        guardrail_result = apply_guardrails(query)

        st.session_state["processing_error"] = ""

        if not guardrail_result.allowed:

            logger.warning("Query blocked by guardrails.")

            history.add_human_message(query)
            history.add_ai_message(guardrail_result.text)

            st.session_state["search_results"] = []
            st.session_state["assistant_audio"] = None
            st.session_state["tts_error"] = None
            st.session_state["search_used"] = False
            st.session_state["search_reason"] = "Blocked by guardrails."

            logger.success("Blocked response stored successfully.")

            return

        logger.info("Adding HumanMessage to conversation history.")

        history.add_human_message(
            guardrail_result.text
        )

        logger.info("Running search decision model.")

        search_decision = decide_search_requirement(
            guardrail_result.text
        )

        st.session_state["search_used"] = search_decision.should_search
        st.session_state["search_reason"] = search_decision.reason

        logger.info(
            "Search Decision: %s | Reason: %s",
            search_decision.should_search,
            search_decision.reason,
        )

        search_results = []

        if search_decision.should_search:

            logger.info("Performing Tavily web search.")

            search_results = search_web(
                guardrail_result.text
            )

            logger.success(
                f"Retrieved {len(search_results)} search results."
            )

            logger.info("Generating grounded response using search context.")

            answer = generate_response(
                history.get_messages(),
                format_search_context(search_results),
            )

        else:

            logger.info("Generating response without web search.")

            answer = generate_direct_response(
                history.get_messages()
            )

        logger.success("LLM response generated successfully.")

        logger.info("Adding AIMessage to conversation history.")

        history.add_ai_message(answer)

        st.session_state["search_results"] = search_results

        logger.info("Generating speech using ElevenLabs.")

        last_ai = history.get_last_ai_message()

        st.session_state["assistant_audio"] = synthesize_speech(
            last_ai.content
        )

        st.session_state["tts_error"] = None

        logger.success("Speech generated successfully.")

        logger.success("Assistant pipeline completed successfully.")

    except Exception as e:

        logger.exception("Assistant pipeline failed.")

        st.session_state["assistant_audio"] = None
        st.session_state["tts_error"] = str(e)

        raise VoiceAssistantException(e)


def main() -> None:

    logger.info("Starting Voice AI Assistant application.")

    try:

        st.set_page_config(page_title="Voice AI Assistant")

        logger.info("Initializing Streamlit session.")

        initialize_state()

        logger.success("Session initialized successfully.")

        st.title("Voice AI Assistant")

        logger.info("Rendering API configuration.")

        st.subheader("API Configuration")

        for status in get_configuration_status():
            render_status(
                status.provider,
                status.configured,
                status.message,
            )

        logger.success("API configuration rendered successfully.")

        st.subheader("Voice Input")

        st.write(
            "Capture or upload a question, then transcribe it with Sarvam STT."
        )

        logger.info("Initializing audio source.")

        audio_value, audio_source = get_audio_source()

        if audio_value is not None:

            logger.info("Audio received from user.")

            st.audio(audio_value)

            button_label = (
                "Generate Audio"
                if audio_source == "microphone"
                else "Transcribe Audio"
            )

            if st.button(button_label, type="primary"):

                logger.info("User initiated assistant pipeline.")

                with st.spinner("Generating the Response..."):

                    try:

                        logger.info("Starting speech transcription.")

                        transcript = transcribe_audio(
                            audio_value.getvalue(),
                            filename=audio_value.name
                            or "recording.wav",
                        )

                        logger.success(
                            "Speech transcription completed successfully."
                        )

                        logger.info(
                            "Executing assistant pipeline."
                        )

                        run_assistant(transcript)

                        logger.success(
                            "Assistant pipeline executed successfully."
                        )

                    except Exception as e:

                        logger.exception(
                            "Assistant pipeline execution failed."
                        )

                        st.session_state["processing_error"] = str(e)

                        st.error(
                            f"Transcription or assistant pipeline failed: {e}"
                        )

                    else:

                        st.success(
                            "Transcription complete with Sarvam STT."
                        )

        logger.info("Rendering search decision.")

        search_reason = st.session_state.get("search_reason")

        if search_reason:

            decision_label = (
                "Web search used"
                if st.session_state.get("search_used")
                else "Answered without web search"
            )

            st.caption(
                f"{decision_label}: {search_reason}"
            )

        logger.info("Rendering conversation history.")

        history = st.session_state["chat_history"]

        # if len(history):

        #     st.subheader("Conversation")

        #     for message in history:

        #         if message.type == "human":

        #             with st.chat_message("user"):
        #                 st.write(message.content)

        #         elif message.type == "ai":

        #             with st.chat_message("assistant"):
        #                 st.write(message.content)

        logger.info("Rendering search results.")

        search_results = st.session_state.get(
            "search_results",
            [],
        )

        if search_results:

            st.subheader("Sources")

            for index, result in enumerate(
                search_results,
                start=1,
            ):

                if result.url:

                    st.markdown(
                        f"{index}. [{result.title}]({result.url})"
                    )

                else:

                    st.write(
                        f"{index}. {result.title}"
                    )

        logger.info("Rendering audio response.")

        audio_bytes = st.session_state.get(
            "assistant_audio"
        )

        if audio_bytes:

            st.subheader("Voice Response")

            st.audio(
                audio_bytes,
                format="audio/mp3",
            )

        tts_error = st.session_state.get(
            "tts_error"
        )

        if tts_error:

            logger.warning(
                f"TTS Error : {tts_error}"
            )

            st.warning(
                f"Speech synthesis unavailable: {tts_error}"
            )

        processing_error = st.session_state.get(
            "processing_error"
        )

        if processing_error:

            logger.warning(
                f"Processing Error : {processing_error}"
            )

            st.warning(
                f"Last processing error: {processing_error}"
            )

        if st.button(
            "Reset",
            type="secondary",
        ):

            logger.info(
                "Reset button clicked."
            )

            reset_assistant_state()

            logger.success(
                "Assistant state reset successfully."
            )

            st.rerun()

        logger.success(
            "Voice AI Assistant rendered successfully."
        )

    except Exception as e:

        logger.exception(
            "Fatal error while running the Streamlit application."
        )

        raise VoiceAssistantException(e)



if __name__ == "__main__":
    main()
