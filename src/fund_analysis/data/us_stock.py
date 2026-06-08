import os

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

    import yfinance as yf
    need_start = (
        (cached_all["date"].max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        if cached_all is not None and not cached_all.empty
        else start_dt.strftime("%Y-%m-%d")
    )
    need_end = end_dt.strftime("%Y-%m-%d")

    try:
        vix = yf.download("^VIX", start=need_start, end=need_end, progress=False)
    except Exception as e:
        print(f"  ⚠ VIX 获取失败: {e}")
        if cached_all is not None:
            df = cached_all[(cached_all["date"] >= start_dt) & (cached_all["date"] <= end_dt)]
            if not df.empty:
                print(f"  [缓存] VIX {len(df)} 条（回退缓存）")
                return df.reset_index(drop=True)
        return pd.DataFrame(columns=["date", "close"])

    if vix.empty:
        if cached_all is not None:
            df = cached_all[(cached_all["date"] >= start_dt) & (cached_all["date"] <= end_dt)]
            if not df.empty:
                print(f"  [缓存] VIX {len(df)} 条（无新数据）")
                return df.reset_index(drop=True)
        print("  ⚠ VIX 暂无数据")
        return pd.DataFrame(columns=["date", "close"])

    new_df = vix.reset_index()
    new_df.columns = new_df.columns.map(lambda c: c[0] if isinstance(c, tuple) else c)
    new_df = new_df[["Date", "Close"]].rename(columns={"Date": "date", "Close": "close"})

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
