import pandas as pd


def normalize(series: pd.Series) -> pd.Series:
    return series / series.iloc[0] * 100


def common_dates(*series_list):
    idx = series_list[0].index
    for s in series_list[1:]:
        idx = idx.intersection(s.index)
    return idx
