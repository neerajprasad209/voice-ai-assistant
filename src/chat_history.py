from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


class ChatHistoryManager:
    """
    Maintains conversation history using LangChain Message objects.

    Future extensions:
    - Redis
    - MongoDB
    - SQLite
    - Postgres
    - Conversation Memory
    """

    def __init__(self):
        self._messages: list[BaseMessage] = []

    # -------------------------
    # Add Messages
    # -------------------------

    def add_human_message(self, text: str) -> HumanMessage:
        """Create and store a HumanMessage."""
        message = HumanMessage(content=text.strip())
        self._messages.append(message)
        return message

    def add_ai_message(self, text: str) -> AIMessage:
        """Create and store an AIMessage."""
        message = AIMessage(content=text.strip())
        self._messages.append(message)
        return message

    # -------------------------
    # Get Messages
    # -------------------------

    def get_messages(self) -> list[BaseMessage]:
        """Return all conversation messages."""
        return list(self._messages)

    def get_last_message(self) -> BaseMessage | None:
        """Return last message."""
        if not self._messages:
            return None
        return self._messages[-1]

    def get_last_human_message(self) -> HumanMessage | None:
        """Return latest HumanMessage."""
        for msg in reversed(self._messages):
            if isinstance(msg, HumanMessage):
                return msg
        return None

    def get_last_ai_message(self) -> AIMessage | None:
        """Return latest AIMessage."""
        for msg in reversed(self._messages):
            if isinstance(msg, AIMessage):
                return msg
        return None

    # -------------------------
    # Utilities
    # -------------------------

    def clear(self):
        """Clear conversation."""
        self._messages.clear()

    def __len__(self):
        return len(self._messages)

    def __iter__(self):
        return iter(self._messages)

    # -------------------------
    # Serialization
    # -------------------------

    def to_groq_messages(self) -> list[dict]:
        """
        Convert LangChain messages to Groq/OpenAI format.
        """

        messages = []

        for message in self._messages:

            if isinstance(message, HumanMessage):
                role = "user"

            elif isinstance(message, AIMessage):
                role = "assistant"

            else:
                continue

            messages.append(
                {
                    "role": role,
                    "content": message.content,
                }
            )

        return messages

    def export(self) -> list[dict]:
        """
        Export conversation history.
        """

        history = []

        for message in self._messages:

            if isinstance(message, HumanMessage):
                role = "user"

            elif isinstance(message, AIMessage):
                role = "assistant"

            else:
                role = "unknown"

            history.append(
                {
                    "role": role,
                    "content": message.content,
                }
            )

        return history