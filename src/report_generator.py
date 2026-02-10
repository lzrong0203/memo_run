import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

MAX_LINE_MESSAGE_LENGTH = 5000
MAX_TELEGRAM_MESSAGE_LENGTH = 4096
DEFAULT_REPORTS_DIR = "data/reports"

REQUIRED_TOP_KEYS = ["analyzed_posts", "stats", "keywords", "timestamp"]
REQUIRED_POST_KEYS = ["id", "content", "link"]
REQUIRED_ANALYSIS_KEYS = ["categories", "importance", "summary"]


def validate_monitoring_data(data: Dict) -> Tuple[bool, str]:
    """
    驗證監控資料結構是否完整。

    Args:
        data: 監控資料字典。

    Returns:
        Tuple[bool, str]: (是否有效, 錯誤訊息)。有效時錯誤訊息為空字串。
    """
    if not isinstance(data, dict):
        return False, "資料必須是字典格式"

    for key in REQUIRED_TOP_KEYS:
        if key not in data:
            return False, f"缺少必要欄位: {key}"

    if not isinstance(data["analyzed_posts"], list):
        return False, "analyzed_posts 必須是列表"

    for i, post in enumerate(data["analyzed_posts"]):
        for key in REQUIRED_POST_KEYS:
            if key not in post:
                return False, f"貼文 #{i} 缺少必要欄位: {key}"
        if "analysis" not in post:
            return False, f"貼文 #{i} 缺少 analysis 欄位"
        analysis = post["analysis"]
        for key in REQUIRED_ANALYSIS_KEYS:
            if key not in analysis:
                return False, f"貼文 #{i} 的 analysis 缺少欄位: {key}"

    return True, ""


def classify_posts_by_category(posts: List[Dict]) -> Dict[str, List[Dict]]:
    """
    將已分析的貼文依類別分組。一篇貼文可同時出現在多個類別中。

    Args:
        posts: 已分析的貼文列表（每筆含 analysis 欄位）。

    Returns:
        Dict[str, List[Dict]]: 類別名稱 -> 該類別的貼文列表。
    """
    categorized: Dict[str, List[Dict]] = {}
    for post in posts:
        categories = post.get("analysis", {}).get("categories", [])
        for category in categories:
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(post)
    return categorized


def identify_big_fish(posts: List[Dict]) -> List[Dict]:
    """
    識別大魚（重大議題）貼文。

    判斷標準：
    1. importance >= 9
    2. categories >= 3 且 importance >= 8

    Args:
        posts: 已分析的貼文列表。

    Returns:
        List[Dict]: 大魚貼文列表（依 importance 降序排列）。
    """
    big_fish = []
    for post in posts:
        analysis = post.get("analysis", {})
        importance = analysis.get("importance", 0)
        categories = analysis.get("categories", [])

        if importance >= 9:
            big_fish.append(post)
        elif len(categories) >= 3 and importance >= 8:
            big_fish.append(post)

    big_fish.sort(key=lambda p: p.get("analysis", {}).get("importance", 0), reverse=True)
    return big_fish


def compute_category_stats(categorized: Dict[str, List[Dict]]) -> List[Dict]:
    """
    計算各類別的統計資料。

    Args:
        categorized: 分類後的貼文字典。

    Returns:
        List[Dict]: [{"name": "政治", "count": 4, "percentage": 40.0}, ...]
                     按 count 降序排列。
    """
    if not categorized:
        return []

    # 計算唯一貼文數（用於百分比分母）
    all_post_ids = set()
    for posts in categorized.values():
        for post in posts:
            all_post_ids.add(post.get("id", ""))
    total_unique = len(all_post_ids) if all_post_ids else 1

    stats = []
    for name, posts in categorized.items():
        count = len(posts)
        percentage = round(count / total_unique * 100, 1)
        stats.append({"name": name, "count": count, "percentage": percentage})

    stats.sort(key=lambda s: s["count"], reverse=True)
    return stats


