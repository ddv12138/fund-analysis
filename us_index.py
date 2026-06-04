#!/usr/bin/env python3
"""
美股指数历史行情工具

用法：
  python us_index.py                    # 默认 .NDX 近 180 天
  python us_index.py .INX 365           # 标普 500 近 1 年
  python us_index.py .NDX 30 --chart    # 纳指 100 近 30 天图表

支持代码：.NDX 纳指 100 | .INX 标普 500 | .IXIC 纳斯达克综合 | .DJI 道琼斯
"""

import argparse
import os
import sys
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
import numpy as np

plt.rcParams["font.sans-serif"] = [
    "Noto Sans CJK JP", "Noto Sans CJK SC", "Noto Sans CJK",
    "Songti SC", "Heiti TC", "PingFang HK",
    "WenQuanYi Micro Hei", "SimHei", "Microsoft YaHei",
    "Arial Unicode MS",
]
plt.rcParams["axes.unicode_minus"] = False

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fund_cache")

INDEX_NAMES = {
    ".NDX": "纳斯达克100",
    ".INX": "标普500",
    ".IXIC": "纳斯达克综合",
    ".DJI": "道琼斯",
}


def get_index_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取美股指数历史行情，带本地缓存"""
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


def show_chart(df: pd.DataFrame, symbol: str):
    """弹出收盘价趋势图"""
    close = df["close"]
    mean = close.mean()
    std = close.std()
    upper = mean + std
    lower = mean - std
    dates = df["date"]
    latest = close.iloc[-1]

    fig, ax = plt.subplots(figsize=(10, 4))

    pr_max = close.max()
    pr_min = close.min()

    ax.axhspan(pr_max, upper, color="#ffcccc", alpha=0.3)
    ax.axhspan(upper, lower, color="#ccffcc", alpha=0.3)
    ax.axhspan(lower, pr_min, color="#66cc66", alpha=0.3)

    ax.text(dates.max(), upper, f" {upper:.0f}", va="center", ha="left", fontsize=9, color="#888888")
    ax.text(dates.max(), lower, f" {lower:.0f}", va="center", ha="left", fontsize=9, color="#888888")

    legend_elements = [
        Patch(facecolor="#ffcccc", alpha=0.5, label="> 均值+σ"),
        Patch(facecolor="#ccffcc", alpha=0.5, label="均值±σ"),
        Patch(facecolor="#66cc66", alpha=0.5, label="< 均值-σ"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=8, framealpha=0.9)

    ax.plot(dates, close, color="#1f77b4", linewidth=1.2)

    ax.axhline(y=mean, color="#ff7f0e", linestyle="--", linewidth=0.8)
    ax.text(dates.max(), mean, f" 均值 {mean:.0f}", va="center", ha="left", fontsize=9, color="#ff7f0e")
    ax.axhline(y=upper, color="#ff7f0e", linestyle=":", linewidth=0.5)
    ax.axhline(y=lower, color="#ff7f0e", linestyle=":", linewidth=0.5)

    ax.axhline(y=latest, color="#d62728", linestyle="--", linewidth=0.6)
    ax.text(dates.max(), latest, f" 当前 {latest:.0f}", va="center", ha="left", fontsize=9, color="#d62728")

    vline = ax.axvline(x=dates.iloc[0], color="gray", linewidth=0.8, ls="--", alpha=0.6, visible=False)
    hline = ax.axhline(y=close.iloc[0], color="gray", linewidth=0.8, ls="--", alpha=0.6, visible=False)
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
        x = dates.iloc[idx]
        y = close.iloc[idx]
        vline.set_xdata([x, x])
        vline.set_visible(True)
        hline.set_ydata([y, y])
        hline.set_visible(True)
        label.set_text(f"{x.strftime('%Y-%m-%d')}  {y:.0f}")
        label.set_position((event.xdata, event.ydata))
        label.set_visible(True)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", _on_move)

    ax.grid(True, alpha=0.2)
    ax.set_xlim(dates.min(), dates.max())
    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(locator))
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    plt.show()
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="美股指数历史行情工具")
    parser.add_argument("symbol", nargs="?", default=".NDX", help="指数代码，默认 .NDX")
    parser.add_argument("days", nargs="?", type=int, default=180, help="分析天数，默认 180")
    parser.add_argument("--chart", action="store_true", help="生成图表")
    args = parser.parse_args()

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
