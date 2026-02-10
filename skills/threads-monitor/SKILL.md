---
name: threads-monitor
description: 自動監控 Threads 社群平台的輿情內容，使用關鍵字搜尋、雙重過濾（硬性排除 + AI 語意分析）、去重處理，並觸發戰報生成和通知發送。適用於每 30 分鐘定期執行的輿情監控任務。
user-invocable: true
homepage: https://github.com/lzrong0203/memo_run
metadata: {"openclaw": {"emoji": "🔍", "primaryEnv": "ANTHROPIC_API_KEY", "requires": {"binaries": ["python3"], "envVars": ["ANTHROPIC_API_KEY"]}}}
---

# Threads 社群輿情監控 Skill

## 概述

這個 Skill 會自動登入 Threads 平台，根據設定檔中的關鍵字進行搜尋，並透過雙重過濾機制（硬性排除詞 + AI 語意分析）篩選有價值的內容，最後產出分類戰報並發送通知。

## 重要執行規則

> **你必須直接執行以下所有步驟，不要委派給子 agent。**
> **使用 browser profile "openclaw"，在同一個 tab 中操作，不要開新 tab。**
> **所有 Python 指令都必須使用絕對路徑 `/Users/steveopenclaw/.openclaw/workspace/memo_run/`。**
> **每個步驟必須按順序執行，不可跳過。**
> **所有 Python exec 指令都會回傳 exit code 0，用輸出文字判斷結果。**

## 使用方式

### 手動觸發（指定關鍵字）
```bash
openclaw agent --message "執行 threads-monitor 監控 關鍵字:黃國昌" --local --channel telegram --session-id threads-monitor-manual
```

### 手動觸發（多個關鍵字）
```bash
openclaw agent --message "執行 threads-monitor 監控 關鍵字:內湖,黃國昌" --local --channel telegram --session-id threads-monitor-manual
```

### 手動觸發（使用設定檔中所有啟用的關鍵字）
```bash
openclaw agent --message "執行 threads-monitor 監控" --local --channel telegram --session-id threads-monitor-manual
```

### 設定定期執行（每 30 分鐘）
```bash
openclaw cron add "*/30 * * * *" "openclaw agent --message '執行 threads-monitor 監控' --local --channel telegram"
```

## 工作流程

### 步驟 1: 判斷關鍵字來源

**先檢查觸發訊息中是否有指定關鍵字：**

- 若訊息包含 `關鍵字:XXX`（例如「執行 threads-monitor 監控 關鍵字:黃國昌」），則只搜尋該關鍵字
- 若訊息包含多個關鍵字用逗號分隔（例如 `關鍵字:內湖,黃國昌`），則搜尋這些關鍵字
- 若訊息未指定關鍵字，則讀取設定檔

### 步驟 1b: 讀取設定檔（僅在未指定關鍵字時）

使用 exec 工具讀取設定檔：

```bash
cat /Users/steveopenclaw/.openclaw/workspace/memo_run/config/keywords.yml
```

從 `keywords.yml` 取得 `enabled: true` 的關鍵字列表。

### 步驟 2: 開啟 Threads 並搜尋

使用 browser 工具（profile: openclaw）：

1. 導航到搜尋頁面（在**當前 tab** 中，不要開新 tab），**必須加上 `&filter=recent` 以顯示最新貼文**：
   ```
   browser navigate https://www.threads.net/search?q=關鍵字&filter=recent
   ```
2. 等待頁面載入（等待 5 秒）：
   ```
   browser wait --time 5000
   ```
3. 先擷取第一頁快照，記錄目前看到的貼文數量：
   ```
   browser snapshot
   ```

### 步驟 3: 滑動載入更多貼文

**重複以下迴圈，最多滑動 5 次：**

每次滑動的完整流程：

1. 滑動頁面到底部（**必須用 `window.scrollTo`**）：
   ```
   browser execute window.scrollTo(0, document.body.scrollHeight)
   ```
2. **等待 5 秒**讓新內容載入（Threads 載入較慢，不要縮短）：
   ```
   browser wait --time 5000
   ```
3. **再滑一次**確保觸發載入：
   ```
   browser execute window.scrollTo(0, document.body.scrollHeight)
   ```
4. **再等 3 秒**：
   ```
   browser wait --time 3000
   ```
