import requests
from typing import Union

LINE_NOTIFY_API_URL = "https://notify-api.line.me/api/notify"

def send_line_notification(token: str, message: str) -> bool:
    """
    使用 LINE Notify API 發送通知。
    
    Args:
        token: LINE Notify 的存取令牌。
        message: 要發送的訊息內容。
        
    Returns:
        bool: 如果通知發送成功，則返回 True，否則返回 False。
    """
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'message': message
    }

    try:
        response = requests.post(LINE_NOTIFY_API_URL, headers=headers, data=data)
        response.raise_for_status() # 如果響應狀態碼指示錯誤，則引發 HTTPError
        response_json = response.json()
        if response_json.get("status") == 200:
            # print(f"LINE 通知發送成功: {response_json.get("message")}")
            return True
        else:
            # print(f"LINE 通知發送失敗 ({response_json.get("status")}): {response_json.get("message")}")
            return False
    except requests.exceptions.HTTPError as errh:
        # print(f"HTTP Error: {errh}")
        return False
    except requests.exceptions.ConnectionError as errc:
        # print(f"Error Connecting: {errc}")
        return False
    except requests.exceptions.Timeout as errt:
        # print(f"Timeout Error: {errt}")
        return False
    except requests.exceptions.RequestException as err:
        # print(f"Something went wrong: {err}")
        return False

if __name__ == '__main__':
    # 這裡可以添加一些 CLI 接口的實現，以便從命令行調用
    # 例如：python3 src/line_notify.py --token YOUR_TOKEN --message "Hello from Dobby!"
    import argparse
    import os

    parser = argparse.ArgumentParser(description="發送 LINE 通知模組。")
    parser.add_argument("--token", help="LINE Notify 的存取令牌 (從 .env 或命令行讀取)")
    parser.add_argument("--message", required=True, help="要發送的訊息內容")
    
    args = parser.parse_args()
    
    # 優先從命令行參數獲取 token，如果沒有則嘗試從環境變數 LINE_NOTIFY_TOKEN 獲取
    line_token = args.token if args.token else os.environ.get("LINE_NOTIFY_TOKEN")

    if not line_token:
        print("錯誤: 缺少 LINE Notify Token。請透過 --token 參數或設定環境變數 LINE_NOTIFY_TOKEN 提供。", file=sys.stderr)
        sys.exit(1)

    success = send_line_notification(line_token, args.message)

    if success:
        print("LINE 通知發送成功！")
    else:
        print("LINE 通知發送失敗。", file=sys.stderr)
        sys.exit(1)
