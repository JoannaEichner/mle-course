"""Lag and window features that respect the forecast horizon.

To forecast day ``t + h`` you only know the target up to day ``t``. A lag
shorter than the horizon ``h`` would read a value that does not exist yet.
"""

import pandas as pd


def check_horizon(lag: int, horizon: int) -> None:
    """Raise unless a feature lagged by ``lag`` days is known ``horizon`` days ahead.

    Raises:
        ValueError: ``horizon`` is below 1 or ``lag`` is shorter than it.
    """
    raise NotImplementedError("Zadanie 09.2")


def lag_feature(df: pd.DataFrame, column: str, lag: int, *, horizon: int) -> pd.Series:
    """Return ``column`` from ``lag`` days earlier in the same series.

    Args:
        df: A complete panel sorted by series and date.
        column: The column to look back in.
        lag: How many days back.
        horizon: How many days ahead the model forecasts.

    Returns:
        A Series aligned with ``df``, named ``{column}_lag_{lag}``.

    Raises:
        ValueError: The lag is shorter than the horizon.
    """
    raise NotImplementedError("Zadanie 09.2")


def window_mean_feature(
    df: pd.DataFrame, column: str, window: int, *, horizon: int
) -> pd.Series:
    """Return the mean of ``column`` over the latest window known at forecast time.

    The window spans ``window`` days and ends ``horizon`` days before the
    row, which is the last day whose value is known for every day of the
    forecast horizon.

    Returns:
        A Series aligned with ``df``, named
        ``{column}_mean_{window}_lag_{horizon}``.
    """
    raise NotImplementedError("Zadanie 09.2")
