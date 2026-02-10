import unittest
import os
import sys
import tempfile
import sqlite3

# 將 src 目錄添加到 Python 路徑中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dedup import DedupManager


class TestDedup(unittest.TestCase):

    def setUp(self):
        """每個測試使用臨時資料庫"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.dedup = DedupManager(self.db_path)

    def tearDown(self):
        """測試完成後清理資料庫"""
        self.dedup.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    # ========== Initialization Tests ==========

    def test_create_database(self):
        """測試資料庫和資料表是否正確建立"""
        # 檢查資料庫檔案存在
        self.assertTrue(os.path.exists(self.db_path))

        # 檢查資料表結構
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='processed_posts'")
        result = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(result, "processed_posts 資料表應該存在")

    # ========== Add Post Tests ==========

    def test_add_new_post(self):
        """測試新增新的貼文 ID"""
        post_id = "post_12345"
        result = self.dedup.add_post(post_id)

        self.assertTrue(result, "新增新貼文應該成功")
        self.assertTrue(self.dedup.is_processed(post_id), "新增後應該能查詢到")

    def test_add_duplicate_post(self):
        """測試新增重複的貼文 ID 應該失敗"""
        post_id = "post_duplicate"

        # 第一次新增應該成功
        result1 = self.dedup.add_post(post_id)
        self.assertTrue(result1)

        # 第二次新增應該失敗（重複）
        result2 = self.dedup.add_post(post_id)
        self.assertFalse(result2, "新增重複貼文應該失敗")

    def test_add_empty_post_id(self):
        """測試新增空的貼文 ID 應該失敗"""
        result = self.dedup.add_post("")
        self.assertFalse(result, "新增空 ID 應該失敗")

    def test_add_none_post_id(self):
        """測試新增 None 應該失敗"""
        result = self.dedup.add_post(None)
        self.assertFalse(result, "新增 None 應該失敗")

    # ========== Is Processed Tests ==========

    def test_is_processed_existing_post(self):
        """測試已處理的貼文應該返回 True"""
        post_id = "post_existing"
        self.dedup.add_post(post_id)

        result = self.dedup.is_processed(post_id)
        self.assertTrue(result, "已處理的貼文應該返回 True")

    def test_is_processed_new_post(self):
        """測試未處理的貼文應該返回 False"""
        post_id = "post_new"

        result = self.dedup.is_processed(post_id)
        self.assertFalse(result, "未處理的貼文應該返回 False")

    def test_is_processed_empty_id(self):
        """測試空 ID 應該返回 False"""
        result = self.dedup.is_processed("")
        self.assertFalse(result, "空 ID 應該返回 False")

    def test_is_processed_none_id(self):
        """測試 None 應該返回 False"""
        result = self.dedup.is_processed(None)
        self.assertFalse(result, "None 應該返回 False")

    # ========== Count Tests ==========

    def test_get_processed_count(self):
        """測試取得已處理貼文數量"""
        # 新增幾筆資料
        self.dedup.add_post("post_1")
        self.dedup.add_post("post_2")
        self.dedup.add_post("post_3")

        count = self.dedup.get_processed_count()
        self.assertEqual(count, 3, "應該有 3 筆已處理貼文")

    def test_get_processed_count_empty(self):
        """測試空資料庫的計數"""
        count = self.dedup.get_processed_count()
        self.assertEqual(count, 0, "空資料庫應該返回 0")

    # ========== Clear Tests ==========

    def test_clear_all(self):
        """測試清空所有資料"""
        # 新增幾筆資料
        self.dedup.add_post("post_1")
        self.dedup.add_post("post_2")
        self.dedup.add_post("post_3")

        # 清空
        self.dedup.clear_all()

        # 驗證
        count = self.dedup.get_processed_count()
        self.assertEqual(count, 0, "清空後應該沒有資料")
        self.assertFalse(self.dedup.is_processed("post_1"), "清空後應該查不到")

    # ========== Persistence Tests ==========

    def test_persistence_across_instances(self):
        """測試資料持久化（不同實例間）"""
        post_id = "post_persistent"

        # 第一個實例新增資料
        self.dedup.add_post(post_id)
        self.dedup.close()

        # 第二個實例應該能讀到
        dedup2 = DedupManager(self.db_path)
        result = dedup2.is_processed(post_id)
        dedup2.close()

        self.assertTrue(result, "資料應該持久化到資料庫")

    # ========== Batch Operations Tests ==========

    def test_add_multiple_posts(self):
        """測試批次新增多筆貼文"""
        post_ids = ["post_1", "post_2", "post_3", "post_4", "post_5"]

        for post_id in post_ids:
            self.dedup.add_post(post_id)

        # 驗證全部都新增成功
        for post_id in post_ids:
            self.assertTrue(self.dedup.is_processed(post_id))

        count = self.dedup.get_processed_count()
        self.assertEqual(count, len(post_ids))


if __name__ == '__main__':
    unittest.main()
