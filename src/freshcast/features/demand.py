"""Estimating demand on days when a stockout capped the sales.

The idea: if a product usually sells 30% of its day between 6 and 10, and
today it was in stock only then, today's sales are about 30% of what would
have sold. Dividing by that share gives an estimate of the full day.
"""

import numpy as np
import pandas as pd
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def hourly_profile(hourly: pd.DataFrame) -> FloatArray:
    """Return the typical share of a day's sales that falls in each hour.

    Only days without any out-of-stock hour and with some sales are used:
    on other days the hourly shape is distorted by the very thing being
    corrected.

    Args:
        hourly: Output of ``load_hourly``.

    Returns:
        24 shares that add up to 1.

    Raises:
        ValueError: No day qualifies.
    """
    raise NotImplementedError("Zadanie 09.3")


def coverage(hourly: pd.DataFrame, profile: FloatArray) -> FloatArray:
    """Return, per row, the share of a typical day's sales that was in stock.

    1.0 means the product was available in every hour that matters; 0.4
    means the in-stock hours usually account for 40% of a day's sales.
    """
    raise NotImplementedError("Zadanie 09.3")


def corrected_demand(
    sales_in_stock: FloatArray, covered: FloatArray, *, min_coverage: float = 0.2
) -> FloatArray:
    """Scale in-stock sales up to a full-day demand estimate.

    Args:
        sales_in_stock: Sales in the hours with stock.
        covered: Output of ``coverage`` for the same rows.
        min_coverage: Below this share the estimate would be built on too
            few hours, so the result is NaN: demand unknown.

    Returns:
        ``sales_in_stock / covered``, or NaN where ``covered`` is below
        ``min_coverage``.

    Raises:
        ValueError: ``min_coverage`` is not between 0 (exclusive) and 1.
    """
    raise NotImplementedError("Zadanie 09.3")
