"""Persist Streamlit chat messages in a local SQLite database."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

CHAT_DB_PATH = Path(__file__).resolve().parents[1] / "chat_history.db"


def _connect() -> sqlite3.Connection:
    """
    Return a configured SQLite connection for chat operations.

    Uses a busy timeout and WAL mode to reduce lock contention when multiple
    Streamlit tabs hit the same local DB.
    """
    connection = sqlite3.connect(CHAT_DB_PATH, timeout=10)
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    return connection


def initialize_chat_store() -> None:
    """
    Create the SQLite schema for chat persistence.

    :returns result: None.
    """
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created
            ON chat_messages (session_id, created_at)
            """
        )
        connection.commit()


def create_session_id() -> str:
    """
    Return a short unique chat session identifier.

    :returns session_id: Unique chat session ID.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"chat-{timestamp}-{uuid4().hex[:6]}"


def list_session_ids(limit: int = 50) -> list[str]:
    """
    List recent session identifiers ordered by latest activity.

    :param limit: Maximum number of session IDs to return.

    :returns session_ids: Recent session IDs.
    """
    initialize_chat_store()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT session_id, MAX(created_at) AS last_seen
            FROM chat_messages
            GROUP BY session_id
            ORDER BY last_seen DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row[0] for row in rows]


def load_session_messages(session_id: str) -> list[dict[str, str]]:
    """
    Load all persisted messages for a chat session.

    :param session_id: Session identifier to load.

    :returns messages: Message dictionaries with role/content keys.
    """
    initialize_chat_store()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT role, content
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()
    return [{"role": role, "content": content} for role, content in rows]


def append_session_message(session_id: str, role: str, content: str) -> None:
    """
    Append a message to the persistent chat session log.

    :param session_id: Session identifier to update.
    :param role: Message role value (for example: user or assistant).
    :param content: Message text content.

    :returns result: None.
    """
    initialize_chat_store()
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO chat_messages (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, created_at),
        )
        connection.commit()


def clear_session(session_id: str) -> None:
    """
    Delete all persisted messages for a given session.

    :param session_id: Session identifier to clear.

    :returns result: None.
    """
    initialize_chat_store()
    with _connect() as connection:
        connection.execute(
            "DELETE FROM chat_messages WHERE session_id = ?",
            (session_id,),
        )
        connection.commit()


def get_session_message_counts(session_id: str) -> dict[str, int]:
    """
    Return message counts for a session by role and total.

    :param session_id: Session identifier to inspect.

    :returns counts: Dictionary with total/user/assistant counts.
    """
    initialize_chat_store()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT role, COUNT(*) AS count
            FROM chat_messages
            WHERE session_id = ?
            GROUP BY role
            """,
            (session_id,),
        ).fetchall()

    counts = {"total": 0, "user": 0, "assistant": 0}
    for role, count in rows:
        normalized_role = str(role).lower()
        counts["total"] += int(count)
        if normalized_role in counts:
            counts[normalized_role] = int(count)
    return counts


def delete_last_message(session_id: str, role: str | None = None) -> bool:
    """
    Delete the most recent message for a session (optionally filtered by role).

    :param session_id: Session identifier to update.
    :param role: Optional role filter (for example "assistant" or "user").

    :returns did_delete: True when a message was removed.
    """
    initialize_chat_store()
    with _connect() as connection:
        if role is None:
            row = connection.execute(
                """
                SELECT id
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
        else:
            row = connection.execute(
                """
                SELECT id
                FROM chat_messages
                WHERE session_id = ? AND role = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id, role),
            ).fetchone()
        if row is None:
            return False
        connection.execute(
            "DELETE FROM chat_messages WHERE id = ?",
            (row[0],),
        )
        connection.commit()
        return True


def delete_last_assistant_message(session_id: str) -> bool:
    """
    Delete the most recent assistant message for a session.

    :param session_id: Session identifier to update.

    :returns did_delete: True when a message was removed.
    """
    return delete_last_message(session_id, role="assistant")
