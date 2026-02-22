# Project Context: Threads 社群輿情監控系統 (OpenClaw)

## Goal
建立基於 OpenClaw 的 AI Agent 輿情監控系統，每 30 分鐘自動掃描 Threads，雙重過濾後產出分類戰報，透過 Telegram + LINE 發送通知。

## Current Status
專案目前已由 Claude Code 導師大幅更新並完成了 **Phase 1, Phase 2 (Python 工具模組) 和 Phase 3 (OpenClaw Skills) 的所有實作**。
Dobby 當前的職責是進行 **Phase 5 的驗證與測試，並準備部署**。

### 最新驗證結果 (2026-02-10 by Claude Code)
- **單元測試**: 120/120 全部通過 (1.78s)
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
*   **步驟 5.2: 運行所有 Python 單元測試** (已執行，120/120 tests passed)
*   **步驟 5.3: 運行測試覆蓋率檢查** (已執行，總覆蓋率 63%，Claude 報告 ~90%)
*   **步驟 5.4: 測試 Skills 語法正確性** (已完成 Dobby 的審閱)
*   **步驟 5.5: 端對端驗證整體流程** (已完成)
    *   正確指令: `openclaw agent --message "執行 threads-monitor 監控" --local --channel telegram --session-id threads-monitor-manual`
    *   Browser 環境: openclaw profile 已設定，Threads 已登入
    *   Skills 安裝: 透過 symlink `~/.openclaw/workspace/skills/` → 專案 `skills/`
    *   **環境變數狀態：** 所有必要的環境變數已設定於 `.env`（不進版控，值已加引號）
    *   **結果：** 端對端測試成功（scout agent + claude-haiku-4-5）
*   **步驟 5.6: 實際部署與執行測試** (進行中)
    *   設定 cron job（每 30 分鐘）
    *   監控執行狀況
    *   調整參數（關鍵字、排除詞、延遲時間）
*   **步驟 5.7: 監控與調整** (待執行)
*   **步驟 5.8: 文檔同步** (待執行)
    *   更新 `CLAUDE.md`（Implementation Progress）
    *   更新 `README.md`（開發狀態）
    *   Commit 和 push 所有變更

---

## 里程碑時間線

| 日期 | 事件 |
|------|------|
| 2026-02-10 14:30 | Claude Code Multi-Agent Review 完成 |
| 2026-02-10 15:00 | Claude Code 修正實作（安全修正、input validation） |
| 2026-02-10 16:00 | Phase 2 Python 工具模組完成（120 tests passed） |
| 2026-02-10 17:00 | Phase 3 OpenClaw Skills 完成（3/3 驗證通過） |
| 2026-02-10 18:00 | 端對端測試成功（scout agent + claude-haiku-4-5） |
| 2026-02-11 | pipeline.py 批次處理、MIN_VALID_POSTS 門檻、report_generator 接上 SKILL.md |

## Current Status & Next Action

- **v2.2.0 狀態**：端對端驗證通過，可作為穩定 baseline
- **v4.0.0 已完成**：innerText + LLM 自適應解析（取代 v3.0.0 寫死 JS selector）
- **SKILL 精簡**：三個 SKILL.md 從 1942 行 → ~330 行（-83%），大幅降低 agent token 消耗
- **待補**：健康檢查機制、錯誤通知機制、cron job 部署、端對端驗證 v4.0.0

---

## 待實作計劃：SKILL.md v3.0.0 — 自適應 DOM 抽取取代截圖解析

### 前置條件（實作前必須確認）

1. **v2.2.0 baseline 穩定**：確認 v2.2.0 能端對端成功跑完搜尋→過濾→去重→通知全流程（至少成功 2 次）
2. **建立回滾點**：`git tag v2.2.0-stable` 保留可回退的版本
3. **記錄 v2.2.0 效能數據**：實際每關鍵字耗時、token 消耗，作為 v3.0.0 改善的 baseline

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

### 新步驟 2：導航（不需要每次分析 DOM）

1. `browser navigate` 到搜尋頁面（加 `&filter=recent`）
2. `browser wait --time 5000`
3. **不做 snapshot** — 直接進入步驟 3（JS 抽取用寫死的 selector）

> **設計理念**：`a[href*="/post/"]` 是 Threads URL 的基本結構，改變機率極低。
> 不需要每次都 snapshot 分析 DOM，省下一次 LLM 呼叫。
> 只有在 JS 抽取失敗（回傳 0 篇）時才做 snapshot fallback。

### 新步驟 3：先滾完，再用 JS 一次抽取

**Phase A：連續滾動（不截圖）**
- 最多 5 輪，每輪：scroll → wait 3s → scroll → wait 2s
- 每輪 5 秒（vs 舊版 8 秒），不需要 snapshot

