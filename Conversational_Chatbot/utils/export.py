"""Helpers for exporting conversations from Streamlit session state."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def normalize_messages(messages: Sequence[Any]) -> list[dict[str, str]]:
    """
    Normalize mixed message objects into role/content dictionaries.

    :param messages: Mixed dict/BaseMessage message list.

    :returns normalized_messages: List of dictionaries with role/content keys.
    """
    normalized_messages: list[dict[str, str]] = []
    for message in messages:
        if isinstance(message, HumanMessage):
            role = "user"
            content = str(message.content)
        elif isinstance(message, AIMessage):
            role = "assistant"
            content = str(message.content)
        elif isinstance(message, dict):
            role = str(message.get("role", "assistant"))
            content = str(message.get("content", ""))
        elif isinstance(message, BaseMessage):
            role = str(getattr(message, "type", "assistant"))
            content = str(getattr(message, "content", ""))
        else:
            role = "assistant"
            content = str(message)
        normalized_messages.append({"role": role, "content": content})
    return normalized_messages


def export_messages_as_json(messages: Sequence[Any]) -> str:
    """
    Serialize messages in JSON format.

    :param messages: Mixed dict/BaseMessage message list.

    :returns payload: JSON payload string.
    """
    return json.dumps(normalize_messages(messages), indent=2)


def export_messages_as_markdown(messages: Sequence[Any], *, title: str = "Conversation") -> str:
    """
    Serialize messages in Markdown format.

    :param messages: Mixed dict/BaseMessage message list.
    :param title: Markdown heading title.

    :returns markdown_text: Markdown payload string.
    """
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [f"# {title}", "", f"_Exported: {now_utc}_", ""]
    for message in normalize_messages(messages):
        role = message["role"].lower()
        label = "User" if role == "user" else "Assistant" if role == "assistant" else role.title()
        content = message["content"].strip() or "(empty message)"
        lines.extend([f"## {label}", "", content, ""])
    return "\n".join(lines).strip() + "\n"

