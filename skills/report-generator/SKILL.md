---
name: report-generator
description: 接收 Threads 監控資料，使用 AI 進行語意分析和分類，產出結構化戰報並透過 Telegram + LINE 發送通知。自動識別「大魚」(重大議題)。
user-invocable: true
homepage: https://github.com/lzrong0203/memo_run
metadata: {"openclaw": {"emoji": "📊", "primaryEnv": "ANTHROPIC_API_KEY", "requires": {"binaries": ["python3"], "envVars": ["ANTHROPIC_API_KEY", "LINE_CHANNEL_ACCESS_TOKEN", "LINE_USER_ID", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]}}}
---

# Threads 戰報生成與通知 Skill

## 概述

這個 Skill 會接收來自 `threads-monitor` Skill 的有效貼文資料，使用 OpenClaw 內建的 LLM 進行智能分類和摘要，產出結構化戰報（Markdown 格式），並透過 Telegram + LINE 雙通道發送通知。系統會自動識別「大魚」（重大議題），並標記為高優先級通知。

## 重要執行規則

> **你必須直接執行以下所有步驟，不要委派給子 agent。**
> **工作目錄為 `~/.openclaw/workspace/memo_run/`，所有 Python 指令需在此目錄下執行。**

## 使用方式

### 由 threads-monitor 自動觸發（推薦）

```bash
# threads-monitor 發現有效貼文後會自動呼叫
openclaw agent --message "執行 threads-monitor 監控" --local --channel telegram
# → 自動觸發 report-generator
```

### 手動觸發（測試用）

```bash
# 使用範例 JSON 資料測試戰報生成
openclaw agent --message "使用 test/sample_data.json 資料產生戰報" --local --channel telegram --channel telegram
```

## 工作流程

### 1. 接收輸入資料

從 `threads-monitor` Skill 接收 JSON 格式的有效貼文資料：

```json
{
  "timestamp": "2026-02-10T15:30:00Z",
  "keywords": ["台北市政府", "交通建設", "選舉"],
  "validPosts": [
    {
      "id": "post_12345",
      "keyword": "台北市政府",
      "content": "台北市政府今日宣布將投入 50 億元改善捷運系統...",
      "author": "user_abc",
      "link": "https://www.threads.net/@user_abc/post/12345",
      "timestamp": "2026-02-10T14:20:00Z"
    },
    {
      "id": "post_67890",
      "keyword": "交通建設",
      "content": "新北環狀線延伸計畫環評通過，預計 2028 年完工...",
      "author": "user_xyz",
      "link": "https://www.threads.net/@user_xyz/post/67890",
      "timestamp": "2026-02-10T14:50:00Z"
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

**輸入驗證**：
- 檢查 `validPosts` 是否為空陣列（若為空，記錄資訊並結束）
- 驗證每筆貼文是否包含必要欄位（id, content, link）
- 驗證時間戳格式是否有效

### 2. AI 分類與分析

使用 OpenClaw 內建 LLM（Anthropic Claude API）對每筆有效貼文進行語意分析：

#### 分類維度

系統會將貼文分類到以下類別（一篇貼文可能同時屬於多個類別）：

| 類別 | 定義 | 範例 |
|------|------|------|
| **政治** | 選舉、政黨、政策辯論、政治人物動態 | 「市長候選人提出交通政見」 |
| **交通** | 道路建設、大眾運輸、交通事故、停車問題 | 「捷運延伸案環評通過」 |
| **社會** | 社會事件、犯罪、治安、社區議題 | 「社區反對垃圾場設置」 |
| **民生** | 物價、水電、食品安全、消費者權益 | 「電價調漲引發民怨」 |
| **投訴** | 公共服務投訴、消費糾紛、環境問題 | 「民眾投訴路面坑洞多月未修」 |
| **教育** | 學校政策、教育改革、學生權益 | 「大學學費調整引發討論」 |
| **環保** | 空汙、水汙、垃圾處理、氣候變遷 | 「工廠排放廢水遭檢舉」 |
| **醫療** | 醫療政策、醫療糾紛、健保議題 | 「急診壅塞問題待解決」 |
| **其他** | 無法歸類到上述類別的公共議題 | 「流浪動物救援行動」 |

#### AI 分類 Prompt

```
請分析以下 Threads 貼文，並進行分類和評估：

