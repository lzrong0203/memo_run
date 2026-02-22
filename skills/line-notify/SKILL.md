---
name: line-notify
description: 透過 LINE Messaging API 發送通知，支援 Broadcast（全好友）和 Push（指定用戶）模式。
user-invocable: true
homepage: https://github.com/lzrong0203/memo_run
metadata: {"openclaw": {"emoji": "📨", "primaryEnv": "LINE_CHANNEL_ACCESS_TOKEN", "requires": {"binaries": ["python3"], "envVars": ["LINE_CHANNEL_ACCESS_TOKEN"]}}}
---

# LINE Messaging API 通知 Skill

## 重要執行規則

> **Token 只能透過環境變數取得，絕不用 CLI 參數傳遞。**
> **所有 Python 指令使用絕對路徑 `/Users/steveopenclaw/.openclaw/workspace/memo_run/`。**

## 使用方式

### 廣播給所有好友（推薦，用於監控通知）

```bash
python3 /Users/steveopenclaw/.openclaw/workspace/memo_run/src/line_notify.py --broadcast --message "訊息內容"
```

### 發送給指定用戶（需設定 LINE_USER_ID）

```bash
python3 /Users/steveopenclaw/.openclaw/workspace/memo_run/src/line_notify.py --message "訊息內容"
```

### Python 呼叫（從其他模組）

```python
from src.line_notify import send_line_broadcast, send_line_message, send_notification_message
import os

# 廣播
send_line_broadcast(os.environ['LINE_CHANNEL_ACCESS_TOKEN'], "訊息")

# Push 給指定用戶
send_line_message(os.environ['LINE_CHANNEL_ACCESS_TOKEN'], os.environ['LINE_USER_ID'], "訊息")

# 格式化監控通知（含關鍵字、摘要、報告連結）
send_notification_message(
    os.environ['LINE_CHANNEL_ACCESS_TOKEN'],
    os.environ['LINE_USER_ID'],
    keywords=["內湖"],
    summary="發現 5 則相關貼文",
    report_url="https://gist.github.com/xxx/yyy"
)
```

## 限制

- 訊息最大 **5000 字元**（超過會被拒絕）
- Request timeout **10 秒**
- LINE Free Plan 月配額 **500 則**
- Token 和 User ID 會驗證無效字元（防 Header Injection）

## 環境變數

```bash
LINE_CHANNEL_ACCESS_TOKEN=your_token    # 必需
LINE_USER_ID=Uxxxxxxxx                  # 僅 push 模式需要（broadcast 不需要）
```

## 常見錯誤

| HTTP 狀態碼 | 原因 | 處理 |
|---|---|---|
| 401 | Token 無效或過期 | 重新簽發 Token |
| 403 | User 不存在或已封鎖 Bot | 確認 User ID 正確 |
| 429 | 超過速率限制 | 等待後重試 |

---

**版本**: 2.0.0
**最後更新**: 2026-02-20
