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
    summarise the hourly arrays and join the summary back, one to one.

    Args:
        raw_path: A raw FreshRetailNet parquet file.
        cities: City ids to keep. None keeps every city.

    Returns:
        A frame with exactly the columns of ``PROCESSED_COLUMNS``, in that
        order, sorted by series and date.

    Raises:
        ValueError: The raw data breaks a panel rule, or the raw stockout
            count disagrees with the hourly arrays.
    """
    raise NotImplementedError("Zadanie 07.6")


def save_processed(daily: pd.DataFrame, directory: Path) -> Path:
    """Write the processed dataset to ``directory`` and return the file path.

    Raises:
        ValueError: The frame's columns differ from ``PROCESSED_COLUMNS``.
    """
    raise NotImplementedError("Zadanie 07.6")


def load_processed(directory: Path) -> pd.DataFrame:
    """Read the processed dataset written by ``save_processed``.

    Raises:
        FileNotFoundError: The dataset has not been built yet.
        ValueError: The file's columns differ from ``PROCESSED_COLUMNS``,
            which means it was written by an older version of the code.
    """
    raise NotImplementedError("Zadanie 07.6")
