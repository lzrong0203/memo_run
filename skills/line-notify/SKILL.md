---
name: line-notify
description: 發送 LINE Messaging API 通知，支援結構化訊息格式（關鍵字、摘要、報告連結）
user-invocable: true
homepage: https://github.com/lzrong0203/memo_run
metadata: {"openclaw": {"emoji": "📨", "primaryEnv": "LINE_CHANNEL_ACCESS_TOKEN", "requires": {"binaries": ["python3"], "envVars": ["LINE_CHANNEL_ACCESS_TOKEN", "LINE_USER_ID"]}}}
---

# LINE Messaging API 通知 Skill

## 概述

這個 Skill 包裝了 `src/line_notify.py` Python 模組，提供簡單易用的 LINE 通知功能。支援發送純文字訊息或格式化的 Threads 監控通知（包含關鍵字、摘要、報告連結）。使用 LINE Messaging API 推送訊息到指定的 LINE 用戶。

## 使用方式

### 手動呼叫（發送自訂訊息）

```bash
# 發送純文字訊息
python3 src/line_notify.py --message "測試訊息"
```

### 從其他 Skill 呼叫

其他 Skill（如 `report-generator`）可以透過 Python import 方式呼叫：

```python
from src.line_notify import send_notification_message

# 發送格式化的監控通知
success = send_notification_message(
    channel_access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"],
    to_user_id=os.environ["LINE_USER_ID"],
    keywords=["台北市政府", "交通建設"],
    summary="今日發現 5 則相關貼文，包含 2 則高優先級議題...",
    report_url="https://example.com/report/2026-02-10-15-30.html"
)
```

### OpenClaw Skill 整合

在其他 Skill 中使用 Bash 呼叫：

```javascript
// 發送純文字通知
await bash(`python3 src/line_notify.py --message "監控任務完成，共發現 10 則新貼文"`);
```

## 環境變數需求

```bash
# LINE Messaging API Channel Access Token（必需）
LINE_CHANNEL_ACCESS_TOKEN=your-channel-access-token-here

# LINE User ID（接收通知的用戶 ID，必需）
LINE_USER_ID=U1234567890abcdef1234567890abcdef
```

**取得方式**:

