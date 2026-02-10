import unittest
import os
import sys
from unittest.mock import patch, Mock
import requests

# 將 src 目錄添加到 Python 路徑中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from line_notify import send_line_notification, MAX_MESSAGE_LENGTH


class TestLineNotify(unittest.TestCase):

    def setUp(self):
        self.mock_token = "mock_line_notify_token"
        self.mock_message = "Test message from Claude Code."

    # ========== Success Cases ==========

    @patch('line_notify.requests.post')
    def test_send_success(self, mock_post):
        """測試成功發送 LINE 通知"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": 200, "message": "ok"}
        mock_post.return_value = mock_response

        success = send_line_notification(self.mock_token, self.mock_message)

        self.assertTrue(success, "應該成功發送通知")
        mock_post.assert_called_once()
        # 檢查呼叫參數（包括新加的 timeout 和 verify）
        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(call_kwargs['timeout'], 10)
        self.assertEqual(call_kwargs['verify'], True)

    # ========== Input Validation Tests ==========

    @patch('line_notify.requests.post')
    def test_empty_token(self, mock_post):
        """測試空 token"""
        success = send_line_notification("", self.mock_message)
        self.assertFalse(success, "空 token 應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_none_token(self, mock_post):
        """測試 None token"""
        success = send_line_notification(None, self.mock_message)
        self.assertFalse(success, "None token 應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_empty_message(self, mock_post):
        """測試空訊息"""
        success = send_line_notification(self.mock_token, "")
        self.assertFalse(success, "空訊息應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_none_message(self, mock_post):
        """測試 None 訊息"""
        success = send_line_notification(self.mock_token, None)
        self.assertFalse(success, "None 訊息應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_message_too_long(self, mock_post):
        """測試超長訊息（超過 1000 字元）"""
        long_message = "x" * (MAX_MESSAGE_LENGTH + 1)
        success = send_line_notification(self.mock_token, long_message)
        self.assertFalse(success, "超長訊息應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_token_with_newline(self, mock_post):
        """測試包含換行符的 token（header injection 風險）"""
        malicious_token = "token\r\nX-Evil: header"
        success = send_line_notification(malicious_token, self.mock_message)
        self.assertFalse(success, "包含換行符的 token 應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_token_with_tab(self, mock_post):
        """測試包含 tab 的 token"""
        malicious_token = "token\tspace"
        success = send_line_notification(malicious_token, self.mock_message)
        self.assertFalse(success, "包含 tab 的 token 應該失敗")
        mock_post.assert_not_called()

    # ========== API Response Tests ==========

    @patch('line_notify.requests.post')
    def test_api_failure_status(self, mock_post):
        """測試 API 返回失敗狀態（HTTP 200 但 JSON status != 200）"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": 400, "message": "Bad Request"}
        mock_post.return_value = mock_response

        success = send_line_notification(self.mock_token, self.mock_message)
        self.assertFalse(success, "API 返回失敗狀態應該失敗")

    @patch('line_notify.requests.post')
    def test_json_decode_error(self, mock_post):
        """測試 JSON 解析失敗"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        success = send_line_notification(self.mock_token, self.mock_message)
        self.assertFalse(success, "JSON 解析失敗應該失敗")

    @patch('line_notify.requests.post')
    def test_json_missing_status_field(self, mock_post):
        """測試 JSON 缺少 status 欄位"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"message": "ok"}  # 沒有 status
        mock_post.return_value = mock_response

        success = send_line_notification(self.mock_token, self.mock_message)
        self.assertFalse(success, "缺少 status 欄位應該失敗（status=None != 200）")

    # ========== Exception Tests ==========

    @patch('line_notify.requests.post')
    def test_http_error(self, mock_post):
        """測試 HTTP 錯誤（raise_for_status 拋出異常）"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_post.return_value = mock_response

        success = send_line_notification(self.mock_token, self.mock_message)
        self.assertFalse(success, "HTTP 錯誤應該失敗")

    @patch('line_notify.requests.post')
    def test_connection_error(self, mock_post):
        """測試網路連接錯誤"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        success = send_line_notification(self.mock_token, self.mock_message)
        self.assertFalse(success, "連接錯誤應該失敗")

    @patch('line_notify.requests.post')
    def test_timeout_error(self, mock_post):
        """測試 timeout 錯誤"""
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        success = send_line_notification(self.mock_token, self.mock_message)
        self.assertFalse(success, "Timeout 應該失敗")

    @patch('line_notify.requests.post')
    def test_generic_request_exception(self, mock_post):
        """測試一般 requests 異常"""
        mock_post.side_effect = requests.exceptions.RequestException("Unknown error")

        success = send_line_notification(self.mock_token, self.mock_message)
        self.assertFalse(success, "一般 request 異常應該失敗")


if __name__ == '__main__':
    unittest.main()
