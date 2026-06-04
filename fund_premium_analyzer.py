#!/usr/bin/env python3
"""
场内基金溢价率分析工具
用法：
  python fund_premium_analyzer.py                    # 默认分析 513870 近1年，打印每日数据
  python fund_premium_analyzer.py 513500 180         # 分析 513500 近180天
  python fund_premium_analyzer.py 513870 365 --chart  # 生成图表
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


def get_fund_name(symbol: str) -> str:
    """获取基金名称（全量缓存 ETF/LOF 行情数据）"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    etf_file = os.path.join(CACHE_DIR, "fund_etf_spot_em.csv")
    lof_file = os.path.join(CACHE_DIR, "fund_lof_spot_em.csv")

    def _find_name(df: pd.DataFrame) -> str | None:
        row = df[df["代码"] == symbol]
        return row.iloc[0]["名称"] if not row.empty else None

    # 优先从缓存的全量数据中查找
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

    # 请求 API 并缓存全量结果
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
    """获取历史市场价（收盘价），使用新浪财经数据源，带本地缓存"""
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_market.csv")
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    # 尝试读缓存
    cached = None
    if os.path.exists(cache_file):
        cached = pd.read_csv(cache_file, parse_dates=["日期"])
        if not cached.empty and cached["日期"].max() >= end_dt - pd.Timedelta(days=1):
            df = cached[(cached["日期"] >= start_dt) & (cached["日期"] <= end_dt)]
            if not df.empty:
                print(f"  [缓存] 市场价 {len(df)} 条")
                return df.reset_index(drop=True)

    # 请求新浪 API（全量历史）
    prefix = "sh" if symbol.startswith("5") else "sz"
    df = ak.fund_etf_hist_sina(symbol=f"{prefix}{symbol}")
    df = df.rename(columns={"date": "日期", "close": "市场价", "volume": "成交量", "amount": "成交额"})
    df["日期"] = pd.to_datetime(df["日期"])

    # 写缓存（全量）
    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(cache_file, index=False)
    print(f"  [网络] 市场价已缓存 {len(df)} 条")

    # 筛选日期区间
    df = df[(df["日期"] >= start_dt) & (df["日期"] <= end_dt)]
    return df.reset_index(drop=True)


def get_nav(symbol: str) -> pd.DataFrame:
    """获取历史单位净值，带本地缓存"""
    cache_file = os.path.join(CACHE_DIR, f"{symbol}_nav.csv")

    if os.path.exists(cache_file):
        cached = pd.read_csv(cache_file, parse_dates=["日期"])
        if not cached.empty:
            # 缓存文件在 3 天内创建过就直接用（QDII 净值有 T+2 延迟）
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


def calculate_premium(market: pd.DataFrame, nav: pd.DataFrame) -> pd.DataFrame:
    """
    合并计算溢价率（与同花顺一致）。
    QDII 基金净值公布有 T+2 延迟，交易日当天能拿到的最新净值是前一交易日的。
    同花顺用 T-1 净值计算溢价率，因此将 NAV 日期 +1 天后再 merge_asof。
    """
    market = market.sort_values("日期").reset_index(drop=True)
    nav = nav.sort_values("日期").reset_index(drop=True)
    # NAV 日期 +1 天，使得 merge_asof 匹配到前一交易日净值
    nav_shifted = nav.copy()
    nav_shifted["日期"] = nav_shifted["日期"] + pd.Timedelta(days=1)
    merged = pd.merge_asof(market, nav_shifted, on="日期", direction="backward")
    merged = merged.dropna(subset=["单位净值"]).reset_index(drop=True)
    merged["溢价率(%)"] = (
        (merged["市场价"] - merged["单位净值"]) / merged["单位净值"] * 100
    )
    return merged


def create_premium_figure(df: pd.DataFrame) -> plt.Figure:
    """生成溢价率趋势图，返回 Figure 对象（不弹窗）"""
    pr = df["溢价率(%)"]
    mean = pr.mean()
    dates = df["日期"]
    latest = pr.iloc[-1]

    fig, ax = plt.subplots(figsize=(10, 4))

    pr_max = pr.max()
    pr_min = pr.min()
    std = pr.std()
    upper = mean + std
    lower = mean - std

    ax.axhspan(pr_max, upper, color="#ffcccc", alpha=0.3)
    ax.axhspan(upper, lower, color="#ccffcc", alpha=0.3)
    ax.axhspan(lower, pr_min, color="#66cc66", alpha=0.3)

    ax.text(dates.max(), upper, f" {upper:.2f}%", va="center", ha="left", fontsize=9, color="#888888")
    ax.text(dates.max(), lower, f" {lower:.2f}%", va="center", ha="left", fontsize=9, color="#888888")

    legend_elements = [
        Patch(facecolor="#ffcccc", alpha=0.5, label="> 均值+σ"),
        Patch(facecolor="#ccffcc", alpha=0.5, label="均值±σ (适合买入)"),
        Patch(facecolor="#66cc66", alpha=0.5, label="< 均值-σ"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=8, framealpha=0.9)

    ax.plot(dates, pr, color="#1f77b4", linewidth=1.2)

    ax.axhline(y=mean, color="#ff7f0e", linestyle="--", linewidth=0.8)
    ax.text(dates.max(), mean, f" 均值 {mean:.2f}%", va="center", ha="left", fontsize=9, color="#ff7f0e")
    ax.axhline(y=upper, color="#ff7f0e", linestyle=":", linewidth=0.5)
    ax.axhline(y=lower, color="#ff7f0e", linestyle=":", linewidth=0.5)
    ax.axhline(y=latest, color="#d62728", linestyle="--", linewidth=0.6)
    ax.text(dates.max(), latest, f" 当前 {latest:.2f}%", va="center", ha="left", fontsize=9, color="#d62728")

    ax.grid(True, alpha=0.2)
    ax.set_xlim(dates.min(), dates.max())
    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(locator))
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    return fig


def show_chart(df: pd.DataFrame, symbol: str):
    """弹出窗口展示溢价率趋势图（交互式）"""
    pr = df["溢价率(%)"]
    dates = df["日期"]
    mean = pr.mean()
    std = pr.std()
    fig = create_premium_figure(df)
    ax = fig.axes[0]

    vline = ax.axvline(x=dates.iloc[0], color="gray", linewidth=0.8, ls="--", alpha=0.6, visible=False)
    hline = ax.axhline(y=pr.iloc[0], color="gray", linewidth=0.8, ls="--", alpha=0.6, visible=False)
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
        y = pr.iloc[idx]
        vline.set_xdata([x, x])
        vline.set_visible(True)
        hline.set_ydata([y, y])
        hline.set_visible(True)
        label.set_text(f"{x.strftime('%Y-%m-%d')}  {y:.2f}%")
        label.set_position((event.xdata, event.ydata))
        label.set_visible(True)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", _on_move)
    plt.show()
    plt.close()
    print(f"  均值: {mean:.2f}%  |  溢价率范围: {pr.min():.2f}% ~ {pr.max():.2f}%")


def main():
    parser = argparse.ArgumentParser(description="场内基金溢价率分析工具")
    parser.add_argument("symbol", nargs="?", default="513870", help="基金代码，默认513870")
    parser.add_argument("days", nargs="?", type=int, default=365, help="分析天数，默认365")
    parser.add_argument("--chart", action="store_true", help="生成图表")
    args = parser.parse_args()

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
