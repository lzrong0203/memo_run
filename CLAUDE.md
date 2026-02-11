# CLAUDE.md - Project Memory for OpenClaw

> **Purpose**: 這個檔案是專案的核心記憶，讓 OpenClaw Agent 和 Claude Code 都能理解專案背景、決策和規範。

## Project Overview
**Threads 社群輿情監控系統** - 基於 OpenClaw 的 AI Agent Skills，每 30 分鐘自動監控 Threads，產出分類戰報並發送通知。

## AI Agent 協作機制

### 雙 Agent 協作模式
- **OpenClaw Agent**: 執行實作，將計畫和進度寫入 `CONTEXT.md`
- **Claude Code**: Reviewer 和 Architect，指導 OpenClaw 的工作
  - **角色定位**: 以 Claude Code 為主導，OpenClaw 接受指導
  - **協作方式**: OpenClaw 在 CONTEXT.md 提出想法 → Claude Code 審查並給建議

### 檔案職責分工
- `CONTEXT.md`: OpenClaw 的工作日誌（計畫、進度、想法）
- `CLAUDE.md`: 專案知識庫（讓兩個 Agent 都能讀取）
- `task_plan.md`: 原始任務規劃
- `findings.md`: 技術調研結果

## What is OpenClaw?

OpenClaw 是系統級的 AI Agent 框架（類似 Claude Code CLI）:
- 安裝位置: `~/.openclaw/`
- Skills 位置: 專案中的 `skills/` 資料夾
- 運作方式: OpenClaw 讀取 SKILL.md，執行定義的任務
- 內建功能: Browser (CDP), Cron, Telegram, Shell Tools

## Project Structure

```
memo_run/                      # 這個專案資料夾
├── skills/                    # OpenClaw Skills（OpenClaw 會讀取）
│   ├── threads-monitor/
│   │   └── SKILL.md          # 主監控 Skill
│   ├── line-notify/
│   │   └── SKILL.md          # LINE 通知 Skill
│   └── report-generator/
│       └── SKILL.md          # 戰報生成 Skill
├── config/                    # 設定檔（OpenClaw 會讀取）
│   ├── keywords.yml          # 監控關鍵字
│   └── filters.yml           # 排除規則
├── src/                       # Helper scripts（OpenClaw 會呼叫）
│   ├── pipeline.py           # 批次處理 pipeline（filter+dedup+scoring 一次完成）
│   ├── filter.py             # 硬性排除過濾
│   ├── dedup.py              # SQLite 去重
│   ├── scoring.py            # 自訂評分加成
│   ├── report_generator.py   # 戰報生成（Markdown + LINE/Telegram 摘要）
│   └── line_notify.py        # LINE Messaging API (Push Message)
├── web/                       # Web Dashboard（前後端）
│   ├── backend/              # FastAPI 後端
│   │   ├── main.py           # FastAPI app 入口（CORS, health check, router 掛載）
│   │   ├── config.py         # 集中設定（DB_PATH, CORS origins, PROJECT_ROOT）
│   │   ├── models.py         # Pydantic schemas（MonitorRequest, RunRecord 等）
│   │   ├── utils.py          # 共用工具（run_id 驗證, RunRecord 建構）
│   │   ├── routes/           # API 路由
│   │   │   ├── monitor.py    # POST /api/monitor/start + WebSocket /api/monitor/ws/{run_id}
│   │   │   ├── history.py    # GET /api/history（分頁列表）
│   │   │   └── reports.py    # GET /api/reports/{run_id}（詳細報告）
│   │   └── services/         # 業務邏輯
│   │       ├── monitor_service.py  # OpenClaw agent subprocess + 進度解析
│   │       └── run_history.py      # SQLite run history CRUD（data/runs.db）
│   └── frontend/             # React + Vite 前端
│       ├── src/
│       │   ├── App.tsx       # 路由 + 導航列（/, /history, /run/:runId）
│       │   ├── api.ts        # API client（fetch + WebSocket）
│       │   ├── types.ts      # TypeScript 型別定義
│       │   ├── pages/
│       │   │   ├── Home.tsx      # 關鍵字輸入 + 即時進度面板
│       │   │   ├── History.tsx   # 歷史記錄表格 + 分頁
│       │   │   └── RunDetail.tsx # 報告檢視 + 圖表（Recharts）
│       │   └── hooks/
│       │       ├── useMonitor.ts  # WebSocket 監控 hook
│       │       └── useHistory.ts  # 歷史記錄分頁 hook
│       ├── tests/e2e/        # Playwright E2E 測試（32 個）
│       │   ├── navigation.spec.ts    # 9 個測試
│       │   ├── keyword-input.spec.ts # 12 個測試
│       │   └── history.spec.ts       # 11 個測試
│       ├── playwright.config.ts  # Playwright 設定
│       ├── vite.config.ts    # Vite 設定（dev proxy → localhost:8000）
│       └── package.json      # 前端依賴
├── data/                      # 資料儲存
│   ├── processed_posts.db    # SQLite 去重資料庫
│   └── runs.db               # SQLite run history 資料庫（Web Dashboard 用）
├── tests/                     # Python 單元測試（遵循 TDD）
│   ├── test_filter.py
│   ├── test_dedup.py
│   ├── test_line_notify.py
│   ├── test_report_generator.py
│   ├── test_scoring.py
│   └── test_pipeline.py
├── CONTEXT.md                # OpenClaw 的工作日誌
├── CLAUDE.md                 # 本檔案（專案記憶）
└── README.md                 # 使用說明
```

