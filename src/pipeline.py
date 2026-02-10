"""
批次處理 pipeline — 一次完成 filter + dedup + scoring。

取代逐篇呼叫 filter.py / dedup.py 的方式，
將所有貼文以 JSON 輸入，一次處理完畢輸出結果。

用法：
    echo '[{"content":"...","author":"...","link":"..."}]' | python3 src/pipeline.py
    python3 src/pipeline.py --input posts.json
"""

import copy
import json
import logging
import os
import sys
from typing import Dict, List

logger = logging.getLogger(__name__)

# 預設路徑
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_FILTER_CONFIG = os.path.join(_PROJECT_ROOT, "config", "filters.yml")
DEFAULT_DEDUP_DB = os.path.join(_PROJECT_ROOT, "data", "processed_posts.db")
DEFAULT_SCORING_CONFIG = os.path.join(_PROJECT_ROOT, "config", "scoring.yml")


def process_posts(
    posts: List[Dict],
    filter_config_path: str = DEFAULT_FILTER_CONFIG,
    dedup_db_path: str = DEFAULT_DEDUP_DB,
    scoring_config_path: str = DEFAULT_SCORING_CONFIG,
) -> Dict:
    """
    批次處理貼文：filter → dedup → scoring。

    Args:
        posts: 貼文列表，每篇至少含 content, author, link。
        filter_config_path: filters.yml 路徑。
        dedup_db_path: SQLite 去重資料庫路徑。
        scoring_config_path: scoring.yml 路徑。

    Returns:
        Dict: {
            passed_posts, filtered_count, duplicate_count,
            new_count, total_input, summary
        }
    """
    from filter import load_filter_config, should_filter_content
    from dedup import DedupManager
    from scoring import load_scoring_config, apply_scoring_bonus

    total_input = len(posts)
    filtered_count = 0
    duplicate_count = 0
    passed_posts = []

    # 載入設定（一次性）
    try:
        filter_config = load_filter_config(filter_config_path)
    except FileNotFoundError:
        logger.warning("過濾設定檔不存在: %s，跳過過濾", filter_config_path)
        filter_config = {}

    dedup = DedupManager(dedup_db_path)
    scoring_config = load_scoring_config(scoring_config_path)

    for post in posts:
        # 深複製，不修改原始資料
        p = copy.deepcopy(post)

        # 檢查必要欄位
        content = p.get("content")
        link = p.get("link")
        if not content or not link:
            filtered_count += 1
            continue

        # 步驟 1: 過濾
        if should_filter_content(content, filter_config):
            filtered_count += 1
            continue

        # 步驟 2: 去重
        if dedup.is_processed(link):
            duplicate_count += 1
            continue

        # 新貼文 → 加入去重資料庫
        dedup.add_post(link)

        # 步驟 3: 評分加成（只加 bonus 到 content 層級，不需要完整 analysis）
        bonus_applied = []
        for rule in scoring_config.get("bonus_rules", []):
            keywords = rule.get("keywords", [])
            for kw in keywords:
                if kw in content:
                    bonus_applied.append(rule.get("name", "unknown"))
                    break

        p["bonus_applied"] = bonus_applied
        passed_posts.append(p)

    dedup.close()

    new_count = len(passed_posts)
    summary = (
        f"掃描 {total_input} 篇 → "
        f"過濾 {filtered_count} 篇 → "
        f"重複 {duplicate_count} 篇 → "
        f"有效 {new_count} 篇"
    )

    return {
        "passed_posts": passed_posts,
        "filtered_count": filtered_count,
        "duplicate_count": duplicate_count,
        "new_count": new_count,
        "total_input": total_input,
        "summary": summary,
    }


if __name__ == '__main__':
    import argparse

    try:
        from dotenv import load_dotenv
        env_path = os.path.join(_PROJECT_ROOT, '.env')
        load_dotenv(env_path)
    except ImportError:
        pass

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="批次處理 pipeline — 一次完成 filter + dedup + scoring"
    )
    parser.add_argument("--input", help="JSON 輸入檔案路徑（省略則從 stdin 讀取）")
    parser.add_argument("--filter-config", default=DEFAULT_FILTER_CONFIG)
    parser.add_argument("--dedup-db", default=DEFAULT_DEDUP_DB)
    parser.add_argument("--scoring-config", default=DEFAULT_SCORING_CONFIG)

    args = parser.parse_args()

    # 讀取輸入
    try:
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                posts = json.load(f)
        else:
            posts = json.load(sys.stdin)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"錯誤: 無法讀取輸入 - {e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(posts, list):
        print("錯誤: 輸入必須是 JSON 陣列", file=sys.stderr)
        sys.exit(2)

    # 處理
    result = process_posts(
        posts,
        filter_config_path=args.filter_config,
        dedup_db_path=args.dedup_db,
        scoring_config_path=args.scoring_config,
    )

    # 輸出 JSON 結果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)
