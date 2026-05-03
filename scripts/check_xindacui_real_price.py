"""Search Taiwan MOI real-price registry batch data for 新大萃 / 高鐵站前西路二段 / 青埔."""
import io
import re
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

BASE_URL = "https://plvr.land.moi.gov.tw/DownloadSeason"

KEYWORDS = [
    "新大萃",
    "高鐵站前西路二段",
    "青埔",
    "中壢區",
]

START_ROC_YEAR = 110
START_SEASON = 3


def current_roc_year() -> int:
    return datetime.now().year - 1911


def generate_seasons(start_year: int = 110, start_season: int = 3) -> list[str]:
    seasons: list[str] = []
    year_now = current_roc_year()
    for year in range(start_year, year_now + 1):
        for season in range(1, 5):
            if year == start_year and season < start_season:
                continue
            seasons.append(f"{year}S{season}")
    return seasons


def build_download_url(season: str) -> str:
    return (
        f"{BASE_URL}"
        f"?season={season}"
        f"&type=zip"
        f"&fileName=lvr_landcsv.zip"
    )


def download_zip(season: str, out_dir: Path) -> Path | None:
    out_dir.mkdir(parents=True, exist_ok=True)
    url = build_download_url(season)
    out_path = out_dir / f"{season}_lvr_landcsv.zip"
    if out_path.exists() and out_path.stat().st_size > 1000:
        return out_path
    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code != 200:
            return None
        content = resp.content
        if not content.startswith(b"PK"):
            return None
        out_path.write_bytes(content)
        return out_path
    except requests.RequestException:
        return None


def read_csv_safely(raw: bytes) -> pd.DataFrame | None:
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc, dtype=str)
        except Exception:
            continue
    return None


def read_all_csv_from_zip(zip_path: Path, season: str) -> pd.DataFrame:
    dfs = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if not name.lower().endswith((".csv", ".txt")):
                continue
            raw = zf.read(name)
            df = read_csv_safely(raw)
            if df is None or df.empty:
                continue
            df["資料季別"] = season
            df["來源檔案"] = name
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def row_text_blob(df: pd.DataFrame) -> pd.Series:
    return df.fillna("").astype(str).agg(" ".join, axis=1)


def search_keywords(df: pd.DataFrame, keywords: list[str]) -> pd.DataFrame:
    if df.empty:
        return df
    blob = row_text_blob(df)
    pattern = "|".join(re.escape(k) for k in keywords)
    mask = blob.str.contains(pattern, case=False, regex=True, na=False)
    return df.loc[mask].copy()


def add_cancel_detection(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    cancel_cols = [
        col for col in df.columns
        if any(k in str(col) for k in ["解約", "解除", "特殊", "備註", "交易備註"])
    ]
    df["疑似解約欄位"] = ", ".join(cancel_cols)
    if cancel_cols:
        df["疑似解約內容"] = (
            df[cancel_cols]
            .fillna("")
            .astype(str)
            .agg(" | ".join, axis=1)
        )
        df["是否疑似解約"] = df["疑似解約內容"].str.contains(
            "解約|解除", regex=True, na=False
        )
    else:
        df["疑似解約內容"] = ""
        df["是否疑似解約"] = False
    return df


def add_price_per_ping(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    price_col_candidates = ["單價元平方公尺", "單價元/平方公尺", "單價"]
    price_col = None
    for col in price_col_candidates:
        if col in df.columns:
            price_col = col
            break
    if price_col is None:
        df["推估單價_萬坪"] = ""
        return df
    numeric = (
        df[price_col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.extract(r"(\d+\.?\d*)")[0]
    )
    df["推估單價_萬坪"] = pd.to_numeric(numeric, errors="coerce") * 3.305785 / 10000
    df["推估單價_萬坪"] = df["推估單價_萬坪"].round(2)
    return df


def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    preferred = [
        "資料季別",
        "鄉鎮市區",
        "建案名稱",
        "土地位置建物門牌",
        "交易年月日",
        "總價元",
        "車位總價元",
        "單價元平方公尺",
        "推估單價_萬坪",
        "建物移轉總面積平方公尺",
        "交易標的",
        "交易筆棟數",
        "移轉層次",
        "總樓層數",
        "主要用途",
        "建物型態",
        "備註",
        "特殊交易備註",
        "解約日期",
        "解約情形",
        "是否疑似解約",
        "疑似解約內容",
        "來源檔案",
    ]
    cols = [c for c in preferred if c in df.columns]
    rest = [c for c in df.columns if c not in cols]
    return df[cols + rest]


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    raw_dir = project_root / "data" / "moi_lvr_raw"
    out_dir = project_root / "data" / "xindacui_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    seasons = generate_seasons(START_ROC_YEAR, START_SEASON)
    all_dfs = []

    print("開始下載內政部實價登錄批次資料...")
    for season in tqdm(seasons):
        zip_path = download_zip(season, raw_dir)
        if zip_path is None:
            continue
        df = read_all_csv_from_zip(zip_path, season)
        if not df.empty:
            all_dfs.append(df)

    if not all_dfs:
        print("沒有成功讀到任何資料。可能是內政部下載網址格式變更，或目前網路連線被擋。")
        return

    full_df = pd.concat(all_dfs, ignore_index=True)
    matched = search_keywords(full_df, KEYWORDS)
    matched = add_cancel_detection(matched)
    matched = add_price_per_ping(matched)
    matched = reorder_columns(matched)

    output_csv = out_dir / "新大萃_實價登錄_解約檢查.csv"
    matched.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print("\n========== 搜尋結果 ==========")
    print(f"關鍵字：{', '.join(KEYWORDS)}")
    print(f"總讀取筆數：{len(full_df)}")
    print(f"找到筆數：{len(matched)}")
    if "是否疑似解約" in matched.columns:
        print(f"疑似解約筆數：{int(matched['是否疑似解約'].sum())}")
    print(f"輸出檔案：{output_csv.resolve()}")

    if len(matched) > 0:
        preview_cols = [
            c for c in [
                "資料季別",
                "鄉鎮市區",
                "建案名稱",
                "土地位置建物門牌",
                "交易年月日",
                "總價元",
                "車位總價元",
                "推估單價_萬坪",
                "是否疑似解約",
                "解約日期",
                "解約情形",
                "備註",
                "來源檔案",
            ]
            if c in matched.columns
        ]
        print("\n前 20 筆預覽：")
        print(matched[preview_cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
