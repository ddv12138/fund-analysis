import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from fund_analysis.plotting.style import HoverTool


def create_premium_figure(df) -> plt.Figure:
    pr = df["溢价率(%)"]
    mean = pr.mean()
    dates = df["日期"]
    latest = pr.iloc[-1]

    fig, ax = plt.subplots(figsize=(10, 4))

    pr_max = pr.max()
    pr_min = pr.min()
    std = pr.std()
    upper = min(mean + std, mean * 1.5)
    lower = max(mean - std, 0)

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


def show_chart(df, symbol: str):
    pr = df["溢价率(%)"]
    dates = df["日期"]
    mean = pr.mean()
    fig = create_premium_figure(df)
    _ = HoverTool(fig, fig.axes[0], dates, pr.values)
    plt.show()
    plt.close()
    print(f"  均值: {mean:.2f}%  |  溢价率范围: {pr.min():.2f}% ~ {pr.max():.2f}%")
