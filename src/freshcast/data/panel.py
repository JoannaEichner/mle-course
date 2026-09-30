"""Per-series computations on a sorted panel: lags, rolling means, profiles."""

import pandas as pd


def is_sorted_panel(df: pd.DataFrame) -> bool:
    """Tell whether the rows are ordered by series, then by date.

    Lags and rolling windows read "the previous row of the same series", so
    they are only correct on a frame for which this returns True.
    """
    raise NotImplementedError("Zadanie 07.5")


def add_lag(df: pd.DataFrame, column: str, lag: int) -> pd.DataFrame:
    """Add the value of ``column`` from ``lag`` days earlier in the same series.

    Args:
        df: A complete panel sorted by series and date.
        column: The column to look back in.
        lag: How many days back, at least 1.

    Returns:
        A new frame with the column ``{column}_lag_{lag}``. The first
        ``lag`` days of every series are NaN: there is no earlier value, and
        a value from another series must never fill the gap.

    Raises:
        ValueError: ``lag`` is below 1 or the frame is not sorted.
    """
    raise NotImplementedError("Zadanie 07.5")


def add_rolling_mean(
    df: pd.DataFrame, column: str, window: int, lag: int = 1
) -> pd.DataFrame:
    """Add the mean of ``column`` over a window of past days of the same series.

    The window ends ``lag`` days before the row and spans ``window`` days.
    With the default ``lag=1`` it covers yesterday and the days before it,
    never the row's own day.

    Args:
        df: A complete panel sorted by series and date.
        column: The column to average.
        window: Number of days in the window, at least 1.
        lag: Distance in days between the row and the end of the window,
            at least 1.

    Returns:
        A new frame with the column ``{column}_mean_{window}_lag_{lag}``.
        Rows without ``window`` full past days are NaN.

    Raises:
        ValueError: ``window`` or ``lag`` is below 1, or the frame is not
            sorted.
    """
    raise NotImplementedError("Zadanie 07.5")


def dow_profile(df: pd.DataFrame) -> pd.Series:
    """Return the typical shape of a week: relative sales by day of week.

    Each series is first divided by its own mean, so a big seller and a
    small one weigh the same. The result is the mean of those relative
    sales per weekday, over all series.

    Args:
        df: Daily sales with the series key, the date and the target.

    Returns:
        A Series indexed 0 (Monday) to 6 (Sunday), named ``dow_profile``.
        A value of 1.2 means sales 20% above the series average.

    Raises:
        ValueError: A series has zero mean sales, so its relative sales are
            undefined.
    """
    raise NotImplementedError("Zadanie 07.5")
