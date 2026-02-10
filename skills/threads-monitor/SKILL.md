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

## 使用方式

### 手動觸發
```bash
openclaw agent --message "執行 threads-monitor 監控" --local
```

### 設定定期執行（每 30 分鐘）
```bash
openclaw cron add "*/30 * * * *" "openclaw agent --message '執行 threads-monitor 監控' --local"
```

## 工作流程

1. **登入 Threads**
   - 使用 OpenClaw Browser (CDP) 登入 Threads 平台
   - 利用 persistent profile，首次登入後 session 永久保留
   - 若需首次登入，從環境變數讀取 `THREADS_USERNAME` 和 `THREADS_PASSWORD`

2. **讀取監控設定**
   - 讀取 `config/keywords.yml` 取得關鍵字列表
   - 讀取 `config/filters.yml` 取得硬性排除詞和白名單設定

3. **搜尋與抓取**
   - 對每個關鍵字執行 Threads 搜尋
   - 抓取搜尋結果（貼文內容、作者、連結、時間戳）
   - 限制每個關鍵字最多抓取 20 筆最新貼文

4. **硬性過濾**
   - 呼叫 `python3 src/filter.py` 進行第一層過濾
   - 使用詞組比對（非單字）+ 白名單優先機制
   - 過濾掉廣告、預售屋等無關內容
   - **重要**: 白名單關鍵字（如「警方」、「逮捕」、「毒品」）優先級最高，即使包含排除詞也會保留

5. **去重處理**
   - 呼叫 `python3 src/dedup.py --check <post_id>` 檢查是否已處理過
   - 若為新貼文，呼叫 `python3 src/dedup.py --add <post_id>` 加入資料庫
   - 使用 SQLite (data/processed_posts.db) 儲存已處理的貼文 ID

6. **AI 語意分析**
   - 使用 OpenClaw 內建的 LLM 進行語意分析
   - 判斷內容是否與公共議題相關（政治、社會、交通、民生等）
   - 過濾掉純私人抱怨、閒聊等內容

7. **觸發後續處理**
   - 呼叫 `report-generator` Skill 產出分類戰報
   - 若發現重大議題（「大魚」），標記為高優先級

## 環境變數需求

```bash
# 必需（OpenClaw 使用）
ANTHROPIC_API_KEY=sk-ant-xxx

# 可選（僅首次登入 Threads 時需要，之後可刪除）
THREADS_USERNAME=your_username
THREADS_PASSWORD=your_password
```

**安全提示**: Threads 登入後會儲存在 OpenClaw 的 persistent Chrome profile (`~/.openclaw/browsers/`)，不需要每次都提供密碼。建議首次登入成功後，從 `.env` 檔案中移除帳密。

## 設定檔格式

### config/keywords.yml
```yaml
keywords:
  - "台北市政府"
  - "交通建設"
  - "選舉"
  - "公投"
```

### config/filters.yml
```yaml
# 硬性排除詞（詞組，非單字）
hard_exclude:
  - "預售屋"
  - "代購"
  - "團購"
  - "出售"

# 白名單關鍵字（最高優先級，即使包含排除詞也保留）
priority_keep_keywords:
  - "警方"
  - "逮捕"
  - "檢方"
  - "起訴"
  - "毒品"
  - "貪污"
  - "弊案"

# 最小內容長度（字元）
min_content_length: 30

# 排除詞最小長度（避免誤殺）
min_exclude_word_length: 2
```

## Python Helper Scripts 呼叫方式

### 硬性過濾
```bash
# 檢查內容是否應該被過濾
python3 src/filter.py --content "貼文內容文字"
# 回傳: KEEP 或 FILTER
```

### 去重檢查與新增
```bash
# 檢查貼文是否已處理
python3 src/dedup.py --check "post_12345"
# 若已處理則 exit code 0，否則 exit code 1

# 新增已處理貼文
python3 src/dedup.py --add "post_12345"
# 成功則 exit code 0
```

### 查詢統計
```bash
# 查詢已處理貼文總數
python3 src/dedup.py --count
# 輸出: "📊 已處理貼文數量: 123"
```

## Browser 操作範例

