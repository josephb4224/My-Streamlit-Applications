"""Format chat history for plain-text prompts (Streamlit + LangChain)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def _trim_messages(messages: Sequence[Any], *, max_messages: int | None = None) -> list[Any]:
    """Return the most recent messages when a limit is provided."""
    if max_messages is None or max_messages <= 0:
        return list(messages)
    return list(messages[-max_messages:])


def format_messages_as_transcript(
    messages: Sequence[Any], *, max_messages: int | None = None
) -> str:
    """Turn LangChain messages (or role/content dicts) into a readable transcript."""
    trimmed_messages = _trim_messages(messages, max_messages=max_messages)
    lines: list[str] = []
    for msg in trimmed_messages:
        if isinstance(msg, HumanMessage):
            lines.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage):
            lines.append(f"Assistant: {msg.content}")
        elif isinstance(msg, dict) and "role" in msg and "content" in msg:
            role = msg["role"]
            label = "User" if role == "user" else "Assistant" if role == "assistant" else role
            lines.append(f"{label}: {msg['content']}")
        elif isinstance(msg, BaseMessage):
            role = getattr(msg, "type", "unknown")
            content = getattr(msg, "content", "")
            lines.append(f"{role}: {content}")
        else:
            lines.append(str(msg))
    return "\n".join(lines) if lines else "(no prior messages)"
