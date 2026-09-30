"""The stockout label and the features for predicting it one day ahead.

The question: at the end of day ``t``, will this product be out of stock for
the whole window 06:00-22:00 on day ``t + 1``?

That changes what counts as known. In the 7-day forecast every feature had to
look back at least 7 days. Here the forecast is made after day ``t`` is over,
so everything observed on day ``t`` is legal, today's stockout hours and
today's sales included. What is not legal is the outcome of day ``t + 1``.
Only what is decided in advance may come from tomorrow: the calendar and the
planned discount.
"""

import pandas as pd

from freshcast.data.panel import is_sorted_panel
from freshcast.data.schema import (
    DATE,
    OOS_HOURS,
    OOS_WINDOW,
    SERIES_KEY,
    TARGET,
)
from freshcast.split import split_by_date

LABEL = "oos_full_tomorrow"
# The window 06:00-22:00 has 16 hours. A day with 16 stockout hours has no
# product on the shelf at any time of it.
FULL_STOCKOUT_HOURS = OOS_WINDOW.stop - OOS_WINDOW.start
# Day-off flag of the data (weekends and public holidays). Named in schema.FLAGS.
HOLIDAY_FLAG = "holiday_flag"
ONE_DAY = pd.Timedelta(days=1)

# Columns that ``add_stockout_features`` adds, plus the two raw columns it
# uses as they are (today's stockout hours and today's sales).
FEATURES = [
    OOS_HOURS,
    "oos_full_today",
    "oos_hours_lag_1",
    "oos_hours_lag_7",
    "oos_hours_mean_7",
    "oos_full_share_7",
    "oos_full_share_28",
    TARGET,
    "sale_amount_mean_7",
    "discount_tomorrow",
    "tomorrow_is_day_off",
]


def require_daily_panel(df: pd.DataFrame) -> None:
    """Raise unless the next row of a series is always the next day.

    Shifting by one row means "one day" only on a frame sorted by series and
    date in which no series skips or repeats a day.

    Raises:
        ValueError: The frame is not sorted by series and date, or some rows
            follow the previous row of their series by other than one day.
    """
    if not is_sorted_panel(df):
        raise ValueError("The frame must be sorted by series and date.")
    step = df.groupby(SERIES_KEY, sort=False)[DATE].diff()
    # The first row of every series has no previous row, so its step is NaT.
    broken = int((step.notna() & (step != ONE_DAY)).sum())
    if broken:
        raise ValueError(
            f"{broken} rows do not follow the previous row of their series by "
            "exactly one day."
        )


def next_day_value(df: pd.DataFrame, column: str) -> pd.Series:
    """Return the value of ``column`` on the next day of the same series.

    This is the look-ahead that builds the label. Used on a column of
    outcomes it is the answer to be predicted; used on a column decided in
    advance, such as the planned discount, it is a legal feature.

    Args:
        df: A complete daily panel sorted by series and date.
        column: The column to look ahead in.

    Returns:
        A Series aligned with ``df``. The last day of every series has no next
        day and gets NaN: a value from another series must never fill it.

    Raises:
        ValueError: As ``require_daily_panel``.
    """
    raise NotImplementedError("Zadanie 12.1")


def add_stockout_label(df: pd.DataFrame) -> pd.DataFrame:
    """Add the label: will tomorrow be a full-stockout day?

    Args:
        df: A complete daily panel sorted by series and date, with
            ``oos_hours``.

    Returns:
        A new frame with the float column ``oos_full_tomorrow``: 1.0 when
        ``oos_hours`` of the next day of the series is 16, 0.0 when it is
        any other number. The last day of every series has no tomorrow, so
        its label is NaN (unknown), never 0.0.

    Raises:
        ValueError: As ``require_daily_panel``.
    """
    raise NotImplementedError("Zadanie 12.1")


def drop_unlabelled(df: pd.DataFrame) -> pd.DataFrame:
    """Return the rows that have a label, with the label as an integer.

    The rule: a row has no label exactly when it is the last day of its
    series. Those rows have no tomorrow. They are dropped from training and
    scoring, and only they. Call this on the whole panel, before any split in
    time.

    Args:
        df: A frame with the column ``oos_full_tomorrow`` from
            ``add_stockout_label``.

    Returns:
        A new frame without the unlabelled rows, keeping the index of ``df``,
        with the label as ``int8`` (0 or 1).

    Raises:
        ValueError: The rule is broken: a row without a label is not the last
            day of its series, or a last day has a label. The message says how
            many rows break it.
    """
    raise NotImplementedError("Zadanie 12.1")


def rolling_mean_through_today(df: pd.DataFrame, column: str, window: int) -> pd.Series:
    """Return the mean of ``column`` over the last ``window`` days, today included.

    The forecast is made after today is over, so today is known and the
    window ends today. The lags of module 09 end further back only because a
    7-day forecast cannot see the last 6 days.

    Args:
        df: A complete daily panel sorted by series and date.
        column: The column to average.
        window: Number of days, at least 1.

    Returns:
        A Series aligned with ``df``, named ``{column}_mean_{window}``. It is
        NaN on the first ``window - 1`` days of every series, where the
        window is not full yet.

    Raises:
        ValueError: ``window`` is below 1, or as ``require_daily_panel``.
    """
    raise NotImplementedError("Zadanie 12.2")


def add_stockout_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the features known at the end of day ``t``, for predicting day ``t + 1``.

    Every column describes the row's own day ``t`` and the days before it, or
    something decided in advance for day ``t + 1``. The columns added:

    - ``oos_full_today``: 1 if ``oos_hours`` is 16 today, else 0 (``int8``),
    - ``oos_hours_lag_1``, ``oos_hours_lag_7``: ``oos_hours`` of yesterday and
      of a week ago,
    - ``oos_hours_mean_7``: mean ``oos_hours`` over the last 7 days, today
      included,
    - ``oos_full_share_7``, ``oos_full_share_28``: share of the last 7 and 28
      days, today included, that were full stockouts,
    - ``sale_amount_mean_7``: mean sales over the last 7 days, today included,
    - ``discount_tomorrow``: the planned discount of the next day,
    - ``tomorrow_is_day_off``: the day-off flag of the next day.

    Windows and lags are NaN where the series has not run long enough. The
    next day's columns are NaN on the last day of every series. The raw
    columns ``oos_hours`` and ``sale_amount`` of today are features too and
    stay as they are. Nothing else is taken from tomorrow: its sales and its
    stockout hours are the outcome.

    Args:
        df: A complete daily panel sorted by series and date, with the columns
            of the processed dataset.

    Returns:
        A new frame with the columns above added.

    Raises:
        ValueError: As ``require_daily_panel``.
    """
    raise NotImplementedError("Zadanie 12.2")


def split_by_label_date(
    df: pd.DataFrame, cutoff: pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a labelled frame in time so that no label crosses the cutoff.

    The label of the row for day ``t`` is the outcome of day ``t + 1``. The
    row just before the cutoff is therefore labelled by the first day after
    it. When you train, that outcome is not known yet. So the row of the day
    before the cutoff is dropped from the first part.

    Args:
        df: A labelled frame with the date column.
        cutoff: First date of the second part.

    Returns:
        ``(before, after)``, keeping the index of ``df``. Every label in
        ``before`` describes a day earlier than ``cutoff``.

    Raises:
        ValueError: One of the parts would be empty.
    """
    before, after = split_by_date(df, cutoff)
    kept = before.loc[before[DATE] < cutoff - ONE_DAY]
    if kept.empty:
        raise ValueError(f"Nothing is left before {cutoff} once its label day is cut.")
    return kept, after
