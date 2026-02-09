# Task Plan: Threads 社群輿情監控系統 (OpenClaw)

## Goal
建立基於 OpenClaw 的 AI Agent 輿情監控系統，每 30 分鐘自動掃描 Threads，雙重過濾後產出分類戰報，透過 Telegram + LINE 發送通知。

## Current Phase
Phase 1

## Phases

### Phase 1: 專案骨架與設定檔
- [ ] 建立專案目錄結構
- [ ] 建立 config/keywords.yml
- [ ] 建立 config/filters.yml
- [ ] 建立 .env.example
- [ ] 建立 .gitignore
- **Status:** in_progress

### Phase 2: Python 工具模組
- [ ] 實作 src/filter.py（硬性排除詞過濾 CLI）
- [ ] 實作 src/dedup.py（SQLite 去重 CLI）
- [ ] 實作 src/line_notify.py（LINE 通知 CLI）
- [ ] 測試各模組
- **Status:** pending

### Phase 3: OpenClaw Skills
- [ ] 撰寫 skills/threads-monitor/SKILL.md（核心監控）
- [ ] 撰寫 skills/line-notify/SKILL.md（LINE 通知）
- [ ] 撰寫 skills/report-generator/SKILL.md（AI 戰報）
- [ ] 撰寫 CLAUDE.md（Agent 核心記憶）
- **Status:** pending

### Phase 4: Docker 部署
- [ ] 建立 Dockerfile
- [ ] 建立 docker-compose.yml
- **Status:** pending

### Phase 5: 驗證與測試
- [ ] 測試 filter.py / dedup.py / line_notify.py
- [ ] 確認 OpenClaw 安裝與設定流程文件完整
- [ ] 端對端驗證流程
- **Status:** pending

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 用 OpenClaw 而非純 Playwright | AI Agent 理解頁面語義，抗 Threads 改版 |
| Telegram 用原生 channel | OpenClaw 內建 grammY 支援 |
| LINE 用自製 Python CLI skill | OpenClaw 不原生支援 LINE |
| 雙重過濾（硬性詞 + AI） | 學自朋友的 code，先排雜訊再 AI 分析 |
| SQLite 去重 | 輕量、適合 Docker volume 持久化 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |

## Notes
- 朋友的 code 參考：Selenium + Gemini + Telegram/Discord，已登入 Chrome Profile
- OpenClaw 需 Node >= 22
- 預估 LLM 成本：Haiku ~$1.8/月
