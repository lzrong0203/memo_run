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

1. **回報進度**：在 Telegram channel 回報目前正在搜尋的關鍵字：
   ```
   🔍 正在搜尋關鍵字: [關鍵字名稱]（第 N/M 個）
   ```
2. 導航到搜尋頁面（在**當前 tab** 中，不要開新 tab），**必須加上 `&filter=recent` 以顯示最新貼文**：
   ```
   browser navigate https://www.threads.net/search?q=關鍵字&filter=recent
   ```
3. 等待頁面載入（等待 5 秒）：
   ```
   browser wait --time 5000
   ```
4. **不做 snapshot** — 直接進入步驟 3

> **設計理念**：`a[href*="/post/"]` 是 Threads URL 的基本結構，改變機率極低。
> 不需要每次都 snapshot 分析 DOM，省下一次 LLM 呼叫。
> 只有在 JS 抽取失敗（回傳 0 篇）時才做 snapshot fallback（見步驟 3 Phase C）。

### 步驟 3: 連續滾動 + JS 一次抽取

本步驟分為三個 Phase：先滾動載入所有內容，再用 JS 一次抽取，最後處理失敗情況。

#### Phase A：連續滾動（不截圖）

**重複以下迴圈，最多滾動 5 輪：**

每輪滾動流程：

1. 記錄目前頁面高度（用來判斷是否有新內容載入）：
   ```
   browser execute document.body.scrollHeight
   ```
2. 滑動頁面到底部（**必須用 `window.scrollTo`**）：
   ```
   browser execute window.scrollTo(0, document.body.scrollHeight)
   ```
3. **等待 3 秒**讓新內容載入：
   ```
   browser wait --time 3000
   ```
4. **再滑一次**確保觸發載入：
   ```
   browser execute window.scrollTo(0, document.body.scrollHeight)
   ```
5. **再等 2 秒**：
   ```
   browser wait --time 2000
   ```
6. 取得新的頁面高度：
   ```
   browser execute document.body.scrollHeight
   ```
7. 比較新舊頁面高度：
   - 若高度有增加，表示有新內容載入，繼續下一輪滾動（回到 Phase A 第 1 步）
   - 若高度沒有增加，表示已到底，停止滾動

> **注意**：每輪滾動約 5 秒（vs 舊版 8 秒），不需要 snapshot，大幅減少耗時和 token 消耗。

#### Phase B：一次 JS 抽取所有貼文

滾動結束後，執行一次 JS 把頁面上所有貼文抽出來（**selector 寫死，不需要 Agent 分析 DOM**）：

```
browser execute (function() { var posts = []; var seen = new Set(); var allLinks = document.querySelectorAll('a[href*="/post/"]'); allLinks.forEach(function(link) { var href = link.getAttribute('href'); if (!href || seen.has(href)) return; var fullUrl = href.startsWith('http') ? href : 'https://www.threads.net' + href; var container = link; for (var i = 0; i < 8; i++) { if (!container.parentElement) break; var next = container.parentElement; var otherLinks = next.querySelectorAll('a[href*="/post/"]'); if (otherLinks.length > 1) break; container = next; if (container.innerText && container.innerText.length > 50) break; } var textContent = container.innerText || ''; var authorMatch = href.match(/\/@([^\/]+)\/post\//); var author = authorMatch ? authorMatch[1] : ''; if (textContent.length < 15) return; seen.add(href); posts.push({ content: textContent.substring(0, 2000), author: author, link: fullUrl }); }); return JSON.stringify(posts); })()
```

> **Selector 策略**：
> - 錨點 `a[href*="/post/"]` 寫死 — 這是 Threads 貼文 URL 的基本結構，極少變動
> - Container 用「向上最多 8 層，找到 innerText > 50 字元的祖先」取代固定層數
> - **防止跨貼文污染**：若父元素包含多個 `/post/` 連結，停止向上（避免抓到相鄰貼文內容）
> - 這樣即使 Threads 改了 DOM 層級，只要 URL 結構不變就能抽取
> - Author 從 URL 中的 `/@username/post/` 格式解析

