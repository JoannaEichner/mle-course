"""Building and storing the processed dataset that later modules read."""

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

DAILY_FILE = "daily.parquet"


def prepare_daily(
    raw_path: Path, *, cities: Sequence[int] | None = None
) -> pd.DataFrame:
    """Build the processed daily dataset from a raw file.

    Steps: load the scalar columns, check the panel, clean the discount,
    summarise the hourly arrays and join the summary back, one to one, on
    the series key and the date. Before the raw ``stock_hour6_22_cnt`` is
    dropped, it is compared with ``oos_hours`` computed from the arrays.

    Args:
        raw_path: A raw FreshRetailNet parquet file, e.g. ``paths.FRN_TRAIN``.
        cities: ``city_id`` values to keep, e.g. ``(3,)``. None keeps every
            city.

    Returns:
        One row per series and day with exactly the columns of
        ``PROCESSED_COLUMNS``, in that order, sorted by ``store_id``,
        ``product_id``, then ``dt``, with a fresh 0..n-1 index. ``discount``
        is cleaned as by ``clean_discount``; the four hourly columns are
        those of ``summarise_hours``.

    Raises:
        ValueError: The raw data breaks a panel rule, a discount is negative
            or missing, or the raw stockout count disagrees with the hourly
            arrays.
    """
    raise NotImplementedError("Zadanie 07.6")


def save_processed(daily: pd.DataFrame, directory: Path) -> Path:
    """Write the processed dataset to ``directory`` and return the file path.

    The file is ``directory / "daily.parquet"`` (``DAILY_FILE``), written
    without the index. Missing directories are created and an existing file
    is overwritten.

    Args:
        daily: The processed dataset, e.g. the result of ``prepare_daily``.
        directory: Where to write, e.g. ``paths.PROCESSED_DIR``.

    Returns:
        The path of the written file.

    Raises:
        ValueError: The frame's columns differ from ``PROCESSED_COLUMNS``
            (names or order). Nothing is written then.
    """
    raise NotImplementedError("Zadanie 07.6")


def load_processed(directory: Path) -> pd.DataFrame:
    """Read the processed dataset written by ``save_processed``.

    Args:
        directory: The directory passed to ``save_processed``, e.g.
            ``paths.PROCESSED_DIR``.

    Returns:
        The frame stored in ``directory / "daily.parquet"``, with the columns
        of ``PROCESSED_COLUMNS`` in that order and a 0..n-1 index.

    Raises:
        FileNotFoundError: The dataset has not been built yet.
        ValueError: The file's columns differ from ``PROCESSED_COLUMNS``,
            which means it was written by an older version of the code.
    """
    raise NotImplementedError("Zadanie 07.6")
