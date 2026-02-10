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
│   ├── filter.py             # 硬性排除過濾
│   ├── dedup.py              # SQLite 去重
│   └── line_notify.py        # LINE Notify API
├── data/                      # 資料儲存
│   └── processed_posts.db    # SQLite 去重資料庫
├── tests/                     # 測試（遵循 TDD）
│   ├── test_filter.py
│   ├── test_dedup.py
│   └── test_line_notify.py
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

### 整合服務
- **Threads**: Browser automation（OpenClaw Browser + CDP）
- **Telegram**: OpenClaw 內建（grammY 框架）
- **LINE**: LINE Notify API（透過 Python script）

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
5. 抓取貼文 → 呼叫 src/filter.py（硬性排除）
   ↓
6. 呼叫 src/dedup.py（SQLite 去重）
   ↓
7. AI 語意分析（OpenClaw 內建 LLM）
   ↓
8. report-generator Skill 產出戰報
   ↓
9. Telegram 通知（OpenClaw 內建）
   ↓
10. LINE 通知（呼叫 src/line_notify.py）
```

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
THREADS_USERNAME=your_username
THREADS_PASSWORD=your_password
TELEGRAM_BOT_TOKEN=your_bot_token
LINE_NOTIFY_TOKEN=your_line_token
ANTHROPIC_API_KEY=your_api_key  # OpenClaw 會用
```

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
- **工具**: pytest（Python），pytest-cov（coverage）
- **何時寫**: Phase 2 開始就要 test-first（TDD）

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

### 🔴 CRITICAL Issues from CONTEXT.md Review

1. **Phase 1 不完整**
   - ❌ 缺少 README.md（OpenClaw 怎麼用這個專案？）
   - ❌ 缺少 requirements.txt 或 pyproject.toml（Python 依賴）
   - ❌ 缺少 .env.example 的詳細說明

2. **Phase 2 缺少 TDD**
   - ❌ 計畫中沒有 "先寫測試" 的步驟
   - ✅ 修正建議：改為 test-first 流程

### 🟠 HIGH Priority

3. **Skill 格式不明確**
   - ⚠️ SKILL.md 的格式規範是什麼？
   - ⚠️ OpenClaw 如何讀取和執行 SKILL.md？
   - 建議：先研究 OpenClaw 官方文件或範例

4. **安全策略不完整**
   - ⚠️ Threads 密碼如何安全儲存？
   - ⚠️ API tokens 如何管理？
   - 建議：明確定義在 Phase 1

### 🟡 MEDIUM Priority

5. **錯誤處理和監控**
   - 缺少日誌系統（logging）
   - 缺少健康檢查（如果 Threads 改版怎麼辦？）
   - 缺少錯誤通知（監控系統壞了誰知道？）

6. **合規性風險**
   - Threads 服務條款是否允許自動化？
   - Rate limiting 策略夠嗎？（目前 7 秒延遲）
   - 建議：加入 User-Agent 輪換、隨機延遲

## Recommendations for OpenClaw

### Phase 1 修正建議
```markdown
- [x] config/keywords.yml
- [x] config/filters.yml
- [x] .env.example
- [x] .gitignore
- [ ] requirements.txt（Python 依賴: requests, pyyaml, sqlite3）
- [ ] README.md（安裝、設定、啟動說明）
- [ ] data/.gitkeep（確保資料夾存在）
- [ ] 研究 SKILL.md 格式（OpenClaw 官方文件）
```

### Phase 2 修正建議（TDD）
```markdown
- [ ] tests/test_filter.py（先寫測試）
- [ ] src/filter.py（實作讓測試通過）
- [ ] tests/test_dedup.py
- [ ] src/dedup.py
- [ ] tests/test_line_notify.py
- [ ] src/line_notify.py
- [ ] 跑 pytest --cov（確保 80%+ coverage）
```

### Phase 3 新增建議
```markdown
- [ ] 研究 OpenClaw SKILL.md 格式
- [ ] skills/threads-monitor/SKILL.md
- [ ] skills/line-notify/SKILL.md
- [ ] skills/report-generator/SKILL.md
- [ ] 測試 Skills 是否能被 OpenClaw 讀取
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

## Next Steps

**OpenClaw 應該做的事**（優先順序）:
1. ✅ 讀取這個 CLAUDE.md，理解專案架構
2. 📝 完善 Phase 1（補 README, requirements.txt）
3. 📚 研究 OpenClaw SKILL.md 格式（看官方文件或範例）
4. 🧪 修正 Phase 2 為 TDD 流程
5. 🔐 定義安全策略（敏感資訊處理）
6. 📝 更新 CONTEXT.md，說明修正計畫

**Claude Code 會做的事**:
- 審查 OpenClaw 的修正計畫
- 提供技術建議
- 確保符合 coding standards
- 把關安全和測試品質

---

**Last Updated**: 2026-02-10
**Architecture**: OpenClaw (系統級) + Python Helper Scripts
**Collaboration**: Claude Code (Reviewer) + OpenClaw (Executor)
**No Docker Needed**: OpenClaw 跑在系統上，這個專案是 Skills 和資料
