import pandas as pd


def calculate_drawdown(close: pd.Series) -> pd.DataFrame:
    rolling_max = close.cummax()
    drawdown = (close - rolling_max) / rolling_max * 100
    return pd.DataFrame({
        "close": close,
        "高点": rolling_max,
        "回撤(%)": drawdown,
    })


def drawdown_status(dd_pct: float) -> str:
    if dd_pct >= -5:
        return "🔵 正常，按计划定投"
    elif dd_pct >= -10:
        return "🟢 轻度回调，可适当加仓"
    elif dd_pct >= -20:
        return "🟡 回调区间，加大买入"
    elif dd_pct >= -30:
        return "🟠 深度低估，显著加仓"
    else:
        return "🔴 历史机会，全力买入"


def vix_status(vix: float) -> str:
    if vix < 20:
        return "正常区间"
    elif vix < 30:
        return "恐慌区间"
    else:
        return "极度恐慌"
