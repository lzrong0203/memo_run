# Project Context: Threads 社群輿情監控系統 (OpenClaw)

## Goal
建立基於 OpenClaw 的 AI Agent 輿情監控系統，每 30 分鐘自動掃描 Threads，雙重過濾後產出分類戰報，透過 Telegram + LINE 發送通知。

## Current Status
專案目前已由 Claude Code 導師大幅更新並完成了 **Phase 1, Phase 2 (Python 工具模組) 和 Phase 3 (OpenClaw Skills) 的所有實作**。
Dobby 當前的職責是進行 **Phase 5 的驗證與測試，並準備部署**。

### 最新驗證結果 (2026-02-10 by Claude Code)
- **單元測試**: 48/48 全部通過 (0.22s)
- **測試覆蓋率**: 63%（核心函數接近 100%，`__main__` CLI 區塊未覆蓋拉低整體數字）
- **Skills 驗證**: 3/3 全部通過（YAML frontmatter、必要欄位、環境變數一致性）
- **安全性修正**: 已從 git 歷史中清除所有明文 tokens
- **LINE 發送測試**: 成功（`send_line_message` 正常運作）
- **Browser 環境**: 已設定 openclaw profile，Threads 已登入，搜尋「內湖」成功
- **Skills 安裝**: 已透過 symlink 安裝到 `~/.openclaw/workspace/skills/`，3/3 Ready

### 端對端測試發現的問題與修正 (2026-02-10)
1. **`openclaw run` 不存在** → 已改為 `openclaw agent --message --local`
2. **WhatsApp channel 錯誤** → 所有指令加上 `--channel telegram`
3. **Agent 委派子 agent** → SKILL.md 加上「不要委派子 agent，直接執行」指示
4. **Browser 開新 tab** → SKILL.md 加上「在同一 tab 中操作」指示
5. **Browser profile 錯誤** → 設定 `browser.defaultProfile=openclaw`，SKILL.md 指定 profile
6. **`.env` source 問題** → token 值加上單引號，使用 `set -a` export
7. **keywords.yml 範例過時** → 更新為實際格式（含 enabled 欄位）

## My Detailed Execution Plan (Dobby's Role: Verification, Testing & Deployment)

### Phase 1: 專案骨架與設定檔 (已完成 by Claude Code)

### Phase 2: Python 工具模組 (已完成 by Claude Code)
*   所有輔助腳本 (`src/filter.py`, `src/dedup.py`, `src/line_notify.py`) 已完成實作並通過測試。
*   測試覆蓋率：實測 63%（`--cov=src`）。核心邏輯函數覆蓋率接近 100%，拉低整體數字的是各檔案的 `if __name__ == '__main__'` CLI 入口區塊（約 30-50 行/檔）。
    *   `line_notify.py`: 74%（未覆蓋: CLI 區塊 L150-195）
    *   `dedup.py`: 58%（未覆蓋: CLI 區塊 + 部分 error path）
    *   `filter.py`: 56%（未覆蓋: CLI 區塊 + 部分 error path）

### Phase 3: OpenClaw Skills (已完成 by Claude Code)
*   所有 Skills (`threads-monitor`, `line-notify`, `report-generator`) 已完成實作。
*   **Dobby 驗證結果：** 已完成所有 `SKILL.md` 檔案的語法和結構審閱，確認其 YAML frontmatter 格式、Markdown 語法和環境變數命名一致性都符合規範，看起來良好。

### Phase 4: Docker 部署 (已刪除)

### Phase 5: 驗證與測試 (進行中 - 由 Dobby 執行)
*   **步驟 5.1: 重新安裝 Python 依賴** (已執行)
*   **步驟 5.2: 運行所有 Python 單元測試** (已執行，48/48 tests passed)
*   **步驟 5.3: 運行測試覆蓋率檢查** (已執行，總覆蓋率 63%，Claude 報告 ~90%)
*   **步驟 5.4: 測試 Skills 語法正確性** (已完成 Dobby 的審閱)
*   **步驟 5.5: 端對端驗證整體流程** (進行中)
    *   正確指令: `openclaw agent --message "執行 threads-monitor 監控" --local --channel telegram --session-id threads-monitor-manual`
    *   Browser 環境: openclaw profile 已設定，Threads 已登入
    *   Skills 安裝: 透過 symlink `~/.openclaw/workspace/skills/` → 專案 `skills/`
    *   **環境變數狀態：** 所有必要的環境變數已設定於 `.env`（不進版控，值已加引號）
*   **步驟 5.6: 實際部署與執行測試** (待執行)
    *   設定 cron job（每 30 分鐘）
    *   監控執行狀況
    *   調整參數（關鍵字、排除詞、延遲時間）
*   **步驟 5.7: 監控與調整** (待執行)
*   **步驟 5.8: 文檔同步** (待執行)
    *   更新 `CLAUDE.md`（Implementation Progress）
    *   更新 `README.md`（開發狀態）
    *   Commit 和 push 所有變更

---

## Claude Code Multi-Agent Review (2026-02-10 14:30)
(此部分內容已由 Claude Code 導師的後續實作報告所取代，在此僅作為歷史參考。)

## 🔧 Claude Code 修正實作 (2026-02-10 15:00)
(此部分內容已由 Claude Code 導師的後續實作報告所取代，在此僅作為歷史參考。)

