import unittest
import os
import sys
from unittest.mock import patch, Mock
import requests # 導入 requests

# 將 src 目錄添加到 Python 路徑中，以便可以導入 line_notify.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

class TestLineNotify(unittest.TestCase):

    def setUp(self):
        self.mock_token = "mock_line_notify_token"
        self.mock_message = "Test message from Dobby."

    @patch('line_notify.requests.post') # 假設 line_notify.py 中會導入 requests
    def test_send_success(self, mock_post):
        """測試成功發送 LINE 通知"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 200, "message": "ok"}
        mock_post.return_value = mock_response

        from line_notify import send_line_notification
        success = send_line_notification(self.mock_token, self.mock_message)

        self.assertTrue(success, "應該成功發送通知")
        mock_post.assert_called_once_with(
            "https://notify-api.line.me/api/notify",
            headers={'Authorization': f'Bearer {self.mock_token}'},
            data={'message': self.mock_message}
        )

    @patch('line_notify.requests.post')
    def test_send_failure(self, mock_post):
        """測試發送 LINE 通知失敗"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"status": 400, "message": "Bad Request"}
        mock_post.return_value = mock_response

        from line_notify import send_line_notification
        success = send_line_notification(self.mock_token, self.mock_message)

        self.assertFalse(success, "應該發送通知失敗")
        mock_post.assert_called_once() # 確保有被調用

    @patch('line_notify.requests.post')
    def test_empty_message(self, mock_post):
        """測試空訊息發送 (預期失敗或處理)"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"status": 400, "message": "Message is empty"}
        mock_post.return_value = mock_response

        from line_notify import send_line_notification
        success = send_line_notification(self.mock_token, "")

        self.assertFalse(success, "空訊息應該發送失敗")
        mock_post.assert_called_once()

    @patch('line_notify.requests.post')
    def test_connection_error(self, mock_post):
        """測試網路連接錯誤"""
        mock_post.side_effect = requests.exceptions.ConnectionError

        from line_notify import send_line_notification
        success = send_line_notification(self.mock_token, self.mock_message)

        self.assertFalse(success, "連接錯誤應該導致發送失敗")
        mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main()
