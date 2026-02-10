import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class DedupManager:
    """
    SQLite 去重管理器

    使用 SQLite 資料庫儲存已處理的貼文 ID，避免重複處理。
    """

    def __init__(self, db_path: str = "data/processed_posts.db"):
        """
        初始化去重管理器

        Args:
            db_path: SQLite 資料庫檔案路徑
        """
        self.db_path = db_path
        self._ensure_database()
        logger.info("DedupManager initialized with database: %s", db_path)

    def _ensure_database(self):
        """確保資料庫和資料表存在"""
        # 確保目錄存在
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info("Created directory: %s", db_dir)

        # 建立資料庫連線
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 建立資料表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_posts (
                post_id TEXT PRIMARY KEY,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 建立索引以提升查詢效能
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_processed_at
            ON processed_posts(processed_at)
        """)

        conn.commit()
        conn.close()
        logger.debug("Database and table ensured")

    def add_post(self, post_id: Optional[str]) -> bool:
        """
        新增已處理的貼文 ID

        Args:
            post_id: 貼文 ID

        Returns:
            bool: True = 新增成功，False = 新增失敗（重複或無效）
        """
        # 驗證輸入
        if not post_id or not isinstance(post_id, str):
            logger.warning("Invalid post_id: %s", post_id)
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO processed_posts (post_id) VALUES (?)",
                (post_id,)
            )

            conn.commit()
            conn.close()

            logger.info("Added post_id: %s", post_id)
            return True

        except sqlite3.IntegrityError:
            # UNIQUE constraint 違反 = 重複的 post_id
            logger.debug("Duplicate post_id: %s", post_id)
            return False

        except Exception as e:
            logger.error("Failed to add post_id %s: %s", post_id, e)
            return False

    def is_processed(self, post_id: Optional[str]) -> bool:
        """
        檢查貼文是否已處理過

        Args:
            post_id: 貼文 ID

        Returns:
            bool: True = 已處理過，False = 未處理
        """
        # 驗證輸入
        if not post_id or not isinstance(post_id, str):
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT 1 FROM processed_posts WHERE post_id = ? LIMIT 1",
                (post_id,)
            )

            result = cursor.fetchone()
            conn.close()

            exists = result is not None
            logger.debug("Post %s processed: %s", post_id, exists)
            return exists

        except Exception as e:
            logger.error("Failed to check post_id %s: %s", post_id, e)
            return False

    def get_processed_count(self) -> int:
        """
        取得已處理貼文總數

        Returns:
            int: 已處理貼文數量
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM processed_posts")
            count = cursor.fetchone()[0]

            conn.close()

            logger.debug("Processed posts count: %d", count)
            return count

        except Exception as e:
            logger.error("Failed to get count: %s", e)
            return 0

    def clear_all(self):
        """清空所有已處理的貼文記錄"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM processed_posts")
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            logger.info("Cleared all processed posts (%d records)", deleted_count)

        except Exception as e:
            logger.error("Failed to clear all posts: %s", e)

    def close(self):
        """關閉資料庫連線（用於清理資源）"""
        # SQLite 每次操作都開關連線，所以這裡不需要做什麼
        # 但保留這個方法以符合測試預期
        logger.debug("DedupManager closed")


if __name__ == '__main__':
    import argparse
    import sys

    # Configure logging for CLI usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="貼文去重工具 - 使用 SQLite 管理已處理的貼文 ID"
    )
    parser.add_argument("--db", default="data/processed_posts.db", help="資料庫檔案路徑")
    parser.add_argument("--check", metavar="POST_ID", help="檢查貼文是否已處理")
    parser.add_argument("--add", metavar="POST_ID", help="新增貼文 ID")
    parser.add_argument("--count", action="store_true", help="顯示已處理貼文數量")
    parser.add_argument("--clear", action="store_true", help="清空所有記錄")

    args = parser.parse_args()

    dedup = DedupManager(args.db)

    try:
        if args.check:
            is_processed = dedup.is_processed(args.check)
            if is_processed:
                print(f"DUPLICATE 貼文 {args.check} 已處理過")
                sys.exit(0)
            else:
                print(f"NEW 貼文 {args.check} 尚未處理")
                sys.exit(0)

        elif args.add:
            success = dedup.add_post(args.add)
            if success:
                print(f"✅ 新增貼文 {args.add} 成功")
                sys.exit(0)
            else:
                print(f"❌ 新增失敗（可能重複）")
                sys.exit(1)

        elif args.count:
            count = dedup.get_processed_count()
            print(f"📊 已處理貼文數量: {count}")
            sys.exit(0)

        elif args.clear:
            dedup.clear_all()
            print("✅ 已清空所有記錄")
            sys.exit(0)

        else:
            parser.print_help()
            sys.exit(0)

    finally:
        dedup.close()
