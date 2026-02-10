import unittest
import os
import sys
import json
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from report_generator import (
    validate_monitoring_data,
    classify_posts_by_category,
    identify_big_fish,
    compute_category_stats,
    generate_markdown_report,
    generate_line_summary,
    generate_telegram_summary,
    save_report,
    generate_all_outputs,
    MAX_LINE_MESSAGE_LENGTH,
    MAX_TELEGRAM_MESSAGE_LENGTH,
)


class TestReportGenerator(unittest.TestCase):

    def setUp(self):
        """設置測試用的監控資料"""
        self.post_big_fish_importance = {
            "id": "post_001",
            "keyword": "台北市政府",
            "content": "台北市政府今日宣布將投入 50 億元改善捷運系統，涵蓋三條新路線。",
            "author": "user_abc",
            "link": "https://www.threads.net/@user_abc/post/12345",
            "timestamp": "2026-02-10T14:20:00Z",
            "analysis": {
                "categories": ["政治", "交通"],
                "importance": 9,
                "summary": "市政府宣布 50 億改善捷運系統，涵蓋三條路線。",
                "entities": {
                    "persons": ["市長"],
                    "locations": ["台北市"],
                    "organizations": ["市政府", "捷運局"],
                    "events": ["捷運改善計畫"]
                },
                "reasoning": "重大交通政策，影響範圍廣。"
            }
        }

        self.post_big_fish_multi_category = {
            "id": "post_002",
            "keyword": "交通建設",
            "content": "環評爭議引發大規模抗議，涉及環保、政治和社會層面。",
            "author": "user_def",
            "link": "https://www.threads.net/@user_def/post/23456",
            "timestamp": "2026-02-10T14:35:00Z",
            "analysis": {
                "categories": ["政治", "社會", "環保"],
                "importance": 8,
                "summary": "環評爭議引發抗議，涉及多個層面。",
                "entities": {
                    "persons": ["居民代表"],
                    "locations": ["某某區"],
                    "organizations": ["環保署"],
                    "events": ["環評爭議"]
                },
                "reasoning": "跨領域議題，社會關注度高。"
            }
        }

        self.post_normal = {
            "id": "post_003",
            "keyword": "交通建設",
            "content": "新北環狀線延伸計畫環評通過，預計 2028 年完工。",
            "author": "user_xyz",
            "link": "https://www.threads.net/@user_xyz/post/67890",
            "timestamp": "2026-02-10T14:50:00Z",
            "analysis": {
                "categories": ["交通"],
                "importance": 6,
                "summary": "新北環狀線延伸案環評通過。",
                "entities": {
                    "persons": [],
                    "locations": ["新北市"],
                    "organizations": [],
                    "events": ["環狀線延伸"]
                },
                "reasoning": "一般交通建設進展。"
            }
        }

        self.sample_data = {
            "timestamp": "2026-02-10T15:30:00Z",
            "keywords": ["台北市政府", "交通建設"],
            "analyzed_posts": [
                self.post_big_fish_importance,
                self.post_big_fish_multi_category,
                self.post_normal,
            ],
            "stats": {
                "total_searched": 100,
                "filtered_by_hard_rules": 45,
                "filtered_by_dedup": 30,
                "filtered_by_ai": 15,
                "valid_count": 10
            }
        }

    # ========== Validation Tests ==========

    def test_validate_valid_data(self):
        """驗證正確的資料結構"""
        valid, error = validate_monitoring_data(self.sample_data)
        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_validate_missing_analyzed_posts(self):
        """驗證缺少 analyzed_posts 欄位"""
        data = {"timestamp": "2026-02-10T15:30:00Z", "keywords": ["test"], "stats": {}}
        valid, error = validate_monitoring_data(data)
        self.assertFalse(valid)
        self.assertIn("analyzed_posts", error)

    def test_validate_empty_analyzed_posts(self):
        """驗證空的 analyzed_posts（合法但無資料）"""
        data = {**self.sample_data, "analyzed_posts": []}
        valid, error = validate_monitoring_data(data)
        self.assertTrue(valid)

    def test_validate_post_missing_required_field(self):
        """驗證貼文缺少必要欄位 (link)"""
        bad_post = {
            "id": "post_bad",
            "content": "some content",
            "author": "user",
            "timestamp": "2026-02-10T14:00:00Z",
            "analysis": {"categories": [], "importance": 1, "summary": "test"}
        }
        data = {**self.sample_data, "analyzed_posts": [bad_post]}
        valid, error = validate_monitoring_data(data)
        self.assertFalse(valid)
        self.assertIn("link", error)

    def test_validate_post_missing_analysis(self):
        """驗證貼文缺少 analysis 欄位"""
        bad_post = {
            "id": "post_bad",
            "content": "some content",
            "author": "user",
            "link": "https://example.com/post",
            "timestamp": "2026-02-10T14:00:00Z",
        }
        data = {**self.sample_data, "analyzed_posts": [bad_post]}
        valid, error = validate_monitoring_data(data)
        self.assertFalse(valid)
        self.assertIn("analysis", error)

    # ========== Classification Tests ==========

    def test_classify_posts_by_category(self):
        """測試貼文按類別分組"""
        posts = [self.post_big_fish_importance, self.post_normal]
        result = classify_posts_by_category(posts)
        self.assertIn("政治", result)
        self.assertIn("交通", result)
        self.assertEqual(len(result["政治"]), 1)
        self.assertEqual(len(result["交通"]), 2)

    def test_classify_multi_category_post(self):
        """測試多類別貼文出現在所有類別中"""
        posts = [self.post_big_fish_multi_category]
        result = classify_posts_by_category(posts)
        self.assertIn("政治", result)
        self.assertIn("社會", result)
        self.assertIn("環保", result)
        # 同一篇貼文出現在三個類別中
        self.assertEqual(result["政治"][0]["id"], "post_002")
        self.assertEqual(result["社會"][0]["id"], "post_002")
        self.assertEqual(result["環保"][0]["id"], "post_002")

    def test_classify_empty_posts(self):
        """測試空列表"""
        result = classify_posts_by_category([])
        self.assertEqual(result, {})

    # ========== Big Fish Tests ==========

    def test_identify_big_fish_high_importance(self):
        """測試 importance >= 9 為大魚"""
        posts = [self.post_big_fish_importance, self.post_normal]
        big_fish = identify_big_fish(posts)
        self.assertEqual(len(big_fish), 1)
        self.assertEqual(big_fish[0]["id"], "post_001")

    def test_identify_big_fish_multi_category(self):
        """測試 categories >= 3 且 importance >= 8 為大魚"""
        posts = [self.post_big_fish_multi_category, self.post_normal]
        big_fish = identify_big_fish(posts)
        self.assertEqual(len(big_fish), 1)
        self.assertEqual(big_fish[0]["id"], "post_002")

    def test_identify_big_fish_not_qualified(self):
        """測試 importance=6 單一類別不是大魚"""
        posts = [self.post_normal]
        big_fish = identify_big_fish(posts)
        self.assertEqual(len(big_fish), 0)

    def test_identify_big_fish_sorted(self):
        """測試大魚按 importance 降序排列"""
        posts = [self.post_big_fish_multi_category, self.post_big_fish_importance]
        big_fish = identify_big_fish(posts)
        self.assertEqual(len(big_fish), 2)
        self.assertEqual(big_fish[0]["id"], "post_001")  # importance 9
        self.assertEqual(big_fish[1]["id"], "post_002")  # importance 8

    # ========== Category Stats Tests ==========

    def test_compute_category_stats(self):
        """測試統計計算"""
        categorized = classify_posts_by_category(self.sample_data["analyzed_posts"])
        stats = compute_category_stats(categorized)
        self.assertTrue(len(stats) > 0)
        # 按 count 降序排列
        for i in range(len(stats) - 1):
            self.assertGreaterEqual(stats[i]["count"], stats[i + 1]["count"])
        # 每項都有 name, count, percentage
        for stat in stats:
            self.assertIn("name", stat)
            self.assertIn("count", stat)
            self.assertIn("percentage", stat)

    def test_compute_category_stats_empty(self):
        """測試空輸入"""
        stats = compute_category_stats({})
        self.assertEqual(stats, [])

    # ========== Markdown Report Tests ==========

    def test_generate_markdown_report_contains_header(self):
        """測試報告包含時間戳和關鍵字"""
        report = generate_markdown_report(self.sample_data)
        self.assertIn("2026-02-10", report)
        self.assertIn("台北市政府", report)
        self.assertIn("交通建設", report)

    def test_generate_markdown_report_contains_big_fish(self):
        """測試報告包含大魚區塊"""
        report = generate_markdown_report(self.sample_data)
        self.assertIn("大魚", report)
        self.assertIn("9/10", report)
        self.assertIn("市政府宣布", report)

    def test_generate_markdown_report_contains_links(self):
        """測試報告包含貼文連結"""
        report = generate_markdown_report(self.sample_data)
        self.assertIn("https://www.threads.net/@user_abc/post/12345", report)
        self.assertIn("https://www.threads.net/@user_xyz/post/67890", report)

    def test_generate_markdown_report_contains_stats(self):
        """測試報告包含統計區塊"""
        report = generate_markdown_report(self.sample_data)
        self.assertIn("100", report)  # total_searched
        self.assertIn("45", report)   # filtered_by_hard_rules

    # ========== LINE Summary Tests ==========

    def test_generate_line_summary_under_limit(self):
        """測試 LINE 摘要不超過 5000 字元"""
        summary = generate_line_summary(self.sample_data)
        self.assertLessEqual(len(summary), MAX_LINE_MESSAGE_LENGTH)

    def test_generate_line_summary_contains_urls(self):
        """測試 LINE 摘要包含貼文 URL"""
        summary = generate_line_summary(self.sample_data)
        self.assertIn("https://www.threads.net/", summary)

    def test_generate_line_summary_contains_big_fish(self):
        """測試 LINE 摘要包含大魚標記"""
        summary = generate_line_summary(self.sample_data)
        self.assertIn("大魚", summary)

    # ========== Telegram Summary Tests ==========

    def test_generate_telegram_summary_under_limit(self):
        """測試 Telegram 摘要不超過 4096 字元"""
        summary = generate_telegram_summary(self.sample_data)
        self.assertLessEqual(len(summary), MAX_TELEGRAM_MESSAGE_LENGTH)

    def test_generate_telegram_summary_markdown_links(self):
        """測試 Telegram 摘要包含 Markdown 連結語法"""
        summary = generate_telegram_summary(self.sample_data)
        # Telegram Markdown link: [text](url)
        self.assertIn("](https://www.threads.net/", summary)

    # ========== Save Report Tests ==========

    def test_save_report_creates_file(self):
        """測試報告儲存為檔案"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = save_report("# Test Report", reports_dir=tmpdir)
            self.assertTrue(os.path.exists(path))
            with open(path, 'r', encoding='utf-8') as f:
                self.assertEqual(f.read(), "# Test Report")

    def test_save_report_creates_directory(self):
        """測試自動建立不存在的目錄"""
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_dir = os.path.join(tmpdir, "reports", "nested")
            path = save_report("# Test", reports_dir=reports_dir)
            self.assertTrue(os.path.exists(path))

    def test_save_report_filename_format(self):
        """測試檔名格式為 report_YYYYMMDD_HHMMSS.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = save_report("# Test", reports_dir=tmpdir,
                               timestamp="2026-02-10T15:30:00Z")
            filename = os.path.basename(path)
            self.assertTrue(filename.startswith("report_"))
            self.assertTrue(filename.endswith(".md"))
            # 應含有日期部分
            self.assertIn("20260210", filename)

    # ========== Integration Tests ==========

    def test_generate_all_outputs_returns_all_keys(self):
        """測試 generate_all_outputs 回傳所有必要的 key"""
        with tempfile.TemporaryDirectory() as tmpdir:
            outputs = generate_all_outputs(self.sample_data, reports_dir=tmpdir)
            self.assertIn("report_path", outputs)
            self.assertIn("markdown_report", outputs)
            self.assertIn("line_summary", outputs)
            self.assertIn("telegram_summary", outputs)
            # 報告檔案應已存在
            self.assertTrue(os.path.exists(outputs["report_path"]))

    def test_generate_all_outputs_invalid_data(self):
        """測試無效資料時回傳 None 或引發錯誤"""
        invalid_data = {"bad": "data"}
        result = generate_all_outputs(invalid_data)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
