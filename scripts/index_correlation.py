#!/usr/bin/env python3
"""
指数相关性分析工具

比较两个指数过去一段时间的相关性（Pearson / Spearman / 滚动相关系数）。

用法：
  python scripts/index_correlation.py                              # 默认：上证 vs 纳指 近 1 年
  python scripts/index_correlation.py sh000001 .INX 180            # 上证 vs 标普 近 180 天
  python scripts/index_correlation.py --chart                      # 含图表
  python scripts/index_correlation.py 365 --chart                  # 指定天数 + 图表

A 股指数代码：sh000001(上证) sh000300(沪深300) sz399001(深证成指) sz399006(创业板指)
美股指数代码：.NDX(纳指100) .INX(标普500) .IXIC(纳斯达克综合) .DJI(道琼斯)
"""

import argparse
import sys
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from fund_analysis.config import INDEX_NAMES, setup_matplotlib
from fund_analysis.data.index import get_cn_index_data, get_index_data
from fund_analysis.plotting.style import HoverTool

CN_PREFIXES = ("sh", "sz")


def fetch_index(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    if symbol.startswith(CN_PREFIXES):
        return get_cn_index_data(symbol, start_date, end_date)
    return get_index_data(symbol, start_date, end_date)


def align_series(df_a: pd.DataFrame, df_b: pd.DataFrame, col_a: str, col_b: str):
    sa = df_a.set_index("date")[col_a].sort_index()
    sb = df_b.set_index("date")[col_b].sort_index()
    idx = sa.index.intersection(sb.index)
    return sa.loc[idx], sb.loc[idx]


def calc_correlation(returns_a: pd.Series, returns_b: pd.Series):
    mask = returns_a.notna() & returns_b.notna()
    a, b = returns_a[mask], returns_b[mask]
    pearson_r, pearson_p = stats.pearsonr(a, b)
    spearman_r, spearman_p = stats.spearmanr(a, b)
    return pearson_r, pearson_p, spearman_r, spearman_p


def rolling_corr(returns_a: pd.Series, returns_b: pd.Series, window: int):
    return returns_a.rolling(window).corr(returns_b)


def show_chart(price_a, price_b, name_a, name_b, roll30, roll60, days):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), height_ratios=[2, 1], sharex=True)

    norm_a = price_a / price_a.iloc[0] * 100
    norm_b = price_b / price_b.iloc[0] * 100
    dates = norm_a.index

    color_a, color_b = "#d62728", "#1f77b4"
    ax1.plot(dates, norm_a, color=color_a, linewidth=1.2, label=name_a)
    ax1.plot(dates, norm_b, color=color_b, linewidth=1.2, label=name_b)
    ax1.axhline(y=100, color="#888888", linestyle="--", linewidth=0.5)
    ax1.set_ylabel("归一化价格 (基准=100)")
    ax1.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax1.grid(True, alpha=0.2)

    def fmt_price(x, _):
        va = norm_a.get(x, np.nan)
        vb = norm_b.get(x, np.nan)
        return f"{x.strftime('%Y-%m-%d')}  {name_a}: {va:.2f}  {name_b}: {vb:.2f}"

    mid_y = (norm_a.min() + norm_a.max()) / 2
    HoverTool(fig, ax1, dates, [mid_y] * len(dates), fmt_func=fmt_price)

    ax2.plot(roll30.index, roll30, color="#ff7f0e", linewidth=1, label="滚动30天")
    ax2.plot(roll60.index, roll60, color="#2ca02c", linewidth=1, label="滚动60天")
    ax2.axhline(y=0, color="#888888", linestyle="-", linewidth=0.5)
    ax2.axhline(y=0.5, color="#888888", linestyle=":", linewidth=0.5)
    ax2.axhline(y=-0.5, color="#888888", linestyle=":", linewidth=0.5)
    ax2.set_ylabel("相关系数")
    ax2.set_ylim(-1.05, 1.05)
    ax2.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax2.grid(True, alpha=0.2)

    locator = mdates.AutoDateLocator()
    ax2.xaxis.set_major_locator(locator)
    ax2.xaxis.set_major_formatter(mdates.AutoDateFormatter(locator))
    ax2.tick_params(axis="x", rotation=45)

    fig.suptitle(f"{name_a} vs {name_b}  相关性分析（近 {days} 天）", fontsize=12)
    plt.tight_layout()
    plt.show()
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="指数相关性分析工具")
    parser.add_argument("params", nargs="*", help="symbol_a [symbol_b] [days]")
    parser.add_argument("--chart", action="store_true", help="生成图表")
    parsed = parser.parse_args()

    symbol_a = "sh000001"
    symbol_b = ".NDX"
    days = 365

    positional = []
    for a in parsed.params:
        if a.startswith(CN_PREFIXES) or a.startswith("."):
            positional.append(a)
        else:
            try:
                days = int(a)
            except ValueError:
                positional.append(a)

    if len(positional) >= 1:
        symbol_a = positional[0]
    if len(positional) >= 2:
        symbol_b = positional[1]
    chart = parsed.chart

    if chart:
        setup_matplotlib()

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    name_a = INDEX_NAMES.get(symbol_a, symbol_a)
    name_b = INDEX_NAMES.get(symbol_b, symbol_b)

    print(f"正在分析 {name_a} ({symbol_a}) vs {name_b} ({symbol_b}) 近 {days} 天的相关性...\n")

    print(f"[1/2] 获取 {name_a} 数据...")
    df_a = fetch_index(symbol_a, start_date, end_date)
    if df_a.empty:
        print(f"  ❌ {name_a} 无数据")
        sys.exit(1)
    print(f"  共 {len(df_a)} 条")

    print(f"[2/2] 获取 {name_b} 数据...")
    df_b = fetch_index(symbol_b, start_date, end_date)
    if df_b.empty:
        print(f"  ❌ {name_b} 无数据")
        sys.exit(1)
    print(f"  共 {len(df_b)} 条")

    price_a, price_b = align_series(df_a, df_b, "close", "close")
    if len(price_a) < 30:
        print("  ❌ 共同交易日不足 30 天，无法分析")
        sys.exit(1)

    returns_a = price_a.pct_change().dropna()
    returns_b = price_b.pct_change().dropna()

    pearson_r, pearson_p, spearman_r, spearman_p = calc_correlation(returns_a, returns_b)

    roll30 = rolling_corr(returns_a, returns_b, 30)
    roll60 = rolling_corr(returns_a, returns_b, 60)

    print(f"\n{'='*50}")
    print(f"  相关性分析结果")
    print(f"{'='*50}")
    print(f"  共同交易日:  {len(price_a)} 天")
    print(f"  分析区间:    {price_a.index[0].strftime('%Y-%m-%d')} ~ {price_a.index[-1].strftime('%Y-%m-%d')}")
    print()
    print(f"  日收益率 Pearson 相关系数:   {pearson_r:+.4f}  (p={pearson_p:.2e})")
    print(f"  日收益率 Spearman 相关系数:  {spearman_r:+.4f}  (p={spearman_p:.2e})")
    print()
    print(f"  滚动 30 天相关系数:  均值={roll30.dropna().mean():+.4f}  范围=[{roll30.dropna().min():+.4f}, {roll30.dropna().max():+.4f}]")
    print(f"  滚动 60 天相关系数:  均值={roll60.dropna().mean():+.4f}  范围=[{roll60.dropna().min():+.4f}, {roll60.dropna().max():+.4f}]")
    print(f"{'='*50}")

    if chart:
        show_chart(price_a, price_b, name_a, name_b, roll30, roll60, days)


if __name__ == "__main__":
    main()
