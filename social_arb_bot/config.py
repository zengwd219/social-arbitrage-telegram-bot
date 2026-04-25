from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class BrandConfig:
    name: str
    ticker: str
    sector: str
    keywords: List[str]


@dataclass
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    youtube_api_key: str
    serpapi_key: str


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_settings(project_root: Path) -> Settings:
    load_env_file(project_root / ".env")
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        youtube_api_key=os.getenv("YOUTUBE_API_KEY", ""),
        serpapi_key=os.getenv("SERPAPI_KEY", ""),
    )


def load_watchlist(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["brands"] = [BrandConfig(**brand) for brand in data.get("brands", [])]
    return data