## 🎉 Claude Code 完成 Phase 2 實作 (2026-02-10 16:00)
(此部分包含 Phase 2 的詳細實作內容、測試結果和 CLI 工具使用範例，將被 Dobby 參考進行驗證。)

## 📦 Phase 3: OpenClaw Skills 實作完成 (2026-02-10)
(此部分包含 Phase 3 的詳細實作內容、Skills 統計和品質保證，將被 Dobby 參考進行驗證。)

---

**Current Status & Next Action:**
- 已完成：單元測試 (120/120)、Skills 驗證 (3/3)、安全修正、LINE 發送測試、Browser 環境設定、SKILL.md 全面修正
- 已完成：pipeline.py 批次處理、MIN_VALID_POSTS 門檻、report_generator 接上 SKILL.md
- 已完成：端對端測試成功（scout agent + claude-haiku-4-5）
- 下一步：**實作 SKILL.md v3.0.0 自適應 DOM 抽取**

---

## 待實作計劃：SKILL.md v3.0.0 — 自適應 DOM 抽取取代截圖解析

### 背景

目前 SKILL.md v2.2.0 的步驟 2-4 使用 `browser snapshot` 讓 AI 看頁面內容再手動解析貼文。每輪滑動都要截圖+AI 解析，導致：
- **慢**：5 輪滑動 x 8 秒等待 + 6 次 snapshot 解析 = 60 秒+
- **數量不夠**：AI 從 snapshot 文字中解析容易遺漏
- **耗 token**：每次 snapshot 都要 LLM 處理大量 DOM 文字

### 策略：「看一次 DOM，之後全用 JS」

1. **一次 snapshot** — 開頭看一次頁面，了解 Threads 目前的 DOM 結構（selector、class name 等）
2. **全部滾完再抽** — 先連續滾動載入所有內容（不截圖），滾完後跑一次 JS 把所有貼文抽出來
3. **snapshot 當備案** — JS 抽取失敗才用 snapshot fallback

### 效能比較

| 指標 | v2.2.0（截圖） | v3.0.0（JS 抽取） |
|------|----------------|-------------------|
| Snapshot 次數 | 6 次 | 1 次（開頭分析 DOM） |
| AI 解析 snapshot | 6 次 | 1 次 |
| 滾動等待 | 5 x 8s = 40s | 5 x 5s = 25s |
| 抽取方式 | AI 讀文字 | JS 回傳 JSON |
| 預估每關鍵字耗時 | ~60s+ | ~35s |

### 修改範圍

**只改 2 個檔案：**
1. `skills/threads-monitor/SKILL.md` — 改寫步驟 2、3、4
2. `CLAUDE.md` — 更新架構說明

**不動的檔案：** `src/pipeline.py`、`src/report_generator.py`、`src/line_notify.py`、`tests/`、`config/`

### 新步驟 2：導航 + DOM 結構分析

1. `browser navigate` 到搜尋頁面（加 `&filter=recent`）
2. `browser wait --time 5000`
3. `browser snapshot`（唯一一次，用來了解 DOM 結構）
4. 從 snapshot 中辨識貼文容器 selector、內容位置、作者位置、連結位置
5. 根據觀察到的結構，準備 JS 抽取函數

### 新步驟 3：先滾完，再用 JS 一次抽取

**Phase A：連續滾動（不截圖）**
- 最多 5 輪，每輪：scroll → wait 3s → scroll → wait 2s
- 每輪 5 秒（vs 舊版 8 秒），不需要 snapshot

**Phase B：一次 JS 抽取所有貼文**
```javascript
browser execute (function() {
  var posts = [];
  var seen = new Set();
  var allLinks = document.querySelectorAll('a[href*="/post/"]');
  allLinks.forEach(function(link) {
    var href = link.getAttribute('href');
    if (!href || seen.has(href)) return;
    var fullUrl = href.startsWith('http') ? href : 'https://www.threads.net' + href;
    var container = link.closest('[根據步驟2觀察到的selector]') || link.parentElement.parentElement.parentElement;
    if (!container) return;
    var textContent = container.innerText || '';
    var authorMatch = href.match(/\/@([^\/]+)\/post\//);
    var author = authorMatch ? authorMatch[1] : '';
    if (textContent.length < 15) return;
    seen.add(href);
    posts.push({ content: textContent.substring(0, 2000), author: author, link: fullUrl });
  });
  return JSON.stringify(posts);
})()
```

> JS 是模板，Agent 根據步驟 2 snapshot 觀察到的實際 DOM 結構調整 selector。
> 最穩定的錨點是 `a[href*="/post/"]`，因為 `/post/` 是 Threads URL 的基本結構。

**Phase C：fallback**
- JS 回傳 0 篇 → 再 snapshot 一次 → 嘗試替代策略（`<script type="application/json">`）→ 最後才手動解析

### 新步驟 4：驗證並格式化

- 解析 JS 回傳的 JSON
- 驗證每篇有 content、author、link
- 去重（by link），最多取 20 篇
- 輸出格式不變，直接給 pipeline.py

### 實作順序

1. 改寫 `SKILL.md` 步驟 2、3、4
2. 更新版本號為 3.0.0
3. 更新 `CLAUDE.md` 架構說明
4. Commit + push
5. 用 scout agent 實際跑一次驗證
