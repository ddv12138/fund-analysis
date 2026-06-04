#!/usr/bin/env python3
"""
基金 vs 指数归一化对比工具

归一化对比：以起始日为基准 100，显示基金市场价 vs 纳指 100 指数的相对涨跌幅。

用法：
  python us_index_compare.py                           # 默认 513100 近 365 天
  python us_index_compare.py 180                       # 默认 513100 近 180 天
  python us_index_compare.py 365 513100 513500         # 两个基金近 365 天
  python us_index_compare.py 180 513500 --no-chart     # 仅打印表格
"""

import sys
from datetime import datetime, timedelta

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

import fund_premium_analyzer
import us_index

plt.rcParams["font.sans-serif"] = [
    "Songti SC", "Heiti TC", "PingFang HK", "Arial Unicode MS",
]
plt.rcParams["axes.unicode_minus"] = False

INDEX_SYMBOL = ".NDX"


def normalize(series: pd.Series) -> pd.Series:
    return series / series.iloc[0] * 100


def load_data(fund_codes, start_date, end_date):
    fund_data = {}
    for code in fund_codes:
        df = fund_premium_analyzer.get_market_price(code, start_date, end_date)
        if df.empty:
            print(f"  ⚠ {code} 无数据，跳过")
            continue
        series = df.set_index("日期")["市场价"].sort_index()
        fund_data[code] = series
        print(f"  {code}: {len(series)} 条")

    index_df = us_index.get_index_data(INDEX_SYMBOL, start_date, end_date)
    index_series = index_df.set_index("date")["close"].sort_index()
    print(f"  {INDEX_SYMBOL}: {len(index_series)} 条")

    return fund_data, index_series


def common_dates(*series_list):
    idx = series_list[0].index
    for s in series_list[1:]:
        idx = idx.intersection(s.index)
    return idx


def show_chart(fund_data, index_series, fund_codes):
    index_norm = normalize(index_series)
    fund_norm = {}
    for code in fund_codes:
        fund_norm[code] = normalize(fund_data[code])

    all_series = list(fund_norm.values()) + [index_norm]
    dates = common_dates(*all_series)

    fig, ax = plt.subplots(figsize=(10, 4))

    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    fund_lines = []
    for i, code in enumerate(fund_codes):
        s = fund_norm[code].loc[dates]
        line, = ax.plot(dates, s, color=colors[i % len(colors)], linewidth=1.2, label=code)
        fund_lines.append((code, s, line))
        ax.text(dates[-1], s.iloc[-1], f"  {s.iloc[-1]:.2f}", va="center", ha="left", fontsize=9, color=colors[i % len(colors)])

    i_s = index_norm.loc[dates]
    ax.plot(dates, i_s, color="gray", linewidth=1, linestyle="--", label=INDEX_SYMBOL, alpha=0.8)
    ax.text(dates[-1], i_s.iloc[-1], f"  {i_s.iloc[-1]:.2f}", va="center", ha="left", fontsize=9, color="gray")

    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)

    vline = ax.axvline(x=dates[0], linewidth=0.8, ls="--", alpha=0.6, visible=False, color="gray")
    hline = ax.axhline(y=100, linewidth=0.8, ls="--", alpha=0.6, visible=False, color="gray")
    label = ax.text(0, 0, "", fontsize=9, color="gray", visible=False,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="gray", alpha=0.8))
    dates_num = mdates.date2num(dates)

    def _on_move(event):
        if event.inaxes != ax:
            vline.set_visible(False)
            hline.set_visible(False)
            label.set_visible(False)
            fig.canvas.draw_idle()
            return
        idx = np.argmin(np.abs(dates_num - event.xdata))
        x = dates[idx]
        parts = [x.strftime("%Y-%m-%d")]
        y_vals = []
        for code in fund_codes:
            v = fund_norm[code].loc[x]
            parts.append(f"{code}: {v:.2f}")
            y_vals.append(v)
        parts.append(f"{INDEX_SYMBOL}: {index_norm.loc[x]:.2f}")
        y_vals.append(index_norm.loc[x])
        mid_y = (min(y_vals) + max(y_vals)) / 2
        vline.set_xdata([x, x])
        vline.set_visible(True)
        hline.set_ydata([mid_y, mid_y])
        hline.set_visible(True)
        label.set_text("  ".join(parts))
        label.set_position((event.xdata, mid_y))
        label.set_visible(True)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", _on_move)

    ax.grid(True, alpha=0.2)
    ax.axhline(y=100, color="#888888", linestyle="--", linewidth=0.5)
    ax.set_ylabel("归一化价格 (基准=100)")
    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(locator))
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    plt.show()
    plt.close()


def print_table(fund_data, index_series, fund_codes):
    index_norm = normalize(index_series)
    fund_norm = {}
    for code in fund_codes:
        fund_norm[code] = normalize(fund_data[code])

    all_series = list(fund_norm.values()) + [index_norm]
    dates = common_dates(*all_series)

    header = f"{'日期':<12}"
    sep = "-" * 12
    for code in fund_codes:
        header += f" {code:<10}"
        sep += f" {'-'*10:<10}"
    header += f" {INDEX_SYMBOL:<10}"
    sep += f" {'-'*10:<10}"
    print(f"\n{header}")
    print(sep)

    for dt in dates:
        line = f"{dt.strftime('%m-%d'):<12}"
        for code in fund_codes:
            line += f" {fund_norm[code].loc[dt]:<10.2f}"
        line += f" {index_norm.loc[dt]:<10.2f}"
        print(line)

    print(f"\n累计涨跌幅:")
    for code in fund_codes:
        chg = fund_norm[code].iloc[-1] - 100
        print(f"  {code}: {chg:+.2f}%")
    i_chg = index_norm.iloc[-1] - 100
    print(f"  {INDEX_SYMBOL}: {i_chg:+.2f}%")

    print(f"\n超额收益 (vs {INDEX_SYMBOL}):")
    for code in fund_codes:
        excess = (fund_norm[code].iloc[-1] - 100) - i_chg
        print(f"  {code}: {excess:+.2f}%")


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
        print_table(fund_data, index_series, valid_codes)
    else:
        show_chart(fund_data, index_series, valid_codes)
    print()


if __name__ == "__main__":
    main()
