# Findings & Decisions

## Requirements
- 每 30 分鐘自動監控 Threads 搜尋頁面
- 支援多組關鍵字（地區、人名）
- 雙重過濾：硬性排除詞 + AI 語意分析
- AI 產出分類戰報（政治/交通/社會/投訴）
- 重大議題「大魚」標記
- 透過 Telegram + LINE 雙通道通知
- 支援自動巡邏 + 手動指令
- Docker 部署

## Research Findings
- **Threads 官方 API**: 有 keyword search 但限 500 次/7天，不夠用
- **OpenClaw**: 開源 AI Agent 框架，Node.js，內建 Browser(CDP) + Cron + Telegram
- **OpenClaw Browser**: 持久 Chrome Profile，登入一次永久使用，Snapshot 系統讓 AI 理解頁面
- **OpenClaw Cron**: 五欄 cron 表達式，jobs 持久化在 ~/.openclaw/cron/，支援 session 隔離
- **OpenClaw Telegram**: 原生支援（grammY 框架），DM 共享 main session，群組隔離
- **OpenClaw LINE**: 不原生支援，需自製 skill
- **NanoClaw**: 更輕量替代品（Anthropic Agent SDK），但 browser 控制力不如 OpenClaw
- **朋友的 code 邏輯**: Selenium + 已登入 Chrome Profile + 硬性排除詞 + Gemini AI 分析 + Telegram/Discord 通知

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| OpenClaw 而非純 Playwright | AI 理解頁面語義，Threads 改版不需改 code |
| OpenClaw 而非 NanoClaw | OpenClaw 有完整 CDP browser 控制 + Snapshot |
| Python CLI 工具給 Agent 呼叫 | filter.py, dedup.py, line_notify.py 作為 shell tools |
| SQLite 去重 | 輕量、Docker volume 友好、WAL mode 穩定 |
| YAML 設定檔 | 易讀易改，不需重啟服務 |
| 雙重過濾 | 硬性詞排雜訊（快速），AI 做語意分析（精準） |

## Resources
- OpenClaw Docs: https://docs.openclaw.ai
- OpenClaw Browser: https://docs.openclaw.ai/tools/browser
- OpenClaw Cron: https://docs.openclaw.ai/automation/cron-jobs
- OpenClaw Telegram: https://docs.openclaw.ai/channels/telegram
- LINE Messaging API: https://developers.line.biz/en/docs/messaging-api/

## Visual/Browser Findings
- Threads 搜尋 URL 格式: `https://www.threads.net/search?q={keyword}`
- 搜尋結果有「最近」/「Recent」標籤可切換
- 貼文連結格式: `/post/` 路徑
- 需多次捲動載入更多結果（朋友的 code 捲 25 次）

---
*Update this file after every 2 view/browser/search operations*