```javascript
// 使用 OpenClaw Browser API

// 1. 開啟 Threads
await browser.navigate("https://www.threads.net");

// 2. 等待登入（若尚未登入）
if (await browser.exists("#login-button")) {
  await browser.fill("#username", process.env.THREADS_USERNAME);
  await browser.fill("#password", process.env.THREADS_PASSWORD);
  await browser.click("#login-button");
  await browser.wait(3000);
}

// 3. 執行搜尋
await browser.navigate(`https://www.threads.net/search?q=${keyword}`);
await browser.wait(2000);

// 4. 抓取貼文
const posts = await browser.extractAll(".post-item", {
  id: ".post-id",
  content: ".post-content",
  author: ".post-author",
  timestamp: ".post-time",
  link: ".post-link[href]"
});

// 5. 處理每筆貼文
for (const post of posts) {
  // 呼叫 Python 過濾
  const filterResult = await bash(`python3 src/filter.py --content "${post.content}"`);
  if (filterResult.trim() === "FILTER") continue;

  // 檢查去重
  const dedupCheck = await bash(`python3 src/dedup.py --check "${post.id}"`);
  if (dedupCheck.exitCode === 0) continue; // 已處理過

  // AI 語意分析
  const analysis = await llm(`分析以下 Threads 貼文是否與公共議題相關：\n\n${post.content}\n\n請回答 RELEVANT 或 IRRELEVANT`);
  if (analysis.includes("IRRELEVANT")) continue;

  // 加入去重資料庫
  await bash(`python3 src/dedup.py --add "${post.id}"`);

  // 儲存有效貼文
  validPosts.push(post);
}
```

## 錯誤處理

- 若 Threads 登入失敗，記錄錯誤並終止執行
- 若網路連線問題，最多重試 3 次，每次間隔 10 秒
- 若 Python scripts 執行失敗，記錄錯誤並跳過該筆資料
- 若 SQLite 資料庫鎖定，等待 5 秒後重試

## Rate Limiting

為避免被 Threads 平台偵測為機器人：
- 每次搜尋後等待 7-10 秒（隨機延遲）
- 每抓取 5 筆貼文後暫停 3 秒
- 單次執行最多處理 100 筆貼文
- 使用真實的 User-Agent

## 輸出格式

執行完成後，將有效貼文資料傳遞給 `report-generator` Skill：

```json
{
  "timestamp": "2026-02-10T15:30:00Z",
  "keywords": ["台北市政府", "交通建設"],
  "validPosts": [
    {
      "id": "post_12345",
      "keyword": "台北市政府",
      "content": "台北市政府今日宣布...",
      "author": "user_abc",
      "link": "https://www.threads.net/@user_abc/post/12345",
      "timestamp": "2026-02-10T14:20:00Z"
    }
  ],
  "stats": {
    "totalSearched": 100,
    "filteredByHardRules": 45,
    "filteredByDedup": 30,
    "filteredByAI": 15,
    "validCount": 10
  }
}
```

## 效能考量

- **執行時間**: 預估 5-10 分鐘（視關鍵字數量和結果數量）
- **資料庫大小**: SQLite 資料庫每月約成長 1-2 MB
- **API 成本**: AI 語意分析每月約 $1.8（使用 Haiku 模型）

## Cron 排程建議

```bash
# 每 30 分鐘執行一次（避開整點，減少伺服器負載）
*/30 * * * * openclaw agent --message "執行 threads-monitor 監控" --local

# 或每小時的第 15 和 45 分執行
15,45 * * * * openclaw agent --message "執行 threads-monitor 監控" --local
```

## 相依 Skills

- `report-generator` - 產生戰報
- `line-notify` - 發送 LINE 通知（由 report-generator 觸發）

## 測試模式

開發時可使用測試模式，僅處理前 5 筆結果：

```bash
export THREADS_MONITOR_TEST_MODE=true
openclaw agent --message "執行 threads-monitor 監控（測試模式）" --local
```

## 維護與監控

- 定期檢查 `data/processed_posts.db` 大小
- 每月清理 3 個月前的舊記錄（可選）
- 監控 AI API 用量和成本
- 檢查 Threads 登入 session 是否過期

---

**版本**: 1.0.0
**最後更新**: 2026-02-10
**作者**: Claude Code + OpenClaw
**License**: AGPL-3.0
