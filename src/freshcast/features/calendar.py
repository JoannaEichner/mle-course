"""Features that depend only on the date."""

import pandas as pd

DAYS_IN_WEEK = 7
# Holidays further away than this are all "far": the model needs no more detail.
MAX_DAYS_TO_HOLIDAY = 14
COUNTRY = "CN"


def day_of_week(df: pd.DataFrame) -> pd.Series:
    """Return the day of week of every row: 0 for Monday, 6 for Sunday."""
    raise NotImplementedError("Zadanie 09.1")


def cyclical(values: pd.Series, period: int) -> tuple[pd.Series, pd.Series]:
    """Encode a repeating quantity as a point on a circle.

    Day 6 and day 0 are neighbours in a week, but 6 and 0 are far apart as
    numbers. On the circle they sit next to each other.

    Args:
        values: Positions within the cycle, from 0 to ``period - 1``.
        period: Length of the cycle, for example 7 for days of the week.

    Returns:
        ``(sine, cosine)`` of the angle ``2 * pi * values / period``.
    """
    raise NotImplementedError("Zadanie 09.1")


def public_holidays(first: pd.Timestamp, last: pd.Timestamp) -> pd.DatetimeIndex:
    """Return the public holidays of the data's country between two dates.

    The dates come from the ``holidays`` package. The range is inclusive.
    Days off that were moved from a weekend count as holidays too.
    """
    raise NotImplementedError("Zadanie 09.1")


def is_public_holiday(df: pd.DataFrame) -> pd.Series:
    """Return 1 on rows whose date is a public holiday, else 0."""
    raise NotImplementedError("Zadanie 09.1")


def days_to_next_holiday(df: pd.DataFrame) -> pd.Series:
    """Return how many days remain until the next public holiday.

    0 on a holiday itself. Capped at ``MAX_DAYS_TO_HOLIDAY``, which is also
    the value when no holiday follows within the calendar that was looked up.
    """
    raise NotImplementedError("Zadanie 09.1")
