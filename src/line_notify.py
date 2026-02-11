import logging
import requests
from typing import List, Union

LINE_MESSAGING_API_URL: str = "https://api.line.me/v2/bot/message/push"
LINE_BROADCAST_API_URL: str = "https://api.line.me/v2/bot/message/broadcast"
TIMEOUT_SECONDS = 10
MAX_MESSAGE_LENGTH = 5000

logger = logging.getLogger(__name__)


def send_line_message(channel_access_token: str, to_user_id: str, message: str) -> bool:
    """
    使用 LINE Messaging API 發送訊息到指定用戶。

    Args:
        channel_access_token: LINE Messaging API 的 Channel Access Token。
        to_user_id: 接收訊息的 LINE 用戶 ID。
        message: 要發送的訊息內容。

    Returns:
        bool: 如果訊息發送成功，則返回 True，否則返回 False。
    """
    # Input validation for token
    if not channel_access_token or not isinstance(channel_access_token, str):
        logger.error("Channel access token is empty or invalid")
        return False

    # Check for invalid characters in token (potential header injection)
    if any(c in channel_access_token for c in '\r\n\t '):
        logger.error("Channel access token contains invalid characters")
        return False

    # Input validation for user_id
    if not to_user_id or not isinstance(to_user_id, str):
        logger.error("User ID is empty or invalid")
        return False

    # Check for invalid characters in user_id
    if any(c in to_user_id for c in '\r\n\t '):
        logger.error("User ID contains invalid characters")
        return False

    # Input validation for message
    if not message or not isinstance(message, str):
        logger.error("Message is empty or invalid")
        return False

    if len(message) > MAX_MESSAGE_LENGTH:
        logger.error("Message too long (max %d chars, got %d)", MAX_MESSAGE_LENGTH, len(message))
        return False

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {channel_access_token}'
    }

    payload = {
        'to': to_user_id,
        'messages': [
            {
                'type': 'text',
                'text': message
            }
        ]
    }

    try:
        response = requests.post(
            LINE_MESSAGING_API_URL,
            headers=headers,
            json=payload,
            timeout=TIMEOUT_SECONDS,
            verify=True
        )
        response.raise_for_status()  # 如果響應狀態碼指示錯誤，則引發 HTTPError

        logger.info("LINE message sent successfully to user %s", to_user_id)
        return True

    except requests.exceptions.HTTPError as exc:
        logger.error("LINE message failed - HTTP error: %s", exc)
        return False
    except requests.exceptions.ConnectionError as exc:
        logger.error("LINE message failed - Connection error: %s", exc)
        return False
    except requests.exceptions.Timeout as exc:
        logger.error("LINE message failed - Timeout after %d seconds: %s", TIMEOUT_SECONDS, exc)
        return False
    except requests.exceptions.RequestException as exc:
        logger.error("LINE message failed - Request error: %s", exc)
        return False


def send_line_broadcast(channel_access_token: str, message: str) -> bool:
    """
    使用 LINE Messaging API 廣播訊息給所有好友。

    Args:
        channel_access_token: LINE Messaging API 的 Channel Access Token。
        message: 要發送的訊息內容。

    Returns:
        bool: 如果訊息廣播成功，則返回 True，否則返回 False。
    """
    # Input validation for token
    if not channel_access_token or not isinstance(channel_access_token, str):
        logger.error("Channel access token is empty or invalid")
        return False

    if any(c in channel_access_token for c in '\r\n\t '):
        logger.error("Channel access token contains invalid characters")
        return False

    # Input validation for message
    if not message or not isinstance(message, str):
        logger.error("Message is empty or invalid")
        return False

    if len(message) > MAX_MESSAGE_LENGTH:
        logger.error("Message too long (max %d chars, got %d)", MAX_MESSAGE_LENGTH, len(message))
        return False

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {channel_access_token}'
    }

    payload = {
        'messages': [
            {
                'type': 'text',
                'text': message
            }
        ]
    }

    try:
        response = requests.post(
            LINE_BROADCAST_API_URL,
            headers=headers,
            json=payload,
            timeout=TIMEOUT_SECONDS,
            verify=True
        )
        response.raise_for_status()

        logger.info("LINE broadcast message sent successfully to all friends")
        return True

    except requests.exceptions.HTTPError as exc:
        logger.error("LINE broadcast failed - HTTP error: %s", exc)
        return False
    except requests.exceptions.ConnectionError as exc:
        logger.error("LINE broadcast failed - Connection error: %s", exc)
        return False
    except requests.exceptions.Timeout as exc:
        logger.error("LINE broadcast failed - Timeout after %d seconds: %s", TIMEOUT_SECONDS, exc)
        return False
    except requests.exceptions.RequestException as exc:
        logger.error("LINE broadcast failed - Request error: %s", exc)
        return False


