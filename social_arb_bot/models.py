from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class Mention:
    source: str
    keyword: str
    title: str
    url: str
    published_at: datetime
    score: float = 0.0
    sentiment: float = 0.0


@dataclass
class BrandSignal:
    brand: str
    ticker: str
    sector: str
    keywords: List[str]
    mentions: List[Mention] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    stock_change_5d: float = 0.0
    score: float = 0.0
    risk_level: str = "medium"
    note: str = ""
