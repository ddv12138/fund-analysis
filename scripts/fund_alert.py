#!/usr/bin/env python3
"""
溢价率监控告警脚本
读取环境变量，检查各基金溢价率数据并通过 SMTP 邮件推送日报（含趋势图表）。

用法:
    export FUND_SYMBOLS=513870,513100,513500
    export SMTP_HOST=smtp.qq.com
    export SMTP_PORT=465
    export SMTP_USER=xxx@qq.com
    export SMTP_PASS=授权码
    export MAIL_TO=xxx@qq.com,yyy@qq.com
    python scripts/fund_alert.py                         # 正常执行
    python scripts/fund_alert.py --dry-run               # 仅打印，不推送
"""

import argparse
import os
import sys
from datetime import datetime, timedelta

import pandas as pd

from fund_analysis.config import setup_matplotlib
from fund_analysis.data.fund import get_fund_name, get_fund_overview, get_market_price, get_nav
from fund_analysis.data.index import get_index_data
from fund_analysis.data.us_stock import get_vix_data
from fund_analysis.analysis.premium import calculate_premium, premium_status
from fund_analysis.analysis.drawdown import calculate_drawdown, drawdown_status, vix_status
from fund_analysis.analysis.rating import (
    rank_score, parse_scale, parse_total_fee, parse_est_date,
    score_premium, calculate_rating,
)
from fund_analysis.plotting.premium_chart import create_premium_figure
from fund_analysis.plotting.drawdown_chart import create_drawdown_figure
from fund_analysis.utils.mail_utils import fig_to_base64, read_smtp_config_from_env, send_mail

setup_matplotlib("Agg")


def build_overview_html(info: dict) -> str:
    if not info:
        return ""
    mgmt = info.get("管理费率", "")
    trustee = info.get("托管费率", "")
    scale = info.get("净资产规模", "")
    est = info.get("成立日期/规模", "").split(" / ")[0] if " / " in str(info.get("成立日期/规模", "")) else info.get("成立日期/规模", "")
    parts = [f"管理费 {mgmt}"]
    if trustee:
        parts.append(f"托管费 {trustee}")
    if scale:
        parts.append(f"净资产 {scale}")
    if est:
        parts.append(f"成立 {est}")
    return f'<p style="font-size:12px;color:#666">{" | ".join(parts)}</p>'