【貼文內容】
{post.content}

【來源資訊】
- 作者: {post.author}
- 關鍵字: {post.keyword}
- 時間: {post.timestamp}

【分析任務】
1. 分類: 將貼文歸類到一個或多個類別（政治、交通、社會、民生、投訴、教育、環保、醫療、其他）
2. 重要性評分: 1-10 分，10 分為最重要（大魚）
3. 摘要: 用 1-2 句話總結貼文核心內容（繁體中文，30-80 字）
4. 關鍵實體: 抽取重要的人名、地名、組織名、事件名

【評分標準】
- 9-10 分（大魚）: 重大政策變動、嚴重社會事件、大規模影響
- 7-8 分（中魚）: 區域性重要議題、中等規模影響
- 5-6 分（小魚）: 一般性討論、局部性問題
- 1-4 分（小蝦米）: 個人意見、邊緣議題

請以 JSON 格式回覆：
{
  "categories": ["政治", "交通"],
  "importance": 8,
  "summary": "市長候選人提出捷運延伸計畫，預計投入 100 億元改善北部交通。",
  "entities": {
    "persons": ["候選人姓名"],
    "locations": ["台北市", "新北市"],
    "organizations": ["市政府"],
    "events": ["捷運延伸計畫"]
  },
  "reasoning": "涉及重大交通建設政策，影響範圍廣，具有政治和民生雙重意義。"
}
```

#### 批次處理策略

為提升效率和降低 API 成本：
- 若貼文數量 ≤ 5 筆，逐筆分析
- 若貼文數量 > 5 筆，每次批次處理 3-5 筆（在單一 prompt 中）
- 批次處理時會提供完整上下文，幫助 AI 識別相關議題
- 使用 Haiku 模型（成本效益最佳）進行分類
- 對於「大魚」級別（importance ≥ 9），使用 Sonnet 模型進行二次確認

#### 大魚識別邏輯

系統會自動標記「大魚」（重大議題）：

```javascript
function isBigFish(analysis) {
  // 重要性評分 ≥ 9
  if (analysis.importance >= 9) return true;

  // 包含多個類別（≥ 3）且重要性 ≥ 8
  if (analysis.categories.length >= 3 && analysis.importance >= 8) return true;

  // 包含特定高敏感實體
  const sensitiveKeywords = [
    "市長", "總統", "立委", "議員",
    "貪污", "弊案", "詐騙", "毒品",
    "重大車禍", "死亡", "大規模",
    "環評", "開發案", "抗議"
  ];
  const hasSensitiveEntity = analysis.entities.persons.some(p =>
    sensitiveKeywords.some(k => p.includes(k))
  ) || analysis.content.some(c =>
    sensitiveKeywords.some(k => c.includes(k))
  );

  if (hasSensitiveEntity && analysis.importance >= 7) return true;

  return false;
}
```

### 3. 產出結構化戰報

將 AI 分析結果彙整為 Markdown 格式的戰報：

#### 戰報格式

```markdown
# Threads 輿情戰報

**生成時間**: 2026-02-10 15:30:00 UTC+8
**監控關鍵字**: 台北市政府, 交通建設, 選舉
**有效貼文數**: 10 篇

---

## 🎯 執行摘要

本次監控週期共掃描 100 筆貼文，經雙重過濾後篩選出 10 筆有效內容。主要議題集中在交通建設和政治選舉，發現 2 個「大魚」級重大議題。

### 統計數據

- **總掃描數**: 100 筆
- **硬性過濾移除**: 45 筆（廣告、預售屋等）
- **去重移除**: 30 筆（重複內容）
- **AI 過濾移除**: 15 筆（不相關內容）
- **有效貼文**: 10 筆

### 議題分布

| 類別 | 數量 | 百分比 |
|------|------|--------|
| 政治 | 4 | 40% |
| 交通 | 5 | 50% |
| 社會 | 3 | 30% |
| 投訴 | 2 | 20% |