**檢查 JS 回傳結果並回報進度**：
- 解析回傳的 JSON，計算抽取到的貼文數量
- 在 Telegram channel 回報：`📥 JS 抽取完成: 找到 N 篇貼文`
- 若回傳的貼文數量 > 0，直接進入步驟 4
- 若回傳 0 篇，回報 `⚠️ JS 抽取 0 篇，啟動 fallback...`，進入 Phase C fallback

#### Phase C：三層 Fallback（僅在 Phase B 回傳 0 篇時執行）

**Fallback 第 1 層：Snapshot + 手動調整 Selector**

1. 擷取一次快照，觀察目前的 DOM 結構：
   ```
   browser snapshot
   ```
2. 根據快照中看到的 DOM 結構，調整 JS 中的 selector（例如改用其他 `a[href]` 模式或 `div` class）
3. 用調整後的 JS 再執行一次 `browser execute`
4. 若有結果，進入步驟 4

**Fallback 第 2 層：嘗試內嵌 JSON 資料**

若調整 selector 後仍回傳 0 篇：

1. 嘗試從頁面的 `<script type="application/json">` 標籤中提取內嵌資料：
   ```
   browser execute (function() { var scripts = document.querySelectorAll('script[type="application/json"]'); var results = []; scripts.forEach(function(s) { try { var data = JSON.parse(s.textContent); results.push(JSON.stringify(data).substring(0, 3000)); } catch(e) {} }); return JSON.stringify(results); })()
   ```
2. 從回傳的 JSON 中解析貼文資訊（content、author、link）
3. 若有結果，進入步驟 4

**Fallback 第 3 層：回退到 v2.2.0 Snapshot 逐頁解析模式**

若以上都失敗：

1. 回到頁面頂部：
   ```
   browser execute window.scrollTo(0, 0)
   ```
2. 等待 2 秒：
   ```
   browser wait --time 2000
   ```
3. 擷取快照並由 Agent 直接從快照文字中解析貼文：
   ```
   browser snapshot
   ```
4. 再進行最多 5 輪的滾動+快照解析（和 v2.2.0 步驟 3 相同的行為）：
   - 每輪：`browser execute window.scrollTo(0, document.body.scrollHeight)` → `browser wait --time 5000` → `browser execute window.scrollTo(0, document.body.scrollHeight)` → `browser wait --time 3000` → `browser snapshot` → 從快照中提取貼文
5. 從所有快照中彙整提取貼文資訊，進入步驟 4

> **注意**：若使用了任何 fallback 層，步驟 8 的健康檢查會自動記錄並發送告警通知。

### 步驟 4: 驗證並格式化為 JSON

解析步驟 3 回傳的 JS JSON 結果，驗證並整理成標準格式：

1. **解析 JSON**：將 `browser execute` 回傳的字串解析為 JSON 陣列
2. **驗證欄位**：確認每篇貼文包含 `content`、`author`、`link` 三個欄位，缺少任何欄位的貼文直接丟棄
3. **去重**：以 `link` 為 key 去除重複貼文
4. **數量限制**：最多取前 20 篇貼文

最終輸出格式（和原本一樣，直接給 pipeline.py 使用）：

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

**回報進度**：在 Telegram channel 回報 pipeline 的 `summary` 欄位，例如：
```
📊 [關鍵字名稱] 掃描 12 篇 → 過濾 3 篇 → 重複 2 篇 → 有效 7 篇
```

### 步驟 5b: 不足則繼續搜尋（最多重試 3 輪）

**檢查 pipeline 輸出的 `needs_more` 欄位：**

- 若 `needs_more` 為 `false`（有效貼文已達標），直接進入步驟 6
- 若 `needs_more` 為 `true`（有效貼文不足），執行以下操作：
  1. 記錄目前累積的 `passed_posts`
  2. 回到步驟 3 Phase A 繼續滾動（再滾 5 輪），然後執行 Phase B 抽取新貼文
  3. 從新抽取結果中篩選**尚未送過 pipeline 的新貼文**
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

> **⛔ 絕對禁止自行撰寫 LINE 或 Telegram 訊息。**
> **你必須執行下面的 Python 指令，使用它的輸出作為訊息內容。**
> **不要用自己的理解改寫、重新排版、加入 emoji 或調整格式。原封不動複製程式輸出。**