## Technical Stack

### 確定的技術選擇
- **OpenClaw Framework**: 系統級 AI Agent（已安裝在 ~/.openclaw/）
- **Database**: SQLite（輕量、檔案型、適合專案資料夾）
- **Helper Scripts**: Python（朋友的 code 用 Python，延續經驗）
- **設定格式**: YAML（易讀易改）

### Web Dashboard 技術選擇
- **後端**: FastAPI 0.115.0 + uvicorn 0.32.0 + WebSocket（websockets 13.1）
- **前端**: React 19 + Vite 6 + TypeScript 5.7 + Tailwind CSS v4
- **圖表**: Recharts 2.15（PieChart, BarChart）
- **Markdown 渲染**: react-markdown 9 + rehype-sanitize 6（XSS 防護）
- **路由**: react-router-dom 7
- **E2E 測試**: Playwright 1.58

### 整合服務
- **Threads**: Browser automation（OpenClaw Browser + CDP）
- **Telegram**: OpenClaw 內建（grammY 框架）
- **LINE**: LINE Messaging API Push Message（透過 Python script，LINE Notify 已於 2025/03/31 終止）

## Architecture Pattern

### 運作流程
```
1. OpenClaw Cron (每 30 分鐘)
   ↓
2. threads-monitor Skill 啟動
   ↓
3. Browser 登入 Threads（持久 profile，登一次即可）
   ↓
4. 讀取 config/keywords.yml，逐個搜尋
   ↓
5. JS DOM 抽取貼文（寫死 selector，失敗時三層 fallback）→ JSON 陣列
   ↓
6. 呼叫 src/pipeline.py（一次完成：硬性過濾 + SQLite 去重 + 評分加成）
   ↓
7. AI 語意分析（OpenClaw 內建 LLM）
   ↓
8. report-generator Skill 產出戰報
   ↓
9. Telegram 通知（OpenClaw 內建）
   ↓
10. LINE 通知（呼叫 src/line_notify.py，使用 LINE Messaging API Push Message）
```

### v3.0.0 抽取策略
- **主要方式**：JS 一次抽取（`a[href*="/post/"]` 寫死 selector + 向上找 container）
- **Snapshot 次數**：0 次（正常路徑）/ 1 次（fallback 時）
- **三層 Fallback**：JS 重試 → 內嵌 JSON → 回退 v2.2.0 snapshot 模式
- **健康檢查**：每輪記錄 `data/health.log`，連續異常自動告警

