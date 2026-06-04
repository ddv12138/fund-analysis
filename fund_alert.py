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
    python fund_alert.py                         # 正常执行
    python fund_alert.py --dry-run               # 仅打印，不推送
"""

import argparse
import io
import os
import smtplib
import ssl
import sys
from datetime import datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from fund_premium_analyzer import (
    get_fund_name,
    get_market_price,
    get_nav,
    calculate_premium,
    create_premium_figure,
)


def premium_status(premium: float, mean: float, std: float) -> str:
    upper = min(mean + std, mean * 1.5)
    lower = max(mean - std, 0)
    if premium < lower:
        return "✅ 低估区间"
    elif premium > upper:
        return "❌ 溢价偏高"
    else:
        return "✅ 适合买入(均值±σ)"


def fig_to_base64(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    import base64
    return base64.b64encode(buf.read()).decode()


def build_html_report(results: list[dict]) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    parts = [f"<h2>📊 基金溢价率日报 ({today})</h2><hr>"]

    for r in results:
        parts.append(f"<h3>{r['name']}({r['symbol']})</h3>")
        parts.append(
            f"<p>溢价率: {r['premium']:.2f}% {r['status']}</p>"
            f"<p>买入区间: &lt; {r['buy_threshold']:.2f}% "
            f"(均值 {r['mean']:.2f}% - 标准差 {r['std']:.2f}%)</p>"
        )
        parts.append(f'<img src="data:image/png;base64,{r["chart_base64"]}" style="max-width:100%"><hr>')

    return "\n".join(parts)


def send_mail(smtp_config: dict, recipients: list[str], html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 基金溢价率日报 ({datetime.now().strftime('%Y-%m-%d')})"
    msg["From"] = smtp_config["user"]
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html, "html", "utf-8"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_config["host"], smtp_config["port"], context=ctx) as server:
        server.login(smtp_config["user"], smtp_config["pass"])
        server.sendmail(smtp_config["user"], recipients, msg.as_string())


def main():
    parser = argparse.ArgumentParser(description="基金溢价率监控告警")
    parser.add_argument("--dry-run", action="store_true", help="仅打印结果，不推送通知")
    args = parser.parse_args()

    symbols_str = os.environ.get("FUND_SYMBOLS", "513870")
    symbols = [s.strip() for s in symbols_str.split(",") if s.strip()]
    mail_to_str = os.environ.get("MAIL_TO", "")
    recipients = [r.strip() for r in mail_to_str.split(",") if r.strip()]

    smtp_config = {
        "host": os.environ.get("SMTP_HOST", "smtp.qq.com"),
        "port": int(os.environ.get("SMTP_PORT", "465")),
        "user": os.environ.get("SMTP_USER", ""),
        "pass": os.environ.get("SMTP_PASS", ""),
    }

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
            buy_threshold = mean - std
            status = premium_status(latest_premium, mean, std)

            fig = create_premium_figure(df)
            chart_b64 = fig_to_base64(fig)

            print(f"  最新溢价率: {latest_premium:.3f}%")
            print(f"  均值: {mean:.3f}%  |  标准差: {std:.3f}%")
            print(f"  买入区间: < {buy_threshold:.3f}%")
            print(f"  状态: {status}")

            results.append({
                "symbol": symbol,
                "name": name,
                "premium": latest_premium,
                "mean": mean,
                "std": std,
                "buy_threshold": buy_threshold,
                "status": status,
                "chart_base64": chart_b64,
            })

        except Exception as e:
            print(f"  ❌ 检查 {symbol} 时出错: {e}")
            continue

    if not results:
        print(f"\n{'='*40}")
        print("所有基金均无数据")
        print(f"{'='*40}")
        return

    html = build_html_report(results)

    if args.dry_run:
        print(f"\n{'='*40}")
        print(f"待推送邮件 (DRY RUN - 未实际发送)")
        print(f"{'='*40}")
        for r in results:
            print(f"  {r['name']}({r['symbol']}) 溢价率 {r['premium']:.2f}% {r['status']}")
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
        send_mail(smtp_config, recipients, html)
        print(f"  ✅ 发送成功")
    except Exception as e:
        print(f"  ❌ 发送失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
