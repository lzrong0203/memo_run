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
> **工作目錄為 `~/.openclaw/workspace/memo_run/`，所有 Python 指令都必須加上完整路徑前綴 `~/.openclaw/workspace/memo_run/`。**
> **每個步驟必須按順序執行，不可跳過。**

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
cat ~/.openclaw/workspace/memo_run/config/keywords.yml
cat ~/.openclaw/workspace/memo_run/config/filters.yml
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

**重複以下迴圈，直到收集到足夠的貼文（目標 20 筆）或已滑動 5 次：**

1. 滑動頁面到底部（**必須用 `window.scrollTo`**）：
   ```
   browser execute window.scrollTo(0, document.body.scrollHeight)
   ```
2. **等待新內容載入完成**（這一步很重要，不要跳過）：
   ```
   browser wait --time 4000
   ```
3. 再次擷取快照，檢查是否有新貼文出現：
   ```
   browser snapshot
   ```
4. 如果新快照中的貼文數量比上一次多，繼續滑動（回到步驟 1）
5. 如果新快照中的貼文數量沒有增加，表示已到底，停止滑動

> **注意**：每次 `browser wait` 至少等 4 秒。Threads 的 infinite scroll 需要時間載入，等太短會看不到新內容。

### 步驟 4: 提取貼文內容

從所有快照中彙整提取貼文資訊（去除重複）：
- 貼文內容文字
- 作者名稱
- 貼文連結

每個關鍵字最多抓取 20 筆最新貼文。

### 步驟 5: 硬性過濾（必須先於去重）

**對每筆貼文呼叫 Python 過濾**（注意使用完整路徑）：

```bash
python3 ~/.openclaw/workspace/memo_run/src/filter.py --config ~/.openclaw/workspace/memo_run/config/filters.yml --content "貼文內容文字"
```

- exit code 0 = 保留（通過過濾）
- exit code 1 = 丟棄（被過濾）
- 白名單關鍵字（如「警方」、「逮捕」、「毒品」）優先級最高

### 步驟 6: 去重處理（只處理通過過濾的貼文）

```bash
# 檢查貼文是否已處理（用貼文連結作為 ID）
python3 ~/.openclaw/workspace/memo_run/src/dedup.py --check "貼文連結URL"

# 若未處理過（exit code 1），加入資料庫
python3 ~/.openclaw/workspace/memo_run/src/dedup.py --add "貼文連結URL"
```

### 步驟 7: AI 語意分析

對通過過濾和去重的貼文，直接使用你的 LLM 能力判斷：
- 內容是否與公共議題相關（政治、社會、交通、民生等）
- 回答 RELEVANT 或 IRRELEVANT
- 過濾掉純私人抱怨、閒聊、廣告等內容

### 步驟 8: 產出結果

將有效貼文彙整為摘要，包含：
- 搜尋的關鍵字
- 有效貼文數量和統計
- 每筆貼文的摘要、作者、連結
- 使用以下指令發送 LINE 通知：

```bash
python3 ~/.openclaw/workspace/memo_run/src/line_notify.py --message "摘要內容"
```

## 環境變數需求

```bash
# 必需（OpenClaw 使用）
ANTHROPIC_API_KEY=sk-ant-xxx

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

**版本**: 1.2.0
**最後更新**: 2026-02-11
**作者**: Claude Code + OpenClaw
**License**: AGPL-3.0
