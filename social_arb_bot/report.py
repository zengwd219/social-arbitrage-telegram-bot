from __future__ import annotations

from datetime import datetime
from typing import List

from .models import BrandSignal


def _fmt_float(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def render_weekly_report(signals: List[BrandSignal], top_n: int) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    top_signals = sorted(signals, key=lambda item: item.score, reverse=True)[:top_n]

    lines = [
        f"社交套利周报 | {now}",
        "",
        "方法说明：基于 Reddit / YouTube / Google Trends 的热度、加速度、情绪和近 5 日股价反应做启发式排序。",
        "",
        "本周优先观察：",
    ]

    if not top_signals:
        lines.append("暂无足够信号，建议扩充 watchlist 或检查 API 配置。")
        return "\n".join(lines)

    for index, signal in enumerate(top_signals, start=1):
        metrics = signal.metrics
        lines.extend(
            [
                f"{index}. {signal.brand} ({signal.ticker}) | 综合分 {_fmt_float(signal.score)} | 风险 {signal.risk_level}",
                f"关键词：{', '.join(signal.keywords[:3])}",
                (
                    "热度："
                    f"总提及 {int(metrics.get('total_mentions', 0))}，"
                    f"近 3 日 {int(metrics.get('recent_mentions_3d', 0))}，"
                    f"速度 {_fmt_float(metrics.get('velocity', 0.0))}"
                ),
                (
                    "情绪与市场："
                    f"情绪 {_fmt_float(metrics.get('avg_sentiment', 0.0))}，"
                    f"近 5 日股价 {_fmt_float(signal.stock_change_5d)}%"
                ),
            ]
        )

        trend_velocity = metrics.get("trend_velocity")
        if trend_velocity is not None:
            lines.append(f"搜索趋势：Google Trends 速度 {_fmt_float(trend_velocity)}")

        lines.append(f"策略提示：{signal.note}")

        if signal.mentions:
            lines.append("样本：")
            for mention in signal.mentions[:3]:
                source = mention.source.upper()
                lines.append(f"- [{source}] {mention.title[:100]}")
        lines.append("")

    lines.extend(
        [
            "风险提示：",
            "- 本简报是研究监控，不构成投资建议。",
            "- 社交热度可能被营销、机器人账号和短期事件放大。",
            "- 对于高波动标的，建议结合财报日历、流动性和仓位规则。",
        ]
    )
    return "\n".join(lines).strip()