def generate_markdown_report(data: Dict) -> str:
    """
    從監控資料生成完整的 Markdown 格式戰報。

    Args:
        data: 完整的監控資料字典。

    Returns:
        str: Markdown 格式的完整戰報。
    """
    posts = data.get("analyzed_posts", [])
    stats = data.get("stats", {})
    keywords = data.get("keywords", [])
    timestamp = data.get("timestamp", datetime.now().isoformat())

    categorized = classify_posts_by_category(posts)
    big_fish = identify_big_fish(posts)
    category_stats = compute_category_stats(categorized)

    lines = []

    # Header
    lines.append("# Threads 輿情戰報")
    lines.append("")
    lines.append(f"**生成時間**: {timestamp}")
    lines.append(f"**監控關鍵字**: {', '.join(keywords)}")
    lines.append(f"**有效貼文數**: {len(posts)} 篇")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("## 執行摘要")
    lines.append("")
    big_fish_note = f"，發現 {len(big_fish)} 個重大議題" if big_fish else ""
    lines.append(
        f"本次監控週期共掃描 {stats.get('total_searched', 'N/A')} 筆貼文，"
        f"經雙重過濾後篩選出 {len(posts)} 筆有效內容{big_fish_note}。"
    )
    lines.append("")

    # Stats table
    lines.append("| 項目 | 數量 |")
    lines.append("|------|------|")
    lines.append(f"| 總掃描數 | {stats.get('total_searched', 'N/A')} |")
    lines.append(f"| 硬性過濾移除 | {stats.get('filtered_by_hard_rules', 'N/A')} |")
    lines.append(f"| 去重移除 | {stats.get('filtered_by_dedup', 'N/A')} |")
    lines.append(f"| AI 過濾移除 | {stats.get('filtered_by_ai', 'N/A')} |")
    lines.append(f"| 有效貼文 | {stats.get('valid_count', len(posts))} |")
    lines.append("")

    # Category distribution
    if category_stats:
        lines.append("### 議題分布")
        lines.append("")
        lines.append("| 類別 | 數量 | 百分比 |")
        lines.append("|------|------|--------|")
        for cs in category_stats:
            lines.append(f"| {cs['name']} | {cs['count']} | {cs['percentage']}% |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Big Fish
    if big_fish:
        lines.append("## 大魚警報（重大議題）")
        lines.append("")
        for i, fish in enumerate(big_fish, 1):
            analysis = fish.get("analysis", {})
            cats = analysis.get("categories", [])
            cat_label = "][".join(cats)
            lines.append(f"### {i}. [{cat_label}] {analysis.get('summary', '')}")
            lines.append("")
            lines.append(f"- **重要性**: {analysis.get('importance', 'N/A')}/10")
            lines.append(f"- **作者**: @{fish.get('author', 'unknown')}")
            lines.append(f"- **時間**: {fish.get('timestamp', 'N/A')}")
            lines.append(f"- **摘要**: {analysis.get('summary', '')}")

            entities = analysis.get("entities", {})
            if entities:
                if entities.get("persons"):
                    lines.append(f"- **人物**: {', '.join(entities['persons'])}")
                if entities.get("locations"):
                    lines.append(f"- **地點**: {', '.join(entities['locations'])}")
                if entities.get("organizations"):
                    lines.append(f"- **組織**: {', '.join(entities['organizations'])}")
                if entities.get("events"):
                    lines.append(f"- **事件**: {', '.join(entities['events'])}")

            lines.append(f"- **原文**: {fish.get('link', '')}")
            lines.append(f"- **分析**: {analysis.get('reasoning', '')}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Detailed category sections
    lines.append("## 各類別詳情")
    lines.append("")

    for cs in category_stats:
        cat_name = cs["name"]
        cat_posts = categorized.get(cat_name, [])
        # 按 importance 降序
        cat_posts_sorted = sorted(
            cat_posts,
            key=lambda p: p.get("analysis", {}).get("importance", 0),
            reverse=True
        )
        lines.append(f"### {cat_name}（{len(cat_posts_sorted)} 篇）")
        lines.append("")
        for j, post in enumerate(cat_posts_sorted, 1):
            a = post.get("analysis", {})
            imp = a.get("importance", 0)
            lines.append(f"{j}. [{imp}/10] {a.get('summary', post.get('content', '')[:60])}")
            lines.append(f"   - @{post.get('author', 'unknown')} | "
                         f"[原文]({post.get('link', '')})")
            lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*報告由 OpenClaw AI Agent 自動產生*")

    return "\n".join(lines)


def generate_line_summary(data: Dict) -> str:
    """
    從監控資料生成 LINE 通知用的精簡版文字（含貼文 URL）。

    限制在 MAX_LINE_MESSAGE_LENGTH 字元內。

    Args:
        data: 完整的監控資料字典。

    Returns:
        str: 適合 LINE 發送的純文字摘要（含 URL）。
    """
    posts = data.get("analyzed_posts", [])
    stats = data.get("stats", {})
    keywords = data.get("keywords", [])
    big_fish = identify_big_fish(posts)

    parts = []

    # Header
    parts.append("🔔 Threads 監控通知")
    parts.append(f"📊 掃描 {stats.get('total_searched', 'N/A')} 筆 → 有效 {len(posts)} 筆")
    parts.append(f"🔑 關鍵字: {', '.join(keywords)}")
    parts.append("")

    # Big fish
    if big_fish:
        parts.append(f"🐟 大魚警報（{len(big_fish)} 則）:")
        for fish in big_fish:
            a = fish.get("analysis", {})
            parts.append(f"[{a.get('importance', '?')}/10] {a.get('summary', '')}")
            parts.append(f"→ {fish.get('link', '')}")
        parts.append("")

    # Other posts (non-big-fish)
    big_fish_ids = {f["id"] for f in big_fish}
    other_posts = [p for p in posts if p["id"] not in big_fish_ids]
    other_posts.sort(
        key=lambda p: p.get("analysis", {}).get("importance", 0), reverse=True
    )

    if other_posts:
        parts.append("📋 其他重點:")
        current_text = "\n".join(parts)

        for post in other_posts:
            a = post.get("analysis", {})
            cats = a.get("categories", [])
            cat_label = "/".join(cats) if cats else "其他"
            entry = f"• [{cat_label}] {a.get('summary', post.get('content', '')[:40])}"
            url_line = f"  → {post.get('link', '')}"
            candidate = f"{entry}\n{url_line}"

            # 檢查長度限制
            if len(current_text) + len(candidate) + 2 > MAX_LINE_MESSAGE_LENGTH - 50:
                parts.append("...更多內容見完整報告")
                break
            parts.append(entry)
            parts.append(url_line)
            current_text = "\n".join(parts)

    return "\n".join(parts)


def generate_telegram_summary(data: Dict) -> str:
    """
    從監控資料生成 Telegram 通知用的 Markdown 格式文字（含貼文 URL）。

    限制在 MAX_TELEGRAM_MESSAGE_LENGTH 字元內。

    Args:
        data: 完整的監控資料字典。

    Returns:
        str: 適合 Telegram 發送的 Markdown 文字（含 URL）。
    """
    posts = data.get("analyzed_posts", [])
    stats = data.get("stats", {})
    keywords = data.get("keywords", [])
    big_fish = identify_big_fish(posts)

    parts = []

    # Header
    parts.append("📊 *Threads 輿情戰報*")
    parts.append("")
    parts.append(f"掃描 {stats.get('total_searched', 'N/A')} 筆 → 有效 {len(posts)} 筆")
    parts.append(f"關鍵字: {', '.join(keywords)}")
    parts.append("")

    # Big fish
    if big_fish:
        parts.append(f"🚨 *發現 {len(big_fish)} 個重大議題*")
        parts.append("")
        for fish in big_fish:
            a = fish.get("analysis", {})
            link = fish.get("link", "")
            summary_text = a.get("summary", "")
            parts.append(f"*[{a.get('importance', '?')}/10]* {summary_text}")
            parts.append(f"[查看原文]({link})")
            parts.append("")

    # Other posts
    big_fish_ids = {f["id"] for f in big_fish}
    other_posts = [p for p in posts if p["id"] not in big_fish_ids]
    other_posts.sort(
        key=lambda p: p.get("analysis", {}).get("importance", 0), reverse=True
    )

    if other_posts:
        parts.append("📋 *其他重點*")
        parts.append("")
        current_text = "\n".join(parts)

        for post in other_posts:
            a = post.get("analysis", {})
            cats = a.get("categories", [])
            cat_label = "/".join(cats) if cats else "其他"
            summary_text = a.get("summary", post.get("content", "")[:40])
            link = post.get("link", "")
            entry = f"• [{cat_label}] {summary_text} [原文]({link})"

            if len(current_text) + len(entry) + 2 > MAX_TELEGRAM_MESSAGE_LENGTH - 30:
                parts.append("_...更多內容見完整報告_")
                break
            parts.append(entry)
            current_text = "\n".join(parts)

    return "\n".join(parts)


def save_report(report_content: str, reports_dir: str = DEFAULT_REPORTS_DIR,
                timestamp: Optional[str] = None) -> str:
    """
    將戰報儲存為 Markdown 檔案。

    Args:
        report_content: Markdown 格式的戰報內容。
        reports_dir: 儲存目錄。
        timestamp: 可選的時間戳（ISO 8601），預設使用當前時間。

    Returns:
        str: 儲存的檔案路徑。
    """
    os.makedirs(reports_dir, exist_ok=True)

    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            dt = datetime.now()
    else:
        dt = datetime.now()

    filename = f"report_{dt.strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info("報告已儲存: %s", filepath)
    return filepath


def generate_all_outputs(data: Dict, reports_dir: str = DEFAULT_REPORTS_DIR
                         ) -> Optional[Dict[str, str]]:
    """
    一次性生成所有輸出並儲存報告檔案。

    Args:
        data: 完整的監控資料字典。
        reports_dir: 報告儲存目錄。

    Returns:
        Dict[str, str] 或 None: 包含所有輸出的字典，資料無效時回傳 None。
    """
    valid, error = validate_monitoring_data(data)
    if not valid:
        logger.error("資料驗證失敗: %s", error)
        return None

    markdown_report = generate_markdown_report(data)
    line_summary = generate_line_summary(data)
    telegram_summary = generate_telegram_summary(data)

    report_path = save_report(
        markdown_report,
        reports_dir=reports_dir,
        timestamp=data.get("timestamp")
    )

    return {
        "report_path": report_path,
        "markdown_report": markdown_report,
        "line_summary": line_summary,
        "telegram_summary": telegram_summary,
    }


if __name__ == '__main__':
    import argparse
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description="戰報生成工具 - 從監控資料生成 Markdown 報告和通知摘要"
    )
    parser.add_argument("--input", help="JSON 輸入檔案路徑（省略則從 stdin 讀取）")
    parser.add_argument("--output-dir", default=DEFAULT_REPORTS_DIR, help="報告輸出目錄")
    parser.add_argument("--format", choices=["all", "markdown", "line", "telegram"],
                        default="all", dest="output_format", help="輸出格式")

    args = parser.parse_args()

    # Read JSON input
    try:
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = json.load(sys.stdin)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"錯誤: 無法讀取輸入資料 - {e}", file=sys.stderr)
        sys.exit(2)

    # Validate
    valid, error = validate_monitoring_data(data)
    if not valid:
        print(f"錯誤: 資料驗證失敗 - {error}", file=sys.stderr)
        sys.exit(1)

    # Generate
    if args.output_format == "line":
        print(generate_line_summary(data))
    elif args.output_format == "telegram":
        print(generate_telegram_summary(data))
    elif args.output_format == "markdown":
        report = generate_markdown_report(data)
        path = save_report(report, reports_dir=args.output_dir,
                           timestamp=data.get("timestamp"))
        print(f"報告已儲存: {path}")
    else:  # all
        outputs = generate_all_outputs(data, reports_dir=args.output_dir)
        if outputs:
            print(f"報告已儲存: {outputs['report_path']}")
            print()
            print("=== LINE 摘要 ===")
            print(outputs["line_summary"])
            print()
            print("=== Telegram 摘要 ===")
            print(outputs["telegram_summary"])
        else:
            print("錯誤: 生成報告失敗", file=sys.stderr)
            sys.exit(1)
