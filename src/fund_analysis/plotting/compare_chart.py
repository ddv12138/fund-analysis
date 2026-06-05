import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from fund_analysis.analysis.compare import normalize, common_dates
from fund_analysis.config import INDEX_NAMES
from fund_analysis.plotting.style import HoverTool


def show_compare_chart(fund_data, index_series, fund_codes):
    INDEX_SYMBOL = ".NDX"
    index_norm = normalize(index_series)
    fund_norm = {}
    for code in fund_codes:
        fund_norm[code] = normalize(fund_data[code])

    all_series = list(fund_norm.values()) + [index_norm]
    dates = common_dates(*all_series)

    fig, ax = plt.subplots(figsize=(10, 4))

    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for i, code in enumerate(fund_codes):
        s = fund_norm[code].loc[dates]
        ax.plot(dates, s, color=colors[i % len(colors)], linewidth=1.2, label=code)
        ax.text(dates[-1], s.iloc[-1], f"  {s.iloc[-1]:.2f}", va="center", ha="left", fontsize=9, color=colors[i % len(colors)])

    i_s = index_norm.loc[dates]
    ax.plot(dates, i_s, color="gray", linewidth=1, linestyle="--", label=INDEX_SYMBOL, alpha=0.8)
    ax.text(dates[-1], i_s.iloc[-1], f"  {i_s.iloc[-1]:.2f}", va="center", ha="left", fontsize=9, color="gray")

    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)

    def fmt_compare(x, y):
        parts = [x.strftime("%Y-%m-%d")]
        for code in fund_codes:
            v = fund_norm[code].loc[x]
            parts.append(f"{code}: {v:.2f}")
        parts.append(f"{INDEX_SYMBOL}: {index_norm.loc[x]:.2f}")
        return "  ".join(parts)

    mid_y = (min(index_norm.loc[dates].min(), min(fund_norm[c].loc[dates].min() for c in fund_codes)) +
             max(index_norm.loc[dates].max(), max(fund_norm[c].loc[dates].max() for c in fund_codes))) / 2

    HoverTool(fig, ax, dates, [mid_y] * len(dates), fmt_func=fmt_compare)

    ax.grid(True, alpha=0.2)
    ax.axhline(y=100, color="#888888", linestyle="--", linewidth=0.5)
    ax.set_ylabel("归一化价格 (基准=100)")
    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(locator))
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    plt.show()
    plt.close()


def print_compare_table(fund_data, index_series, fund_codes):
    INDEX_SYMBOL = ".NDX"
    index_norm = normalize(index_series)
    fund_norm = {}
    for code in fund_codes:
        fund_norm[code] = normalize(fund_data[code])

    all_series = list(fund_norm.values()) + [index_norm]
    dates = common_dates(*all_series)

    header = f"{'日期':<12}"
    for code in fund_codes:
        header += f" {code:<10}"
    header += f" {INDEX_SYMBOL:<10}"
    print(f"\n{header}")
    print("-" * len(header))

    for dt in dates:
        line = f"{dt.strftime('%m-%d'):<12}"
        for code in fund_codes:
            line += f" {fund_norm[code].loc[dt]:<10.2f}"
        line += f" {index_norm.loc[dt]:<10.2f}"
        print(line)

    print(f"\n累计涨跌幅:")
    for code in fund_codes:
        chg = fund_norm[code].iloc[-1] - 100
        print(f"  {code}: {chg:+.2f}%")
    i_chg = index_norm.iloc[-1] - 100
    print(f"  {INDEX_SYMBOL}: {i_chg:+.2f}%")

    print(f"\n超额收益 (vs {INDEX_SYMBOL}):")
    for code in fund_codes:
        excess = (fund_norm[code].iloc[-1] - 100) - i_chg
        print(f"  {code}: {excess:+.2f}%")
