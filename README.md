# Threads 社群輿情監控系統

基於 **OpenClaw** AI Agent 的自動化社群監控系統，每 30 分鐘自動掃描 Threads 社群，透過雙重過濾（硬性排除 + AI 語意分析）產出分類戰報，並透過 Telegram + LINE 雙通道發送通知。

## 🎯 專案目標

- ✅ 每 30 分鐘自動監控 Threads 指定關鍵字
- ✅ 雙重過濾機制：硬性排除詞 + AI 語意分析
- ✅ AI 分類戰報（政治/交通/社會/投訴等）
- ✅ 重大議題「大魚」自動標記
- ✅ Telegram + LINE 雙通道通知
- ✅ 支援自動巡邏 + 手動指令觸發

## 🏗️ 專案架構

### 什麼是 OpenClaw？

**OpenClaw** 是系統級的 AI Agent 框架（類似 Claude Code CLI），提供：
- 🌐 Browser automation（基於 Chrome DevTools Protocol）
- ⏰ Cron job 排程（持久化任務）
- 💬 Telegram 整合（內建 grammY 框架）
- 🛠️ Shell tools 呼叫能力
- 🤖 AI 語意理解（內建 LLM）

### 專案結構

```
memo_run/                      # OpenClaw Skills 專案
├── skills/                    # OpenClaw 會讀取的 Skills（待實作）
│   ├── threads-monitor/       # 主監控 Skill
│   ├── line-notify/           # LINE 通知 Skill
│   └── report-generator/      # 戰報生成 Skill
├── config/                    # 設定檔
│   ├── keywords.yml          # 監控關鍵字設定
│   └── filters.yml           # 硬性排除詞 + 白名單設定
├── src/                       # Python Helper Scripts（已完成）
│   ├── filter.py             # 硬性排除過濾 CLI（詞組 + 白名單）
│   ├── dedup.py              # SQLite 去重 CLI（CRUD 操作）
│   └── line_notify.py        # LINE Messaging API CLI（Push Message + 格式化通知）
├── data/                      # 資料儲存
│   └── processed_posts.db    # SQLite 去重資料庫
├── tests/                     # 測試（TDD，48 個測試全部通過）
│   ├── test_filter.py        # 14 個測試
│   ├── test_dedup.py         # 14 個測試
│   └── test_line_notify.py   # 20 個測試
├── CONTEXT.md                # OpenClaw 工作日誌
├── CLAUDE.md                 # 專案知識庫
├── .env.example              # 環境變數範例
├── .gitignore                # Git 忽略檔案
├── requirements.txt          # Python 依賴（版本已 pin）
└── README.md                 # 本檔案
```

## 🚀 快速開始

### 前置需求

1. **OpenClaw 已安裝**
   ```bash
   # 確認 OpenClaw 已安裝（安裝方法請參考 OpenClaw 官方文件）
   openclaw --version
   ```

2. **Node.js >= 22**
   ```bash
   node --version  # 應該 >= 22
   ```

3. **Python 3.x**（用於 helper scripts）
   ```bash
   python3 --version
   ```

### 安裝步驟

1. **Clone 專案**
   ```bash
   git clone <repository-url>
   cd memo_run
   ```

2. **安裝 Python 依賴**（待補充 requirements.txt）
   ```bash
   pip install -r requirements.txt
   ```

3. **設定環境變數**
   ```bash
   cp .env.example .env
   # 編輯 .env，填入你的 API tokens
   ```

4. **設定監控關鍵字**
   ```bash
   # 編輯 config/keywords.yml
   vim config/keywords.yml
   ```

5. **設定排除規則**
   ```bash
   # 編輯 config/filters.yml
   vim config/filters.yml
   ```

### 使用方式（待 OpenClaw 實作 Skills）

```bash
# 手動觸發監控（待實作）
openclaw run skills/threads-monitor

# 設定自動巡邏（每 30 分鐘）（待實作）
openclaw cron add "*/30 * * * *" skills/threads-monitor
```

