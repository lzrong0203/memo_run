import unittest
import os
import sys
from unittest.mock import patch, mock_open

# 將 src 目錄添加到 Python 路徑中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from filter import should_filter_content, load_filter_config


class TestFilter(unittest.TestCase):

    def setUp(self):
        """設置測試用的 filter config"""
        self.config = {
            'hard_exclude': [
                '預售屋',
                '建案推薦',
                '誠徵人才',
                '限時特價',
                '現車價格'
            ],
            'priority_keep_keywords': [
                '毒品',
                '詐騙',
                '貪污',
                '警方',
                '逮捕'
            ],
            'min_content_length': 30,
            'min_exclude_word_length': 2
        }

    # ========== Content Length Tests ==========

    def test_filter_too_short_content(self):
        """測試過短的內容應該被過濾"""
        short_content = "短內容"
        result = should_filter_content(short_content, self.config)
        self.assertTrue(result, "過短的內容應該被過濾")

    def test_keep_sufficient_length_content(self):
        """測試足夠長度的內容應該保留"""
        content = "這是一則足夠長度的內容，應該通過最低長度檢查，不會被過濾掉。"
        result = should_filter_content(content, self.config)
        self.assertFalse(result, "足夠長度的內容應該保留")

    # ========== Hard Exclude Tests ==========

    def test_filter_hard_exclude_keywords(self):
        """測試包含硬性排除詞的內容應該被過濾"""
        content = "全新預售屋，位於台北市精華地段，歡迎預約看屋。"
        result = should_filter_content(content, self.config)
        self.assertTrue(result, "包含硬性排除詞的內容應該被過濾")

    def test_filter_multiple_exclude_keywords(self):
        """測試包含多個排除詞"""
        content = "建案推薦！預售屋現正熱賣中，歡迎來電洽詢各種優惠。"
        result = should_filter_content(content, self.config)
        self.assertTrue(result, "包含多個排除詞的內容應該被過濾")

    def test_filter_exclude_word_too_short(self):
        """測試排除詞太短（少於 min_exclude_word_length）應該跳過"""
        # 如果 hard_exclude 中有單字，應該被 min_exclude_word_length 過濾掉
        config_with_short_word = self.config.copy()
        config_with_short_word['hard_exclude'] = ['售', '預售屋']  # '售' 只有一個字

        content = "警方今日破獲大型販售毒品集團案件，逮捕嫌犯多人，目前已移送檢方偵辦並將起訴。"
        result = should_filter_content(content, config_with_short_word)
        # 應該保留，因為：
        # 1. '售' 太短（< min_exclude_word_length=2），跳過
        # 2. 沒有 '預售屋'
        # 3. 包含白名單詞 '毒品'、'警方'、'逮捕'
        self.assertFalse(result, "排除詞太短應該跳過，且包含白名單詞應該保留")

    # ========== Priority Keep (Whitelist) Tests ==========

    def test_keep_priority_keywords_override_exclude(self):
        """測試白名單優先級高於硬性排除"""
        # 同時包含排除詞和白名單詞
        content = "警方今日破獲大型預售屋詐騙集團案件，逮捕主嫌及共犯數人，檢方目前正在偵辦中。"
        result = should_filter_content(content, self.config)
        self.assertFalse(result, "包含白名單關鍵字應該保留，即使有排除詞")

    def test_keep_priority_keywords_without_exclude(self):
        """測試只包含白名單詞（沒有排除詞）應該保留"""
        content = "警方今日破獲大型毒品走私案，逮捕嫌犯十餘人，查扣大量海洛因。"
        result = should_filter_content(content, self.config)
        self.assertFalse(result, "包含白名單關鍵字應該保留")

    def test_keep_multiple_priority_keywords(self):
        """測試包含多個白名單詞"""
        content = "檢調單位今日偵辦重大貪污弊案，前高官涉嫌收賄遭警方逮捕，檢方將於近日提起公訴。"
        result = should_filter_content(content, self.config)
        self.assertFalse(result, "包含多個白名單關鍵字應該保留")

    # ========== Clean Content Tests ==========

    def test_keep_clean_content(self):
        """測試乾淨的內容（無排除詞、無白名單詞）應該保留"""
        content = "台北市長今日視察交通建設進度，表示將持續改善大眾運輸系統，提升市民生活品質。"
        result = should_filter_content(content, self.config)
        self.assertFalse(result, "乾淨的內容應該保留")

    # ========== Edge Cases ==========

    def test_filter_empty_content(self):
        """測試空內容應該被過濾"""
        result = should_filter_content("", self.config)
        self.assertTrue(result, "空內容應該被過濾")

    def test_filter_none_content(self):
        """測試 None 應該被過濾"""
        result = should_filter_content(None, self.config)
        self.assertTrue(result, "None 應該被過濾")

    def test_handle_empty_config(self):
        """測試空的 config"""
        empty_config = {
            'hard_exclude': [],
            'priority_keep_keywords': [],
            'min_content_length': 10,
            'min_exclude_word_length': 2
        }
        content = "這是一則正常的內容，沒有任何特殊關鍵字。"
        result = should_filter_content(content, empty_config)
        self.assertFalse(result, "空 config 應該保留正常內容")

    # ========== Load Config Tests ==========

    @patch('builtins.open', new_callable=mock_open, read_data="""
hard_exclude:
  - "預售屋"
  - "建案"
priority_keep_keywords:
  - "毒品"
  - "警方"
min_content_length: 30
min_exclude_word_length: 2
""")
    @patch('os.path.exists', return_value=True)
    def test_load_filter_config(self, mock_exists, mock_file):
        """測試從 YAML 載入 config"""
        config = load_filter_config('config/filters.yml')

        self.assertIn('hard_exclude', config)
        self.assertIn('priority_keep_keywords', config)
        self.assertEqual(config['min_content_length'], 30)
        self.assertEqual(config['min_exclude_word_length'], 2)
        self.assertIn('預售屋', config['hard_exclude'])
        self.assertIn('毒品', config['priority_keep_keywords'])

    @patch('os.path.exists', return_value=False)
    def test_load_filter_config_file_not_found(self, mock_exists):
        """測試檔案不存在時的處理"""
        with self.assertRaises(FileNotFoundError):
            load_filter_config('nonexistent.yml')


if __name__ == '__main__':
    unittest.main()
