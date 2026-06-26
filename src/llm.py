import os
from dataclasses import dataclass

from dotenv import load_dotenv


CHAT_MODEL = "llama-3.3-70b-versatile"
DECISION_MODEL = "llama-3.1-8b-instant"


@dataclass(frozen=True)
class SearchDecision:
    should_search: bool
    reason: str


def _get_client():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY")

    from groq import Groq

    return Groq(api_key=api_key)


def decide_search_requirement(question: str) -> SearchDecision:
    """Decide whether live web search is necessary for the current query."""
    normalized_question = question.strip()
    if not normalized_question:
        return SearchDecision(False, "No question provided.")

    client = _get_client()
    response = client.chat.completions.create(
        model=DECISION_MODEL,
        temperature=0.0,
        max_completion_tokens=80,
        messages=[
            {
                "role": "system",
                "content": (
                    "Decide if a user's question needs live web search. "
                    "Use SEARCH for current events, recent facts, fast-changing information, "
                    "specific external facts, or anything where freshness matters. "
                    "Use NO_SEARCH for stable knowledge, explanations, brainstorming, math, writing, "
                    "or opinion-free general concepts. "
                    "Reply in exactly two lines: "
                    "DECISION: SEARCH or DECISION: NO_SEARCH "
                    "REASON: <short reason>"
                ),
            },
            {
                "role": "user",
                "content": normalized_question,
            },
        ],
    )

    content = (response.choices[0].message.content or "").strip()
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    decision_line = next((line for line in lines if line.upper().startswith("DECISION:")), "")
    reason_line = next((line for line in lines if line.upper().startswith("REASON:")), "")

    should_search = "SEARCH" in decision_line.upper() and "NO_SEARCH" not in decision_line.upper()
    reason = reason_line.split(":", 1)[1].strip() if ":" in reason_line else "Decision generated."
    if not reason:
        reason = "Decision generated."

    return SearchDecision(should_search, reason)


def generate_response(question: str, search_context: str) -> str:
    """Generate a grounded answer from web search results."""
    client = _get_client()
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0.2,
        max_completion_tokens=500,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise voice assistant. Answer using the provided web results. "
                    "Format the reply exactly like this:\n"
                    f"Question: {question}\n"
                    "Answer: <answer>\n"
                    "Keep the Answer field within 100 words. "
                    "Do not add bullet points, source lists, or extra sections."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User question:\n{question}\n\n"
                    f"Web search results:\n{search_context}\n\n"
                    "Use only the web results above to answer."
                ),
            },
        ],
    )

    answer = response.choices[0].message.content or ""
    answer = answer.strip()
    if not answer:
        raise RuntimeError("Groq returned an empty response.")

    return answer


def generate_direct_response(question: str) -> str:
    """Generate an answer without calling live web search."""
    client = _get_client()
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0.2,
        max_completion_tokens=400,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise voice assistant. Answer clearly and conversationally. "
                    "If the user asks for something time-sensitive that you are unsure about, say that live lookup may be needed."
                ),
            },
            {
                "role": "user",
                "content": question.strip(),
            },
        ],
    )

    answer = response.choices[0].message.content or ""
    answer = answer.strip()
    if not answer:
        raise RuntimeError("Groq returned an empty response.")

    return answer
