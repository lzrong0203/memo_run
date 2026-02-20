---
name: threads-monitor
description: 自動監控 Threads 社群平台的輿情內容，使用關鍵字搜尋、自適應文字抽取、雙重過濾（硬性排除 + AI 語意分析）、去重處理，並觸發戰報生成和通知發送。
user-invocable: true
homepage: https://github.com/lzrong0203/memo_run
metadata: {"openclaw": {"emoji": "🔍", "primaryEnv": "ANTHROPIC_API_KEY", "requires": {"binaries": ["python3"], "envVars": ["ANTHROPIC_API_KEY"]}}}
---

# Threads 社群輿情監控 Skill

## 重要執行規則

> **你必須直接執行以下所有步驟，不要委派給子 agent。**
> **使用 browser profile "openclaw"，在同一個 tab 中操作，不要開新 tab。**
> **所有 Python 指令都必須使用絕對路徑 `/Users/steveopenclaw/.openclaw/workspace/memo_run/`。**
> **每個步驟必須按順序執行，不可跳過。**

## 使用方式

```bash
# 指定關鍵字
openclaw agent --message "執行 threads-monitor 監控 關鍵字:黃國昌" --local --channel telegram

# 多個關鍵字
openclaw agent --message "執行 threads-monitor 監控 關鍵字:內湖,黃國昌" --local --channel telegram

# 使用設定檔所有啟用的關鍵字
openclaw agent --message "執行 threads-monitor 監控" --local --channel telegram

# Cron（每 30 分鐘）
openclaw cron add "*/30 * * * *" "openclaw agent --message '執行 threads-monitor 監控' --local --channel telegram"
```

## 工作流程

### 步驟 1: 判斷關鍵字來源

- 訊息包含 `關鍵字:XXX` → 搜尋該關鍵字（逗號分隔多個）
- 訊息未指定 → 讀取設定檔：
  ```bash
  cat /Users/steveopenclaw/.openclaw/workspace/memo_run/config/keywords.yml
  ```
  取得 `enabled: true` 的關鍵字列表。

### 步驟 2: 開啟 Threads 搜尋

對每個關鍵字，先在 Telegram 回報：`🔍 正在搜尋關鍵字: [名稱]（第 N/M 個）`

然後導航（**必須加 `&filter=recent`**）：
```
browser navigate https://www.threads.net/search?q=關鍵字&filter=recent
browser wait --time 5000
```

> 不做 snapshot，直接進入步驟 3。

### 步驟 3: 連續滾動載入內容

**最多 5 輪，每輪：**

1. `browser execute document.body.scrollHeight`（記錄高度）
2. `browser execute window.scrollTo(0, document.body.scrollHeight)`
3. `browser wait --time 3000`
4. `browser execute window.scrollTo(0, document.body.scrollHeight)`
5. `browser wait --time 2000`
6. `browser execute document.body.scrollHeight`（比較高度）
   - 高度增加 → 繼續下一輪
   - 高度不變 → 已到底，停止

### 步驟 4: 抽取頁面文字與貼文連結

滾動結束後，執行一次 JS 取得頁面可見文字 + 所有貼文連結：

```
browser execute (function(){var t=document.body.innerText;var l=[];var s=new Set();document.querySelectorAll('a[href]').forEach(function(a){if(a.href&&a.href.includes('/post/')&&!s.has(a.href)){s.add(a.href);l.push(a.href)}});return JSON.stringify({text:t.substring(0,20000),post_links:l})})()
```

> **設計理念**：
> - `a[href]` 是 HTML 通用語法，`/post/` 是 Threads URL 基本結構，兩者都極少變動
> - **不依賴任何 DOM 結構或 CSS class**，文字解析全部交給 AI
> - 比 `browser snapshot` 輕量（只有可見文字，不含 accessibility tree 元資料）

### 步驟 4b: AI 解析貼文

根據步驟 4 回傳的 `text`（頁面可見文字）和 `post_links`（貼文連結），你需要：

1. 從 `text` 中識別每篇貼文的**內容**和**作者**
2. 從 `post_links` 中的 `/@username/post/` 格式輔助辨識作者
3. 將貼文內容配對到對應的連結
4. 整理成以下 JSON：

```json
[
  {
    "content": "貼文內容文字",
    "author": "作者名稱",
    "link": "https://www.threads.net/@作者/post/ID"
  }
]
```

**規則**：
- 每個關鍵字最多 20 篇
- 內容 < 15 字的貼文丟棄
- 回報進度：`📥 抽取完成: 找到 N 篇貼文`

