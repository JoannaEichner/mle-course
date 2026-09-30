"""Turning the 24-element hourly arrays into per-day numbers."""

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd


def load_hourly(path: Path, *, cities: Sequence[int] | None = None) -> pd.DataFrame:
    """Load the series key, the date and the two hourly array columns.

    Args:
        path: A raw FreshRetailNet parquet file.
        cities: City ids to keep. None keeps every city, which needs
            several GB of memory for the full file.

    Returns:
        One row per series and day, sorted by series then date, with a fresh
        0..n-1 index and the date as ``datetime64``.
    """
    raise NotImplementedError("Zadanie 07.4")


def to_matrix(column: pd.Series) -> np.ndarray:
    """Stack a column of 24-element arrays into one ``(n, 24)`` array.

    Raises:
        ValueError: Some row does not hold exactly 24 values.
    """
    raise NotImplementedError("Zadanie 07.4")


def summarise_hours(hourly: pd.DataFrame) -> pd.DataFrame:
    """Reduce the hourly arrays to four numbers per series and day.

    Args:
        hourly: Output of ``load_hourly``.

    Returns:
        A frame with the series key, the date and:

        - ``oos_hours``: hours out of stock between 06:00 and 22:00,
        - ``oos_hours_total``: hours out of stock in the whole day,
        - ``sales_in_stock``: sales in the hours with stock,
        - ``sales_while_oos``: sales recorded in hours flagged out of stock.

        Rows are in the order of the input. The two sales columns add up to
        the day's total sales.
    """
    raise NotImplementedError("Zadanie 07.4")