5. 擷取快照，檢查是否有新貼文出現：
   ```
   browser snapshot
   ```
6. 如果新快照中的貼文數量比上一次多，繼續滑動（回到步驟 1）
7. 如果新快照中的貼文數量沒有增加，表示已到底，停止滑動

> **注意**：每輪滑動要滑兩次+等待共 8 秒。Threads 的 infinite scroll 需要時間載入，等太短會漏掉貼文。

### 步驟 4: 提取貼文並整理為 JSON

從所有快照中彙整提取貼文資訊（去除重複），整理成 JSON 陣列格式：

```json
[
  {
    "content": "貼文內容文字",
    "author": "作者名稱",
    "link": "https://www.threads.net/@作者/post/ID"
  }
]
```

每個關鍵字最多抓取 20 筆最新貼文。

### 步驟 5: 批次處理（過濾 + 去重 + 評分，一次完成）

**將步驟 4 的 JSON 陣列透過 stdin 傳給 pipeline.py，一次完成所有處理：**

```bash
echo '步驟4的JSON陣列' | python3 /Users/steveopenclaw/.openclaw/workspace/memo_run/src/pipeline.py
```

pipeline.py 會一次完成：
- 硬性過濾（排除廣告、太短的內容）
- 去重（跳過已處理過的貼文）
- 評分加成（交通/民意代表等關鍵字加分）

**輸出是 JSON，包含：**
```json
{
  "passed_posts": [通過的貼文陣列],
  "filtered_count": 被過濾數量,
  "duplicate_count": 重複數量,
  "new_count": 有效新貼文數量,
  "total_input": 輸入總數,
  "summary": "掃描 12 篇 → 過濾 3 篇 → 重複 2 篇 → 有效 7 篇",
  "needs_more": true/false,
  "min_valid_posts": 10
}
```

### 步驟 5b: 不足則繼續搜尋（最多重試 3 輪）

**檢查 pipeline 輸出的 `needs_more` 欄位：**

- 若 `needs_more` 為 `false`（有效貼文已達標），直接進入步驟 6
- 若 `needs_more` 為 `true`（有效貼文不足），執行以下操作：
  1. 記錄目前累積的 `passed_posts`
  2. 回到步驟 3 繼續滑動（再滑 5 輪）
  3. 從新快照中提取**尚未送過 pipeline 的新貼文**
  4. 將新貼文再次送入 pipeline.py 處理
  5. 合併新舊 `passed_posts`，重新檢查 `needs_more`

**重試上限：最多額外重試 3 輪。** 若 3 輪後仍不足，以目前收集到的貼文繼續執行。

> **注意**：`MIN_VALID_POSTS` 可透過 `.env` 設定（預設 10）。pipeline.py 會自動讀取此環境變數。

### 步驟 6: AI 語意分析並組成 JSON

對 `passed_posts` 中的每篇貼文，使用你的 LLM 能力進行分析，並將結果組成以下 JSON 格式：

```json
{
  "timestamp": "2026-02-11T03:00:00Z",
  "keywords": ["內湖"],
  "analyzed_posts": [
    {
      "id": "post_001",
      "content": "貼文原始內容",
      "author": "作者名稱",
      "link": "https://www.threads.net/@作者/post/ID",
      "timestamp": "2026-02-11T02:30:00Z",
      "analysis": {
        "categories": ["政治", "社會"],
        "importance": 8,
        "summary": "一句話摘要",
        "entities": {"persons": [], "locations": [], "organizations": []},
        "reasoning": "判斷理由"
      }
    }
  ],
  "stats": {
    "total_searched": 20,
    "filtered_by_hard_rules": 16,
    "filtered_by_dedup": 0,
    "filtered_by_ai": 2,
    "valid_count": 2
  }
}
```

**分析規則：**
- 判斷每篇貼文是否與公共議題相關（政治、社會、交通、民生、犯罪等）
- IRRELEVANT 的貼文（純私人抱怨、閒聊、廣告）**不要放入 analyzed_posts**
- `importance` 評分 1-10（10 最重要）
- `categories` 從以下選擇：政治、社會、交通、民生、犯罪、環境、教育、經濟、其他
- `stats` 中的數字從步驟 5 的 pipeline 結果 + 你過濾的數量計算
- `id` 可用 `post_001`, `post_002` 等流水號

將完成的 JSON 存為檔案：

