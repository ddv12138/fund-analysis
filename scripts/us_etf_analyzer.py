#!/usr/bin/env python3
"""
美股 ETF 回撤分析工具

用法：
  python scripts/us_etf_analyzer.py                    # 默认 QQQM 近 180 天
  python scripts/us_etf_analyzer.py QQQM 365           # 近 1 年
  python scripts/us_etf_analyzer.py QQQM 180 --chart   # 含回撤曲线图 + VIX
"""

import argparse
import sys
from datetime import datetime, timedelta

import pandas as pd

from fund_analysis.data.us_stock import get_us_stock_data, get_vix_data
from fund_analysis.data.index import get_index_data
from fund_analysis.analysis.drawdown import calculate_drawdown, drawdown_status, vix_status


def main():
    parser = argparse.ArgumentParser(description="美股回撤分析工具（ETF / 指数）")
    parser.add_argument("symbol", nargs="?", default="QQQM", help="代码，默认 QQQM")
    parser.add_argument("days", nargs="?", type=int, default=180, help="分析天数，默认 180")
    parser.add_argument("--chart", action="store_true", help="生成回撤曲线图")
    args = parser.parse_args()

    symbol = args.symbol
    days = args.days
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    print(f"正在获取 {symbol} 近 {days} 天的行情...")

    if symbol.startswith("."):
        df = get_index_data(symbol, start_date, end_date)
    else:
        df = get_us_stock_data(symbol, start_date, end_date)
    if df.empty:
        print("❌ 分析期内无数据")
        sys.exit(1)

    df = df.sort_values("date").reset_index(drop=True)

    dd_info = calculate_drawdown(df["close"])
    df["回撤(%)"] = dd_info["回撤(%)"]
    df["高点"] = dd_info["高点"]

    ath_idx = df["high"].idxmax()
    ath_value = df.loc[ath_idx, "high"]
    ath_date = df.loc[ath_idx, "date"]
    current_close = df["close"].iloc[-1]
    df["距 ATH(%)"] = (df["close"] - ath_value) / ath_value * 100
    current_dd = df["距 ATH(%)"].iloc[-1]

    print(f"\n正在获取 VIX 行情...")
    vix_df = get_vix_data(start_date, end_date)
    if vix_df.empty:
        print("❌ VIX 数据获取失败")
        sys.exit(1)
    current_vix = float(vix_df["close"].iloc[-1])
    vix_label = vix_status(current_vix)
    vix_aligned = pd.merge_asof(df[["date"]], vix_df, on="date", direction="backward")["close"]

    print(f"\n{'日期':<14} {'收盘':<10} {'回撤(%)':<10} {'距 ATH(%)':<10} {'VIX':<8}")
    print("-" * 54)
    for i, r in df.iterrows():
        d = r["date"].strftime("%Y-%m-%d")
        c = r["close"]
        dd_val = r["回撤(%)"]
        dd_str = f"{dd_val:.2f}" if pd.notna(dd_val) else "N/A"
        ath_diff = r["距 ATH(%)"]
        sign = "+" if pd.notna(ath_diff) and ath_diff >= 0 else ""
        ath_diff_str = f"{sign}{ath_diff:.2f}" if pd.notna(ath_diff) else "N/A"
        v = vix_aligned.iloc[i]
        vix_str = f"{v:.1f}" if pd.notna(v) else "N/A"
        print(f"{d:<14} {c:<10.2f} {dd_str:<10} {ath_diff_str:<10} {vix_str:<8}")

    need_up = abs(current_dd / (100 + current_dd) * 100) if current_dd < 0 else 0
    status = drawdown_status(current_dd)

    print(f"\n══════════════════════════════════════")
    print(f"  历史最高 (ATH): {ath_value:.2f}  ({ath_date.strftime('%Y-%m-%d')})")
    print(f"  最新收盘:      {current_close:.2f}  ({df['date'].iloc[-1].strftime('%Y-%m-%d')})")
    print(f"  距 ATH:        {current_dd:.2f}%")
    if need_up > 0:
        print(f"  需上涨:        {need_up:.2f}% 回到 ATH")
    print(f"  VIX 当前:      {current_vix:.1f}（{vix_label}）")
    print(f"  建议:          {status}")
    print(f"══════════════════════════════════════\n")

    if args.chart:
        from fund_analysis.config import setup_matplotlib
        from fund_analysis.plotting.drawdown_chart import show_drawdown_chart
        setup_matplotlib()
        show_drawdown_chart(df, symbol, vix_df=vix_df)


if __name__ == "__main__":
    main()