---

## 🐟 大魚警報（重大議題）

### 1️⃣ [政治][交通] 市長候選人提出百億捷運計畫

- **重要性評分**: 9/10
- **發布時間**: 2026-02-10 14:20
- **作者**: @user_abc
- **內容摘要**: 市長候選人提出捷運延伸計畫，預計投入 100 億元改善北部交通，包含三條新路線。
- **關鍵實體**:
  - 人物: 候選人姓名
  - 地點: 台北市, 新北市
  - 組織: 市政府, 捷運局
  - 事件: 捷運延伸計畫
- **原文連結**: https://www.threads.net/@user_abc/post/12345
- **分析說明**: 涉及重大交通建設政策，影響範圍廣，具有政治和民生雙重意義。

### 2️⃣ [社會][投訴] 大型開發案環評爭議引發抗議

- **重要性評分**: 9/10
- **發布時間**: 2026-02-10 14:35
- **作者**: @user_def
- **內容摘要**: 地方居民抗議大型開發案環評程序不透明，質疑環境影響評估報告造假。
- **關鍵實體**:
  - 人物: 居民代表、環保團體
  - 地點: 某某區
  - 組織: 環保署、開發商
  - 事件: 環評爭議、抗議行動
- **原文連結**: https://www.threads.net/@user_def/post/23456
- **分析說明**: 涉及環境正義和公民參與，可能演變為大規模抗爭。

---

## 📋 詳細議題分類

### 政治類（4 篇）

