#!/usr/bin/env python3
"""
溢价率监控告警脚本
读取环境变量 FUND_SYMBOLS 和 BARK_KEY，检查各基金溢价率数据并推送 Bark 通知。

用法:
    export FUND_SYMBOLS=513870,513100,513500
    export BARK_KEY=your_key_here
    python fund_alert.py                         # 正常执行
    python fund_alert.py --dry-run               # 仅打印，不推送
"""

import argparse
import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import requests

from fund_premium_analyzer import (
    get_fund_name,
    get_market_price,
    get_nav,
    calculate_premium,
)


def premium_status(premium: float, mean: float, std: float) -> str:
    if premium < mean - std:
        return "✅ 可买入"
    elif premium > mean + std:
        return "❌ 溢价偏高"
    else:
        return "⚠️ 正常波动"


def check_and_report(
    symbols: list[str],
    days: int,
    bark_key: str,
    dry_run: bool = False,
):
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    report_lines = []
    any_error = False

    for symbol in symbols:
        symbol = symbol.strip()
        if not symbol:
            continue

        print(f"\n{'='*40}")
        print(f"检查: {symbol}")
        print(f"{'='*40}")

        try:
            name = get_fund_name(symbol)
            print(f"基金名称: {name}")

            market = get_market_price(symbol, start_date, end_date)
            if market.empty:
                print(f"  ⚠ 无市场价数据，跳过")
                continue

            nav = get_nav(symbol)
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            nav = nav[(nav["日期"] >= start_dt) & (nav["日期"] <= end_dt)]

            df = calculate_premium(market, nav)
            if df.empty:
                print(f"  ⚠ 合并后无数据，跳过")
                continue

            latest = df.iloc[-1]
            latest_date = latest["日期"].strftime("%Y-%m-%d")
            latest_premium = latest["溢价率(%)"]
            latest_price = latest["市场价"]
            latest_nav = latest["单位净值"]

            pr = df["溢价率(%)"]
            mean = pr.mean()
            std = pr.std()
            buy_threshold = mean - std

            status_icon = premium_status(latest_premium, mean, std)

            print(f"  最新日期: {latest_date}")
            print(f"  最新溢价率: {latest_premium:.3f}%")
            print(f"  均值: {mean:.3f}%  |  标准差: {std:.3f}%")
            print(f"  买入区间(均值-标准差): < {buy_threshold:.3f}%")
            print(f"  状态: {status_icon}")

            report_lines.append(
                f"{name}({symbol})\n"
                f"溢价率 {latest_premium:.2f}% {status_icon}\n"
                f"买入区间: < {buy_threshold:.2f}%  "
                f"(均值 {mean:.2f}% - 标准差 {std:.2f}%)\n"
            )

        except Exception as e:
            print(f"  ❌ 检查 {symbol} 时出错: {e}")
            any_error = True
            continue

    if not report_lines:
        print(f"\n{'='*40}")
        print("所有基金均无数据")
        print(f"{'='*40}")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    title = f"📊 基金溢价率日报 ({today})"
    body = "\n".join(report_lines)

    if dry_run:
        print(f"\n{'='*40}")
        print(f"待推送通知 (DRY RUN - 未实际发送)")
        print(f"{'='*40}")
        print(f"标题: {title}")
        print(f"内容:\n{body}")
        return

    if not bark_key:
        print(f"\n❌ BARK_KEY 未配置，无法推送通知")
        print("请在 GitHub 仓库 Settings > Secrets > Actions 中添加 BARK_KEY")
        sys.exit(1)

    print(f"\n{'='*40}")
    print(f"推送 Bark 通知...")
    print(f"{'='*40}")

    try:
        resp = requests.post(
            f"https://api.day.app/{bark_key}",
            json={
                "title": title,
                "body": body,
                "group": "基金溢价率",
                "sound": "push.cat",
            },
            timeout=10,
        )
        resp.raise_for_status()
        print(f"  ✅ 推送成功")
    except Exception as e:
        print(f"  ❌ 推送失败: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="基金溢价率监控告警")
    parser.add_argument("--dry-run", action="store_true", help="仅打印结果，不推送通知")
    args = parser.parse_args()

    symbols_str = os.environ.get("FUND_SYMBOLS", "513870")
    symbols = [s.strip() for s in symbols_str.split(",") if s.strip()]
    bark_key = os.environ.get("BARK_KEY", "")

    if not symbols:
        print("❌ 未配置 FUND_SYMBOLS 环境变量")
        sys.exit(1)

    if args.dry_run:
        print(f"🔍 DRY RUN 模式 - 仅打印，不推送\n")

    check_and_report(symbols, days=365, bark_key=bark_key, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
