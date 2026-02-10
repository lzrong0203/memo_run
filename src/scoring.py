"""
自訂評分模組 — 依 config/scoring.yml 的加分規則調整貼文重要性分數。

加分邏輯：
1. 讀取 YAML 設定檔中的 bonus_rules
2. 對每篇貼文的 content + summary 進行關鍵字比對
3. 每條規則最多觸發一次（同規則的多個關鍵字不重複加分）
4. 多條規則可同時觸發，分數累加
5. 最終分數不超過 max_score 上限

用法：
    python3 src/scoring.py --input data.json [--config config/scoring.yml]
"""

import copy
import json
import logging
import os
import sys
from typing import Dict, List

logger = logging.getLogger(__name__)

DEFAULT_SCORING_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "scoring.yml"
)

DEFAULT_MAX_SCORE = 15


def load_scoring_config(config_path: str = DEFAULT_SCORING_CONFIG_PATH) -> Dict:
    """
    載入評分設定檔。

    Args:
        config_path: YAML 設定檔路徑。

    Returns:
        Dict: 包含 bonus_rules 和 max_score 的設定字典。
              檔案不存在時回傳空規則。
    """
    import yaml

    if not os.path.exists(config_path):
        logger.warning("評分設定檔不存在: %s，使用空規則", config_path)
        return {"bonus_rules": [], "max_score": DEFAULT_MAX_SCORE}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error("讀取評分設定失敗: %s", e)
        return {"bonus_rules": [], "max_score": DEFAULT_MAX_SCORE}

    if not isinstance(config, dict):
        return {"bonus_rules": [], "max_score": DEFAULT_MAX_SCORE}

    return {
        "bonus_rules": config.get("bonus_rules", []),
        "max_score": config.get("max_score", DEFAULT_MAX_SCORE),
    }


def apply_scoring_bonus(post: Dict, config: Dict) -> Dict:
    """
    對單篇貼文套用加分規則，回傳新的 post（不修改原始資料）。

    比對範圍：content + analysis.summary
    每條規則最多觸發一次。

    Args:
        post: 貼文字典（含 analysis.importance）。
        config: 評分設定（含 bonus_rules, max_score）。

    Returns:
        Dict: 新的 post，analysis 中增加 adjusted_importance 和 bonus_detail。
    """
    result = copy.deepcopy(post)
    analysis = result.get("analysis", {})
    base_importance = analysis.get("importance", 0)

    # 建立比對文字（content + summary）
    content = post.get("content", "")
    summary = post.get("analysis", {}).get("summary", "")
    match_text = f"{content} {summary}"

    bonus_total = 0
    bonus_detail = []

    for rule in config.get("bonus_rules", []):
        keywords = rule.get("keywords", [])
        bonus = rule.get("bonus", 0)
        rule_name = rule.get("name", "unknown")

        # 同一規則只要有任一關鍵字命中就觸發，不重複加分
        matched = False
        for kw in keywords:
            if kw in match_text:
                matched = True
                break

        if matched:
            bonus_total += bonus
            bonus_detail.append({
                "rule_name": rule_name,
                "bonus": bonus,
            })

    max_score = config.get("max_score", DEFAULT_MAX_SCORE)
    adjusted = min(base_importance + bonus_total, max_score)

    analysis["adjusted_importance"] = adjusted
    analysis["bonus_detail"] = bonus_detail
    result["analysis"] = analysis

    if bonus_detail:
        logger.debug(
            "貼文 %s: %d → %d (加分: %s)",
            post.get("id", "?"), base_importance, adjusted,
            ", ".join(f"{d['rule_name']}+{d['bonus']}" for d in bonus_detail)
        )

    return result


def apply_scoring_to_posts(posts: List[Dict], config: Dict) -> List[Dict]:
    """
    對所有貼文批次套用加分規則。

    Args:
        posts: 貼文列表。
        config: 評分設定。

    Returns:
        List[Dict]: 加分後的貼文列表（新建立，不修改原始資料）。
    """
    return [apply_scoring_bonus(post, config) for post in posts]


if __name__ == '__main__':
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="自訂評分工具 - 依設定檔對貼文加分"
    )
    parser.add_argument("--input", required=True, help="JSON 輸入檔案路徑")
    parser.add_argument("--config", default=DEFAULT_SCORING_CONFIG_PATH,
                        help="評分設定檔路徑")
    parser.add_argument("--output", help="輸出 JSON 檔案路徑（省略則輸出到 stdout）")

    args = parser.parse_args()

    # 載入設定
    config = load_scoring_config(args.config)
    logger.info("載入 %d 條加分規則，上限 %d 分", len(config["bonus_rules"]), config["max_score"])

    # 載入資料
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"錯誤: 無法讀取輸入資料 - {e}", file=sys.stderr)
        sys.exit(2)

    # 套用加分
    posts = data.get("analyzed_posts", [])
    scored_posts = apply_scoring_to_posts(posts, config)

    # 輸出結果
    scored_data = {**data, "analyzed_posts": scored_posts}

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(scored_data, f, ensure_ascii=False, indent=2)
        print(f"已輸出: {args.output}")
    else:
        # 輸出摘要到 stdout
        for post in scored_posts:
            a = post["analysis"]
            base = a.get("importance", 0)
            adj = a.get("adjusted_importance", base)
            detail = a.get("bonus_detail", [])
            bonus_str = ", ".join(f"{d['rule_name']}+{d['bonus']}" for d in detail) if detail else "無加分"
            print(f"[{base}→{adj}] {a.get('summary', '?')[:50]}  ({bonus_str})")