#### [重要性: 9/10] 🔴 市長候選人提出百億捷運計畫
- **時間**: 2026-02-10 14:20
- **摘要**: 市長候選人提出捷運延伸計畫，預計投入 100 億元改善北部交通。
- **連結**: [查看原文](https://www.threads.net/@user_abc/post/12345)

#### [重要性: 7/10] 🟡 議員質詢預算分配不均
- **時間**: 2026-02-10 13:15
- **摘要**: 市議員在議會質詢時指出預算分配偏重特定區域，要求重新檢討。
- **連結**: [查看原文](https://www.threads.net/@user_ghi/post/34567)

（其他政治類貼文...）

### 交通類（5 篇）

#### [重要性: 8/10] 🟠 新北環狀線延伸案環評通過
- **時間**: 2026-02-10 14:50
- **摘要**: 新北環狀線延伸計畫環評通過，預計 2028 年完工，將串聯三條主要幹線。
- **連結**: [查看原文](https://www.threads.net/@user_xyz/post/67890)

（其他交通類貼文...）

### 社會類（3 篇）

（社會類貼文詳情...）

### 投訴類（2 篇）

（投訴類貼文詳情...）

---

## 📊 熱門關鍵實體

### 人物
1. 候選人姓名（4 次提及）
2. 市長現任（3 次提及）
3. 議員 A（2 次提及）

### 地點
1. 台北市（7 次提及）
2. 新北市（5 次提及）
3. 某某區（3 次提及）

### 組織
1. 市政府（6 次提及）
2. 捷運局（4 次提及）
3. 環保署（3 次提及）

### 事件
1. 捷運延伸計畫（3 次提及）
2. 環評爭議（2 次提及）
3. 預算質詢（2 次提及）

---

## 🔍 趨勢觀察

### 主要趨勢
1. **交通建設成為選舉焦點**: 多位候選人提出交通政見，顯示民眾對交通議題高度關注。
2. **環評爭議持續發酵**: 開發案環評問題引發公民團體關注，可能形成長期抗爭。
3. **預算分配引發討論**: 議員質詢預算分配問題，反映區域發展不均議題。

### 後續追蹤建議
- 持續監控「捷運延伸」相關討論
- 關注「環評爭議」後續發展
- 追蹤「預算質詢」議會回應

---

## 📌 附錄

### 監控設定
- **監控週期**: 30 分鐘
- **關鍵字數量**: 3 個
- **過濾規則**: 硬性排除 + AI 語意分析
- **去重機制**: SQLite 資料庫

### 系統資訊
- **OpenClaw 版本**: 1.x
- **AI 模型**: Claude 3.5 Haiku（分類）+ Sonnet（大魚確認）
- **生成耗時**: 45 秒
- **API 成本**: 約 $0.15

---

**報告生成**: 使用 OpenClaw AI Agent 自動產生
**版本**: 1.0.0
**License**: AGPL-3.0
```

#### 戰報儲存

戰報會儲存為檔案（可選）：

```javascript
// 檔案命名格式: report_YYYYMMDD_HHMMSS.md
const reportFilename = `report_${timestamp.format('YYYYMMDD_HHMMSS')}.md`;
const reportPath = `data/reports/${reportFilename}`;

// 寫入檔案
await writeFile(reportPath, reportMarkdown);
```

儲存位置：`data/reports/`

清理策略：保留最近 30 天的報告，自動刪除舊報告（可在 cron job 中設定）

### 4. 發送通知

戰報產生後，會透過 Telegram 和 LINE 雙通道發送通知。

#### Telegram 通知

使用 OpenClaw 內建的 Telegram 功能：

```javascript
// 使用 OpenClaw Telegram Bot API
await telegram.sendMessage({
  chat_id: process.env.TELEGRAM_CHAT_ID,
  text: buildTelegramMessage(reportSummary, bigFishCount, reportUrl),
  parse_mode: "Markdown"
});

function buildTelegramMessage(summary, bigFishCount, reportUrl) {
  let message = "📊 *Threads 輿情戰報*\n\n";

  if (bigFishCount > 0) {
    message += `🚨 *發現 ${bigFishCount} 個重大議題！*\n\n`;
  }

  message += `📝 *執行摘要*\n${summary}\n\n`;
  message += `🔗 [查看完整報告](${reportUrl})`;

  return message;
}
```

**Telegram 通知內容**（簡潔版）：
```
📊 Threads 輿情戰報

🚨 發現 2 個重大議題！

📝 執行摘要
本次監控發現 10 篇有效貼文，主要議題：
• 政治: 市長候選人提出百億捷運計畫
• 社會: 開發案環評爭議引發抗議
• 交通: 新北環狀線延伸案環評通過

🔗 查看完整報告
```

#### LINE 通知

呼叫 Python `line_notify.py` 模組：

```bash
python3 src/line_notify.py \
  --message "$(cat <<EOF
🔔 Threads 監控通知

關鍵字: 台北市政府, 交通建設, 選舉

摘要:
本次監控發現 10 篇有效貼文，包含 2 個重大議題。主要討論集中在交通建設和政治選舉。

完整報告:
https://example.com/reports/report_20260210_153000.md
EOF
)"
```

或使用 Python 函數直接呼叫：

```javascript
// 使用 OpenClaw 的 bash() 函數呼叫 Python
await bash(`python3 src/line_notify.py --message "${lineMessage}"`);
```

或使用 `send_notification_message()` 函數（推薦）：

```python
from src.line_notify import send_notification_message

success = send_notification_message(
    channel_access_token=os.environ['LINE_CHANNEL_ACCESS_TOKEN'],
    to_user_id=os.environ['LINE_USER_ID'],
    keywords=["台北市政府", "交通建設", "選舉"],
    summary="本次監控發現 10 篇有效貼文，包含 2 個重大議題。主要討論集中在交通建設和政治選舉。",
    report_url="https://example.com/reports/report_20260210_153000.md"
)
```

**LINE 通知內容**（結構化）：
```
🔔 Threads 監控通知

關鍵字: 台北市政府, 交通建設, 選舉

摘要:
本次監控發現 10 篇有效貼文，包含 2 個重大議題。主要討論集中在交通建設和政治選舉。

完整報告:
https://example.com/reports/report_20260210_153000.md
```

#### 大魚特別通知

若發現「大魚」級重大議題，會額外發送獨立通知：

```javascript
// 對每個大魚發送獨立通知
for (const bigFish of bigFishList) {
  // Telegram 通知（加上 🚨 emoji）
  await telegram.sendMessage({
    chat_id: process.env.TELEGRAM_CHAT_ID,
    text: buildBigFishTelegramMessage(bigFish),
    parse_mode: "Markdown"
  });

  // LINE 通知（加上 🚨 emoji）
  const lineMessage = buildBigFishLineMessage(bigFish);
  await bash(`python3 src/line_notify.py --message "${lineMessage}"`);

  // 間隔 2 秒避免 rate limit
  await sleep(2000);
}
```

**大魚通知內容**（Telegram）：
```
🚨 重大議題警報

[政治][交通] 市長候選人提出百億捷運計畫

重要性: 9/10

摘要:
市長候選人提出捷運延伸計畫，預計投入 100 億元改善北部交通，包含三條新路線。

關鍵實體:
• 人物: 候選人姓名
• 地點: 台北市, 新北市
• 事件: 捷運延伸計畫

原文連結:
https://www.threads.net/@user_abc/post/12345
```

### 5. 記錄日誌

所有操作會記錄到日誌系統（使用 OpenClaw 內建 logging）：

```javascript
logger.info(`Report generation started for ${validPosts.length} posts`);
logger.info(`AI classification completed: ${categories.size} categories identified`);
logger.info(`Big fish detected: ${bigFishCount} major issues`);
logger.info(`Report saved to ${reportPath}`);
logger.info(`Telegram notification sent successfully`);
logger.info(`LINE notification sent successfully`);
logger.info(`Report generation completed in ${elapsedTime}ms`);
```

日誌檔案位置：`~/.openclaw/logs/report-generator.log`

## 環境變數需求

```bash
# 必需（OpenClaw AI 分類使用）
ANTHROPIC_API_KEY=sk-ant-xxx

# 必需（LINE 通知）
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token
LINE_USER_ID=U1234567890abcdef1234567890abcdef

# 必需（Telegram 通知）
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# 可選（戰報 URL 前綴）
REPORT_BASE_URL=https://example.com/reports
```

## 設定檔格式

### config/report-generator.yml

```yaml
# AI 分類設定
ai_classification:
  model: "claude-3.5-haiku"     # 使用 Haiku（成本效益最佳）
  bigfish_model: "claude-3.5-sonnet"  # 大魚確認使用 Sonnet
  batch_size: 5                 # 每次批次處理的貼文數量
  temperature: 0.3              # 降低隨機性，提升分類穩定性
  max_tokens: 2000              # 每次請求的最大 token 數
  timeout: 30                   # API 請求逾時（秒）

# 分類類別定義
categories:
  - id: "politics"
    name: "政治"
    keywords: ["選舉", "政黨", "政策", "候選人", "議員", "市長", "總統"]
  - id: "traffic"
    name: "交通"
    keywords: ["交通", "捷運", "公車", "停車", "道路", "建設"]
  - id: "society"
    name: "社會"
    keywords: ["社會", "犯罪", "治安", "社區", "抗議"]
  - id: "livelihood"
    name: "民生"
    keywords: ["物價", "水電", "食品", "消費"]
  - id: "complaint"
    name: "投訴"
    keywords: ["投訴", "抱怨", "糾紛", "維權"]
  - id: "education"
    name: "教育"
    keywords: ["學校", "教育", "學生", "教師", "學費"]
  - id: "environment"
    name: "環保"
    keywords: ["環保", "汙染", "垃圾", "空氣", "水質"]
  - id: "healthcare"
    name: "醫療"
    keywords: ["醫療", "健保", "醫院", "看病", "醫生"]
  - id: "other"
    name: "其他"
    keywords: []

# 大魚識別設定
bigfish_detection:
  importance_threshold: 9       # 重要性評分門檻（≥9 為大魚）
  multi_category_threshold: 3   # 多類別門檻（≥3 個類別且 importance ≥8）
  sensitive_keywords:           # 高敏感關鍵字
    - "市長"
    - "總統"
    - "立委"
    - "議員"
    - "貪污"
    - "弊案"
    - "詐騙"
    - "毒品"
    - "重大車禍"
    - "死亡"
    - "大規模"
    - "環評"
    - "開發案"
    - "抗議"

# 戰報設定
report:
  output_dir: "data/reports"    # 戰報儲存目錄
  retention_days: 30            # 報告保留天數（超過自動刪除）
  format: "markdown"            # 報告格式（markdown 或 html）
  include_full_content: false   # 是否包含完整貼文內容（預設僅摘要）

# 通知設定
notification:
  telegram:
    enabled: true
    max_message_length: 4096    # Telegram 訊息最大長度
    parse_mode: "Markdown"
  line:
    enabled: true
    max_message_length: 5000    # LINE 訊息最大長度
  bigfish_separate_notification: true  # 大魚是否發送獨立通知
  notification_interval: 2      # 多則通知間隔（秒）

# 錯誤處理
error_handling:
  retry_count: 3                # API 失敗重試次數
  retry_interval: 5             # 重試間隔（秒）
  fallback_on_ai_failure: true  # AI 失敗時是否使用規則分類
  send_error_notification: true # 是否發送錯誤通知
```

## Python Helper 整合

### 呼叫 line_notify.py

#### 方式 1: 使用 OpenClaw bash() 函數（簡單）

```javascript
// 基本訊息發送
await bash(`python3 src/line_notify.py --message "${message}"`);

// 確認環境變數已設定
if (!process.env.LINE_CHANNEL_ACCESS_TOKEN || !process.env.LINE_USER_ID) {
  logger.error("LINE credentials not configured");
  return false;
}
```

#### 方式 2: 使用 Python 函數（推薦，結構化）

```javascript
// 建立 Python script 呼叫 send_notification_message()
const pythonScript = `
import sys
import os
sys.path.insert(0, '${process.cwd()}/src')

from line_notify import send_notification_message

success = send_notification_message(
    channel_access_token=os.environ['LINE_CHANNEL_ACCESS_TOKEN'],
    to_user_id=os.environ['LINE_USER_ID'],
    keywords=${JSON.stringify(keywords)},
    summary="${summary}",
    report_url="${reportUrl}"
)

sys.exit(0 if success else 1)
`;

// 執行 Python
const result = await bash(`python3 -c "${pythonScript}"`);

if (result.exitCode !== 0) {
  logger.error("LINE notification failed");
  return false;
}
```

#### 方式 3: 使用 requests 直接呼叫（最佳效能）

```javascript
// 如果需要在 JavaScript 中直接呼叫 LINE API
const axios = require('axios');

async function sendLineNotification(keywords, summary, reportUrl) {
  const message = `🔔 Threads 監控通知\n\n關鍵字: ${keywords.join(', ')}\n\n摘要:\n${summary}\n\n完整報告:\n${reportUrl}`;

  const response = await axios.post(
    'https://api.line.me/v2/bot/message/push',
    {
      to: process.env.LINE_USER_ID,
      messages: [{ type: 'text', text: message }]
    },
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.LINE_CHANNEL_ACCESS_TOKEN}`
      },
      timeout: 10000
    }
  );

  return response.status === 200;
}
```

## 錯誤處理

### AI API 失敗

```javascript
try {
  const analysis = await llm(classificationPrompt);
  const parsed = JSON.parse(analysis);
} catch (error) {
  logger.error(`AI classification failed: ${error.message}`);

  // 降級策略 1: 使用規則式分類
  if (config.error_handling.fallback_on_ai_failure) {
    logger.info("Falling back to rule-based classification");
    const categories = ruleBasedClassification(post.content);
    const importance = estimateImportance(categories);
    const summary = post.content.substring(0, 80) + "...";
  }

  // 降級策略 2: 重試
  if (retryCount < config.error_handling.retry_count) {
    logger.info(`Retrying AI classification (attempt ${retryCount + 1})`);
    await sleep(config.error_handling.retry_interval * 1000);
    return await classifyPost(post, retryCount + 1);
  }

  // 最終失敗: 記錄錯誤並跳過
  logger.error(`AI classification failed after ${retryCount} retries, skipping post ${post.id}`);
  return null;
}
```

### 通知發送失敗

```javascript
// Telegram 通知失敗
try {
  await telegram.sendMessage(telegramMessage);
  logger.info("Telegram notification sent successfully");
} catch (error) {
  logger.error(`Telegram notification failed: ${error.message}`);
  // 繼續執行（不中斷 LINE 通知）
}

// LINE 通知失敗
try {
  const result = await bash(`python3 src/line_notify.py --message "${lineMessage}"`);
  if (result.exitCode !== 0) {
    throw new Error("LINE notification script failed");
  }
  logger.info("LINE notification sent successfully");
} catch (error) {
  logger.error(`LINE notification failed: ${error.message}`);
  // 繼續執行（不中斷戰報產生）
}

// 錯誤通知（如果設定啟用）
if (config.error_handling.send_error_notification) {
  await sendErrorNotification(`Report generation completed with errors: ${errorMessages.join(', ')}`);
}
```

### 檔案寫入失敗

```javascript
try {
  await writeFile(reportPath, reportMarkdown);
  logger.info(`Report saved to ${reportPath}`);
} catch (error) {
  logger.error(`Failed to save report: ${error.message}`);

  // 嘗試寫入備份位置
  const backupPath = `/tmp/report_${timestamp}.md`;
  try {
    await writeFile(backupPath, reportMarkdown);
    logger.info(`Report saved to backup location: ${backupPath}`);
  } catch (backupError) {
    logger.error(`Failed to save backup report: ${backupError.message}`);
  }

  // 戰報無法儲存也不影響通知發送
}
```

### 輸入資料異常

```javascript
// 空陣列檢查
if (!validPosts || validPosts.length === 0) {
  logger.info("No valid posts to process, exiting gracefully");
  await sendInfoNotification("本次監控週期無有效貼文，未產生戰報。");
  return;
}

// 資料完整性檢查
const validatedPosts = validPosts.filter(post => {
  if (!post.id || !post.content || !post.link) {
    logger.warning(`Skipping invalid post (missing required fields): ${JSON.stringify(post)}`);
    return false;
  }
  return true;
});

if (validatedPosts.length === 0) {
  logger.error("All posts are invalid (missing required fields)");
  return;
}
```

## Rate Limiting

為避免 API 使用過量：

```javascript
// AI API rate limiting
const AI_REQUEST_DELAY = 1000; // 每次請求間隔 1 秒

for (let i = 0; i < batches.length; i++) {
  const batch = batches[i];
  const analysis = await classifyBatch(batch);

  if (i < batches.length - 1) {
    await sleep(AI_REQUEST_DELAY);
  }
}

// 通知 rate limiting
const NOTIFICATION_DELAY = 2000; // 多則通知間隔 2 秒

await telegram.sendMessage(mainReportNotification);
await sleep(NOTIFICATION_DELAY);
await sendLineNotification(mainReportNotification);
await sleep(NOTIFICATION_DELAY);

// 大魚通知
for (const bigFish of bigFishList) {
  await telegram.sendMessage(buildBigFishNotification(bigFish));
  await sleep(NOTIFICATION_DELAY);
  await sendLineNotification(buildBigFishNotification(bigFish));
  await sleep(NOTIFICATION_DELAY);
}
```

## 效能考量

- **AI 分類耗時**: 約 30-60 秒（10 筆貼文，批次處理）
- **戰報產生耗時**: 約 5-10 秒
- **通知發送耗時**: 約 5 秒（Telegram + LINE）
- **總執行時間**: 約 1-2 分鐘
- **API 成本**:
  - AI 分類（Haiku）: $0.0003/1K tokens × 2K tokens × 3 batches ≈ $0.002
  - 大魚確認（Sonnet）: $0.003/1K tokens × 1K tokens × 2 posts ≈ $0.006
  - 總成本: 約 $0.01/次（10 篇貼文）
  - 每日成本（每 30 分鐘執行）: $0.01 × 48 = $0.48
  - 每月成本: 約 $14.40

## Telegram vs LINE 比較

| 特性 | Telegram | LINE |
|------|----------|------|
| **訊息長度** | 4096 字元 | 5000 字元 |
| **Markdown 支援** | ✅ 完整支援 | ❌ 不支援 |
| **連結預覽** | ✅ 自動顯示 | ⚠️ 部分支援 |
| **通知優先級** | ✅ 可設定 | ❌ 無 |
| **訊息編輯** | ✅ 可編輯 | ❌ 不可編輯 |
| **適用場景** | 技術團隊、詳細報告 | 一般使用者、簡潔通知 |

**建議策略**：
- **Telegram**: 發送完整摘要（含 Markdown 格式）
- **LINE**: 發送簡潔版本（純文字 + 連結）

## 測試模式

開發時可使用測試模式：

```bash
# 使用範例資料測試（不發送通知）
export REPORT_GENERATOR_TEST_MODE=true
export REPORT_NO_NOTIFICATION=true
openclaw agent --message "使用 test/sample_data.json 資料產生戰報" --local --channel telegram

# 僅測試 AI 分類（不產生完整報告）
export REPORT_AI_TEST_ONLY=true
openclaw agent --message "使用 test/sample_data.json 測試 AI 分類" --local --channel telegram

# 使用 mock LLM（不呼叫真實 API）
export REPORT_USE_MOCK_LLM=true
openclaw agent --message "使用 test/sample_data.json 產生戰報（mock 模式）" --local --channel telegram
```

## 整合測試範例

### 端對端測試流程

```bash
# 1. 準備測試資料
cat > test/sample_data.json <<EOF
{
  "timestamp": "2026-02-10T15:30:00Z",
  "keywords": ["測試關鍵字"],
  "validPosts": [
    {
      "id": "test_post_1",
      "keyword": "測試關鍵字",
      "content": "台北市長今日宣布投入 100 億元改善交通建設，預計新增三條捷運路線。",
      "author": "test_user",
      "link": "https://example.com/test_post_1",
      "timestamp": "2026-02-10T14:00:00Z"
    }
  ],
  "stats": {
    "totalSearched": 10,
    "filteredByHardRules": 5,
    "filteredByDedup": 3,
    "filteredByAI": 1,
    "validCount": 1
  }
}
EOF

# 2. 設定測試環境變數
export ANTHROPIC_API_KEY="sk-ant-test-xxx"
export LINE_CHANNEL_ACCESS_TOKEN="test_token"
export LINE_USER_ID="test_user_id"
export TELEGRAM_BOT_TOKEN="test_bot_token"
export TELEGRAM_CHAT_ID="test_chat_id"
export REPORT_GENERATOR_TEST_MODE=true

# 3. 執行測試
openclaw agent --message "使用 test/sample_data.json 資料產生戰報" --local --channel telegram

# 4. 驗證輸出
ls -la data/reports/  # 檢查戰報是否產生
tail -f ~/.openclaw/logs/report-generator.log  # 檢查日誌
```

### 單元測試（AI 分類）

```bash
# 測試單筆貼文分類
export REPORT_AI_TEST_ONLY=true
openclaw agent --message "分類測試：台北市長宣布投入 100 億元改善交通建設" --local --channel telegram

# 預期輸出:
# {
#   "categories": ["政治", "交通"],
#   "importance": 8,
#   "summary": "市長宣布百億交通建設計畫",
#   "entities": {...}
# }
```

## 相依 Skills

- `threads-monitor` - 提供有效貼文資料（上游）
- `line-notify` - LINE 通知發送（可選，也可直接呼叫 Python）

## 維護與監控

- 定期檢查 `data/reports/` 目錄大小（可設定自動清理）
- 監控 AI API 用量和成本（使用 Anthropic Dashboard）
- 檢查通知發送成功率（查看日誌）
- 定期審查分類準確性（人工抽查報告）
- 調整 `config/report-generator.yml` 設定（分類類別、大魚門檻等）

## Changelog

### v1.0.0 (2026-02-10)
- 初始版本
- 支援 AI 分類和摘要
- 產出 Markdown 格式戰報
- Telegram + LINE 雙通道通知
- 大魚自動識別與特別通知
- 完整錯誤處理和降級策略

---

**版本**: 1.0.0
**最後更新**: 2026-02-10
**作者**: Claude Code + OpenClaw
**License**: AGPL-3.0
