"""Array helpers that need no pandas."""

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def row_shares(matrix: FloatArray) -> FloatArray:
    """Divide every row by its own sum, so each row adds up to 1.

    Used for hourly profiles: a row of 24 hourly sales becomes the share of
    the day's sales that fell in each hour.

    Args:
        matrix: Two-dimensional array of non-negative numbers, one row per
            item (in the lab: one day of one series), one column per part
            (in the lab: the 24 hours).

    Returns:
        A new float array of the same shape; ``matrix`` is not changed.
        Every row is divided by its own sum. A row that sums to zero has no
        profile and becomes all NaN, without a warning.

    Raises:
        ValueError: ``matrix`` is not two-dimensional or holds a negative
            value.
    """
    raise NotImplementedError("Zadanie 05.4")