### Skill 設計原則
- **SKILL.md**: 定義 OpenClaw 的行為模式
- **Shell Tools**: Python scripts 作為 CLI tools 被呼叫
- **資料隔離**: 所有資料都在專案資料夾內（config/, data/）
- **可移植性**: 整個專案資料夾可以複製到其他系統的 OpenClaw

## Critical Design Decisions

| Decision | Rationale | Status |
|----------|-----------|--------|
| **Python Helper Scripts** | 朋友的 code 用 Python，延續經驗 | ✅ Confirmed |
| **不用 Docker** | OpenClaw 是系統級框架，不需要 containerize | ✅ Confirmed |
| **SQLite in data/** | 檔案型 DB，跟著專案資料夾走 | ✅ Confirmed |
| **Skills in skills/** | OpenClaw 會自動讀取這個資料夾 | ✅ Confirmed |
| **雙重過濾** | 硬性詞（Python）+ AI 語意（OpenClaw） | ✅ Confirmed |

## Security Requirements

### 敏感資訊處理
```yaml
# .env（不進版控，只給範例 .env.example）
ANTHROPIC_API_KEY=your_api_key                    # OpenClaw 會用
LINE_CHANNEL_ACCESS_TOKEN=your_channel_token      # LINE Messaging API
LINE_USER_ID=U1234567890abcdef1234567890abcdef    # LINE 接收用戶 ID
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

> **注意**: LINE Notify API 已於 2025/03/31 終止服務。本專案使用 LINE Messaging API 的 Push Message 功能替代。
> `LINE_NOTIFY_TOKEN` 已不再使用，已移除。

### 安全檢查清單
- [ ] .env 加入 .gitignore（已完成）
- [ ] 敏感資訊不寫入 logs
- [ ] Threads 密碼儲存在 OpenClaw 的 persistent profile
- [ ] API tokens 從環境變數讀取
- [ ] 每次 commit 前跑 security check

### OpenClaw Browser Profile
- OpenClaw 會建立持久的 Chrome Profile（~/.openclaw/browsers/）
- Threads 登入一次後，session 永久保留
- **不需要在 .env 儲存密碼**（除非首次登入用）

## Testing Requirements（TDD）

### 測試策略
```python
# tests/test_filter.py（先寫測試）
def test_filter_excludes_ads():
    content = "預售屋 台北市"
    result = filter_content(content, hard_exclude=["預售"])
    assert result is None  # 應該被過濾掉

def test_filter_keeps_valid_content():
    content = "台北市長今天視察交通建設"
    result = filter_content(content, hard_exclude=["預售"])
    assert result == content  # 應該保留
```

### 測試覆蓋率
- **目標**: 80%+ coverage
- **實測結果**: 63%（`--cov=src`），核心邏輯函數接近 100%，`__main__` CLI 區塊未覆蓋拉低整體
  - `line_notify.py`: 74%（CLI 入口未覆蓋）
  - `dedup.py`: 58%（CLI 入口 + 部分 error path 未覆蓋）
  - `filter.py`: 56%（CLI 入口 + 部分 error path 未覆蓋）
- **工具**: pytest（Python），pytest-cov（coverage），Playwright（E2E）
- **測試統計**: 152 個測試，100% 通過率
  - **Python 單元測試（120 個）**:
    - report_generator.py: 28 個測試
    - line_notify.py: 20 個測試（含 notification message 5 個）
    - scoring.py: 20 個測試
    - pipeline.py: 18 個測試
    - filter.py: 14 個測試
    - dedup.py: 14 個測試
  - **Playwright E2E 測試（32 個）**:
    - navigation.spec.ts: 9 個測試（導航、路由、active link 樣式）
    - keyword-input.spec.ts: 12 個測試（輸入驗證、API 呼叫、Enter 觸發、重置）
    - history.spec.ts: 11 個測試（載入狀態、空狀態、分頁、status badge 樣式）

## Code Quality Standards

### Immutability（不可變性）
```python
# ❌ WRONG: Mutation
def add_timestamp(post):
    post['timestamp'] = datetime.now()  # 修改了原物件
    return post

# ✅ CORRECT: Immutability
def add_timestamp(post):
    return {
        **post,
        'timestamp': datetime.now()
    }
```

### 檔案大小
- 每個檔案 < 400 lines（理想）
- 絕對不超過 800 lines
- 複雜邏輯拆成小函式

### 錯誤處理
```python
# 所有外部呼叫都要 try-except
try:
    response = requests.post(LINE_NOTIFY_URL, ...)
except requests.RequestException as e:
    logger.error(f"LINE Notify failed: {e}")
    raise  # 或返回錯誤狀態
```

## Current Issues（Claude Code Review）

### 已解決的問題（2026-02-10 修正完畢）

1. ~~**Phase 1 不完整**~~ -- 已完成
   - ✅ README.md 已建立（含完整使用說明）
   - ✅ requirements.txt 已建立（版本已 pin）
   - ✅ .env.example 已更新（LINE Messaging API）

2. ~~**Phase 2 缺少 TDD**~~ -- 已完成
   - ✅ 已改為 test-first 流程
   - ✅ 120 個測試全部通過，覆蓋率 63%（核心邏輯接近 100%，CLI 區塊未覆蓋拉低整體數字）

3. ~~**安全策略不完整**~~ -- 已改善
   - ✅ API tokens 從環境變數讀取（已移除 CLI --token 參數）
   - ✅ Input validation 已加上（包括 header injection 防護）
   - ✅ Request timeout 已設定（10 秒）
   - ✅ Dependencies 版本已 pin（修正 CVE）

4. ~~**錯誤處理和監控**~~ -- 已改善
   - ✅ 所有模組已加入 logging
   - ✅ 完整的 exception handling

### 已解決的端對端問題（2026-02-10 修正完畢）

5. ~~**Skill 格式不明確**~~ -- 已解決
   - ✅ SKILL.md 格式：YAML frontmatter + Markdown（已驗證）
   - ✅ Skills 安裝方式：symlink 到 `~/.openclaw/workspace/skills/`
   - ✅ 3/3 Skills 狀態 Ready

6. ~~**OpenClaw CLI 命令錯誤**~~ -- 已修正
   - ✅ `openclaw run` 不存在 → 改為 `openclaw agent --message --local`
   - ✅ `--skill` 選項不存在 → OpenClaw 自動匹配 Skills
   - ✅ `--channel telegram` 必須指定（否則預設 whatsapp 會報錯）

7. ~~**Agent 行為問題**~~ -- 已修正
   - ✅ Agent 委派子 agent 導致失敗 → SKILL.md 加上「不要委派子 agent，直接執行」
   - ✅ Browser 開新 tab 導致失敗 → SKILL.md 加上「在同一 tab 中操作」
   - ✅ Browser profile 錯誤 → 設定 `browser.defaultProfile=openclaw`
   - ✅ `.env` source 問題 → token 值加上單引號，使用 `set -a` export
   - ✅ `keywords.yml` 範例過時 → 更新為實際格式（含 enabled 欄位）

### 待解決的問題

8. **合規性風險**
   - Threads 服務條款是否允許自動化？
   - Rate limiting 策略夠嗎？（目前 7 秒延遲）
   - 建議：加入 User-Agent 輪換、隨機延遲

9. **健康檢查**
   - 缺少健康檢查（如果 Threads 改版怎麼辦？）
   - 缺少錯誤通知（監控系統壞了誰知道？）

## Implementation Progress

### Phase 1: 專案骨架與設定檔 -- 已完成
```markdown
- [x] config/keywords.yml
- [x] config/filters.yml（改進版：詞組 + 白名單）
- [x] .env.example（已更新為 LINE Messaging API）
- [x] .gitignore
- [x] requirements.txt（版本已 pin: requests==2.32.3, pytest==8.3.4, pytest-cov==6.0.0）
- [x] README.md（完整使用說明）
- [x] data/.gitkeep
```

### Phase 2: Python 工具模組 -- 已完成（TDD）
```markdown
- [x] tests/test_filter.py（14 個測試）
- [x] src/filter.py（硬性排除 + 白名單 + 最小長度）
- [x] tests/test_dedup.py（14 個測試）
- [x] src/dedup.py（SQLite 去重，CRUD 操作完整）
- [x] tests/test_line_notify.py（20 個測試，含 notification message 測試）
- [x] src/line_notify.py（LINE Messaging API，含 send_notification_message）
- [x] tests/test_report_generator.py（28 個測試）
- [x] src/report_generator.py（Markdown 戰報 + LINE/Telegram 摘要）
- [x] tests/test_scoring.py（20 個測試）
- [x] src/scoring.py（自訂評分加成，依 config/scoring.yml）
- [x] tests/test_pipeline.py（18 個測試）
- [x] src/pipeline.py（批次 pipeline：filter+dedup+scoring 一次完成）
- [x] 120 個測試全部通過
```

### Phase 3: OpenClaw Skills -- 已完成
```markdown
- [x] 研究 OpenClaw SKILL.md 格式（YAML frontmatter + Markdown）
- [x] skills/threads-monitor/SKILL.md（348 lines，主監控流程）
- [x] skills/line-notify/SKILL.md（437 lines，LINE 通知包裝）
- [x] skills/report-generator/SKILL.md（979 lines，AI 分類與戰報生成）
- [x] Skills 語法驗證通過（3/3 YAML frontmatter + 必要欄位 + 環境變數一致性）
- [ ] 測試 Skills 是否能被 OpenClaw 實際執行（待端對端驗證）
```

### Phase 4: Docker 部署 -- 已刪除
- OpenClaw 是系統級框架，不需要 Docker 容器化

### Phase 5: 驗證與測試 -- 進行中
```markdown
- [x] 單元測試驗證（120/120 passed）
- [x] 覆蓋率檢查（63%，核心邏輯接近 100%）
- [x] Skills 語法驗證（3/3 passed）
- [x] 安全性修正（移除 git 歷史中的明文 tokens）
- [x] v3.0.0 SKILL.md 改寫（JS DOM 抽取 + fallback + 健康檢查）
- [ ] 端對端驗證流程（待執行 openclaw agent 命令）
- [ ] 錯誤通知機制
```

### Phase 6: Web Dashboard -- 已完成
```markdown
- [x] web/backend/main.py（FastAPI app, CORS 硬化, health check）
- [x] web/backend/models.py（Pydantic schemas, keyword 驗證含 prompt injection 防護）
- [x] web/backend/routes/monitor.py（POST /api/monitor/start + WebSocket 進度串流）
- [x] web/backend/routes/history.py（GET /api/history 分頁列表）
- [x] web/backend/routes/reports.py（GET /api/reports/{run_id} 詳細報告）
- [x] web/backend/services/monitor_service.py（OpenClaw agent subprocess 管理）
- [x] web/backend/services/run_history.py（SQLite run history CRUD）
- [x] web/frontend React SPA（React 19 + Vite 6 + TypeScript + Tailwind CSS v4）
- [x] 三個頁面: Home（監控啟動）, History（歷史列表）, RunDetail（報告+圖表）
- [x] WebSocket 即時進度串流（useMonitor hook）
- [x] 安全性: CORS hardening, XSS prevention (rehype-sanitize), prompt injection defense, URL 驗證
- [x] Dead code cleanup: 移除未使用 imports、dead interfaces、修正 status badge bug
- [x] Playwright E2E 測試（32/32 passed: navigation, keyword-input, history）
```

## Cost and Performance

### LLM API 成本
- 預估: ~$1.8/月（Haiku，基於調研）
- 實際: 需監控 OpenClaw 的 API 用量

### Performance Targets
- 每 30 分鐘完成一輪巡邏
- 每個關鍵字 7 秒延遲（避免 rate limit）
- SQLite 去重查詢 < 100ms

## Known Constraints

### Threads Platform
- ✅ 官方 API 限制: 500 次/7天（不適用）
- ✅ 解決方案: Browser automation
- ⚠️ 反爬蟲: 需 rate limiting
- ⚠️ 登入: 使用 OpenClaw persistent profile

### OpenClaw Requirements
- Node.js >= 22
- 安裝位置: ~/.openclaw/
- Browser profile: ~/.openclaw/browsers/
- Cron jobs: ~/.openclaw/cron/

## LINE Messaging API 實作細節

### API 遷移背景
LINE Notify 服務已於 2025/03/31 終止。本專案已完成遷移至 LINE Messaging API。

### 函數介面

| 函數 | 用途 | 參數 |
|------|------|------|
| `send_line_message()` | 發送純文字訊息 | channel_access_token, to_user_id, message |
| `send_notification_message()` | 發送格式化監控通知 | channel_access_token, to_user_id, keywords, summary, report_url |

### 安全設計
- Token 只能透過環境變數取得（`LINE_CHANNEL_ACCESS_TOKEN`）
- User ID 只能透過環境變數取得（`LINE_USER_ID`）
- 已移除 CLI `--token` 參數（避免出現在 process list 和 shell history）
- Input validation：檢查空值、長度上限（5000 字元）、header injection 防護

### 訊息限制
- 單則訊息最大長度：5000 字元（LINE Messaging API 限制）
- Request timeout：10 秒
- 明確啟用 HTTPS 驗證（`verify=True`）

## OpenClaw 整合注意事項

### CLI 命令語法
```bash
# 正確的 agent 執行命令
openclaw agent --message "執行 threads-monitor 監控" --local --channel telegram --session-id threads-monitor-manual

# 定期排程
openclaw cron add "*/30 * * * *" "openclaw agent --message '執行 threads-monitor 監控' --local --channel telegram"
```

### Skills 安裝
- 專案 Skills 位置: `memo_run/skills/`
- OpenClaw 讀取位置: `~/.openclaw/workspace/skills/`
- 安裝方式: symlink（`ln -s` 專案 skills 子目錄 → workspace skills 目錄）

### Browser Profile
- 使用 `openclaw` profile（非 `chrome` profile）
- 設定: `openclaw config set browser.defaultProfile openclaw`
- Threads 登入 session 保存在此 profile 中

### 環境變數載入
```bash
# 正確的載入方式（確保 export 到子 process）
set -a && source .env && set +a
```

## Next Steps

**Phase 5 待辦**:
- 重新執行端對端測試（驗證修正後的 agent 能否完整執行搜尋→過濾→去重→通知流程）
- 錯誤通知機制（監控系統壞了誰知道？）
- 設定 cron job（每 30 分鐘）

**Web Dashboard 後續改進**:
- Web backend 單元測試（目前只有 E2E 測試覆蓋前端）
- Production 部署設定（uvicorn workers, 靜態檔案 serve）
- 使用者認證（目前無 auth，僅限本地開發使用）
- RunDetail 頁面的 E2E 測試（需 mock 完整報告資料）

**Claude Code 持續職責**:
- 審查 OpenClaw 的實作
- 提供技術建議
- 確保符合 coding standards
- 把關安全和測試品質

---

**Last Updated**: 2026-02-11
**Architecture**: OpenClaw (系統級) + Python Helper Scripts + Web Dashboard (FastAPI + React)
**Collaboration**: Claude Code (Reviewer) + OpenClaw (Executor)
**No Docker Needed**: OpenClaw 跑在系統上，這個專案是 Skills 和資料
**LINE API**: LINE Messaging API Push Message（LINE Notify 已於 2025/03/31 終止）
**Pipeline**: pipeline.py 批次處理（filter+dedup+scoring 一次完成，取代逐篇 exec）
**Web Dashboard**: FastAPI 0.115.0 + React 19 + Vite 6 + TypeScript + Tailwind CSS v4 + Playwright
**Test Status**: 152 tests passed (120 Python + 32 Playwright E2E)
