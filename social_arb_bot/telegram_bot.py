from __future__ import annotations

from typing import List

import requests


def _chunk_message(text: str, limit: int = 3500) -> List[str]:
    if len(text) <= limit:
        return [text]

    chunks = []
    current = []
    current_length = 0
    for line in text.splitlines():
        line_length = len(line) + 1
        if current and current_length + line_length > limit:
            chunks.append("\n".join(current))
            current = [line]
            current_length = line_length
        else:
            current.append(line)
            current_length += line_length
    if current:
        chunks.append("\n".join(current))
    return chunks


def send_telegram_message(bot_token: str, chat_id: str, text: str) -> None:
    if not bot_token or not chat_id:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")

    for chunk in _chunk_message(text):
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": chunk},
            timeout=20,
        )
        response.raise_for_status()
