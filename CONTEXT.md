# Project Context: Threads 社群輿情監控系統 (OpenClaw)

## Goal
建立基於 OpenClaw 的 AI Agent 輿情監控系統，每 30 分鐘自動掃描 Threads，雙重過濾後產出分類戰報，透過 Telegram + LINE 發送通知。

## Current Status
專案目前處於 **Phase 1: 專案骨架與設定檔**。已完成專案目錄結構的建立。

## My Updated Detailed Execution Plan (Addressing Claude Code's Review)

### Phase 1: 專案骨架與設定檔 (已完成)
*   **步驟 1.1: 建立 `config/` 資料夾。** (已完成)
*   **步驟 1.2: 建立 `config/keywords.yml`。** (已完成 by repo)
*   **步驟 1.3: 建立 `config/filters.yml`。** (已完成 by repo)
*   **步驟 1.4: 建立 `.env.example`。** (已完成 by repo)
*   **步驟 1.5: 建立 `.gitignore`。** (已完成 by repo)
*   **步驟 1.6: 補充 `requirements.txt`。**
    *   我將創建 `requirements.txt`，並加入 `requests` 和 `pyyaml`。`sqlite3` 是 Python 內建的，因此無需列出。(已完成)
*   **步驟 1.7: 建立 `data/.gitkeep`。**
    *   我將創建 `data/` 資料夾並在其中建立一個空的 `.gitkeep` 檔案，以確保該資料夾被納入版本控制。(已完成)

### Phase 2: Python 工具模組 (進行中 - 遵循 TDD 流程)
*   **步驟 2.1: 準備測試環境。**
    *   我將創建 `tests/` 資料夾。(已完成)
*   **步驟 2.2: 實作 `src/filter.py`。**
    *   **先寫 `tests/test_filter.py`。** 定義 `filter.py` 預期的行為，包括硬性排除詞過濾。
    *   **再寫 `src/filter.py`。** 編寫 Python 腳本，使其通過測試。
    *   使其可以作為 CLI 工具被呼叫。
*   **步驟 2.3: 實作 `src/dedup.py`。**
    *   **先寫 `tests/test_dedup.py`。** 定義 `dedup.py` 預期的行為，包括使用 SQLite 進行去重。
    *   **再寫 `src/dedup.py`。** 編寫 Python 腳本，使其通過測試。
    *   使其可以作為 CLI 工具被呼叫。
*   **步驟 2.4: 實作 `src/line_notify.py`。**
    *   **先寫 `tests/test_line_notify.py`。** 定義 `line_notify.py` 預期的行為，包括使用 LINE Notify API 發送訊息。
    *   **再寫 `src/line_notify.py`。** 編寫 Python 腳本，使其通過測試。
    *   使其可以作為 CLI 工具被呼叫，接收訊息內容和 LINE Notify Token。
*   **步驟 2.5: 執行測試並檢查覆蓋率。**
    *   執行 `pytest --cov=src`，確保達到 80% 以上的測試覆蓋率。

### Phase 3: OpenClaw Skills (待辦 - 研究 SKILL.md 格式，定義安全策略)
*   **步驟 3.1: 研究 OpenClaw `SKILL.md` 格式。**
    *   在實作 Skills 之前，我會查閱 OpenClaw 官方文件，了解 `SKILL.md` 的標準格式和最佳實踐。
*   **步驟 3.2: 定義 Threads 憑證和 API tokens 的安全策略。**
    *   確認 Threads 登入將使用 OpenClaw 的 persistent Chrome profile，不需要在 `.env` 中儲存密碼（除非首次登入用）。
    *   確保所有 API tokens 都從環境變數讀取。
*   **步驟 3.3: 撰寫 `skills/threads-monitor/SKILL.md`。** (細節待研究後填寫)
*   **步驟 3.4: 撰寫 `skills/line-notify/SKILL.md`。** (細節待研究後填寫)
*   **步驟 3.5: 撰寫 `skills/report-generator/SKILL.md`。** (細節待研究後填寫)

### Phase 4: 刪除 Docker 部署相關步驟
*   根據 Claude Code 的建議，刪除所有關於 Docker 部署的步驟，因為 OpenClaw 是系統級框架，不需要容器化。

### Phase 5: 驗證與測試 (待辦 - 補充錯誤處理和監控)
*   **步驟 5.1: 測試 `filter.py` / `dedup.py` / `line_notify.py`。** (在 Phase 2 完成)
*   **步驟 5.2: 確認 OpenClaw 安裝與設定流程文件完整。** (在 Phase 1 檢查 `README.md` 是否足夠)
*   **步驟 5.3: 端對端驗證流程。** (待 Phase 3 完成後實作)
*   **步驟 5.4: 補充錯誤處理和監控機制。**
    *   引入日誌系統 (logging)。
    *   考慮健康檢查和錯誤通知機制。
    *   規劃備援機制。

---

**Review Status**: 已更新 Dobby 的執行計畫，並移除舊的 Claude Code Review。
**Next Action**: 根據 Dobby 的更新計畫，由 Claude Code 進行審查並提供回饋。
