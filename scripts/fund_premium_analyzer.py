#!/usr/bin/env python3
"""
场内基金溢价率分析工具
用法：
  python scripts/fund_premium_analyzer.py                    # 默认 513870 近1年
  python scripts/fund_premium_analyzer.py 513500 180
  python scripts/fund_premium_analyzer.py 513870 365 --chart
"""

import argparse
import sys
from datetime import datetime, timedelta

import pandas as pd

from fund_analysis.config import setup_matplotlib
from fund_analysis.data.fund import get_fund_name, get_market_price, get_nav
from fund_analysis.analysis.premium import calculate_premium
from fund_analysis.plotting.premium_chart import create_premium_figure, show_chart


def main():
    parser = argparse.ArgumentParser(description="场内基金溢价率分析工具")
    parser.add_argument("symbol", nargs="?", default="513870", help="基金代码，默认513870")
    parser.add_argument("days", nargs="?", type=int, default=365, help="分析天数，默认365")
    parser.add_argument("--chart", action="store_true", help="生成图表")
    args = parser.parse_args()

    if args.chart:
        setup_matplotlib()

    symbol = args.symbol
    days = args.days
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    print(f"正在分析 {symbol} 近 {days} 天的溢价率数据...")
    name = get_fund_name(symbol)
    print(f"基金名称: {name}\n")

    print("获取历史市场价...")
    market = get_market_price(symbol, start_date, end_date)

    print("获取历史净值...")
    nav = get_nav(symbol)
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    nav = nav[(nav["日期"] >= start_dt) & (nav["日期"] <= end_dt)]

    df = calculate_premium(market, nav)
    if df.empty:
        print("❌ 分析期内无数据")
        sys.exit(1)

    if args.chart:
        show_chart(df, symbol)
    else:
        print(f"\n{'日期':<12} {'市场价':<8} {'单位净值':<10} {'溢价率(%)':<10}")
        print("-" * 42)
        for _, r in df.iterrows():
            d = r["日期"].strftime("%m-%d")
            p = r["市场价"]
            n = r["单位净值"]
            pr = r["溢价率(%)"]
            print(f"{d:<12} {p:<8.3f} {n:<10.4f} {pr:<10.3f}")
        pr = df["溢价率(%)"]
        print(f"\n均值: {pr.mean():.2f}%  |  标准差: {pr.std():.2f}%  |  范围: {pr.min():.2f}% ~ {pr.max():.2f}%")
    print()


if __name__ == "__main__":
    main()
