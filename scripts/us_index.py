#!/usr/bin/env python3
"""
美股指数历史行情工具

用法：
  python scripts/us_index.py                    # 默认 .NDX 近 180 天
  python scripts/us_index.py .INX 365           # 标普 500 近 1 年
  python scripts/us_index.py .NDX 30 --chart    # 纳指 100 近 30 天图表

支持代码：.NDX 纳指 100 | .INX 标普 500 | .IXIC 纳斯达克综合 | .DJI 道琼斯
"""

import argparse
import sys
from datetime import datetime, timedelta

import pandas as pd

from fund_analysis.config import setup_matplotlib, INDEX_NAMES
from fund_analysis.data.index import get_index_data
from fund_analysis.plotting.index_chart import show_chart


def main():
    parser = argparse.ArgumentParser(description="美股指数历史行情工具")
    parser.add_argument("symbol", nargs="?", default=".NDX", help="指数代码，默认 .NDX")
    parser.add_argument("days", nargs="?", type=int, default=180, help="分析天数，默认 180")
    parser.add_argument("--chart", action="store_true", help="生成图表")
    args = parser.parse_args()

    if args.chart:
        setup_matplotlib()

    symbol = args.symbol
    days = args.days
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    name = INDEX_NAMES.get(symbol, symbol)
    print(f"正在获取 {name} ({symbol}) 近 {days} 天的行情...")

    df = get_index_data(symbol, start_date, end_date)
    if df.empty:
        print("❌ 分析期内无数据")
        sys.exit(1)

    df = df.sort_values("date").reset_index(drop=True)
    df["涨跌幅(%)"] = df["close"].pct_change() * 100

    if args.chart:
        show_chart(df, symbol)
    else:
        print(f"\n{'日期':<14} {'收盘':<12} {'涨跌幅(%)':<12}")
        print("-" * 40)
        for _, r in df.iterrows():
            d = r["date"].strftime("%Y-%m-%d")
            c = r["close"]
            chg = r["涨跌幅(%)"]
            sign = "+" if chg is not None and chg >= 0 else ""
            chg_str = f"{sign}{chg:.2f}" if pd.notna(chg) else "N/A"
            print(f"{d:<14} {c:<12.2f} {chg_str:<12}")
        print(f"\n均值: {df['close'].mean():.2f}  |  范围: {df['close'].min():.2f} ~ {df['close'].max():.2f}")
    print()


if __name__ == "__main__":
    main()
