"""The daily product table: aggregation, its contract, the stored dataset.

Tasks 06.6 and 06.7. The contract is stated in the docstring of
``online_retail`` and in ``DAILY_COLUMNS``.
"""

from pathlib import Path

import pandas as pd


def daily_totals(lines: pd.DataFrame) -> pd.DataFrame:
    """Sum product lines to one row per product and day.

    Args:
        lines: Output of ``product_lines``.

    Returns:
        A frame with exactly the columns of ``DAILY_COLUMNS``, one row per
        ``(stock_code, date)`` pair that occurs in ``lines``, sorted by
        ``stock_code`` then ``date``, with a fresh 0..n-1 index. The measures
        are sums and keep their integer or float type. A day on which a
        product was only returned has ``units_sold`` 0 and ``revenue`` 0.0.
        Days without any line have no row; that is not the same as zero
        demand (see the note on trading days in ``online_retail``). A line
        with a missing ``stock_code`` or ``date`` is not dropped: it forms a
        row of its own, with the key missing, so that ``check_daily`` can
        reject it.
    """
    raise NotImplementedError("Zadanie 06.6")


def _wrong_dtypes(daily: pd.DataFrame) -> list[str]:
    """Return the columns of ``daily`` whose type breaks the contract."""
    is_right = {
        "stock_code": pd.api.types.is_string_dtype(daily["stock_code"]),
        "date": pd.api.types.is_datetime64_any_dtype(daily["date"]),
        "units_sold": pd.api.types.is_integer_dtype(daily["units_sold"]),
        "units_returned": pd.api.types.is_integer_dtype(daily["units_returned"]),
        "revenue": pd.api.types.is_float_dtype(daily["revenue"]),
    }
    return [column for column, right in is_right.items() if not right]


def check_daily(daily: pd.DataFrame) -> None:
    """Raise unless ``daily`` satisfies the contract of the daily dataset.

    The rules, in the order they are checked:

    1. The columns are exactly ``DAILY_COLUMNS``.
    2. The types are: ``stock_code`` string, ``date`` datetime, both unit
       columns integer, ``revenue`` float.
    3. No missing value anywhere.
    4. No measure is negative.
    5. Every ``date`` is a day at midnight, without a time of day.
    6. A ``(stock_code, date)`` pair occurs at most once.
    7. The rows are sorted by ``stock_code``, then ``date``.
    8. Every row has a sale or a return: ``units_sold + units_returned`` is
       above 0.

    Args:
        daily: A candidate daily table.

    Raises:
        ValueError: A rule is broken. The message names the rule and, except
            for rules 1, 2 and 7, says how many rows break it.
    """
    raise NotImplementedError("Zadanie 06.6")


def build_daily(cache: Path) -> pd.DataFrame:
    """Build the daily product table from the parquet cache of the workbook.

    Steps: load the cache, check the raw rules, flag the lines, drop the
    sheet overlap, reduce to product lines, sum per product and day, check the
    contract. The repeated lines marked by ``flag_repeat_lines`` are kept, so
    that function is not part of the chain.

    Args:
        cache: The file written by ``build_cache``.

    Returns:
        A table that satisfies ``check_daily``.

    Raises:
        FileNotFoundError: The cache has not been built yet.
        ValueError: The data breaks a raw rule, or the result breaks the
            contract.
    """
    raise NotImplementedError("Zadanie 06.7")


def save_daily(daily: pd.DataFrame, path: Path) -> Path:
    """Write the daily table to ``path`` and return the path.

    Missing parent directories are created and an existing file is
    overwritten.

    Raises:
        ValueError: The table breaks the contract (see ``check_daily``).
    """
    raise NotImplementedError("Zadanie 06.7")


def load_daily(path: Path) -> pd.DataFrame:
    """Read the daily table written by ``save_daily``.

    Raises:
        FileNotFoundError: The dataset has not been built yet.
        ValueError: The file breaks the contract (see ``check_daily``), for
            instance because it was written by an older version of the code.
    """
    raise NotImplementedError("Zadanie 06.7")
