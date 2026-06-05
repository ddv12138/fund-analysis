import pandas as pd


def calculate_premium(market: pd.DataFrame, nav: pd.DataFrame) -> pd.DataFrame:
    market = market.sort_values("日期").reset_index(drop=True)
    nav = nav.sort_values("日期").reset_index(drop=True)
    nav_shifted = nav.copy()
    nav_shifted["日期"] = nav_shifted["日期"] + pd.Timedelta(days=1)
    merged = pd.merge_asof(market, nav_shifted, on="日期", direction="backward")
    merged = merged.dropna(subset=["单位净值"]).reset_index(drop=True)
    merged["溢价率(%)"] = (
        (merged["市场价"] - merged["单位净值"]) / merged["单位净值"] * 100
    )
    return merged


def premium_status(premium: float, mean: float, std: float) -> str:
    upper = min(mean + std, mean * 1.5)
    lower = max(mean - std, 0)
    if premium < lower:
        return "✅ 低估区间"
    elif premium > upper:
        return "❌ 溢价偏高"
    else:
        return "✅ 适合买入(均值±σ)"
