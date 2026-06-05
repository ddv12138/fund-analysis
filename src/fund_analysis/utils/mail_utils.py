"""
邮件发送工具模块
提供 SMTP 配置读取、邮件发送、matplotlib 图表转 base64 等通用功能。
"""

import base64
import io
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def read_smtp_config_from_env() -> dict:
    """从环境变量读取 SMTP 配置"""
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.qq.com"),
        "port": int(os.environ.get("SMTP_PORT", "465")),
        "user": os.environ.get("SMTP_USER", ""),
        "pass": os.environ.get("SMTP_PASS", ""),
    }


def send_mail(subject: str, smtp_config: dict, recipients: list[str], html: str):
    """发送 HTML 邮件"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_config["user"]
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html, "html", "utf-8"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_config["host"], smtp_config["port"], context=ctx) as server:
        server.login(smtp_config["user"], smtp_config["pass"])
        server.sendmail(smtp_config["user"], recipients, msg.as_string())


def fig_to_base64(fig) -> str:
    """matplotlib Figure 转 base64 字符串"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()
