"""The company calendar: weeks start on Monday."""

import pandas as pd


def week_start(dates: pd.Series, first_day: int = 0) -> pd.Series:
    """Return the first day of the week that each date belongs to.

    Args:
        dates: Timestamps, with or without a time of day.
        first_day: 0 for weeks starting on Monday, 6 for Sunday.
    """
    days = dates.dt.normalize()
    offset = (days.dt.weekday + 1) % 7 - first_day
    return days - pd.to_timedelta(offset, unit="D")


def week_range(first: pd.Timestamp, last: pd.Timestamp) -> pd.DatetimeIndex:
    """All week starts from ``first`` to ``last`` (both week starts)."""
    return pd.date_range(first, last, freq="7D")
