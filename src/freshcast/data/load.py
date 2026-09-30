"""Reading the raw parquet files without loading more than needed."""

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from freshcast.data.schema import DAILY_COLUMNS


def shrink_integers(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with every integer column in its smallest fitting type.

    Floats are left alone: halving their precision changes values, halving
    an integer's width does not.

    Args:
        df: Any frame.

    Returns:
        A new frame with the same values and column order.
    """
    raise NotImplementedError("Zadanie 07.1")


def load_sales(
    path: Path,
    *,
    cities: Sequence[int] | None = None,
    columns: Sequence[str] = DAILY_COLUMNS,
) -> pd.DataFrame:
    """Load daily sales rows for the chosen cities.

    Only the requested columns are read from disk, and rows of other cities
    are dropped while reading, so memory use follows the result, not the file.

    Args:
        path: A raw FreshRetailNet parquet file.
        cities: City ids to keep. None keeps every city.
        columns: Columns to read. Must include the series key and the date.

    Returns:
        One row per series and day, sorted by series then date, with a fresh
        0..n-1 index, the date as ``datetime64`` and integers shrunk.
    """
    raise NotImplementedError("Zadanie 07.1")