def send_notification_message(
    channel_access_token: str,
    to_user_id: str,
    keywords: Union[List[str], str],
    summary: str,
    report_url: str
) -> bool:
    """
    發送格式化的 Threads 監控通知訊息。

    Args:
        channel_access_token: LINE Messaging API 的 Channel Access Token。
        to_user_id: 接收訊息的 LINE 用戶 ID。
        keywords: 關鍵字列表或單一關鍵字字串。
        summary: 摘要內容。
        report_url: 完整報告的連結。

    Returns:
        bool: 如果訊息發送成功，則返回 True，否則返回 False。
    """
    # Input validation
    if not keywords:
        logger.error("Keywords is empty")
        return False

    if not summary or not isinstance(summary, str):
        logger.error("Summary is empty or invalid")
        return False

    if not report_url or not isinstance(report_url, str):
        logger.error("Report URL is empty or invalid")
        return False

    # Format keywords
    if isinstance(keywords, list):
        keywords_str = ", ".join(keywords)
    else:
        keywords_str = keywords

    # Build formatted message
    message = f"""🔔 Threads 監控通知

關鍵字: {keywords_str}

摘要:
{summary}

完整報告:
{report_url}"""

    # Send using the base function
    return send_line_message(channel_access_token, to_user_id, message)


if __name__ == '__main__':
    import argparse
    import os
    import sys

    # 自動載入 .env 檔案（支援 OpenClaw exec 環境）
    try:
        from dotenv import load_dotenv
        # 嘗試從專案根目錄載入 .env
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(env_path)
    except ImportError:
        pass  # python-dotenv 未安裝時跳過

    # Configure logging for CLI usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="發送 LINE 訊息模組（使用 LINE Messaging API）。",
        epilog="安全提示: 請使用環境變數 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_USER_ID 提供認證資訊，避免在命令列中暴露敏感資訊。"
    )
    parser.add_argument("--message", help="要發送的純文字訊息")
    parser.add_argument("--broadcast", action="store_true",
                        help="廣播模式：發送給所有好友（不需要 LINE_USER_ID）")
    parser.add_argument("--notification", action="store_true",
                        help="發送格式化監控通知（需搭配 --keywords, --summary, --report-url）")
    parser.add_argument("--keywords", help="監控關鍵字（逗號分隔）")
    parser.add_argument("--summary", help="監控摘要內容")
    parser.add_argument("--report-url", help="完整報告連結或本地路徑")

    args = parser.parse_args()

    if not args.message and not args.notification:
        parser.error("請指定 --message 或 --notification 模式")

    # 從環境變數獲取 token（安全做法）
    channel_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

    if not channel_token:
        print(
            "錯誤: 缺少 LINE Channel Access Token。請設定環境變數 LINE_CHANNEL_ACCESS_TOKEN。\n"
            "範例: export LINE_CHANNEL_ACCESS_TOKEN='your-token-here'",
            file=sys.stderr
        )
        sys.exit(1)

    if args.broadcast:
        # 廣播模式：發給所有好友，不需要 user_id
        if args.notification:
            if not args.keywords or not args.summary or not args.report_url:
                parser.error("--notification 模式需要 --keywords, --summary, --report-url")
            keywords_list = [k.strip() for k in args.keywords.split(",")]
            keywords_str = ", ".join(keywords_list)
            formatted_message = (
                f"🔔 Threads 監控通知\n\n"
                f"關鍵字: {keywords_str}\n\n"
                f"摘要:\n{args.summary}\n\n"
                f"完整報告:\n{args.report_url}"
            )
            success = send_line_broadcast(channel_token, formatted_message)
        else:
            success = send_line_broadcast(channel_token, args.message)
    else:
        # Push 模式：發給指定用戶，需要 user_id
        user_id = os.environ.get("LINE_USER_ID")
        if not user_id:
            print(
                "錯誤: 缺少 LINE User ID。請設定環境變數 LINE_USER_ID，或使用 --broadcast 模式。\n"
                "範例: export LINE_USER_ID='U1234567890abcdef1234567890abcdef'",
                file=sys.stderr
            )
            sys.exit(1)

        if args.notification:
            if not args.keywords or not args.summary or not args.report_url:
                parser.error("--notification 模式需要 --keywords, --summary, --report-url")
            keywords_list = [k.strip() for k in args.keywords.split(",")]
            success = send_notification_message(
                channel_token, user_id, keywords_list, args.summary, args.report_url
            )
        else:
            success = send_line_message(channel_token, user_id, args.message)

    if success:
        print("LINE 訊息發送成功！")
        sys.exit(0)
    else:
        print("LINE 訊息發送失敗。", file=sys.stderr)
        sys.exit(1)
