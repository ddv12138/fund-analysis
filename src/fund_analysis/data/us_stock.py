import os
import time

import akshare as ak
import pandas as pd

from fund_analysis.config import CACHE_DIR


def get_us_stock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_us_stock.csv")
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    if os.path.exists(cache_file):
        cached = pd.read_csv(cache_file, parse_dates=["date"])
        if not cached.empty and cached["date"].max() >= end_dt - pd.Timedelta(days=1):
            df = cached[(cached["date"] >= start_dt) & (cached["date"] <= end_dt)]
            if not df.empty:
                print(f"  [缓存] {len(df)} 条")
                return df.reset_index(drop=True)

    df = ak.stock_us_daily(symbol=symbol)
    df["date"] = pd.to_datetime(df["date"])

    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(cache_file, index=False)
    print(f"  [网络] 已缓存 {len(df)} 条")

    df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]
    return df.reset_index(drop=True)


def get_vix_data(start_date: str, end_date: str) -> pd.DataFrame:
    cache_file = os.path.join(CACHE_DIR, "VIX_us_stock.csv")
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    cached_all = None
    if os.path.exists(cache_file):
        cached_all = pd.read_csv(cache_file, parse_dates=["date"])
        cached_all = cached_all.sort_values("date").reset_index(drop=True)
        if not cached_all.empty and cached_all["date"].max() >= end_dt - pd.Timedelta(days=3):
            df = cached_all[(cached_all["date"] >= start_dt) & (cached_all["date"] <= end_dt)]
            if not df.empty:
                print(f"  [缓存] VIX {len(df)} 条")
                return df.reset_index(drop=True)

    import requests
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        print("  ⚠ 环境变量 FRED_API_KEY 未设置")
        return pd.DataFrame(columns=["date", "close"])

    time.sleep(1)
    url = "https://api.stlouisfed.org/fred/series/observations"

    if cached_all is not None and not cached_all.empty:
        need_start = (cached_all["date"].max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        need_start = start_dt.strftime("%Y-%m-%d")
    need_end = end_dt.strftime("%Y-%m-%d")

    params = {
        "series_id": "VIXCLS",
        "api_key": api_key,
        "file_type": "json",
        "observation_start": need_start,
        "observation_end": need_end,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("observations", [])
    except Exception as e:
        print(f"  ⚠ VIX 获取失败: {e}")
        return pd.DataFrame(columns=["date", "close"])

    if not data:
        if cached_all is not None:
            df = cached_all[(cached_all["date"] >= start_dt) & (cached_all["date"] <= end_dt)]
            if not df.empty:
                print(f"  [缓存] VIX {len(df)} 条（无新数据）")
                return df.reset_index(drop=True)
        print("  ⚠ VIX 暂无数据")
        return pd.DataFrame(columns=["date", "close"])

    new_df = pd.DataFrame(data)
    new_df = new_df[new_df["value"] != "."].copy()
    new_df["date"] = pd.to_datetime(new_df["date"])
    new_df["close"] = new_df["value"].astype(float)
    new_df = new_df[["date", "close"]].reset_index(drop=True)

    if cached_all is not None and not cached_all.empty:
        merged = pd.concat([cached_all, new_df], ignore_index=True)
        merged = merged.drop_duplicates(subset="date", keep="last").sort_values("date").reset_index(drop=True)
    else:
        merged = new_df

    os.makedirs(CACHE_DIR, exist_ok=True)
    merged.to_csv(cache_file, index=False)
    print(f"  [网络] VIX 增量更新 {len(new_df)} 条，总计 {len(merged)} 条")

    merged = merged[(merged["date"] >= start_dt) & (merged["date"] <= end_dt)]
    return merged.reset_index(drop=True)
