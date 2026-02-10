import logging
import requests

LINE_NOTIFY_API_URL: str = "https://notify-api.line.me/api/notify"
TIMEOUT_SECONDS = 10
MAX_MESSAGE_LENGTH = 1000

logger = logging.getLogger(__name__)


def send_line_notification(token: str, message: str) -> bool:
    """
    使用 LINE Notify API 發送通知。

    Args:
        token: LINE Notify 的存取令牌。
        message: 要發送的訊息內容。

    Returns:
        bool: 如果通知發送成功，則返回 True，否則返回 False。
    """
    # Input validation
    if not token or not isinstance(token, str):
        logger.error("Token is empty or invalid")
        return False

    if not message or not isinstance(message, str):
        logger.error("Message is empty or invalid")
        return False

    if len(message) > MAX_MESSAGE_LENGTH:
        logger.error("Message too long (max %d chars, got %d)", MAX_MESSAGE_LENGTH, len(message))
        return False

    # Check for invalid characters in token (potential header injection)
    if any(c in token for c in '\r\n\t '):
        logger.error("Token contains invalid characters")
        return False

    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'message': message
    }

    try:
        response = requests.post(
            LINE_NOTIFY_API_URL,
            headers=headers,
            data=data,
            timeout=TIMEOUT_SECONDS,
            verify=True
        )
        response.raise_for_status()  # 如果響應狀態碼指示錯誤，則引發 HTTPError

        try:
            response_json = response.json()
        except ValueError as exc:
            logger.error("Failed to parse LINE API response as JSON: %s", exc)
            return False

        if response_json.get("status") == 200:
            logger.info("LINE notification sent successfully")
            return True
        else:
            logger.warning(
                "LINE notification failed - API status: %s, message: %s",
                response_json.get("status"),
                response_json.get("message")
            )
            return False

    except requests.exceptions.HTTPError as exc:
        logger.error("LINE notification failed - HTTP error: %s", exc)
        return False
    except requests.exceptions.ConnectionError as exc:
        logger.error("LINE notification failed - Connection error: %s", exc)
        return False
    except requests.exceptions.Timeout as exc:
        logger.error("LINE notification failed - Timeout after %d seconds: %s", TIMEOUT_SECONDS, exc)
        return False
    except requests.exceptions.RequestException as exc:
        logger.error("LINE notification failed - Request error: %s", exc)
        return False


if __name__ == '__main__':
    import argparse
    import os
    import sys

    # Configure logging for CLI usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="發送 LINE 通知模組。",
        epilog="安全提示: 請使用環境變數 LINE_NOTIFY_TOKEN 提供 token，避免在命令列中暴露敏感資訊。"
    )
    parser.add_argument("--message", required=True, help="要發送的訊息內容")

    args = parser.parse_args()

    # 從環境變數獲取 token（安全做法）
    line_token = os.environ.get("LINE_NOTIFY_TOKEN")

    if not line_token:
        print(
            "錯誤: 缺少 LINE Notify Token。請設定環境變數 LINE_NOTIFY_TOKEN。\n"
            "範例: export LINE_NOTIFY_TOKEN='your-token-here'",
            file=sys.stderr
        )
        sys.exit(1)

    success = send_line_notification(line_token, args.message)

    if success:
        print("LINE 通知發送成功！")
        sys.exit(0)
    else:
        print("LINE 通知發送失敗。", file=sys.stderr)
        sys.exit(1)
