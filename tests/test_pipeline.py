import unittest
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from pipeline import process_posts

# 測試用長內容（>30 字元以通過 min_content_length）
VALID_CONTENT_1 = "台北市長今天視察交通建設，宣布內湖地區的通勤改善方案即日起開始執行，預計惠及十萬名居民"
VALID_CONTENT_2 = "內湖科技園區新增三條接駁巴士路線，方便上班族從捷運站轉乘直達辦公區域，即日起試營運"
VALID_CONTENT_3 = "樂活公園的櫻花已經盛開了，週末吸引大批遊客前往拍照打卡，內湖區公所建議避開上午尖峰時段"
VALID_TRAFFIC = "台北市的交通建設改善計畫今天正式啟動了，涵蓋捷運延伸線和公車專用道等多項工程非常值得關注"


class TestProcessPosts(unittest.TestCase):

    def setUp(self):
        """每個測試使用臨時去重資料庫和真實設定檔"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.filter_config = os.path.join(self.project_root, 'config', 'filters.yml')
        self.scoring_config = os.path.join(self.project_root, 'config', 'scoring.yml')

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def _make_post(self, content, author="user1", link=None):
        if link is None:
            link = f"https://www.threads.net/@{author}/post/{abs(hash(content)) % 100000}"
        return {"content": content, "author": author, "link": link}

    # ========== Basic Processing ==========

    def test_empty_input(self):
        """空輸入應回傳空結果"""
        result = process_posts([], self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result["total_input"], 0)
        self.assertEqual(result["passed_posts"], [])
        self.assertEqual(result["new_count"], 0)

    def test_single_valid_post(self):
        """一篇有效貼文應通過 pipeline"""
        posts = [self._make_post(VALID_CONTENT_1)]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result["total_input"], 1)
        self.assertEqual(result["new_count"], 1)
        self.assertEqual(len(result["passed_posts"]), 1)

    def test_multiple_valid_posts(self):
        """多篇有效貼文都應通過"""
        posts = [
            self._make_post(VALID_CONTENT_1),
            self._make_post(VALID_CONTENT_2),
            self._make_post(VALID_CONTENT_3),
        ]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result["total_input"], 3)
        self.assertEqual(result["new_count"], 3)

    # ========== Filter Integration ==========

    def test_short_content_filtered(self):
        """過短的內容應被過濾"""
        posts = [self._make_post("太短了")]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result["filtered_count"], 1)
        self.assertEqual(result["new_count"], 0)
        self.assertEqual(len(result["passed_posts"]), 0)

    def test_excluded_keyword_filtered(self):
        """含排除詞的貼文應被過濾"""
        posts = [self._make_post("這個建案推薦超級好，快來看預售屋優惠方案，限時特價中，歡迎來電洽詢")]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result["filtered_count"], 1)
        self.assertEqual(result["new_count"], 0)

    def test_mixed_filter_and_pass(self):
        """混合過濾和通過的貼文"""
        posts = [
            self._make_post("太短"),  # filtered (too short)
            self._make_post(VALID_CONTENT_1),  # pass
            self._make_post("這個建案推薦真的很讚，預售屋優惠不要錯過，歡迎來電洽詢了解更多訊息"),  # filtered
        ]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result["total_input"], 3)
        self.assertEqual(result["filtered_count"], 2)
        self.assertEqual(result["new_count"], 1)

    # ========== Dedup Integration ==========

    def test_duplicate_post_detected(self):
        """重複的貼文應被去重"""
        link = "https://www.threads.net/@user/post/same123"
        posts = [
            self._make_post(VALID_CONTENT_1, link=link),
            self._make_post(VALID_CONTENT_2, link=link),
        ]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result["new_count"], 1)
        self.assertEqual(result["duplicate_count"], 1)

    def test_dedup_persists_across_calls(self):
        """去重跨批次持久化"""
        link = "https://www.threads.net/@user/post/persist456"
        posts1 = [self._make_post(VALID_CONTENT_1, link=link)]
        posts2 = [self._make_post(VALID_CONTENT_2, link=link)]

        result1 = process_posts(posts1, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result1["new_count"], 1)

        result2 = process_posts(posts2, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result2["duplicate_count"], 1)
        self.assertEqual(result2["new_count"], 0)

    def test_different_links_not_duplicate(self):
        """不同連結的貼文不應被去重"""
        posts = [
            self._make_post(VALID_CONTENT_1, link="https://www.threads.net/@a/post/111"),
            self._make_post(VALID_CONTENT_2, link="https://www.threads.net/@b/post/222"),
        ]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result["new_count"], 2)
        self.assertEqual(result["duplicate_count"], 0)

    # ========== Filter before Dedup ==========

    def test_filter_runs_before_dedup(self):
        """被過濾的貼文不應進入去重資料庫"""
        link = "https://www.threads.net/@user/post/filterme"
        # First call: content too short, should be filtered (not added to dedup DB)
        posts1 = [self._make_post("太短", link=link)]
        result1 = process_posts(posts1, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result1["filtered_count"], 1)

        # Second call: same link but valid content, should pass (not marked as duplicate)
        posts2 = [self._make_post(VALID_CONTENT_1, link=link)]
        result2 = process_posts(posts2, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result2["new_count"], 1)
        self.assertEqual(result2["duplicate_count"], 0)

    # ========== Output Structure ==========

    def test_output_has_required_keys(self):
        """輸出應包含所有必要欄位"""
        posts = [self._make_post(VALID_CONTENT_1)]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)

        required_keys = ["passed_posts", "filtered_count", "duplicate_count",
                         "new_count", "total_input", "summary"]
        for key in required_keys:
            self.assertIn(key, result)

    def test_passed_post_preserves_fields(self):
        """通過的貼文應保留原始欄位"""
        posts = [self._make_post(VALID_CONTENT_1,
                                 author="test_author",
                                 link="https://www.threads.net/@test/post/abc")]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        passed = result["passed_posts"][0]
        self.assertEqual(passed["author"], "test_author")
        self.assertEqual(passed["link"], "https://www.threads.net/@test/post/abc")
        self.assertIn("content", passed)

    def test_summary_text(self):
        """摘要文字應包含統計數字"""
        posts = [
            self._make_post(VALID_CONTENT_1),
            self._make_post("太短"),
        ]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertIn("2", result["summary"])  # total_input
        self.assertIn("1", result["summary"])  # filtered or new count

    # ========== Scoring Integration ==========

    def test_scoring_applied_to_passed_posts(self):
        """通過的貼文如含交通關鍵字應有加分"""
        posts = [self._make_post(VALID_TRAFFIC)]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        passed = result["passed_posts"][0]
        self.assertIn("bonus_applied", passed)

    # ========== Immutability ==========

    def test_original_posts_not_mutated(self):
        """原始輸入不應被修改"""
        posts = [self._make_post(VALID_CONTENT_1)]
        original = json.dumps(posts)
        process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(json.dumps(posts), original)

    # ========== MIN_VALID_POSTS / needs_more ==========

    def test_needs_more_true_when_below_min(self):
        """有效貼文不足 min_valid_posts 時，needs_more 應為 True"""
        posts = [self._make_post(VALID_CONTENT_1)]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config,
                               min_valid_posts=5)
        self.assertTrue(result["needs_more"])
        self.assertEqual(result["min_valid_posts"], 5)

    def test_needs_more_false_when_meets_min(self):
        """有效貼文達到 min_valid_posts 時，needs_more 應為 False"""
        posts = [
            self._make_post(VALID_CONTENT_1, link="https://www.threads.net/@a/post/1"),
            self._make_post(VALID_CONTENT_2, link="https://www.threads.net/@b/post/2"),
            self._make_post(VALID_CONTENT_3, link="https://www.threads.net/@c/post/3"),
        ]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config,
                               min_valid_posts=3)
        self.assertFalse(result["needs_more"])

    def test_needs_more_false_when_exceeds_min(self):
        """有效貼文超過 min_valid_posts 時，needs_more 應為 False"""
        posts = [
            self._make_post(VALID_CONTENT_1, link="https://www.threads.net/@a/post/1"),
            self._make_post(VALID_CONTENT_2, link="https://www.threads.net/@b/post/2"),
            self._make_post(VALID_CONTENT_3, link="https://www.threads.net/@c/post/3"),
        ]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config,
                               min_valid_posts=2)
        self.assertFalse(result["needs_more"])

    def test_needs_more_default_is_10(self):
        """預設 min_valid_posts 為 10"""
        posts = [self._make_post(VALID_CONTENT_1)]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result["min_valid_posts"], 10)
        self.assertTrue(result["needs_more"])

    def test_needs_more_with_zero_valid(self):
        """所有貼文都被過濾時，needs_more 應為 True"""
        posts = [self._make_post("短")]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config,
                               min_valid_posts=1)
        self.assertTrue(result["needs_more"])
        self.assertEqual(result["new_count"], 0)

    def test_needs_more_in_output_keys(self):
        """輸出應包含 needs_more 和 min_valid_posts 欄位"""
        posts = [self._make_post(VALID_CONTENT_1)]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertIn("needs_more", result)
        self.assertIn("min_valid_posts", result)

    # ========== Error Handling ==========

    def test_missing_filter_config(self):
        """過濾設定檔不存在時應使用空設定繼續處理"""
        posts = [self._make_post(VALID_CONTENT_1)]
        result = process_posts(posts, "/nonexistent/filters.yml", self.db_path, self.scoring_config)
        self.assertEqual(result["total_input"], 1)

    def test_post_missing_content(self):
        """缺少 content 欄位的貼文應被過濾"""
        posts = [{"author": "user", "link": "https://www.threads.net/@u/post/1"}]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result["filtered_count"], 1)

    def test_post_missing_link(self):
        """缺少 link 欄位的貼文應被過濾"""
        posts = [{"content": VALID_CONTENT_1, "author": "user"}]
        result = process_posts(posts, self.filter_config, self.db_path, self.scoring_config)
        self.assertEqual(result["filtered_count"], 1)


if __name__ == '__main__':
    unittest.main()