**Phase B：一次 JS 抽取所有貼文（寫死 selector）**
```javascript
browser execute (function() {
  var posts = [];
  var seen = new Set();
  // 錨點：a[href*="/post/"] 是最穩定的 selector（URL 結構不太會變）
  var allLinks = document.querySelectorAll('a[href*="/post/"]');
  allLinks.forEach(function(link) {
    var href = link.getAttribute('href');
    if (!href || seen.has(href)) return;
    var fullUrl = href.startsWith('http') ? href : 'https://www.threads.net' + href;
    // 向上找包含足夠文字的祖先元素（比固定層數更穩健）
    // 若父元素包含多個 /post/ 連結則停止（防止跨貼文污染）
    var container = link;
    for (var i = 0; i < 8; i++) {
      if (!container.parentElement) break;
      var next = container.parentElement;
      var otherLinks = next.querySelectorAll('a[href*="/post/"]');
      if (otherLinks.length > 1) break;
      container = next;
      if (container.innerText && container.innerText.length > 50) break;
    }
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

> **selector 策略**：不再依賴 Agent 每次分析 DOM 調整 selector。
> 錨點 `a[href*="/post/"]` 寫死，container 用「向上找到 innerText > 50 字元的祖先」取代固定 `parentElement` 層數。
> 這樣即使 Threads 改了 DOM 層級，只要 URL 結構不變就能抽取。

**Phase C：三層 fallback**
1. JS 回傳 0 篇 → **snapshot 一次**，Agent 根據觀察到的 DOM 手動調整 selector 再試一次 JS
2. 調整後仍 0 篇 → 嘗試 `<script type="application/json">` 內嵌資料
3. 都失敗 → 回退到 v2.2.0 的 snapshot 逐頁解析模式
4. **發送錯誤通知**（Telegram）告知 DOM 結構可能已變更，需人工檢查

### 新步驟 4：驗證並格式化

- 解析 JS 回傳的 JSON
- 驗證每篇有 content、author、link
- 去重（by link），最多取 20 篇
- 輸出格式不變，直接給 pipeline.py

### 回滾機制

- 實作前先 `git tag v2.2.0-stable`
- v3.0.0 失敗時可一行回退：`git checkout v2.2.0-stable -- skills/threads-monitor/SKILL.md`
- fallback Phase C 第 3 層本身就是 v2.2.0 的行為，等同運行中自動降級

### 健康檢查（v3.0.0 一起實作）

在 SKILL.md 步驟 7 之後新增步驟 8：
1. 若整輪所有關鍵字的有效貼文數 = 0，發送 Telegram 告警：「本輪巡邏 0 則有效貼文，可能 Threads 改版或登入失效」
2. 記錄每輪執行結果到 `data/health.log`（時間、關鍵字數、有效貼文數、是否 fallback）
3. 若連續 3 輪 fallback 到 snapshot 模式 → 發送升級告警

### 實作順序

1. `git tag v2.2.0-stable`（建立回滾點）
2. 改寫 `SKILL.md` 步驟 2、3、4（JS 抽取 + fallback）
3. 新增步驟 8（健康檢查 + 錯誤通知）
4. 更新版本號為 3.0.0
5. 更新 `CLAUDE.md` 架構說明
6. Commit（不 push，先本地驗證）
7. 用 scout agent 實際跑一次驗證
8. 驗證通過 → push；失敗 → 回滾 `git checkout v2.2.0-stable -- skills/threads-monitor/SKILL.md`

---

## SKILL.md v4.0.0 — innerText + LLM 自適應解析（2026-02-20）

### 改進動機

v3.0.0 使用寫死的 JS selector（`a[href*="/post/"]` + 向上找 container + innerText > 50）來抽取貼文。
雖然比 v2.2.0 的 snapshot 模式快，但仍依賴 DOM 結構（container 層級、文字長度閾值），Threads 改版時容易壞掉。

### v4.0.0 策略：「JS 取文字，AI 解析結構」

1. JS 只做最簡單的事：取 `document.body.innerText`（頁面可見文字）+ 所有 `/post/` 連結
2. 不走 DOM 結構、不找 container、不提取 author — 全部交給 LLM 自適應解析
3. LLM 根據文字內容 + 連結列表，自行配對出每篇貼文的內容、作者、連結

### 版本比較

| 指標 | v2.x snapshot | v3.0.0 寫死 JS | v4.0.0 innerText + LLM |
|------|---------------|----------------|------------------------|
| 自適應 | 有（但很重） | 沒有 | **有** |
| Snapshot 次數 | 6 次 | 0 次 | **0 次** |
| LLM 解析次數 | 6 次 | 0 次 | **1 次**（比 v2.x 少 5 次） |
| DOM 依賴 | 無 | 高（selector + container） | **無**（只用 `a[href]`） |
| 速度 | 最慢 | 最快 | **中等**（比 v2.x 快很多） |
| Threads 改版 | 不怕 | 會壞 | **不怕** |

### SKILL 精簡效果

| Skill | v3.0.0 行數 | v4.0.0 行數 | 縮減 |
|-------|------------|------------|------|
| threads-monitor | 520 | ~180 | -65% |
| report-generator | 985 | ~90 | -91% |
| line-notify | 437 | ~55 | -87% |
| **總計** | **1942** | **~330** | **-83%** |

精簡內容：
- 移除 report-generator 中的 JS 程式碼範例（OpenClaw agent 不執行 JS）
- 移除 report-generator 中重複的 LINE 通知邏輯（已在 line-notify 中）
- 移除 line-notify 中過長的 API 文件和 troubleshooting（不影響 agent 執行）
- 移除 threads-monitor 中的三層 fallback（簡化為：LLM 解析失敗 → snapshot 一次）

### 待驗證

- [ ] 實際執行 v4.0.0 agent 驗證 innerText 解析效果
- [ ] 確認 `document.body.innerText` 回傳的文字大小在合理範圍（< 20KB）
- [ ] 確認 LLM 能正確配對文字和連結
