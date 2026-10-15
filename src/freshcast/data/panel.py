"""Per-series computations on a sorted panel: lags, rolling means, profiles."""

import pandas as pd


def is_sorted_panel(df: pd.DataFrame) -> bool:
    """Tell whether the rows are ordered by series, then by date.

    Lags and rolling windows read "the previous row of the same series", so
    they are only correct on a frame for which this returns True.

    Args:
        df: A frame with ``store_id``, ``product_id`` and ``dt``.

    Returns:
        True if the rows, top to bottom, are in ascending order of
        ``store_id``, then ``product_id``, then ``dt``; False otherwise. A
        repeated (series, day) pair does not count as disorder; that is
        ``check_panel``'s job. The frame is not changed.
    """
    raise NotImplementedError("Zadanie 07.5")


def add_lag(df: pd.DataFrame, column: str, lag: int) -> pd.DataFrame:
    """Add the value of ``column`` from ``lag`` days earlier in the same series.

    Args:
        df: A complete panel sorted by series and date (see ``check_panel``
            and ``is_sorted_panel``), e.g. daily sales after ``load_sales``.
        column: The column to look back in, e.g. ``"sale_amount"``.
        lag: How many days back, at least 1.

    Returns:
        A new frame: every column of ``df`` plus the column
        ``{column}_lag_{lag}`` at the end, same rows, order and index. The
        first ``lag`` days of every series are NaN: there is no earlier
        value, and a value from another series must never fill the gap. The
        input is not modified.

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
    never the row's own day. For a row on day ``t`` the window is the days
    ``t - lag - window + 1`` to ``t - lag``.

    Args:
        df: A complete panel sorted by series and date (see ``check_panel``
            and ``is_sorted_panel``).
        column: The column to average, e.g. ``"sale_amount"``.
        window: Number of days in the window, at least 1.
        lag: Distance in days between the row and the end of the window,
            at least 1.

    Returns:
        A new frame: every column of ``df`` plus the column
        ``{column}_mean_{window}_lag_{lag}`` at the end, same rows, order and
        index. Rows without ``window`` full past days in their own series are
        NaN. The input is not modified.

    Raises:
        ValueError: ``window`` or ``lag`` is below 1, or the frame is not
            sorted.
    """
    raise NotImplementedError("Zadanie 07.5")


def dow_profile(df: pd.DataFrame) -> pd.Series:
    """Return the typical shape of a week: relative sales by day of week.

    Each series is first divided by its own mean, so a big seller and a
    small one weigh the same. The result is the mean of those relative
    sales per weekday, over all rows of all series.

    Args:
        df: Daily sales with the series key, ``dt`` (``datetime64``) and
            ``sale_amount``, e.g. daily sales after ``load_sales``.

    Returns:
        A float Series of 7 values indexed 0 (Monday) to 6 (Sunday), named
        ``dow_profile``. A value of 1.2 means sales 20% above the series
        average.

    Raises:
        ValueError: A series has zero mean sales, so its relative sales are
            undefined. The message gives the number of affected rows.
    """
    raise NotImplementedError("Zadanie 07.5")
