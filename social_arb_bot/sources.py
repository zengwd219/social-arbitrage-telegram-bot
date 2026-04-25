from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List

import requests

from .config import BrandConfig
from .models import Mention

USER_AGENT = "social-arb-bot/0.1 (research monitor)"
POSITIVE_WORDS = {
    "bullish",
    "beat",
    "growth",
    "love",
    "buy",
    "winner",
    "popular",
    "viral",
    "hot",
    "surge",
    "strong",
}
NEGATIVE_WORDS = {
    "bearish",
    "miss",
    "hate",
    "sell",
    "weak",
    "risk",
    "lawsuit",
    "down",
    "drop",
    "problem",
}


def _sentiment_score(text: str) -> float:
    tokens = [token.strip(".,!?:;()[]{}\"'").lower() for token in text.split()]
    if not tokens:
        return 0.0
    positive = sum(1 for token in tokens if token in POSITIVE_WORDS)
    negative = sum(1 for token in tokens if token in NEGATIVE_WORDS)
    return (positive - negative) / max(1, len(tokens))


def _within_days(published_at: datetime, days: int = 7) -> bool:
    now = datetime.now(timezone.utc)
    return published_at >= now - timedelta(days=days)


def fetch_reddit_mentions(
    session: requests.Session,
    brand: BrandConfig,
    subreddits: List[str],
    limit_per_keyword: int,
) -> List[Mention]:
    mentions: List[Mention] = []
    headers = {"User-Agent": USER_AGENT}

    for keyword in brand.keywords:
        for subreddit in subreddits:
            response = session.get(
                "https://www.reddit.com/search.json",
                params={
                    "q": f'"{keyword}" subreddit:{subreddit}',
                    "sort": "new",
                    "t": "week",
                    "limit": limit_per_keyword,
                },
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            posts = payload.get("data", {}).get("children", [])
            for post in posts:
                data = post.get("data", {})
                created_utc = data.get("created_utc")
                permalink = data.get("permalink")
                if not created_utc or not permalink:
                    continue
                published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                if not _within_days(published_at):
                    continue
                title = data.get("title", "")
                body = data.get("selftext", "")
                mentions.append(
                    Mention(
                        source="reddit",
                        keyword=keyword,
                        title=title,
                        url=f"https://www.reddit.com{permalink}",
                        published_at=published_at,
                        score=float(data.get("score", 0)),
                        sentiment=_sentiment_score(f"{title} {body}"),
                    )
                )
    return mentions


def fetch_youtube_mentions(
    session: requests.Session,
    brand: BrandConfig,
    api_key: str,
    max_results_per_keyword: int,
) -> List[Mention]:
    if not api_key:
        return []

    mentions: List[Mention] = []
    published_after = (
        datetime.now(timezone.utc) - timedelta(days=7)
    ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for keyword in brand.keywords:
        response = session.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "date",
                "publishedAfter": published_after,
                "maxResults": max_results_per_keyword,
                "key": api_key,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId")
            published_at_raw = snippet.get("publishedAt")
            if not video_id or not published_at_raw:
                continue
            published_at = datetime.fromisoformat(
                published_at_raw.replace("Z", "+00:00")
            ).astimezone(timezone.utc)
            mentions.append(
                Mention(
                    source="youtube",
                    keyword=keyword,
                    title=snippet.get("title", ""),
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    published_at=published_at,
                    sentiment=_sentiment_score(
                        f"{snippet.get('title', '')} {snippet.get('description', '')}"
                    ),
                )
            )
    return mentions


def fetch_google_trends_snapshot(
    session: requests.Session,
    brand: BrandConfig,
    serpapi_key: str,
    geo: str,
    timeframe: str,
) -> Dict[str, float]:
    if not serpapi_key:
        return {}

    keyword = brand.keywords[0]
    response = session.get(
        "https://serpapi.com/search.json",
        params={
            "engine": "google_trends",
            "q": keyword,
            "date": timeframe,
            "geo": geo,
            "api_key": serpapi_key,
        },
        timeout=25,
    )
    response.raise_for_status()
    payload = response.json()
    timeline = payload.get("interest_over_time", {}).get("timeline_data", [])
    values = []
    for point in timeline[-8:]:
        extracted = point.get("values", [])
        if extracted:
            values.append(float(extracted[0].get("extracted_value", 0)))
    if not values:
        return {}
    recent = values[-1]
    baseline = sum(values[:-1]) / max(1, len(values) - 1)
    return {
        "trend_recent": recent,
        "trend_baseline": baseline,
        "trend_velocity": recent / max(1.0, baseline),
    }


def fetch_stock_change_5d(session: requests.Session, ticker: str) -> float:
    response = session.get(
        "https://query1.finance.yahoo.com/v8/finance/chart/{}".format(ticker),
        params={"interval": "1d", "range": "5d"},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    result = payload.get("chart", {}).get("result", [])
    if not result:
        return 0.0
    prices = result[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
    cleaned = [price for price in prices if isinstance(price, (int, float))]
    if len(cleaned) < 2:
        return 0.0
    return ((cleaned[-1] - cleaned[0]) / cleaned[0]) * 100
