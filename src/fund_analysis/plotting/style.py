import numpy as np
import matplotlib.dates as mdates

from fund_analysis.config import setup_matplotlib

setup_matplotlib()


class HoverTool:
    def __init__(self, fig, ax, dates, y_values, fmt_func=None):
        self.fig = fig
        self.ax = ax
        self.dates = dates
        self.dates_num = mdates.date2num(dates)
        self.y_values = y_values

        self.vline = ax.axvline(x=dates[0], linewidth=0.8, ls="--", alpha=0.6, visible=False, color="gray")
        self.hline = ax.axhline(y=y_values[0], linewidth=0.8, ls="--", alpha=0.6, visible=False, color="gray")
        self.label = ax.text(0, 0, "", fontsize=9, color="gray", visible=False,
                             bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="gray", alpha=0.8))

        if fmt_func is None:
            self.fmt_func = lambda x, y: f"{x.strftime('%Y-%m-%d')}  {y:.2f}"
        else:
            self.fmt_func = fmt_func

        self.fig.canvas.mpl_connect("motion_notify_event", self._on_move)

    def _on_move(self, event):
        if event.inaxes != self.ax:
            self.vline.set_visible(False)
            self.hline.set_visible(False)
            self.label.set_visible(False)
            self.fig.canvas.draw_idle()
            return
        idx = np.argmin(np.abs(self.dates_num - event.xdata))
        x = self.dates[idx]
        y = self.y_values[idx]
        self.vline.set_xdata([x, x])
        self.vline.set_visible(True)
        self.hline.set_ydata([y, y])
        self.hline.set_visible(True)
        self.label.set_text(self.fmt_func(x, y))
        self.label.set_position((event.xdata, event.ydata))
        self.label.set_visible(True)
        self.fig.canvas.draw_idle()
