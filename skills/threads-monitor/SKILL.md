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
> **工作目錄為 `~/.openclaw/workspace/memo_run/`，所有 Python 指令需在此目錄下執行。**

## 使用方式

### 手動觸發
```bash
openclaw agent --message "執行 threads-monitor 監控" --local --channel telegram --session-id threads-monitor-manual
```

### 設定定期執行（每 30 分鐘）
```bash
openclaw cron add "*/30 * * * *" "openclaw agent --message '執行 threads-monitor 監控' --local --channel telegram"
```

## 工作流程

### 步驟 1: 讀取監控設定

使用 exec 工具讀取設定檔（workdir: `~/.openclaw/workspace/memo_run/`）：

```bash
cat config/keywords.yml
cat config/filters.yml
```

從 `keywords.yml` 取得 `enabled: true` 的關鍵字列表。

### 步驟 2: 開啟 Threads 並搜尋

使用 browser 工具（profile: openclaw）：

1. 導航到搜尋頁面（在**當前 tab** 中，不要開新 tab）：
   ```
   browser navigate https://www.threads.net/search?q=關鍵字
   ```
2. 等待頁面載入（等待 3-5 秒）：
   ```
   browser wait --time 5000
   ```
3. 擷取頁面快照：
   ```
   browser snapshot
   ```

### 步驟 3: 抓取貼文內容

從 snapshot 中提取貼文資訊：
- 貼文內容文字
- 作者名稱
- 貼文連結

每個關鍵字最多抓取 20 筆最新貼文。

### 步驟 4: 硬性過濾

對每筆貼文呼叫 Python 過濾（workdir: `~/.openclaw/workspace/memo_run/`）：

```bash
python3 src/filter.py --config config/filters.yml --content "貼文內容文字"
```

- exit code 0 = 保留（通過過濾）
- exit code 1 = 丟棄（被過濾）
- 白名單關鍵字（如「警方」、「逮捕」、「毒品」）優先級最高

### 步驟 5: 去重處理

```bash
# 檢查貼文是否已處理（用貼文連結作為 ID）
python3 src/dedup.py --check "貼文連結URL"

# 若未處理過（exit code 1），加入資料庫
python3 src/dedup.py --add "貼文連結URL"
```

### 步驟 6: AI 語意分析

對通過過濾和去重的貼文，直接使用你的 LLM 能力判斷：
- 內容是否與公共議題相關（政治、社會、交通、民生等）
- 回答 RELEVANT 或 IRRELEVANT
- 過濾掉純私人抱怨、閒聊、廣告等內容

### 步驟 7: 產出結果

將有效貼文彙整為摘要，包含：
- 搜尋的關鍵字
- 有效貼文數量和統計
- 每筆貼文的摘要、作者、連結
- 使用 `python3 src/line_notify.py --message "摘要內容"` 發送 LINE 通知

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

**版本**: 1.1.0
**最後更新**: 2026-02-10
**作者**: Claude Code + OpenClaw
**License**: AGPL-3.0
