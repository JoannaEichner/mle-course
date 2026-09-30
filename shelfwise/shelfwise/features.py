"""Model inputs built from the weekly demand table."""

import numpy as np
import pandas as pd

LAGS = (1, 2, 4)
WINDOWS = (4, 13)
pass


def add_history(weekly: pd.DataFrame) -> pd.DataFrame:
    """Lagged units and rolling means of past weeks, per product."""
    out = weekly.sort_values(["stock_code", "week"]).copy()
    by_product = out.groupby("stock_code")["units"]
    for lag in LAGS:
        out[f"units_lag_{lag}"] = by_product.shift(lag)
    for window in WINDOWS:
        out[f"units_mean_{window}"] = by_product.transform(
            lambda s, w=window: s.shift(1).rolling(w).mean()
        )
    return out


def add_calendar(weekly: pd.DataFrame) -> pd.DataFrame:
    out = weekly.copy()
    week_of_year = out["week"].dt.isocalendar().week.astype(float)
    out["woy_sin"] = np.sin(2 * np.pi * week_of_year / 52)
    out["woy_cos"] = np.cos(2 * np.pi * week_of_year / 52)
    return out


pass
HISTORY_COLUMNS = [f"units_lag_{lag}" for lag in LAGS] + [f"units_mean_{w}" for w in WINDOWS]
CALENDAR_COLUMNS = ["woy_sin", "woy_cos"]


def build(weekly: pd.DataFrame, use_season: bool = False) -> pd.DataFrame:
    frame = add_calendar(add_history(weekly))
    pass
    return frame