## 開發狀態

### Phase 1: 專案骨架與設定檔 -- 已完成
- [x] 專案目錄結構
- [x] config/keywords.yml（監控關鍵字設定）
- [x] config/filters.yml（硬性排除詞 + 白名單設定）
- [x] .env.example（環境變數範例，已更新為 LINE Messaging API）
- [x] .gitignore
- [x] requirements.txt（版本已 pin）
- [x] README.md / CLAUDE.md / CONTEXT.md

### Phase 2: Python 工具模組 -- 已完成（TDD，48 個測試，85%+ 覆蓋率）
- [x] src/filter.py -- 硬性排除過濾（詞組 + 白名單 + 最小長度）
- [x] src/dedup.py -- SQLite 去重管理（CRUD 完整）
- [x] src/line_notify.py -- LINE Messaging API Push Message + 格式化通知
- [x] 完整測試套件（line_notify: 20, filter: 14, dedup: 14）

### Phase 3: OpenClaw Skills -- 待開始
- [ ] 研究 OpenClaw SKILL.md 格式
- [ ] skills/threads-monitor/SKILL.md
- [ ] skills/line-notify/SKILL.md
- [ ] skills/report-generator/SKILL.md

### Phase 5: 驗證與測試 -- 待 Phase 3 完成
- [ ] 端對端驗證流程
- [ ] 健康檢查與錯誤通知機制

詳細開發計畫請見 [CONTEXT.md](CONTEXT.md)

## 🔒 安全性

### 敏感資訊處理

```bash
# .env 檔案格式（不進版控）
THREADS_USERNAME=your_username                    # 首次登入用（之後可刪除）
THREADS_PASSWORD=your_password                    # 首次登入用（之後可刪除）
TELEGRAM_BOT_TOKEN=your_bot_token
LINE_CHANNEL_ACCESS_TOKEN=your_channel_token      # LINE Messaging API
LINE_USER_ID=your_user_id                         # LINE 接收用戶 ID
ANTHROPIC_API_KEY=your_api_key                    # OpenClaw 使用
```

### 安全檢查清單
- ✅ .env 已加入 .gitignore
- ⚠️ Threads 登入使用 OpenClaw persistent profile（登入一次，永久保留）
- ⚠️ 不在 logs 中記錄敏感資訊
- ⚠️ API tokens 從環境變數讀取

## 📨 LINE 通知功能

### 結構化訊息格式

系統會發送包含關鍵字、摘要和報告連結的格式化訊息：

```
🔔 Threads 監控通知

關鍵字: 政治, 選舉, 投票

摘要:
本週 Threads 熱門討論包含多項選舉相關議題...

完整報告:
https://example.com/report/12345
```

### 使用方式

```python
from line_notify import send_notification_message

# 發送結構化通知
success = send_notification_message(
    channel_access_token="your_token",
    to_user_id="U1234567890abcdef",
    keywords=["政治", "選舉", "投票"],  # 可為列表或字串
    summary="本週熱門討論摘要...",
    report_url="https://example.com/report/123"
)
```

### CLI 工具

```bash
# 設定環境變數
export LINE_CHANNEL_ACCESS_TOKEN='your_token'
export LINE_USER_ID='U1234567890abcdef'

# 發送簡單訊息
python3 src/line_notify.py --message "測試訊息"
```

## 🧪 測試

### 測試策略（TDD）

本專案遵循 **Test-Driven Development**：
1. 先寫測試（RED）
2. 實作程式碼（GREEN）
3. 重構優化（REFACTOR）

### 執行測試

```bash
# 執行所有測試
python3 -m unittest discover tests

# 執行特定測試
python3 tests/test_line_notify.py
python3 tests/test_filter.py
python3 tests/test_dedup.py

# 測試覆蓋率
- line_notify.py: 85%+ coverage (20 tests)
- filter.py: 85%+ coverage (15 tests)
- dedup.py: 85%+ coverage (13 tests)
```