#### Fallback（僅在解析結果 0 篇時）

1. `browser snapshot` 一次，觀察頁面內容
2. 從 snapshot 文字中手動提取貼文
3. 若仍為 0 篇，記錄到 health.log 並繼續下個關鍵字

### 步驟 5: 批次處理（過濾 + 去重 + 評分）

```bash
echo '步驟4b的JSON陣列' | python3 /Users/steveopenclaw/.openclaw/workspace/memo_run/src/pipeline.py
```

回報 pipeline 的 `summary` 到 Telegram，例如：
```
📊 [關鍵字] 掃描 12 篇 → 過濾 3 篇 → 重複 2 篇 → 有效 7 篇
```

若 `needs_more` 為 `true`，回到步驟 3 繼續滾動（最多重試 3 輪）。

### 步驟 6: AI 語意分析

對 `passed_posts` 每篇貼文分析：

- `categories`：政治/社會/交通/民生/犯罪/環境/教育/經濟/其他
- `importance`：1-10（9-10 為大魚）
- `summary`：一句話摘要（30-80 字）
- `entities`：`{persons, locations, organizations}`
- `reasoning`：判斷理由

IRRELEVANT 的貼文（純私人、閒聊、廣告）不放入結果。

組成完整 JSON 存入 `/tmp/threads_analysis.json`：

```json
{
  "timestamp": "ISO 時間",
  "keywords": ["關鍵字"],
  "analyzed_posts": [
    {
      "id": "post_001",
      "content": "原始內容",
      "author": "作者",
      "link": "連結",
      "analysis": {
        "categories": ["政治"],
        "importance": 8,
        "summary": "摘要",
        "entities": {"persons": [], "locations": [], "organizations": []},
        "reasoning": "理由"
      }
    }
  ],
  "stats": {
    "total_searched": 20,
    "filtered_by_hard_rules": 10,
    "filtered_by_dedup": 3,
    "filtered_by_ai": 2,
    "valid_count": 5
  }
}
```

### 步驟 7: 生成戰報並發送通知

> **⛔ 絕對禁止自行撰寫通知訊息。必須使用程式輸出，原封不動複製。**

**7a. 生成戰報 + Gist + 摘要：**

```bash
python3 /Users/steveopenclaw/.openclaw/workspace/memo_run/src/report_generator.py --input /tmp/threads_analysis.json --format all --gist
```

**7b. 發送 LINE（從輸出中 `=== LINE 摘要 ===` 到 `=== Telegram 摘要 ===` 之間的文字完整複製）：**

```bash
python3 /Users/steveopenclaw/.openclaw/workspace/memo_run/src/line_notify.py --broadcast --message "複製的 LINE 摘要完整文字"
```

**7c. 發送 Telegram（從輸出中 `=== Telegram 摘要 ===` 之後的文字完整複製到 Telegram channel）。**

> 訊息必須包含所有貼文連結和完整戰報 Gist 連結。不要加入程式沒有輸出的符號。

### 步驟 8: 健康檢查

```bash
echo "$(date -Iseconds) | keywords=N | valid=N | fallback=yes/no | status=success/partial/fail" >> /Users/steveopenclaw/.openclaw/workspace/memo_run/data/health.log
```

**異常告警（透過 Telegram）：**
- 所有關鍵字有效貼文 = 0 → 告警
- 觸發了 Fallback → 告警
- 連續 3 筆 health.log 都是 fail/fallback → 緊急告警

## 環境變數

```bash
ANTHROPIC_API_KEY=sk-ant-xxx           # 必需
MIN_VALID_POSTS=10                     # 可選（預設 10）
THREADS_USERNAME=your_username         # 可選（僅首次登入）
THREADS_PASSWORD=your_password         # 可選（僅首次登入）
```

## 設定檔格式

### config/keywords.yml
```yaml
keywords:
  - keyword: "內湖"
    enabled: true
  - keyword: "台北"
    enabled: false

patrol:
  interval_minutes: 30
  delay_between_keywords_seconds: 7
```

### config/filters.yml
```yaml
hard_exclude:
  - "預售屋"
  - "建案推薦"
  - "限時特價"

priority_keep_keywords:
  - "警方"
  - "逮捕"

min_content_length: 30
```

## Rate Limiting

- 每個關鍵字搜尋間隔 7-10 秒（隨機）
- 單次最多 100 筆貼文

---

**版本**: 4.0.0
**最後更新**: 2026-02-20
**核心改進**: innerText + LLM 自適應解析（取代 v3.0.0 寫死 JS selector）
