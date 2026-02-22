---
name: report-generator
description: 接收 Threads 監控 JSON，產出結構化戰報（Markdown + Gist），並透過 Telegram + LINE 雙通道發送通知摘要。
user-invocable: true
homepage: https://github.com/lzrong0203/memo_run
metadata: {"openclaw": {"emoji": "📊", "primaryEnv": "ANTHROPIC_API_KEY", "requires": {"binaries": ["python3"], "envVars": ["ANTHROPIC_API_KEY", "LINE_CHANNEL_ACCESS_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]}}}
---

# 戰報生成與通知 Skill

## 重要執行規則

> **你必須直接執行以下所有步驟，不要委派給子 agent。**
> **所有 Python 指令使用絕對路徑 `/Users/steveopenclaw/.openclaw/workspace/memo_run/`。**
> **⛔ 絕對禁止自行撰寫通知訊息。必須原封不動使用 report_generator.py 的輸出。**

## 使用方式

```bash
# 由 threads-monitor 步驟 7 自動觸發（推薦）

# 獨立使用（需先準備 /tmp/threads_analysis.json）
openclaw agent --message "使用 /tmp/threads_analysis.json 產生戰報" --local --channel telegram
```

## 工作流程

### 步驟 1: 驗證輸入

讀取 `/tmp/threads_analysis.json`，確認：
- 檔案存在且為有效 JSON
- `analyzed_posts` 陣列不為空
- 若為空，回報「本次無有效貼文，未產生戰報」並結束

### 步驟 2: 生成戰報

```bash
python3 /Users/steveopenclaw/.openclaw/workspace/memo_run/src/report_generator.py --input /tmp/threads_analysis.json --format all --gist
```

程式輸出包含：
1. 戰報儲存路徑（`data/reports/report_YYYYMMDD_HHMMSS.md`）
2. Gist URL
3. `=== LINE 摘要 ===` 區塊
4. `=== Telegram 摘要 ===` 區塊

### 步驟 3: 發送 Telegram 通知

從輸出中找到 `=== Telegram 摘要 ===` 之後的文字，**完整複製**發送到 Telegram channel。

### 步驟 4: 發送 LINE 通知

從輸出中找到 `=== LINE 摘要 ===` 到 `=== Telegram 摘要 ===` 之間的文字，**完整複製**：

```bash
python3 /Users/steveopenclaw/.openclaw/workspace/memo_run/src/line_notify.py --broadcast --message "複製的 LINE 摘要完整文字"
```

> **必須包含**：所有貼文連結 `→ https://www.threads.net/...` 和完整戰報 Gist 連結。
> **不要加入**任何 report_generator.py 沒有輸出的符號（如 ⭐、🔴🟡🟢、━━━）。

## AI 分類參考（供 threads-monitor 步驟 6 使用）

### 類別
政治 | 社會 | 交通 | 民生 | 投訴 | 教育 | 環保 | 醫療 | 其他

### 重要性評分
- 9-10（大魚）：重大政策變動、嚴重事件、大規模影響
- 7-8（中魚）：區域性重要議題
- 5-6（小魚）：一般性討論
- 1-4（小蝦米）：個人意見、邊緣議題

### 大魚識別條件（任一成立）
- `importance` ≥ 9
- `categories` ≥ 3 個且 `importance` ≥ 8
- 包含敏感關鍵字（市長/總統/立委/貪污/弊案/詐騙/毒品/死亡/抗議/環評）且 `importance` ≥ 7

## 環境變數

```bash
ANTHROPIC_API_KEY=sk-ant-xxx                  # 必需
LINE_CHANNEL_ACCESS_TOKEN=your_token          # 必需（LINE 通知）
LINE_USER_ID=Uxxxxxxxx                        # 可選（push 模式，broadcast 不需要）
TELEGRAM_BOT_TOKEN=your_bot_token             # 必需
TELEGRAM_CHAT_ID=your_chat_id                 # 必需
```

## 錯誤處理

- report_generator.py 失敗 → 記錄錯誤，嘗試至少發送純文字摘要
- LINE 通知失敗 → 記錄錯誤，不中斷 Telegram 通知
- Telegram 通知失敗 → 記錄錯誤，不中斷 LINE 通知

---

**版本**: 2.0.0
**最後更新**: 2026-02-20