## 🤝 雙 Agent 協作機制

本專案採用**雙 Agent 協作模式**：

### 角色分工
- **Claude Code**: Reviewer 和 Architect（指導者）
  - 審查計畫和程式碼
  - 提供技術建議
  - 確保符合最佳實踐

- **OpenClaw**: Executor（執行者）
  - 執行實作
  - 在 CONTEXT.md 記錄進度
  - 根據建議調整

### 協作流程
```
1. OpenClaw 在 CONTEXT.md 提出計畫
   ↓
2. Claude Code 審查並在 CONTEXT.md 留下 Review
   ↓
3. OpenClaw 根據 Review 調整計畫
   ↓
4. Claude Code 再次審查
   ↓
（循環直到達成品質標準）
```

### 重要檔案
- **CONTEXT.md**: OpenClaw 的工作日誌（計畫、進度、想法）
- **CLAUDE.md**: 專案知識庫（架構、規範、決策）
- **README.md**: 本檔案（使用說明）

## 📚 技術棧

- **AI Agent**: OpenClaw（系統級框架）
- **Browser**: OpenClaw Browser (Chrome DevTools Protocol)
- **Scheduling**: OpenClaw Cron
- **Database**: SQLite（輕量、檔案型）
- **Helper Scripts**: Python 3.x
- **Notifications**:
  - Telegram: OpenClaw 內建（grammY）
  - LINE: LINE Messaging API（自製整合，支援結構化通知）
- **Testing**: pytest, pytest-cov

## 📖 相關文件

- [CONTEXT.md](CONTEXT.md) - OpenClaw 工作日誌
- [CLAUDE.md](CLAUDE.md) - 專案知識庫
- [task_plan.md](task_plan.md) - 原始任務規劃
- [findings.md](findings.md) - 技術調研結果

## 🔗 參考資源

- [OpenClaw 官方文件](https://docs.openclaw.ai)
- [OpenClaw Browser](https://docs.openclaw.ai/tools/browser)
- [OpenClaw Cron](https://docs.openclaw.ai/automation/cron-jobs)
- [OpenClaw Telegram](https://docs.openclaw.ai/channels/telegram)
- [LINE Messaging API](https://developers.line.biz/en/docs/messaging-api/)

## 💰 成本估算

- **LLM API**: ~$1.8/月（Haiku，基於調研）
- **需監控實際用量**

## ⚠️ 注意事項

### Threads 平台限制
- ⚠️ Threads 官方 API 限制: 500 次/7天（不適用，我們用 browser automation）
- ⚠️ 需注意服務條款合規性
- ⚠️ 需實作 rate limiting（目前設定 7 秒延遲）
- ⚠️ 建議加入 User-Agent 輪換、隨機延遲

### OpenClaw 需求
- Node.js >= 22
- 安裝位置: `~/.openclaw/`
- Browser profile: `~/.openclaw/browsers/`
- Cron jobs: `~/.openclaw/cron/`

## 📝 開發規範

遵循以下 coding standards（詳見 `~/.claude/rules/`）:
- **Immutability**: 不可變性原則
- **TDD**: Test-Driven Development（80%+ coverage）
- **Security**: 敏感資訊處理、輸入驗證
- **Code Quality**: 小檔案（<800 lines）、完整錯誤處理

## 🐛 已知問題

請見 [CONTEXT.md - Claude Code Review](CONTEXT.md#-claude-code-review-2026-02-10) 章節

## 📄 License

[GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE)

---

**Last Updated**: 2026-02-10
**Status**: Phase 2 已完成，Phase 3 待開始
**Tests**: 48/48 passed, 85%+ coverage
**Maintainer**: Claude Code (Reviewer) + OpenClaw (Executor)