**7a. 呼叫 report_generator.py 生成戰報 + 上傳 Gist + 產出 LINE/Telegram 摘要：**

```bash
python3 /Users/steveopenclaw/.openclaw/workspace/memo_run/src/report_generator.py --input /tmp/threads_analysis.json --format all --gist
```

這個指令會一次輸出所有結果。你需要做的是：
1. 執行上面的指令
2. 等待輸出完成
3. 從輸出中找到 `=== LINE 摘要 ===` 和 `=== Telegram 摘要 ===` 區塊
4. **原封不動**複製這些區塊的內容（包含所有 URL）

**輸出範例（程式實際會產出的格式）：**
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
📊 *Threads 輿情戰報*

掃描 20 筆 → 有效 2 筆
關鍵字: 內湖

🚨 *發現 1 個重大議題*

*[9/10]* 內湖驚傳隨機擄童事件
[查看原文](https://www.threads.net/@user/post/xxx)

📋 *其他重點*

• [政治] 內湖南港議員提名 [原文](https://www.threads.net/@user/post/yyy)

📄 [完整戰報](https://gist.github.com/xxx/yyy)
```

**7b. 發送 LINE 通知（複製程式輸出，不要自己寫）：**

從上面的輸出中，找到 `=== LINE 摘要 ===` 到 `=== Telegram 摘要 ===` 之間的文字，**完整複製**，用 line_notify.py 發送：

```bash
python3 /Users/steveopenclaw/.openclaw/workspace/memo_run/src/line_notify.py --message "從程式輸出複製的 LINE 摘要完整文字"
```

> **⛔ 再次強調**：
> - 訊息內容必須來自 `report_generator.py` 的輸出，不是你自己寫的
> - 必須包含所有 `→ https://www.threads.net/...` 貼文連結
> - 必須包含 `📄 完整戰報: https://gist.github.com/...` 連結
> - 不要加入 ⭐、🔴🟡🟢、━━━ 等 report_generator.py 沒有輸出的符號

### 步驟 8: 健康檢查與執行記錄

**8a. 記錄執行結果到 health.log：**

每輪執行結束後，將結果追加到 `data/health.log`：

```bash
echo "$(date -Iseconds) | keywords=搜尋的關鍵字數 | valid=有效貼文數 | fallback=是否觸發fallback | status=success/partial/fail" >> /Users/steveopenclaw/.openclaw/workspace/memo_run/data/health.log
```

範例：
```
2026-02-11T15:30:00+08:00 | keywords=3 | valid=15 | fallback=no | status=success
2026-02-11T16:00:00+08:00 | keywords=3 | valid=0 | fallback=yes | status=fail
```

**8b. 異常告警（透過 Telegram）：**

檢查以下異常條件，觸發時在 Telegram channel 發送告警訊息：

1. **零結果告警**：整輪所有關鍵字的有效貼文數 = 0
   - 告警訊息：「⚠️ 本輪巡邏 0 則有效貼文。可能原因：Threads 改版、登入失效、或搜尋結果為空。請檢查。」

2. **Fallback 告警**：任何關鍵字觸發了 Phase C fallback
   - 告警訊息：「⚠️ JS 抽取失敗，已啟用 fallback 模式。DOM 結構可能已變更，建議檢查 SKILL.md selector。」

3. **連續失敗告警**：讀取 health.log 最近 3 筆記錄：
   ```bash
   tail -3 /Users/steveopenclaw/.openclaw/workspace/memo_run/data/health.log
   ```
   - 若連續 3 筆都是 `status=fail` 或 `fallback=yes`：
   - 告警訊息：「🚨 連續 3 輪異常！系統可能需要維護。請立即檢查 Threads 登入狀態和 DOM 結構。」

> **注意**：告警訊息直接透過 Telegram channel 發送（OpenClaw 內建），不需要額外的 Python script。

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

**版本**: 3.0.0
**最後更新**: 2026-02-11
**作者**: Claude Code + OpenClaw
**License**: AGPL-3.0
