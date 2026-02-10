import logging
import os
import yaml
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def load_filter_config(config_path: str) -> Dict:
    """
    從 YAML 檔案載入過濾設定

    Args:
        config_path: YAML 設定檔路徑

    Returns:
        Dict: 過濾設定字典

    Raises:
        FileNotFoundError: 設定檔不存在
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Filter config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    logger.info("Loaded filter config from %s", config_path)
    return config


def should_filter_content(content: Optional[str], config: Dict) -> bool:
    """
    判斷內容是否應該被過濾

    過濾邏輯：
    1. 檢查內容長度（太短則過濾）
    2. 檢查白名單關鍵字（優先級最高，有則保留）
    3. 檢查硬性排除詞（有則過濾）
    4. 都沒匹配則保留

    Args:
        content: 要檢查的內容
        config: 過濾設定字典

    Returns:
        bool: True = 應該過濾（丟棄），False = 應該保留
    """
    # 處理 None 或空字串
    if not content:
        logger.debug("Content is None or empty, filtering")
        return True

    # 1. 檢查內容長度
    min_length = config.get('min_content_length', 0)
    if len(content) < min_length:
        logger.debug("Content too short (%d < %d), filtering", len(content), min_length)
        return True

    # 2. 檢查白名單（優先級最高）
    priority_keywords = config.get('priority_keep_keywords', [])
    for keyword in priority_keywords:
        if keyword in content:
            logger.info("Content contains priority keyword '%s', keeping", keyword)
            return False  # 保留

    # 3. 檢查硬性排除詞
    hard_exclude = config.get('hard_exclude', [])
    min_exclude_length = config.get('min_exclude_word_length', 0)

    for exclude_word in hard_exclude:
        # 跳過太短的排除詞（避免誤判）
        if len(exclude_word) < min_exclude_length:
            logger.debug("Skipping exclude word '%s' (too short)", exclude_word)
            continue

        if exclude_word in content:
            logger.info("Content contains exclude word '%s', filtering", exclude_word)
            return True  # 過濾

    # 4. 都沒匹配，保留
    logger.debug("Content passed all filters, keeping")
    return False


if __name__ == '__main__':
    import argparse
    import sys

    # Configure logging for CLI usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="內容過濾工具 - 根據硬性排除詞和白名單過濾內容"
    )
    parser.add_argument("--config", default="config/filters.yml", help="過濾設定檔路徑")
    parser.add_argument("--content", required=True, help="要檢查的內容")

    args = parser.parse_args()

    try:
        config = load_filter_config(args.config)
        should_filter = should_filter_content(args.content, config)

        if should_filter:
            print("❌ 內容被過濾（應該丟棄）")
            sys.exit(1)
        else:
            print("✅ 內容通過過濾（應該保留）")
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"錯誤: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        print(f"錯誤: {e}", file=sys.stderr)
        sys.exit(2)
