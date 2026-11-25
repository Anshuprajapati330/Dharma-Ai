"""Persistent, per-user chat history for Dharma-AI."""

import json
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

STORE_PATH = Path(__file__).resolve().parent / "dharma_chat_history.json"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _read_store():
    if not STORE_PATH.exists():
        return {}
    try:
        data = json.loads(STORE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_store(data):
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix="dharma_chat_",
        suffix=".tmp",
        dir=str(STORE_PATH.parent),
    )
    try:
        with open(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        Path(temp_name).replace(STORE_PATH)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def _make_title(text):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    text = re.sub(
        r"^(please|can you|could you|tell me|i want to know)\s+",
        "",
        text,
        flags=re.I,
    )

    if not text:
        return "New Chat"

    words = text.split()
    title = " ".join(words[:8])
    if len(words) > 8:
        title += "…"

    if len(title) > 48:
        title = title[:45].rstrip() + "…"

    return title[0].upper() + title[1:]


def list_chats(username):
    if not username:
        return []

    data = _read_store()
    chats = data.get(str(username), [])

    if not isinstance(chats, list):
        return []

    chats = [
        chat for chat in chats
        if isinstance(chat, dict)
        and isinstance(chat.get("messages"), list)
        and chat.get("messages")
    ]

    chats.sort(
        key=lambda chat: chat.get("updated_at", ""),
        reverse=True,
    )
    return chats


def save_message(username, chat_id, messages):
    """Create/update one complete conversation."""
    if not username:
        return None

    username = str(username)
    data = _read_store()

    user_chats = data.setdefault(username, [])
    if not isinstance(user_chats, list):
        user_chats = []
        data[username] = user_chats

    normalized = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        if not message.get("role"):
            continue

        item = {
            "role": str(message["role"]),
            "content": str(message.get("content", "")),
        }

        if message.get("mode") is not None:
            item["mode"] = str(message["mode"])

        normalized.append(item)

    now = _now()

    existing = None
    for chat in user_chats:
        if str(chat.get("id")) == str(chat_id):
            existing = chat
            break

    if existing is None:
        first_user_message = next(
            (
                m["content"]
                for m in normalized
                if m.get("role") == "user"
            ),
            "",
        )

        existing = {
            "id": str(chat_id or uuid.uuid4()),
            "title": _make_title(first_user_message),
            "created_at": now,
            "updated_at": now,
            "messages": normalized,
        }

        user_chats.append(existing)

    else:
        existing["messages"] = normalized
        existing["updated_at"] = now

        if not existing.get("title"):
            first_user_message = next(
                (
                    m["content"]
                    for m in normalized
                    if m.get("role") == "user"
                ),
                "",
            )
            existing["title"] = _make_title(first_user_message)

    _write_store(data)
    return existing
