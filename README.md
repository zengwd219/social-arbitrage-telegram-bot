# Social Arbitrage Telegram Bot

一个面向“社交热度领先、股价后反应”场景的监控机器人。当前版本会每周扫描配置里的品牌/公司关键词，汇总：

- Reddit 讨论热度
- YouTube 新增评测/讨论视频
- Google Trends 搜索速度
- 相关股票近 5 日价格变化

然后生成一份简报，并发送到 Telegram。

## 当前实现范围

已实现：

- Reddit：通过 RSS 搜索公开帖子
- YouTube：通过 YouTube Data API 搜索近 7 天视频
- Google Trends：通过 SerpApi 获取趋势快照
- 股票：通过 Yahoo Finance 公共接口获取近 5 日价格变化
- Telegram：通过 Bot API 发送周报
- GitHub Actions：每周自动运行一次

已预留但未直接接入：

- TikTok
- X / Twitter
- Instagram
- Amazon / App Store
- Discord / Telegram 群组

这些平台多数需要官方 API 权限、商业数据源或更稳定的第三方采集服务。当前项目结构已经可以继续往里扩展。

## 快速开始

1. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. 配置环境变量

```bash
cp .env.example .env
```

填写：

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `YOUTUBE_API_KEY`
- `SERPAPI_KEY`

3. 配置监控标的

```bash
cp config/watchlist.example.json config/watchlist.json
```

按你的策略修改 `config/watchlist.json`，为每个品牌指定：

- `name`
- `ticker`
- `sector`
- `keywords`

4. 本地运行

```bash
python main.py
python main.py --send-telegram
```

## Telegram 配置

1. 在 Telegram 里创建一个 bot，拿到 token。
2. 把 bot 拉进你要接收消息的私聊或群。
3. 通过 Telegram API 或机器人工具拿到 `chat_id`。
4. 写入 `.env`。

## 自动发送

仓库里已经带了 GitHub Actions 工作流：

- 文件：`.github/workflows/weekly_report.yml`
- 计划时间：每周一北京时间 09:00

你需要在 GitHub 仓库 Secrets 里设置：

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `YOUTUBE_API_KEY`
- `SERPAPI_KEY`

## 评分逻辑

当前是启发式评分，不是机器学习模型。综合考虑：

- 总提及量
- 近 3 日 / 前 4 日的热度速度
- 标题情绪
- 跨平台来源数量
- Google Trends 搜索速度
- 股票近 5 日表现

适合做每周研究简报，不适合直接当成自动交易信号。

## 建议的下一步增强

- 接入大模型摘要，把“为什么上榜”写得更像投研简报
- 给 TikTok / X / Instagram 接第三方数据源
- 增加行业映射，一个热点自动关联多个受益公司
- 增加回测模块，验证社交热度与未来收益的相关性
- 输出 CSV / Notion / Google Sheets 历史记录

## 风险说明

- 这不是投资建议。
- 社交热度信号很容易受刷量、营销投放、机器人账号影响。
- 医疗、制药、迷因股等主题波动极大，建议额外加入流动性和事件过滤规则。
