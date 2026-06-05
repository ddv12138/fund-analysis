import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from fund_analysis.plotting.style import HoverTool


def show_chart(df, symbol: str):
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

    _ = HoverTool(fig, ax, dates, close.values,
                  fmt_func=lambda x, y: f"{x.strftime('%Y-%m-%d')}  {y:.0f}")

    ax.grid(True, alpha=0.2)
    ax.set_xlim(dates.min(), dates.max())
    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    plt.show()
    plt.close()
