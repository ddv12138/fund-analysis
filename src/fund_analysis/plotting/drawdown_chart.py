import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from fund_analysis.plotting.style import HoverTool


def create_drawdown_figure(df: pd.DataFrame, symbol: str, vix_df: pd.DataFrame | None = None) -> plt.Figure:
    dates = df["date"]
    dd = df["回撤(%)"]
    latest_dd = dd.iloc[-1]
    close = df["close"]

    fig, (ax, ax_vix) = plt.subplots(2, 1, figsize=(10, 6), sharex=True, constrained_layout=True,
                                      gridspec_kw={"height_ratios": [3, 1], "hspace": 0.08})

    # ── Top: drawdown chart ──
    ax.fill_between(dates, dd, 0, where=(dd < 0), color="#ff6b6b", alpha=0.15)
    ax.plot(dates, dd, color="#d62728", linewidth=1.2)

    ax.axhline(y=0, color="#333333", linestyle="-", linewidth=0.5)
    ax.axhline(y=latest_dd, color="#d62728", linestyle="--", linewidth=0.6)
    ax.text(dates.max(), latest_dd, f" 当前 {latest_dd:.2f}%",
            va="center", ha="left", fontsize=9, color="#d62728")

    ax_close = ax.twinx()
    ax_close.plot(dates, close, color="#1f77b4", linewidth=0.8, alpha=0.6)
    ax_close.set_ylabel("Close", color="#1f77b4", fontsize=9)
    ax_close.tick_params(axis="y", labelcolor="#1f77b4", labelsize=8)

    extra_labels = {}
    if vix_df is not None and not vix_df.empty:
        latest_vix = vix_df["close"].iloc[-1]
        ax_vix_label = ax.twinx()
        ax_vix_label.set_yticks([])
        ax_vix_label.set_ylim(0, 1)
        ax_vix_label.text(1, 0.95, f"VIX {latest_vix:.1f}", transform=ax_vix_label.transAxes,
                          color="#ff7f0e", fontsize=9, ha="right", va="top")

        aligned = pd.merge_asof(dates.to_frame("date"), vix_df, on="date", direction="backward")
        extra_labels["VIX"] = aligned["close"].values

    extra_labels["Close"] = close.values
    ax.set_title(f"{symbol} Drawdown / Price / VIX", fontsize=8, fontweight="normal", pad=2, loc="left")
    ax.set_ylabel("Drawdown (%)")

    # ── Bottom: VIX chart ──
    if vix_df is not None and not vix_df.empty:
        vix_dates = vix_df["date"]
        vix_close = vix_df["close"]
        vix_top = max(vix_close.max(), 40) * 1.15

        ax_vix.fill_between(vix_dates, 0, 20, color="#ccffcc", alpha=0.25)
        ax_vix.fill_between(vix_dates, 20, 30, color="#ffcccc", alpha=0.25)
        ax_vix.fill_between(vix_dates, 30, vix_top, color="#ff6b6b", alpha=0.25)
        ax_vix.plot(vix_dates, vix_close, color="#ff7f0e", linewidth=0.8)

        ax_vix.axhline(y=20, color="#2ca02c", linestyle=":", linewidth=0.5)
        ax_vix.axhline(y=30, color="#d62728", linestyle="--", linewidth=0.5)

        ax_vix.text(vix_dates.max(), 20, " Normal", va="center", fontsize=7, color="#2ca02c")
        ax_vix.text(vix_dates.max(), 30, " Fear", va="center", fontsize=7, color="#d62728")
        ax_vix.text(vix_dates.max(), vix_top * 0.92, " Extreme Fear", va="center", fontsize=7, color="#d62728")

        ax_vix.set_ylabel("VIX", color="#ff7f0e", fontsize=9)
        ax_vix.tick_params(axis="y", labelcolor="#ff7f0e", labelsize=8)
        ax_vix.set_ylim(0, vix_top)

    # ── HoverTool on main chart, sync vline to VIX subplot ──
    _ = HoverTool(fig, ax, dates, dd.values, fmt_func=lambda x, y: f"{x.strftime('%Y-%m-%d')}  {y:.2f}%",
                  extra_labels=extra_labels, extra_axes=[ax_vix] if vix_df is not None else None)

    # ── Common formatting ──
    xpad = (dates.max() - dates.min()) * 0.08
    ax.set_xlim(dates.min(), dates.max() + xpad)
    ax.grid(True, alpha=0.2)
    ax.tick_params(axis="x", labelbottom=False)
    ax_vix.grid(True, alpha=0.2)
    ax_vix.tick_params(axis="x", rotation=45)
    locator = mdates.AutoDateLocator()
    ax_vix.xaxis.set_major_locator(locator)
    ax_vix.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))

    return fig


def show_drawdown_chart(df: pd.DataFrame, symbol: str, vix_df: pd.DataFrame | None = None, name: str = ""):
    fig = create_drawdown_figure(df, symbol, vix_df=vix_df)
    plt.show()
    plt.close()
