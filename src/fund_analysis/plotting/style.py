import numpy as np
import matplotlib.dates as mdates

from fund_analysis.config import setup_matplotlib

setup_matplotlib()


class HoverTool:
    def __init__(self, fig, ax, dates, y_values, fmt_func=None, extra_labels=None, extra_axes=None):
        self.fig = fig
        self.ax = ax
        self.dates = dates
        self.dates_num = mdates.date2num(dates)
        self.y_values = y_values
        self.extra_labels = extra_labels or {}

        self.vline = ax.axvline(x=dates[0], linewidth=0.8, ls="--", alpha=0.6, visible=False, color="gray", zorder=20)
        self.hline = ax.axhline(y=y_values[0], linewidth=0.8, ls="--", alpha=0.6, visible=False, color="gray", zorder=20)
        self.label = fig.text(0, 0, "", fontsize=9, color="gray", visible=False, zorder=100,
                              bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="gray", alpha=0.8))

        self.extra_vlines = []
        if extra_axes:
            for ea in extra_axes:
                vl = ea.axvline(x=dates[0], linewidth=0.8, ls="--", alpha=0.6, visible=False, color="gray", zorder=20)
                self.extra_vlines.append(vl)

        if fmt_func is None:
            self.base_fmt = lambda x, y: f"{x.strftime('%Y-%m-%d')}  {y:.2f}"
        else:
            self.base_fmt = fmt_func

        self.cid = self.fig.canvas.mpl_connect("motion_notify_event", self._on_move)

    def _on_move(self, event):
        if event.xdata is None or event.ydata is None:
            self.vline.set_visible(False)
            self.hline.set_visible(False)
            self.label.set_visible(False)
            for vl in self.extra_vlines:
                vl.set_visible(False)
            self.fig.canvas.draw()
            return
        min_num, max_num = self.dates_num[0], self.dates_num[-1]
        clamped = max(min(event.xdata, max_num), min_num)
        idx = np.argmin(np.abs(self.dates_num - clamped))
        x = self.dates[idx]
        y = self.y_values[idx]
        line_x = mdates.num2date(clamped).replace(tzinfo=None)
        self.vline.set_xdata([line_x, line_x])
        self.vline.set_visible(True)
        self.hline.set_ydata([y, y])
        self.hline.set_visible(True)
        for vl in self.extra_vlines:
            vl.set_xdata([line_x, line_x])
            vl.set_visible(True)
        text = self.base_fmt(x, y)
        for label, arr in self.extra_labels.items():
            text += f"\n{label}: {arr[idx]:.1f}"
        self.label.set_text(text)
        fx, fy = self.fig.transFigure.inverted().transform((event.x + 10, event.y + 10))
        self.label.set_position((fx, fy))
        self.label.set_visible(True)
        self.fig.canvas.draw()
