#!/usr/bin/env python3
"""
基金 vs 指数归一化对比工具

用法：
  python scripts/us_index_compare.py                           # 默认 513100 近 365 天
  python scripts/us_index_compare.py 180                       # 默认 513100 近 180 天
  python scripts/us_index_compare.py 365 513100 513500         # 两个基金
  python scripts/us_index_compare.py 180 513500 --no-chart     # 仅打印表格
"""

import sys
from datetime import datetime, timedelta

from fund_analysis.config import setup_matplotlib
from fund_analysis.data.fund import get_market_price
from fund_analysis.data.index import get_index_data
from fund_analysis.plotting.compare_chart import show_compare_chart, print_compare_table

INDEX_SYMBOL = ".NDX"


def load_data(fund_codes, start_date, end_date):
    fund_data = {}
    for code in fund_codes:
        df = get_market_price(code, start_date, end_date)
        if df.empty:
            print(f"  ⚠ {code} 无数据，跳过")
            continue
        series = df.set_index("日期")["市场价"].sort_index()
        fund_data[code] = series
        print(f"  {code}: {len(series)} 条")

    index_df = get_index_data(INDEX_SYMBOL, start_date, end_date)
    index_series = index_df.set_index("date")["close"].sort_index()
    print(f"  {INDEX_SYMBOL}: {len(index_series)} 条")

    return fund_data, index_series


def parse_args():
    raw = [a for a in sys.argv[1:] if a != "--no-chart"]
    no_chart = "--no-chart" in sys.argv[1:]

    days = 365
    fund_codes = ["513100"]

    if raw:
        try:
            val = int(raw[0])
            if val < 10000:
                days = val
                raw = raw[1:]
        except ValueError:
            pass
        if raw:
            fund_codes = raw

    return days, fund_codes, no_chart


def main():
    days, fund_codes, no_chart = parse_args()

    if not no_chart:
        setup_matplotlib()

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    names = ", ".join(fund_codes)
    print(f"正在分析 [{names}] vs {INDEX_SYMBOL} 近 {days} 天的数据...\n")

    fund_data, index_series = load_data(fund_codes, start_date, end_date)
    valid_codes = [c for c in fund_codes if c in fund_data]
    if not valid_codes or index_series.empty:
        print("❌ 数据不足，无法对比")
        sys.exit(1)

    if no_chart:
        print_compare_table(fund_data, index_series, valid_codes)
    else:
        show_compare_chart(fund_data, index_series, valid_codes)
    print()


if __name__ == "__main__":
    main()