```bash
echo '上面的JSON' > /tmp/threads_analysis.json
```

### 步驟 7: 生成戰報並發送通知

**7a. 呼叫 report_generator.py 生成戰報 + 上傳 Gist + 產出 LINE 摘要：**

```bash
python3 /Users/steveopenclaw/.openclaw/workspace/memo_run/src/report_generator.py --input /tmp/threads_analysis.json --format all --gist
```

這個指令會：
- 生成 Markdown 戰報並儲存到 `data/reports/`
- 上傳戰報到 GitHub Gist（取得公開 URL）
- 輸出 LINE 摘要（含貼文連結 + Gist 戰報連結）

**輸出範例：**
```
報告已儲存: data/reports/report_20260211_030000.md
Gist URL: https://gist.github.com/xxx/yyy

=== LINE 摘要 ===
🔔 Threads 監控通知
📊 掃描 20 筆 → 有效 2 筆
🔑 關鍵字: 內湖

🐟 大魚警報（1 則）:
[9/10] 內湖驚傳隨機擄童事件
→ https://www.threads.net/@user/post/xxx

📋 其他重點:
• [政治] 內湖南港議員提名
  → https://www.threads.net/@user/post/yyy

📄 完整戰報: https://gist.github.com/xxx/yyy

=== Telegram 摘要 ===
...
```

**7b. 複製「=== LINE 摘要 ===」區塊的內容，用 line_notify.py 發送：**

```bash
python3 /Users/steveopenclaw/.openclaw/workspace/memo_run/src/line_notify.py --message "上面 LINE 摘要的完整文字"
```

> **重要**：LINE 摘要內容必須完整複製，包含所有貼文連結和 Gist 戰報連結。

## 環境變數需求

```bash
# 必需（OpenClaw 使用）
ANTHROPIC_API_KEY=sk-ant-xxx

# Pipeline 最少需要的有效貼文數，不足則繼續滑動搜尋（預設 10）
MIN_VALID_POSTS=10

# 可選（僅首次登入 Threads 時需要，之後可刪除）
THREADS_USERNAME=your_username
THREADS_PASSWORD=your_password
```

**安全提示**: Threads 登入後會儲存在 OpenClaw 的 persistent Chrome profile（browser profile: openclaw），不需要每次都提供密碼。

## 設定檔格式

### config/keywords.yml
```yaml
mission_mode: "政治/公關偵察"

keywords:
  - keyword: "內湖"
    enabled: true
  - keyword: "台北"
    enabled: false

patrol:
  interval_minutes: 30
  max_scroll_attempts: 20
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
  - "毒品"
  - "貪污"

min_content_length: 30
min_exclude_word_length: 2
```

## Rate Limiting

為避免被 Threads 平台偵測為機器人：
- 每次搜尋後等待 7-10 秒（隨機延遲）
- 每抓取 5 筆貼文後暫停 3 秒
- 單次執行最多處理 100 筆貼文

## 錯誤處理

- 若 Threads 登入失敗，記錄錯誤並終止執行
- 若網路連線問題，最多重試 3 次，每次間隔 10 秒
- 若 Python scripts 執行失敗，記錄錯誤並跳過該筆資料
- 若 SQLite 資料庫鎖定，等待 5 秒後重試

## Cron 排程建議

```bash
# 每 30 分鐘執行一次（使用 telegram channel 回報結果）
*/30 * * * * openclaw agent --message "執行 threads-monitor 監控" --local --channel telegram

# 或每小時的第 15 和 45 分執行
15,45 * * * * openclaw agent --message "執行 threads-monitor 監控" --local --channel telegram
```

## 相依 Skills

- `report-generator` - 產生戰報
- `line-notify` - 發送 LINE 通知（由 report-generator 觸發）

## 測試模式

開發時可使用測試模式，僅處理前 5 筆結果：

```bash
export THREADS_MONITOR_TEST_MODE=true
openclaw agent --message "執行 threads-monitor 監控（測試模式）" --local --channel telegram
```

## 維護與監控

- 定期檢查 `data/processed_posts.db` 大小
- 每月清理 3 個月前的舊記錄（可選）
- 監控 AI API 用量和成本
- 檢查 Threads 登入 session 是否過期

---

**版本**: 2.2.0
**最後更新**: 2026-02-11
**作者**: Claude Code + OpenClaw
**License**: AGPL-3.0
