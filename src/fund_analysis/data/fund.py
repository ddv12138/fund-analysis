import os

import akshare as ak
import pandas as pd

from fund_analysis.config import CACHE_DIR


def get_fund_name(symbol: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    etf_file = os.path.join(CACHE_DIR, "fund_etf_spot_em.csv")
    lof_file = os.path.join(CACHE_DIR, "fund_lof_spot_em.csv")

    def _find_name(df: pd.DataFrame) -> str | None:
        row = df[df["代码"] == symbol]
        return row.iloc[0]["名称"] if not row.empty else None

    if os.path.exists(etf_file):
        df = pd.read_csv(etf_file, dtype={"代码": str})
        name = _find_name(df)
        if name:
            return name
    if os.path.exists(lof_file):
        df = pd.read_csv(lof_file, dtype={"代码": str})
        name = _find_name(df)
        if name:
            return name

    try:
        df = ak.fund_etf_spot_em()
        df["代码"] = df["代码"].astype(str)
        df.to_csv(etf_file, index=False)
        name = _find_name(df)
        if name:
            return name
    except Exception:
        pass
    try:
        df = ak.fund_lof_spot_em()
        df["代码"] = df["代码"].astype(str)
        df.to_csv(lof_file, index=False)
        name = _find_name(df)
        if name:
            return name
    except Exception:
        pass
    return symbol


def get_market_price(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_market.csv")
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    cached = None
    if os.path.exists(cache_file):
        cached = pd.read_csv(cache_file, parse_dates=["日期"])
        if not cached.empty and cached["日期"].max() >= end_dt - pd.Timedelta(days=1):
            df = cached[(cached["日期"] >= start_dt) & (cached["日期"] <= end_dt)]
            if not df.empty:
                print(f"  [缓存] 市场价 {len(df)} 条")
                return df.reset_index(drop=True)

    prefix = "sh" if symbol.startswith("5") else "sz"
    df = ak.fund_etf_hist_sina(symbol=f"{prefix}{symbol}")
    df = df.rename(columns={"date": "日期", "close": "市场价", "volume": "成交量", "amount": "成交额"})
    df["日期"] = pd.to_datetime(df["日期"])

    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(cache_file, index=False)
    print(f"  [网络] 市场价已缓存 {len(df)} 条")

    df = df[(df["日期"] >= start_dt) & (df["日期"] <= end_dt)]
    return df.reset_index(drop=True)


def get_nav(symbol: str) -> pd.DataFrame:
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_nav.csv")

    if os.path.exists(cache_file):
        cached = pd.read_csv(cache_file, parse_dates=["日期"])
        if not cached.empty:
            mtime = os.path.getmtime(cache_file)
            if (pd.Timestamp.now() - pd.Timestamp.fromtimestamp(mtime)).days <= 3:
                print(f"  [缓存] 净值 {len(cached)} 条")
                return cached

    df = ak.fund_open_fund_info_em(symbol=symbol, indicator="单位净值走势")
    df = df.rename(columns={"净值日期": "日期"})
    df["日期"] = pd.to_datetime(df["日期"])

    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(cache_file, index=False)
    print(f"  [网络] 净值已缓存 {len(df)} 条")

    return df
