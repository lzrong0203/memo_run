import unittest
import os
import sys
from unittest.mock import patch, Mock
import requests

# 將 src 目錄添加到 Python 路徑中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from line_notify import (
    send_line_message, send_line_broadcast, send_notification_message,
    MAX_MESSAGE_LENGTH, LINE_BROADCAST_API_URL
)


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

    # ========== Notification Message Tests ==========

    @patch('line_notify.requests.post')
    def test_send_notification_with_list_keywords(self, mock_post):
        """測試發送格式化通知（使用關鍵字列表）"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        keywords = ["政治", "選舉", "投票"]
        summary = "這是一則關於選舉的重要報導，內容包含多項關鍵議題。"
        report_url = "https://example.com/report/12345"

        success = send_notification_message(
            self.mock_token,
            self.mock_user_id,
            keywords,
            summary,
            report_url
        )

        self.assertTrue(success, "應該成功發送通知")
        mock_post.assert_called_once()

        # 檢查訊息內容格式
        call_kwargs = mock_post.call_args.kwargs
        message_text = call_kwargs['json']['messages'][0]['text']

        self.assertIn("🔔 Threads 監控通知", message_text)
        self.assertIn("關鍵字: 政治, 選舉, 投票", message_text)
        self.assertIn("摘要:", message_text)
        self.assertIn(summary, message_text)
        self.assertIn("完整報告:", message_text)
        self.assertIn(report_url, message_text)

    @patch('line_notify.requests.post')
    def test_send_notification_with_string_keyword(self, mock_post):
        """測試發送格式化通知（使用單一關鍵字字串）"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        keyword = "緊急通知"
        summary = "這是一則緊急通知，請立即注意。"
        report_url = "https://example.com/urgent/001"

        success = send_notification_message(
            self.mock_token,
            self.mock_user_id,
            keyword,
            summary,
            report_url
        )

        self.assertTrue(success, "應該成功發送通知")

        # 檢查訊息內容格式
        call_kwargs = mock_post.call_args.kwargs
        message_text = call_kwargs['json']['messages'][0]['text']

        self.assertIn("關鍵字: 緊急通知", message_text)
        self.assertIn(summary, message_text)
        self.assertIn(report_url, message_text)

    @patch('line_notify.requests.post')
    def test_send_notification_empty_keywords(self, mock_post):
        """測試空關鍵字應該失敗"""
        summary = "這是摘要"
        report_url = "https://example.com/report/123"

        success = send_notification_message(
            self.mock_token,
            self.mock_user_id,
            [],
            summary,
            report_url
        )

        self.assertFalse(success, "空關鍵字應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_send_notification_empty_summary(self, mock_post):
        """測試空摘要應該失敗"""
        keywords = ["測試"]
        report_url = "https://example.com/report/123"

        success = send_notification_message(
            self.mock_token,
            self.mock_user_id,
            keywords,
            "",
            report_url
        )

        self.assertFalse(success, "空摘要應該失敗")
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_send_notification_empty_url(self, mock_post):
        """測試空 URL 應該失敗"""
        keywords = ["測試"]
        summary = "這是摘要"

        success = send_notification_message(
            self.mock_token,
            self.mock_user_id,
            keywords,
            summary,
            ""
        )

        self.assertFalse(success, "空 URL 應該失敗")
        mock_post.assert_not_called()


class TestLineBroadcast(unittest.TestCase):

    def setUp(self):
        self.mock_token = "mock_channel_access_token"
        self.mock_message = "Broadcast test message."

    # ========== Success Cases ==========

    @patch('line_notify.requests.post')
    def test_broadcast_success(self, mock_post):
        """測試成功廣播 LINE 訊息"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        success = send_line_broadcast(self.mock_token, self.mock_message)

        self.assertTrue(success, "應該成功廣播訊息")
        mock_post.assert_called_once()

        # 檢查 API endpoint 是 broadcast
        call_args = mock_post.call_args
        self.assertEqual(call_args.args[0], LINE_BROADCAST_API_URL)

        # 檢查 payload 不含 'to' 欄位
        json_payload = call_args.kwargs['json']
        self.assertNotIn('to', json_payload)

        # 檢查 messages 格式
        self.assertEqual(len(json_payload['messages']), 1)
        self.assertEqual(json_payload['messages'][0]['type'], 'text')
        self.assertEqual(json_payload['messages'][0]['text'], self.mock_message)

    @patch('line_notify.requests.post')
    def test_broadcast_headers(self, mock_post):
        """測試 broadcast 使用正確的 headers"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        send_line_broadcast(self.mock_token, self.mock_message)

        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(call_kwargs['headers']['Authorization'], f'Bearer {self.mock_token}')
        self.assertEqual(call_kwargs['headers']['Content-Type'], 'application/json')

    # ========== Input Validation Tests ==========

    @patch('line_notify.requests.post')
    def test_broadcast_empty_token(self, mock_post):
        """測試空 token 廣播應該失敗"""
        success = send_line_broadcast("", self.mock_message)
        self.assertFalse(success)
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_broadcast_none_token(self, mock_post):
        """測試 None token 廣播應該失敗"""
        success = send_line_broadcast(None, self.mock_message)
        self.assertFalse(success)
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_broadcast_token_with_newline(self, mock_post):
        """測試包含換行符的 token（header injection 風險）"""
        success = send_line_broadcast("token\r\nX-Evil: header", self.mock_message)
        self.assertFalse(success)
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_broadcast_empty_message(self, mock_post):
        """測試空訊息廣播應該失敗"""
        success = send_line_broadcast(self.mock_token, "")
        self.assertFalse(success)
        mock_post.assert_not_called()

    @patch('line_notify.requests.post')
    def test_broadcast_message_too_long(self, mock_post):
        """測試超長訊息廣播應該失敗"""
        long_message = "x" * (MAX_MESSAGE_LENGTH + 1)
        success = send_line_broadcast(self.mock_token, long_message)
        self.assertFalse(success)
        mock_post.assert_not_called()

    # ========== Exception Tests ==========

    @patch('line_notify.requests.post')
    def test_broadcast_http_error(self, mock_post):
        """測試 broadcast HTTP 錯誤"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Forbidden")
        mock_post.return_value = mock_response

        success = send_line_broadcast(self.mock_token, self.mock_message)
        self.assertFalse(success)

    @patch('line_notify.requests.post')
    def test_broadcast_timeout(self, mock_post):
        """測試 broadcast timeout"""
        mock_post.side_effect = requests.exceptions.Timeout("Timed out")

        success = send_line_broadcast(self.mock_token, self.mock_message)
        self.assertFalse(success)

    @patch('line_notify.requests.post')
    def test_broadcast_connection_error(self, mock_post):
        """測試 broadcast 連線錯誤"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Refused")

        success = send_line_broadcast(self.mock_token, self.mock_message)
        self.assertFalse(success)


if __name__ == '__main__':
    unittest.main()