1. **Channel Access Token**:
   - 前往 [LINE Developers Console](https://developers.line.biz/console/)
   - 建立 Messaging API Channel
   - 在 Channel 設定中取得 Channel Access Token

2. **User ID**:
   - 使用 LINE Official Account 加入你的 Bot
   - 透過 Webhook 事件或 API 查詢取得 User ID
   - 或使用 [LINE Notify 測試工具](https://developers.line.biz/en/docs/messaging-api/getting-user-ids/)

## Python 呼叫範例

### 發送純文字訊息

```python
from src.line_notify import send_line_message
import os

success = send_line_message(
    channel_access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"],
    to_user_id=os.environ["LINE_USER_ID"],
    message="這是一則測試訊息"
)

if success:
    print("訊息發送成功")
else:
    print("訊息發送失敗")
```

### 發送格式化通知

```python
from src.line_notify import send_notification_message
import os

# 使用列表形式的關鍵字
success = send_notification_message(
    channel_access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"],
    to_user_id=os.environ["LINE_USER_ID"],
    keywords=["台北市政府", "交通建設", "捷運"],
    summary="今日共發現 8 則相關貼文：\n- 5 則關於捷運延伸線規劃\n- 2 則關於公車路線調整\n- 1 則關於交通號誌改善",
    report_url="https://example.com/report/2026-02-10.html"
)

# 或使用單一關鍵字字串
success = send_notification_message(
    channel_access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"],
    to_user_id=os.environ["LINE_USER_ID"],
    keywords="台北市政府",
    summary="發現 3 則高優先級議題...",
    report_url="https://example.com/report/2026-02-10.html"
)
```

## 格式化訊息格式

使用 `send_notification_message` 時，會自動產生以下格式的訊息：

```
🔔 Threads 監控通知

關鍵字: 台北市政府, 交通建設, 捷運

摘要:
今日共發現 8 則相關貼文：
- 5 則關於捷運延伸線規劃
- 2 則關於公車路線調整
- 1 則關於交通號誌改善

完整報告:
https://example.com/report/2026-02-10.html
```

## 輸入驗證與限制

### 訊息長度限制
- 最大長度: **5000 字元**
- 超過限制會被拒絕，不會自動截斷

### 必需參數驗證
- `channel_access_token`: 不可為空，必須是有效的 token 字串
- `to_user_id`: 不可為空，必須是有效的 User ID
- `message`: 不可為空，必須是有效的字串
- `keywords`: 不可為空（列表或字串）
- `summary`: 不可為空
- `report_url`: 不可為空

### 安全性檢查
- Token 和 User ID 會檢查是否包含無效字元（防止 Header Injection）
- 不接受包含 `\r`, `\n`, `\t`, 空格的 token

## 錯誤處理

### HTTP 錯誤
```python
# 401 Unauthorized: Token 無效或過期
# 400 Bad Request: 參數格式錯誤
# 403 Forbidden: User ID 不存在或無權限
# 429 Too Many Requests: 超過速率限制
```

### 網路問題
```python
# ConnectionError: 網路連線失敗
# Timeout: 請求超時（10 秒）
# RequestException: 其他請求錯誤
```

### 範例錯誤處理
```python
from src.line_notify import send_line_message
import os
import logging

logging.basicConfig(level=logging.INFO)

try:
    success = send_line_message(
        channel_access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"],
        to_user_id=os.environ["LINE_USER_ID"],
        message="測試訊息"
    )

    if not success:
        logging.error("LINE 通知發送失敗，請檢查 logs")
        # 可選：記錄到資料庫、重試、或發送備用通知

except KeyError as e:
    logging.error(f"缺少環境變數: {e}")
except Exception as e:
    logging.error(f"未預期的錯誤: {e}")
```

## 安全提示

1. **不在命令列傳遞 Token**
   ```bash
   # ❌ 錯誤：Token 會留在 shell history
   python3 src/line_notify.py --token "xxx" --user-id "yyy" --message "test"

   # ✅ 正確：使用環境變數
   export LINE_CHANNEL_ACCESS_TOKEN="xxx"
   export LINE_USER_ID="yyy"
   python3 src/line_notify.py --message "test"
   ```

2. **不在 logs 中記錄 Token**
   - `src/line_notify.py` 已實作安全的 logging，不會記錄 token
   - 僅記錄 User ID（非敏感資訊）和發送狀態

3. **使用 .env 檔案管理機密資訊**
   ```bash
   # .env
   LINE_CHANNEL_ACCESS_TOKEN=your-token-here
   LINE_USER_ID=your-user-id-here
   ```

   ```python
   # 載入環境變數
   from dotenv import load_dotenv
   load_dotenv()
   ```

4. **定期輪換 Token**
   - 建議每 3-6 個月更換 Channel Access Token
   - 若懷疑 token 洩漏，立即在 LINE Developers Console 重新簽發

## API 速率限制

LINE Messaging API 有以下速率限制：

- **Push 訊息**: 500 則/秒（每個 Channel）
- **月配額**: 依據您的 LINE Official Account 方案而定
  - Free Plan: 500 則/月
  - Light Plan: 無限制（付費）

**建議做法**:
- 對於高頻通知，考慮批次發送或合併訊息
- 監控每月用量，避免超過配額

## CLI 使用範例

```bash
# 基本使用
export LINE_CHANNEL_ACCESS_TOKEN="your-token"
export LINE_USER_ID="your-user-id"
python3 src/line_notify.py --message "Hello, LINE!"

# 發送多行訊息
python3 src/line_notify.py --message "第一行
第二行
第三行"

# 在 cron job 中使用
*/30 * * * * cd /path/to/memo_run && python3 src/line_notify.py --message "定期監控執行中"
```

## 回傳值

### 成功
```python
True  # 訊息發送成功
```

### 失敗
```python
False  # 訊息發送失敗（詳細錯誤見 logs）
```

## 相依套件

在 `requirements.txt` 中確認以下套件：

```
requests>=2.31.0
```

安裝方式：
```bash
pip install -r requirements.txt
```

## 與其他 Skills 整合

### report-generator 呼叫範例

```python
# 在 report-generator Skill 中
from src.line_notify import send_notification_message
import os

def send_report_notification(keywords, summary, report_url):
    """發送戰報通知"""
    return send_notification_message(
        channel_access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"],
        to_user_id=os.environ["LINE_USER_ID"],
        keywords=keywords,
        summary=summary,
        report_url=report_url
    )
```

### threads-monitor 觸發範例

```javascript
// 在 threads-monitor 結束時觸發通知
const reportUrl = await generateReport(validPosts);

await bash(`
python3 -c "
from src.line_notify import send_notification_message
import os

send_notification_message(
    channel_access_token=os.environ['LINE_CHANNEL_ACCESS_TOKEN'],
    to_user_id=os.environ['LINE_USER_ID'],
    keywords=['台北市政府', '交通建設'],
    summary='今日監控完成，發現 ${validPosts.length} 則新貼文',
    report_url='${reportUrl}'
)
"
`);
```

## 測試模式

開發時可使用測試 User ID（自己的帳號）：

```bash
# 測試環境
export LINE_CHANNEL_ACCESS_TOKEN="your-test-token"
export LINE_USER_ID="your-test-user-id"

# 發送測試訊息
python3 src/line_notify.py --message "🧪 測試訊息 - 請忽略"
```

## Troubleshooting

### 問題：訊息發送失敗，沒有錯誤訊息

**解決方案**:
1. 啟用詳細 logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```
2. 檢查環境變數是否正確設定
3. 驗證 Token 和 User ID 有效性

### 問題：收到 401 Unauthorized

**解決方案**:
- Channel Access Token 無效或過期
- 前往 LINE Developers Console 重新簽發 token

### 問題：收到 403 Forbidden

**解決方案**:
- User ID 不存在
- User 尚未加入你的 LINE Official Account
- 確認 User 未封鎖你的 Bot

### 問題：訊息未收到，但 API 回傳成功

**解決方案**:
- 檢查 User 是否已封鎖 Bot
- 確認 LINE App 通知設定已開啟
- 檢查 User ID 是否正確

## 效能考量

- **請求超時**: 10 秒（`TIMEOUT_SECONDS`）
- **SSL 驗證**: 啟用（`verify=True`）
- **連線複用**: 建議使用 `requests.Session()` 以提升效能（若需批次發送）

### 批次發送優化範例

```python
import requests
from src.line_notify import LINE_MESSAGING_API_URL

def send_batch_notifications(channel_access_token, user_ids, message):
    """批次發送通知（優化版）"""
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {channel_access_token}'
    })

    results = []
    for user_id in user_ids:
        payload = {
            'to': user_id,
            'messages': [{'type': 'text', 'text': message}]
        }
        response = session.post(LINE_MESSAGING_API_URL, json=payload, timeout=10)
        results.append(response.ok)

    session.close()
    return results
```

## 監控與日誌

### 查看發送日誌

```bash
# 若使用 systemd 執行 cron job
journalctl -u openclaw -n 100 | grep "LINE message"

# 或查看應用程式日誌
tail -f logs/line_notify.log
```

### 日誌格式範例

```
2026-02-10 15:30:00 - line_notify - INFO - LINE message sent successfully to user U1234567890abcdef1234567890abcdef
2026-02-10 15:45:00 - line_notify - ERROR - LINE message failed - HTTP error: 401 Client Error: Unauthorized
```

## 相依 Skills

本 Skill 被以下 Skills 使用：
- `report-generator` - 產生戰報後發送通知
- `threads-monitor` - 監控任務完成後發送摘要通知

---

**版本**: 1.0.0
**最後更新**: 2026-02-10
**作者**: Claude Code + OpenClaw
**License**: AGPL-3.0
