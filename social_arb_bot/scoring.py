from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Dict

from .config import BrandConfig
from .models import BrandSignal


def build_brand_signal(
    brand: BrandConfig,
    mentions,
    trend_metrics: Dict[str, float],
    stock_change_5d: float,
    risk_rules: Dict[str, float],
) -> BrandSignal:
    now = datetime.now(timezone.utc)
    recent_cutoff = now - timedelta(days=3)
    recent_mentions = [mention for mention in mentions if mention.published_at >= recent_cutoff]
    older_mentions = [mention for mention in mentions if mention.published_at < recent_cutoff]
    total_mentions = len(mentions)
    recent_count = len(recent_mentions)
    older_count = len(older_mentions)
    velocity = recent_count / max(1, older_count)
    avg_sentiment = mean([mention.sentiment for mention in mentions]) if mentions else 0.0
    source_diversity = len({mention.source for mention in mentions})
    trend_velocity = trend_metrics.get("trend_velocity", 1.0)

    score = (
        total_mentions * 0.35
        + velocity * 25
        + avg_sentiment * 100
        + source_diversity * 8
        + (trend_velocity - 1.0) * 15
        - abs(min(stock_change_5d, 0.0)) * 0.25
    )

    high_velocity_threshold = risk_rules.get("high_velocity_threshold", 1.8)
    min_total_mentions = risk_rules.get("min_total_mentions", 4)

    if total_mentions < min_total_mentions:
        risk_level = "high"
        note = "社交样本偏少，容易被单一事件误导。"
    elif velocity >= high_velocity_threshold and avg_sentiment > 0:
        risk_level = "medium"
        note = "热度加速明显，但需防止事件驱动的短期回落。"
    else:
        risk_level = "medium-high"
        note = "热度存在，但尚未形成非常强的跨平台共振。"

    signal = BrandSignal(
        brand=brand.name,
        ticker=brand.ticker,
        sector=brand.sector,
        keywords=brand.keywords,
        mentions=sorted(mentions, key=lambda item: item.published_at, reverse=True),
        metrics={
            "total_mentions": float(total_mentions),
            "recent_mentions_3d": float(recent_count),
            "older_mentions_4d": float(older_count),
            "velocity": velocity,
            "avg_sentiment": avg_sentiment,
            "source_diversity": float(source_diversity),
            **trend_metrics,
        },
        stock_change_5d=stock_change_5d,
        score=score,
        risk_level=risk_level,
        note=note,
    )
    return signal
