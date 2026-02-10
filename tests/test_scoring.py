import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from scoring import (
    load_scoring_config,
    apply_scoring_bonus,
    apply_scoring_to_posts,
    DEFAULT_SCORING_CONFIG_PATH,
)


class TestLoadScoringConfig(unittest.TestCase):

    def test_load_default_config(self):
        """測試載入預設 config/scoring.yml"""
        config = load_scoring_config()
        self.assertIn("bonus_rules", config)
        self.assertIn("max_score", config)
        self.assertIsInstance(config["bonus_rules"], list)
        self.assertGreater(len(config["bonus_rules"]), 0)

    def test_load_custom_config(self):
        """測試載入自訂路徑的設定檔"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("bonus_rules:\n  - name: test\n    keywords: [\"foo\"]\n    bonus: 3\nmax_score: 10\n")
            f.flush()
            config = load_scoring_config(f.name)
        os.unlink(f.name)
        self.assertEqual(len(config["bonus_rules"]), 1)
        self.assertEqual(config["bonus_rules"][0]["bonus"], 3)
        self.assertEqual(config["max_score"], 10)

    def test_load_missing_config_returns_default(self):
        """測試載入不存在的檔案時回傳空規則"""
        config = load_scoring_config("/nonexistent/path/scoring.yml")
        self.assertEqual(config["bonus_rules"], [])
        self.assertEqual(config["max_score"], 15)

    def test_config_rule_structure(self):
        """測試每條規則都有 name, keywords, bonus"""
        config = load_scoring_config()
        for rule in config["bonus_rules"]:
            self.assertIn("name", rule)
            self.assertIn("keywords", rule)
            self.assertIn("bonus", rule)
            self.assertIsInstance(rule["keywords"], list)
            self.assertIsInstance(rule["bonus"], (int, float))


class TestApplyScoringBonus(unittest.TestCase):

    def setUp(self):
        self.config = {
            "bonus_rules": [
                {"name": "交通", "keywords": ["馬路", "交通", "塞車"], "bonus": 2},
                {"name": "民代", "keywords": ["議員", "立委"], "bonus": 1},
                {"name": "人名", "keywords": ["黃國昌"], "bonus": 1},
            ],
            "max_score": 15,
        }

        self.post_traffic = {
            "id": "p1",
            "content": "馬路坑洞害人摔車，市府不管嗎？",
            "link": "https://example.com/p1",
            "analysis": {
                "categories": ["交通"],
                "importance": 5,
                "summary": "馬路坑洞投訴",
            },
        }

        self.post_representative = {
            "id": "p2",
            "content": "某議員今天說要爭取經費修路",
            "link": "https://example.com/p2",
            "analysis": {
                "categories": ["政治"],
                "importance": 4,
                "summary": "議員爭取經費",
            },
        }

        self.post_multi_match = {
            "id": "p3",
            "content": "黃國昌立委質疑交通預算分配不公",
            "link": "https://example.com/p3",
            "analysis": {
                "categories": ["政治", "交通"],
                "importance": 7,
                "summary": "立委質疑交通預算",
            },
        }

        self.post_no_match = {
            "id": "p4",
            "content": "今天天氣好好喔，出去走走",
            "link": "https://example.com/p4",
            "analysis": {
                "categories": ["生活"],
                "importance": 2,
                "summary": "日常閒聊",
            },
        }

    def test_traffic_keyword_bonus(self):
        """測試交通關鍵字加 2 分"""
        result = apply_scoring_bonus(self.post_traffic, self.config)
        self.assertEqual(result["analysis"]["adjusted_importance"], 7)  # 5 + 2

    def test_representative_keyword_bonus(self):
        """測試民代關鍵字加 1 分"""
        result = apply_scoring_bonus(self.post_representative, self.config)
        self.assertEqual(result["analysis"]["adjusted_importance"], 5)  # 4 + 1

    def test_multiple_rules_stack(self):
        """測試多條規則同時觸發，分數累加"""
        result = apply_scoring_bonus(self.post_multi_match, self.config)
        # 交通(+2) + 民代(+1, "立委") + 人名(+1, "黃國昌") = 7 + 4 = 11
        self.assertEqual(result["analysis"]["adjusted_importance"], 11)

    def test_no_match_no_bonus(self):
        """測試無匹配時不加分"""
        result = apply_scoring_bonus(self.post_no_match, self.config)
        self.assertEqual(result["analysis"]["adjusted_importance"], 2)

    def test_max_score_cap(self):
        """測試分數不超過 max_score 上限"""
        post = {
            "id": "p5",
            "content": "馬路上議員和黃國昌一起質疑交通塞車問題",
            "link": "https://example.com/p5",
            "analysis": {
                "categories": ["政治"],
                "importance": 14,
                "summary": "高分測試",
            },
        }
        config = {**self.config, "max_score": 10}
        result = apply_scoring_bonus(post, config)
        self.assertLessEqual(result["analysis"]["adjusted_importance"], 10)

    def test_original_importance_preserved(self):
        """測試原始 importance 不被修改"""
        result = apply_scoring_bonus(self.post_traffic, self.config)
        self.assertEqual(result["analysis"]["importance"], 5)
        self.assertEqual(result["analysis"]["adjusted_importance"], 7)

    def test_bonus_detail_recorded(self):
        """測試加分明細被記錄"""
        result = apply_scoring_bonus(self.post_multi_match, self.config)
        detail = result["analysis"]["bonus_detail"]
        self.assertIsInstance(detail, list)
        self.assertGreater(len(detail), 0)
        # 每個明細包含 rule_name 和 bonus
        for d in detail:
            self.assertIn("rule_name", d)
            self.assertIn("bonus", d)

    def test_immutability(self):
        """測試原始 post 不被修改（不可變性）"""
        original_importance = self.post_traffic["analysis"]["importance"]
        _ = apply_scoring_bonus(self.post_traffic, self.config)
        self.assertEqual(self.post_traffic["analysis"]["importance"], original_importance)
        self.assertNotIn("adjusted_importance", self.post_traffic["analysis"])

    def test_same_rule_only_triggers_once(self):
        """測試同一規則的多個關鍵字只觸發一次"""
        post = {
            "id": "p6",
            "content": "馬路塞車交通大亂",
            "link": "https://example.com/p6",
            "analysis": {
                "categories": ["交通"],
                "importance": 3,
                "summary": "多重交通關鍵字",
            },
        }
        result = apply_scoring_bonus(post, self.config)
        # 交通規則只加一次 +2，不是 +2+2+2
        self.assertEqual(result["analysis"]["adjusted_importance"], 5)

    def test_keyword_in_summary_also_matches(self):
        """測試 summary 中的關鍵字也能匹配"""
        post = {
            "id": "p7",
            "content": "最新消息報導",
            "link": "https://example.com/p7",
            "analysis": {
                "categories": ["政治"],
                "importance": 4,
                "summary": "議員提出交通改善方案",
            },
        }
        result = apply_scoring_bonus(post, self.config)
        # summary 中有「議員」+1，有「交通」+2
        self.assertEqual(result["analysis"]["adjusted_importance"], 7)


class TestApplyScoringToPosts(unittest.TestCase):

    def setUp(self):
        self.config = {
            "bonus_rules": [
                {"name": "交通", "keywords": ["交通"], "bonus": 2},
                {"name": "人名", "keywords": ["黃國昌"], "bonus": 1},
            ],
            "max_score": 15,
        }

        self.posts = [
            {
                "id": "a",
                "content": "交通問題嚴重",
                "link": "https://example.com/a",
                "analysis": {"categories": ["交通"], "importance": 5, "summary": "交通"},
            },
            {
                "id": "b",
                "content": "今天很開心",
                "link": "https://example.com/b",
                "analysis": {"categories": ["生活"], "importance": 3, "summary": "開心"},
            },
            {
                "id": "c",
                "content": "黃國昌談交通政策",
                "link": "https://example.com/c",
                "analysis": {"categories": ["政治"], "importance": 7, "summary": "交通政策"},
            },
        ]

    def test_apply_to_all_posts(self):
        """測試批次處理所有貼文"""
        results = apply_scoring_to_posts(self.posts, self.config)
        self.assertEqual(len(results), 3)

    def test_each_post_has_adjusted_importance(self):
        """測試每篇貼文都有 adjusted_importance"""
        results = apply_scoring_to_posts(self.posts, self.config)
        for post in results:
            self.assertIn("adjusted_importance", post["analysis"])

    def test_correct_bonus_values(self):
        """測試各篇加分正確"""
        results = apply_scoring_to_posts(self.posts, self.config)
        by_id = {p["id"]: p for p in results}
        self.assertEqual(by_id["a"]["analysis"]["adjusted_importance"], 7)   # 5 + 2
        self.assertEqual(by_id["b"]["analysis"]["adjusted_importance"], 3)   # 3 + 0
        self.assertEqual(by_id["c"]["analysis"]["adjusted_importance"], 10)  # 7 + 2 + 1

    def test_original_posts_not_mutated(self):
        """測試原始列表不被修改"""
        _ = apply_scoring_to_posts(self.posts, self.config)
        for post in self.posts:
            self.assertNotIn("adjusted_importance", post["analysis"])

    def test_empty_posts(self):
        """測試空列表"""
        results = apply_scoring_to_posts([], self.config)
        self.assertEqual(results, [])

    def test_empty_rules(self):
        """測試無規則時分數不變"""
        config = {"bonus_rules": [], "max_score": 15}
        results = apply_scoring_to_posts(self.posts, config)
        for orig, result in zip(self.posts, results):
            self.assertEqual(
                result["analysis"]["adjusted_importance"],
                orig["analysis"]["importance"]
            )


if __name__ == '__main__':
    unittest.main()