def build_html_report(results: list[dict]) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    parts = [f"<h2>📊 基金溢价率日报 ({today})</h2><hr>"]

    for r in results:
        parts.append(f"<h3>{r['name']}({r['symbol']})</h3>")
        parts.append(build_overview_html(r.get("overview", {})))
        parts.append(
            f"<p>溢价率: {r['premium']:.2f}% {r['status']}</p>"
            f"<p>合理区间: {r['lower_bound']:.2f}% ~ {r['upper_bound']:.2f}% "
            f"(均值 {r['mean']:.2f}% - 标准差 {r['std']:.2f}%)</p>"
        )
        parts.append(f'<img src="data:image/png;base64,{r["chart_base64"]}" style="max-width:100%"><hr>')

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="基金溢价率监控告警")
    parser.add_argument("--dry-run", action="store_true", help="仅打印结果，不推送通知")
    args = parser.parse_args()

    symbols_str = os.environ.get("FUND_SYMBOLS", "513100,159660,159501,159941,159509,513300,513870,159696")
    symbols = [s.strip() for s in symbols_str.split(",") if s.strip()]
    mail_to_str = os.environ.get("MAIL_TO", "")
    recipients = [r.strip() for r in mail_to_str.split(",") if r.strip()]

    smtp_config = read_smtp_config_from_env()

    if not symbols:
        print("❌ 未配置 FUND_SYMBOLS 环境变量")
        sys.exit(1)

    if args.dry_run:
        print(f"🔍 DRY RUN 模式 - 仅打印，不推送\n")

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

    results = []

    for symbol in symbols:
        print(f"\n{'='*40}")
        print(f"检查: {symbol}")
        print(f"{'='*40}")

        try:
            name = get_fund_name(symbol)
            print(f"基金名称: {name}")

            overview = get_fund_overview(symbol)
            if overview:
                mgmt = overview.get("管理费率", "")
                scale = overview.get("净资产规模", "")
                est = str(overview.get("成立日期/规模", "")).split(" / ")[0] if " / " in str(overview.get("成立日期/规模", "")) else overview.get("成立日期/规模", "")
                print(f"  概览: 管理费 {mgmt} | 规模 {scale} | 成立 {est}")

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
            latest_premium = latest["溢价率(%)"]
            pr = df["溢价率(%)"]
            mean = pr.mean()
            std = pr.std()
            lower_bound = max(mean - std, 0)
            upper_bound = min(mean + std, mean * 1.5)
            status = premium_status(latest_premium, mean, std)

            fig = create_premium_figure(df)
            chart_b64 = fig_to_base64(fig)

            print(f"  最新溢价率: {latest_premium:.3f}%")
            print(f"  均值: {mean:.3f}%  |  标准差: {std:.3f}%")
            print(f"  合理区间: {lower_bound:.3f}% ~ {upper_bound:.3f}%")
            print(f"  状态: {status}")

            results.append({
                "symbol": symbol,
                "name": name,
                "premium": latest_premium,
                "mean": mean,
                "std": std,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "status": status,
                "chart_base64": chart_b64,
                "overview": overview,
            })

        except Exception as e:
            print(f"  ❌ 检查 {symbol} 时出错: {e}")
            continue

    if not results:
        print(f"\n{'='*40}")
        print("所有基金均无数据")
        print(f"{'='*40}")

    print(f"\n{'='*40}")
    print("生成纳指100回撤分析")
    print(f"{'='*40}")

    ndx_html = ""
    try:
        end_dt = datetime.now().strftime("%Y%m%d")
        start_dt = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        ndx_df = get_index_data(".NDX", start_dt, end_dt)
        if not ndx_df.empty:
            ndx_df = ndx_df.sort_values("date").reset_index(drop=True)
            dd_info = calculate_drawdown(ndx_df["close"])
            ndx_df["回撤(%)"] = dd_info["回撤(%)"]
            current_dd = (ndx_df["close"].iloc[-1] - ndx_df["high"].max()) / ndx_df["high"].max() * 100
            status_text = drawdown_status(current_dd)
            vix_df = get_vix_data(start_dt, end_dt)
            if not vix_df.empty:
                current_vix = float(vix_df["close"].iloc[-1])
                vix_text = vix_status(current_vix)
            else:
                current_vix = None
                vix_text = "N/A"
            fig = create_drawdown_figure(ndx_df, ".NDX", vix_df=vix_df)
            chart_b64 = fig_to_base64(fig)
            vix_line = f"VIX: {current_vix:.1f}（{vix_text}）" if current_vix is not None else "VIX: N/A"
            ndx_html = f"""
<hr>
<h2>🇺🇸 纳指100回撤分析 (.NDX)</h2>
<p>距 ATH: {current_dd:.2f}% {status_text}</p>
<p>{vix_line}</p>
<img src="data:image/png;base64,{chart_b64}" style="max-width:100%">"""
            print(f"  ✅ 纳指100回撤分析完成")
    except Exception as e:
        print(f"  ⚠ 纳指100分析失败: {e}")

    print(f"\n{'='*40}")
    print("生成基金评级排名")
    print(f"{'='*40}")

    rating_html = ""
    try:
        rating_records = []
        for r in results:
            ov = r.get("overview", {})
            rating_records.append({
                "name": r["name"],
                "symbol": r["symbol"],
                "scale_val": parse_scale(ov.get("净资产规模", "")),
                "fee_val": parse_total_fee(ov.get("管理费率", ""), ov.get("托管费率", "")),
                "est_str": parse_est_date(ov.get("成立日期/规模", "")),
                "premium": r["premium"],
                "mean": r["mean"],
                "std": r["std"],
            })

        scale_scores = rank_score([x["scale_val"] for x in rating_records], reverse=True)
        fee_scores = rank_score([x["fee_val"] for x in rating_records], reverse=False)
        est_scores = rank_score([x["est_str"] for x in rating_records], reverse=False)
        premium_scores = [score_premium(x["premium"], x["mean"], x["std"]) for x in rating_records]

        for i, x in enumerate(rating_records):
            x["total"] = calculate_rating(scale_scores[i], est_scores[i], fee_scores[i], premium_scores[i])
            x["scale_score"] = scale_scores[i]
            x["fee_score"] = fee_scores[i]
            x["est_score"] = est_scores[i]
            x["premium_score"] = premium_scores[i]

        rating_records.sort(key=lambda x: x["total"], reverse=True)

        rows_html = []
        for x in rating_records:
            s_star = "★" * x["scale_score"] + "☆" * (5 - x["scale_score"])
            f_star = "★" * x["fee_score"] + "☆" * (5 - x["fee_score"])
            rows_html.append(f"""<tr>
<td style="padding:3px 8px;border:1px solid #ddd">{x['symbol']}</td>
<td style="padding:3px 8px;border:1px solid #ddd">{x['name']}</td>
<td style="padding:3px 8px;border:1px solid #ddd">{s_star} {x['scale_val']:.2f}亿</td>
<td style="padding:3px 8px;border:1px solid #ddd">{f_star} {x['fee_val']:.2f}%</td>
<td style="padding:3px 8px;border:1px solid #ddd">{x['total']:.2f}</td>
</tr>""")

        rating_html = f"""
<hr>
<h2>📋 基金评级排名</h2>
<table style="border-collapse:collapse;width:100%;font-size:12px">
<tr style="background:#f5f5f5">
<th style="padding:4px 8px;border:1px solid #ddd;text-align:left">代码</th>
<th style="padding:4px 8px;border:1px solid #ddd;text-align:left">名称</th>
<th style="padding:4px 8px;border:1px solid #ddd;text-align:left">规模</th>
<th style="padding:4px 8px;border:1px solid #ddd;text-align:left">总费率</th>
<th style="padding:4px 8px;border:1px solid #ddd;text-align:left">总分</th>
</tr>
{''.join(rows_html)}
</table>"""
        print(f"  ✅ 基金评级排名完成")
    except Exception as e:
        print(f"  ⚠ 基金评级失败: {e}")

    html = build_html_report(results) + ndx_html + rating_html

    if args.dry_run:
        print(f"\n{'='*40}")
        print(f"待推送邮件 (DRY RUN - 未实际发送)")
        print(f"{'='*40}")
        for r in results:
            print(f"  {r['name']}({r['symbol']}) 溢价率 {r['premium']:.2f}% {r['status']}")
            print(f"  合理区间: {r['lower_bound']:.2f}% ~ {r['upper_bound']:.2f}%")
        return

    if not smtp_config["user"] or not smtp_config["pass"]:
        print("\n❌ SMTP 配置不完整，请设置 SMTP_USER / SMTP_PASS 环境变量")
        sys.exit(1)

    if not recipients:
        print("\n❌ 未配置 MAIL_TO 环境变量")
        sys.exit(1)

    print(f"\n{'='*40}")
    print(f"发送邮件至 {', '.join(recipients)}...")
    print(f"{'='*40}")

    try:
        subject = f"📊 基金溢价率日报 ({datetime.now().strftime('%Y-%m-%d')})"
        send_mail(subject, smtp_config, recipients, html)
        print(f"  ✅ 发送成功")
    except Exception as e:
        print(f"  ❌ 发送失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
