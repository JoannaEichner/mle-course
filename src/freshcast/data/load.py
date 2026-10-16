"""Reading the raw parquet files without loading more than needed."""

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from freshcast.data.schema import DAILY_COLUMNS


def shrink_integers(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with every integer column in its smallest fitting type.

    Each integer column gets the smallest signed integer type (``int8``,
    ``int16``, ``int32`` or ``int64``) that holds all of its values, so no
    value changes. Floats are left alone: halving their precision changes
    values, halving an integer's width does not. Columns of any other type
    (dates, strings, arrays) are left alone too.

    Args:
        df: Any frame. In this course: raw sales read from parquet, where
            the integer columns arrive as ``int64`` or ``int32``.

    Returns:
        A new frame with the same rows, index, values and column order. The
        input is not modified.
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
        path: A raw FreshRetailNet parquet file, e.g. ``paths.FRN_TRAIN``.
            One row in it is the sales of one product in one store on one
            day; ``dt`` is stored as text such as ``"2024-03-28"``.
        cities: ``city_id`` values to keep, e.g. ``(3,)``. None keeps every
            city. The filter works even when ``city_id`` is not among
            ``columns``.
        columns: Columns to read, in the order wanted in the result. Must
            include the series key (``store_id``, ``product_id``) and ``dt``.

    Returns:
        One row per series and day, with exactly ``columns`` in that order,
        sorted by ``store_id``, ``product_id``, then ``dt``, with a fresh
        0..n-1 index, ``dt`` as ``datetime64`` and integer columns shrunk as
        by ``shrink_integers``. Float columns keep ``float64``.
    """
    raise NotImplementedError("Zadanie 07.1")
