import os
from dataclasses import dataclass

from dotenv import load_dotenv
from groq import Groq
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

CHAT_MODEL = "llama-3.3-70b-versatile"
DECISION_MODEL = "llama-3.1-8b-instant"


@dataclass(frozen=True)
class SearchDecision:
    should_search: bool
    reason: str


def _get_client() -> Groq:
    """Create Groq client."""

    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("Missing GROQ_API_KEY")

    return Groq(api_key=api_key)


# ==========================================================
# Message Builder
# ==========================================================


def build_messages(
    *,
    history: list[BaseMessage],
    system_prompt: str,
) -> list[dict]:
    """
    Convert LangChain messages into the format expected by Groq.
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    for message in history:

        if isinstance(message, HumanMessage):
            role = "user"

        elif isinstance(message, AIMessage):
            role = "assistant"

        elif isinstance(message, SystemMessage):
            role = "system"

        else:
            continue

        messages.append(
            {
                "role": role,
                "content": message.content,
            }
        )

    return messages


# ==========================================================
# Generic Groq Chat Completion
# ==========================================================


def chat_completion(
    *,
    history: list[BaseMessage],
    system_prompt: str,
    model: str = CHAT_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 500,
) -> str:
    """
    Generic helper used by every LLM call.
    """

    client = _get_client()

    messages = build_messages(
        history=history,
        system_prompt=system_prompt,
    )

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_tokens,
    )

    answer = response.choices[0].message.content or ""

    answer = answer.strip()

    if not answer:
        raise RuntimeError("Groq returned an empty response.")

    return answer


# ==========================================================
# Search Decision
# ==========================================================


def decide_search_requirement(question: str) -> SearchDecision:
    """
    Decide whether a web search is required.
    """

    question = question.strip()

    if not question:
        return SearchDecision(
            should_search=False,
            reason="No question provided.",
        )

    client = _get_client()

    response = client.chat.completions.create(
        model=DECISION_MODEL,
        temperature=0,
        max_completion_tokens=80,
        messages=[
            {
                "role": "system",
                "content": (
                    "Decide whether the user's latest question "
                    "requires live web search.\n\n"
                    "Reply using exactly two lines.\n\n"
                    "DECISION: SEARCH or NO_SEARCH\n"
                    "REASON: short explanation."
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    content = (response.choices[0].message.content or "").strip()

    lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip()
    ]

    decision_line = next(
        (
            line
            for line in lines
            if line.upper().startswith("DECISION:")
        ),
        "",
    )

    reason_line = next(
        (
            line
            for line in lines
            if line.upper().startswith("REASON:")
        ),
        "",
    )

    should_search = (
        "SEARCH" in decision_line.upper()
        and "NO_SEARCH" not in decision_line.upper()
    )

    reason = (
        reason_line.split(":", 1)[1].strip()
        if ":" in reason_line
        else "Decision generated."
    )

    return SearchDecision(
        should_search=should_search,
        reason=reason,
    )
    
    
# ==========================================================
# Prompt Templates
# ==========================================================

DIRECT_SYSTEM_PROMPT = """
You are a helpful AI Voice Assistant.

Guidelines:
- Answer naturally and conversationally.
- Keep responses concise.
- Use previous conversation whenever helpful.
- If the answer is uncertain or time-sensitive, mention that live web search may be required.
- Keep responses under 100 words.
""".strip()


SEARCH_SYSTEM_PROMPT = """
You are a helpful AI Voice Assistant.

You have access to live web search results.

Rules:
- Answer ONLY using the supplied search results.
- Do not invent facts.
- If the answer cannot be found in the search results,
  clearly say so.
- Previous conversation can be used for context.
- Keep the response under 100 words.

Search Results:

{search_context}
""".strip()


# ==========================================================
# Direct Conversation
# ==========================================================


def generate_direct_response(
    history: list[BaseMessage],
) -> str:
    """
    Generate a conversational response without using web search.
    """

    return chat_completion(
        history=history,
        system_prompt=DIRECT_SYSTEM_PROMPT,
        model=CHAT_MODEL,
        temperature=0.2,
        max_tokens=400,
    )


# ==========================================================
# Search Response
# ==========================================================


def generate_response(
    history: list[BaseMessage],
    search_context: str,
) -> str:
    """
    Generate an answer using Tavily search results.
    """

    system_prompt = SEARCH_SYSTEM_PROMPT.format(
        search_context=search_context
    )

    return chat_completion(
        history=history,
        system_prompt=system_prompt,
        model=CHAT_MODEL,
        temperature=0.2,
        max_tokens=500,
    )