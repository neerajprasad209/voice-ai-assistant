from dataclasses import dataclass


BLOCKED_PATTERNS = (
    "hack someone's account",
    "hack my ex",
    "make a bomb",
    "build a bomb",
    "kill someone",
    "credit card fraud",
    "bypass police",
    "malware",
    "ransomware",
)

BLOCKED_RESPONSE = "Sorry, I can't assist with that request."


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    text: str


def apply_guardrails(text: str) -> GuardrailResult:
    """Reject obviously unsafe requests before the search and LLM pipeline."""
    normalized = text.strip()
    lowered = normalized.lower()

    if any(pattern in lowered for pattern in BLOCKED_PATTERNS):
        return GuardrailResult(False, BLOCKED_RESPONSE)

    if not normalized:
        return GuardrailResult(False, "Please provide a question before generating a response.")

    return GuardrailResult(True, normalized)
