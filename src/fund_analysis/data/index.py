import os

import akshare as ak
import pandas as pd

from fund_analysis.config import CACHE_DIR


def get_index_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    cache_file = os.path.join(CACHE_DIR, f"{symbol[1:]}_index.csv")
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    if os.path.exists(cache_file):
        cached = pd.read_csv(cache_file, parse_dates=["date"])
        if not cached.empty and cached["date"].max() >= end_dt - pd.Timedelta(days=1):
            df = cached[(cached["date"] >= start_dt) & (cached["date"] <= end_dt)]
            if not df.empty:
                print(f"  [缓存] {len(df)} 条")
                return df.reset_index(drop=True)

    df = ak.index_us_stock_sina(symbol=symbol)
    df["date"] = pd.to_datetime(df["date"])

    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(cache_file, index=False)
    print(f"  [网络] 已缓存 {len(df)} 条")

    df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]
    return df.reset_index(drop=True)
