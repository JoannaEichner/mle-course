"""Splitting a panel in time: the past trains, the future validates."""

from dataclasses import dataclass

import pandas as pd


def last_days_start(df: pd.DataFrame, days: int) -> pd.Timestamp:
    """Return the first date of the final ``days`` days of the frame.

    Args:
        df: A frame with the date column.
        days: Length of the final period, at least 1.

    Raises:
        ValueError: ``days`` is below 1 or not shorter than the frame's span.
    """
    raise NotImplementedError("Zadanie 08.1")


def split_by_date(
    df: pd.DataFrame, cutoff: pd.Timestamp
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a frame into the rows before ``cutoff`` and the rows from it on.

    Rows are never shuffled: everything the model trains on happened before
    everything it is validated on.

    Args:
        df: A frame with the date column.
        cutoff: First date of the second part.

    Returns:
        ``(before, after)``. Both keep the index of ``df``, so predictions
        made for one part can be aligned with the original frame.

    Raises:
        ValueError: One of the parts would be empty.
    """
    raise NotImplementedError("Zadanie 08.1")


@dataclass(frozen=True)
class Fold:
    """One step of a rolling-origin backtest.

    The model trains on every day before ``valid_start`` and is scored on
    the days from ``valid_start`` to ``valid_end``, inclusive.
    """

    valid_start: pd.Timestamp
    valid_end: pd.Timestamp

    def split(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Return ``(train, valid)`` for this fold, keeping the index of ``df``."""
        raise NotImplementedError("Zadanie 11.1")


def rolling_origin_folds(
    last_date: pd.Timestamp, n_folds: int, horizon: int
) -> list[Fold]:
    """Build folds whose validation windows are the last weeks of the data.

    The last fold validates on the final ``horizon`` days, the one before it
    on the ``horizon`` days preceding those, and so on. Windows do not
    overlap, and each fold trains on everything before its own window.

    Args:
        last_date: Last date of the data.
        n_folds: Number of folds, at least 1.
        horizon: Length of each validation window in days, at least 1.

    Returns:
        The folds, oldest validation window first.

    Raises:
        ValueError: ``n_folds`` or ``horizon`` is below 1.
    """
    raise NotImplementedError("Zadanie 11.1")
