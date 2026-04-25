from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import requests

from social_arb_bot.config import load_settings, load_watchlist
from social_arb_bot.report import render_weekly_report
from social_arb_bot.scoring import build_brand_signal
from social_arb_bot.sources import (
    fetch_google_trends_snapshot,
    fetch_reddit_mentions,
    fetch_stock_change_5d,
    fetch_youtube_mentions,
)
from social_arb_bot.telegram_bot import send_telegram_message


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and send a social arbitrage brief.")
    parser.add_argument(
        "--config",
        default="config/watchlist.json",
        help="Path to the watchlist JSON config.",
    )
    parser.add_argument(
        "--send-telegram",
        action="store_true",
        help="Send the generated report to Telegram.",
    )
    return parser.parse_args()


def collect_signals(config_path: Path) -> str:
    project_root = Path(__file__).resolve().parent
    settings = load_settings(project_root)
    watchlist = load_watchlist(config_path)
    session = requests.Session()
    signals = []

    reddit_cfg = watchlist.get("reddit", {})
    youtube_cfg = watchlist.get("youtube", {})
    trends_cfg = watchlist.get("google_trends", {})
    risk_rules = watchlist.get("risk_rules", {})

    for brand in watchlist["brands"]:
        mentions: List = []
        try:
            mentions.extend(
                fetch_reddit_mentions(
                    session=session,
                    brand=brand,
                    subreddits=reddit_cfg.get("subreddits", []),
                    limit_per_keyword=reddit_cfg.get("limit_per_keyword", 25),
                )
            )
        except requests.RequestException:
            pass

        try:
            mentions.extend(
                fetch_youtube_mentions(
                    session=session,
                    brand=brand,
                    api_key=settings.youtube_api_key,
                    max_results_per_keyword=youtube_cfg.get("max_results_per_keyword", 10),
                )
            )
        except requests.RequestException:
            pass

        deduped = {}
        for mention in mentions:
            deduped[mention.url] = mention

        try:
            trend_metrics = fetch_google_trends_snapshot(
                session=session,
                brand=brand,
                serpapi_key=settings.serpapi_key,
                geo=trends_cfg.get("geo", "US"),
                timeframe=trends_cfg.get("timeframe", "today 3-m"),
            )
        except requests.RequestException:
            trend_metrics = {}

        try:
            stock_change_5d = fetch_stock_change_5d(session, brand.ticker)
        except requests.RequestException:
            stock_change_5d = 0.0
        signal = build_brand_signal(
            brand=brand,
            mentions=list(deduped.values()),
            trend_metrics=trend_metrics,
            stock_change_5d=stock_change_5d,
            risk_rules=risk_rules,
        )
        signals.append(signal)

    return render_weekly_report(signals, top_n=watchlist.get("top_n", 5))


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).resolve()
    report = collect_signals(config_path)
    print(report)

    if args.send_telegram:
        project_root = Path(__file__).resolve().parent
        settings = load_settings(project_root)
        send_telegram_message(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            text=report,
        )


if __name__ == "__main__":
    main()
