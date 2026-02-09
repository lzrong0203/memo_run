# Project Context: Threads 社群輿情監控系統 (OpenClaw)

## Goal
建立基於 OpenClaw 的 AI Agent 輿情監控系統，每 30 分鐘自動掃描 Threads，雙重過濾後產出分類戰報，透過 Telegram + LINE 發送通知。

## Current Status
專案目前處於 **Phase 1: 專案骨架與設定檔**。已完成專案目錄結構的建立。

## My Detailed Execution Plan

### Phase 1: 專案骨架與設定檔 (進行中)
*   **步驟 1.1: 建立 `config/` 資料夾。** (已完成)
*   **步驟 1.2: 建立 `config/keywords.yml`。** 我會創建一個包含範例關鍵字的 YAML 文件。
*   **步驟 1.3: 建立 `config/filters.yml`。** 我會創建一個包含範例硬性排除詞和 AI 語意分析相關配置的 YAML 文件。
*   **步驟 1.4: 建立 `.env.example`。** 我會創建一個包含所有必要環境變數（如 Threads 登入資訊、Telegram Bot Token、LINE Notify Token 等）範例的 `.env.example` 文件。
*   **步驟 1.5: 建立 `.gitignore`。** 我會創建一個 `.gitignore` 文件，以確保敏感資訊（如 `.env`）和不必要的檔案（如 `__pycache__`、SQLite 數據庫檔案）不會被納入版本控制。

### Phase 2: Python 工具模組 (待辦)
*   **步驟 2.1: 實作 `src/filter.py`。**
    *   我將創建 `src/` 資料夾。
    *   編寫一個 Python 腳本，接受文本輸入和排除關鍵字列表，並根據硬性排除詞進行過濾。
    *   使其可以作為 CLI 工具被呼叫。
*   **步驟 2.2: 實作 `src/dedup.py`。**
    *   編寫一個 Python 腳本，使用 SQLite 數據庫來儲存和檢查已處理的貼文 ID，實現去重功能。
    *   使其可以作為 CLI 工具被呼叫。
*   **步驟 2.3: 實作 `src/line_notify.py`。**
    *   編寫一個 Python 腳本，使用 LINE Notify API 發送訊息。
    *   使其可以作為 CLI 工具被呼叫，接收訊息內容和 LINE Notify Token。
*   **步驟 2.4: 測試各模組。** 我會為每個 Python 腳本編寫簡單的測試，確保它們按預期工作。

### Phase 3: OpenClaw Skills (待辦)
*   **步驟 3.1: 撰寫 `skills/threads-monitor/SKILL.md`。**
    *   我將創建 `skills/threads-monitor/` 資料夾。
    *   定義一個 OpenClaw Skill，該 Skill 將：
        *   使用 `browser` 工具訪問 Threads 搜尋頁面。
        *   模擬登入（如果需要）。
        *   處理關鍵字搜尋。
        *   執行頁面捲動以載入更多結果。
        *   提取貼文內容和連結。
        *   呼叫 `filter.py` 和 `dedup.py` 進行過濾和去重。
        *   使用 AI（透過 OpenClaw 內建的 LLM 能力）進行語意分析和分類。
        *   標記「大魚」議題。
*   **步驟 3.2: 撰寫 `skills/line-notify/SKILL.md`。**
    *   我將創建 `skills/line-notify/` 資料夾。
    *   定義一個 OpenClaw Skill，該 Skill 將包裝 `src/line_notify.py`，以便 OpenClaw Agent 可以方便地呼叫它來發送 LINE 通知。
*   **步驟 3.3: 撰寫 `skills/report-generator/SKILL.md`。**
    *   我將創建 `skills/report-generator/` 資料夾。
    *   定義一個 OpenClaw Skill，負責根據 AI 分析的結果生成分類戰報。
*   **步驟 3.4: 撰寫 `CLAUDE.md` (Agent 核心記憶)。**
    *   創建或更新 `CLAUDE.md`，納入專案的關鍵知識、決策和行為模式，以便 Agent 更好地執行任務。

### Phase 4: Docker 部署 (待辦)
*   **步驟 4.1: 建立 `Dockerfile`。**
    *   編寫 Dockerfile，用於構建包含 OpenClaw、Python 依賴和專案程式碼的 Docker 映像。
*   **步驟 4.2: 建立 `docker-compose.yml`。**
    *   編寫 docker-compose.yml，定義服務（OpenClaw Agent、SQLite 數據庫），配置環境變數，並設置數據卷以持久化數據。

### Phase 5: 驗證與測試 (待辦)
*   **步驟 5.1: 測試 `filter.py` / `dedup.py` / `line_notify.py`。**
    *   運行單元測試和集成測試，確保 Python 工具的穩定性。
*   **步驟 5.2: 確認 OpenClaw 安裝與設定流程文件完整。**
    *   確保專案的 README 或其他文檔清晰地說明瞭如何設定和運行 OpenClaw 環境。
*   **步驟 5.3: 端對端驗證流程。**
    *   執行整個輿情監控流程，從 Threads 抓取到通知發送，確認所有部分都正常運作。
