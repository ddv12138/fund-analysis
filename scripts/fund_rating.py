#!/usr/bin/env python3
"""
基金评级工具
从资金规模、成立时间、管理费率、溢价偏离度四个维度对基金进行评分排名。

用法：
  python scripts/fund_rating.py                              # 默认 FUND_SYMBOLS
  python scripts/fund_rating.py --symbols 513870,513100      # 指定基金
"""

import argparse
import os
import sys
from datetime import datetime, timedelta


def _visual_len(s: str) -> int:
    return sum(2 if ord(c) > 0x2e80 else 1 for c in s)


def _pad(s: str, width: int) -> str:
    return s + ' ' * max(0, width - _visual_len(s))

import pandas as pd

from fund_analysis.data.fund import get_fund_name, get_fund_overview, get_market_price, get_nav
from fund_analysis.analysis.premium import calculate_premium
from fund_analysis.analysis.rating import (
    rank_score, parse_scale, parse_fee, parse_total_fee, parse_est_date,
    score_premium, calculate_rating,
)


def main():
    parser = argparse.ArgumentParser(description="基金评级工具")
    parser.add_argument("--symbols", help="基金代码，逗号分隔")
    args = parser.parse_args()

    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols_str = os.environ.get("FUND_SYMBOLS", "513100,159660,159501,159941,159509,513300,513870,159696")
        symbols = [s.strip() for s in symbols_str.split(",") if s.strip()]

    if not symbols:
        print("❌ 未指定基金代码")
        sys.exit(1)

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

    records = []

    for symbol in symbols:
        print(f"正在获取 {symbol} ...")
        try:
            name = get_fund_name(symbol)
            overview = get_fund_overview(symbol)
            if not overview:
                print(f"  ⚠ 无法获取概览，跳过")
                continue

            scale_str = overview.get("净资产规模", "")
            scale_val = parse_scale(scale_str)
            fee_val = parse_total_fee(overview.get("管理费率", ""), overview.get("托管费率", ""))
            est_str = parse_est_date(overview.get("成立日期/规模", ""))

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
                print(f"  ⚠ 溢价率无数据，跳过")
                continue

            latest = df.iloc[-1]["溢价率(%)"]
            pr = df["溢价率(%)"]
            mean = pr.mean()
            std = pr.std()

            records.append({
                "symbol": symbol,
                "name": name,
                "scale_val": scale_val,
                "fee_val": fee_val,
                "est_str": est_str,
                "premium": latest,
                "mean": mean,
                "std": std,
            })
        except Exception as e:
            print(f"  ❌ 获取 {symbol} 出错: {e}")
            continue

    if not records:
        print("\n无有效数据")
        sys.exit(1)

    # 排名评分
    scale_scores = rank_score([r["scale_val"] for r in records], reverse=True)
    fee_scores = rank_score([r["fee_val"] for r in records], reverse=False)
    est_scores = rank_score([r["est_str"] for r in records], reverse=False)
    premium_scores = [score_premium(r["premium"], r["mean"], r["std"]) for r in records]

    for i, r in enumerate(records):
        total = calculate_rating(scale_scores[i], est_scores[i], fee_scores[i], premium_scores[i])
        r["scale_score"] = scale_scores[i]
        r["fee_score"] = fee_scores[i]
        r["est_score"] = est_scores[i]
        r["premium_score"] = premium_scores[i]
        r["total"] = total

    # 按总分降序排列
    records.sort(key=lambda r: r["total"], reverse=True)

    # 输出表格
    def _est_short(s: str) -> str:
        parts = s.replace("年", "-").replace("月", "-").replace("日", "").split("-")
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[1]}"
        return s[:7]

    cols_def = [("代码", 8), ("名称", 14), ("规模", 18), ("总费率", 14),
                ("成立", 14), ("溢价率", 10), ("溢价状态", 16), ("总分", 6)]

    header_line = "  ".join(_pad(h, w) for h, w in cols_def)
    sep = "  ".join(_pad("", w).replace(" ", "-") for _, w in cols_def)
    print(f"\n{header_line}\n{sep}")

    for r in records:
        if r["premium_score"] == 5:
            status = "✅ 深度折价"
        elif r["premium_score"] == 4:
            status = "🟢 折价区间"
        elif r["premium_score"] == 3:
            status = "✅ 正常区间"
        elif r["premium_score"] == 2:
            status = "🟡 轻度溢价"
        else:
            status = "🔴 溢价偏高"

        row = [
            r["symbol"],
            r["name"],
            f"{r['scale_val']:.2f}亿 {r['scale_score']}/5",
            f"{r['fee_val']:.2f}% {r['fee_score']}/5",
            f"{_est_short(r['est_str'])} {r['est_score']}/5",
            f"{r['premium']:.2f}%",
            status,
            f"{r['total']:.2f}",
        ]
        print("  ".join(_pad(c, w) for c, w in zip(row, [w for _, w in cols_def])))


if __name__ == "__main__":
    main()
