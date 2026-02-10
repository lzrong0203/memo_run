import unittest
import os
import sys
from unittest.mock import patch, Mock
import requests

# 將 src 目錄添加到 Python 路徑中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from line_notify import send_line_message, MAX_MESSAGE_LENGTH


class TestLineMessaging(unittest.TestCase):

    def setUp(self):
        self.mock_token = "mock_channel_access_token"
        self.mock_user_id = "U1234567890abcdef1234567890abcdef"
        self.mock_message = "Test message from Claude Code."

    # ========== Success Cases ==========

    @patch('line_notify.requests.post')
    def test_send_success(self, mock_post):
        """測試成功發送 LINE 訊息"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        success = send_line_message(self.mock_token, self.mock_user_id, self.mock_message)

        self.assertTrue(success, "應該成功發送訊息")
        mock_post.assert_called_once()

        # 檢查呼叫參數
        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(call_kwargs['timeout'], 10)
        self.assertEqual(call_kwargs['verify'], True)

        # 檢查 JSON payload 格式
        json_payload = call_kwargs['json']
        self.assertEqual(json_payload['to'], self.mock_user_id)
        self.assertEqual(len(json_payload['messages']), 1)
        self.assertEqual(json_payload['messages'][0]['type'], 'text')
        self.assertEqual(json_payload['messages'][0]['text'], self.mock_message)

    # ========== Input Validation Tests ==========

    @patch('line_notify.requests.post')
    def test_empty_token(self, mock_post):
        """測試空 token"""
        success = send_line_message("", self.mock_user_id, self.mock_message)
        self.assertFalse(success, "空 token 應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_none_token(self, mock_post):
        """測試 None token"""
        success = send_line_message(None, self.mock_user_id, self.mock_message)
        self.assertFalse(success, "None token 應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_empty_user_id(self, mock_post):
        """測試空 user_id"""
        success = send_line_message(self.mock_token, "", self.mock_message)
        self.assertFalse(success, "空 user_id 應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_none_user_id(self, mock_post):
        """測試 None user_id"""
        success = send_line_message(self.mock_token, None, self.mock_message)
        self.assertFalse(success, "None user_id 應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_empty_message(self, mock_post):
        """測試空訊息"""
        success = send_line_message(self.mock_token, self.mock_user_id, "")
        self.assertFalse(success, "空訊息應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_none_message(self, mock_post):
        """測試 None 訊息"""
        success = send_line_message(self.mock_token, self.mock_user_id, None)
        self.assertFalse(success, "None 訊息應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_message_too_long(self, mock_post):
        """測試超長訊息（超過 5000 字元）"""
        long_message = "x" * (MAX_MESSAGE_LENGTH + 1)
        success = send_line_message(self.mock_token, self.mock_user_id, long_message)
        self.assertFalse(success, "超長訊息應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_token_with_newline(self, mock_post):
        """測試包含換行符的 token（header injection 風險）"""
        malicious_token = "token\r\nX-Evil: header"
        success = send_line_message(malicious_token, self.mock_user_id, self.mock_message)
        self.assertFalse(success, "包含換行符的 token 應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_token_with_tab(self, mock_post):
        """測試包含 tab 的 token"""
        malicious_token = "token\tspace"
        success = send_line_message(malicious_token, self.mock_user_id, self.mock_message)
        self.assertFalse(success, "包含 tab 的 token 應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_invalid_user_id_format(self, mock_post):
        """測試無效的 user_id 格式（包含空白）"""
        invalid_user_id = "U123 456"
        success = send_line_message(self.mock_token, invalid_user_id, self.mock_message)
        self.assertFalse(success, "包含空白的 user_id 應該失敗")
        mock_post.assert_not_called()

    # ========== Exception Tests ==========

    @patch('line_notify.requests.post')
    def test_http_error(self, mock_post):
        """測試 HTTP 錯誤（raise_for_status 拋出異常）"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_post.return_value = mock_response

        success = send_line_message(self.mock_token, self.mock_user_id, self.mock_message)
        self.assertFalse(success, "HTTP 錯誤應該失敗")

    @patch('line_notify.requests.post')
    def test_connection_error(self, mock_post):
        """測試網路連接錯誤"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        success = send_line_message(self.mock_token, self.mock_user_id, self.mock_message)
        self.assertFalse(success, "連接錯誤應該失敗")

    @patch('line_notify.requests.post')
    def test_timeout_error(self, mock_post):
        """測試 timeout 錯誤"""
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        success = send_line_message(self.mock_token, self.mock_user_id, self.mock_message)
        self.assertFalse(success, "Timeout 應該失敗")

    @patch('line_notify.requests.post')
    def test_generic_request_exception(self, mock_post):
        """測試一般 requests 異常"""
        mock_post.side_effect = requests.exceptions.RequestException("Unknown error")

        success = send_line_message(self.mock_token, self.mock_user_id, self.mock_message)
        self.assertFalse(success, "一般 request 異常應該失敗")


if __name__ == '__main__':
    unittest.main()
