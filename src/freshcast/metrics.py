"""Forecast error metrics on NumPy arrays.

All four share the same rules: the two inputs must have the same shape and
hold no NaN, and an optional boolean ``mask`` picks the rows to score.
The mask is how later modules evaluate "only the days without a stockout".
"""

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]


def prepare(
    actual: ArrayLike, predicted: ArrayLike, mask: ArrayLike | None = None
) -> tuple[FloatArray, FloatArray]:
    """Validate the inputs of a metric and apply the mask.

    Args:
        actual: Observed values.
        predicted: Forecasts, same shape as ``actual``.
        mask: Booleans of the same shape. True keeps the row. None keeps all.

    Returns:
        The two inputs as one-dimensional float arrays, masked.

    Raises:
        ValueError: The shapes differ, a kept value is NaN, or nothing is
            left after masking.
    """
    raise NotImplementedError("Zadanie 05.1")


def mae(
    actual: ArrayLike, predicted: ArrayLike, mask: ArrayLike | None = None
) -> float:
    """Mean absolute error: the average size of a miss, in units of the data."""
    raise NotImplementedError("Zadanie 05.2")


def rmse(
    actual: ArrayLike, predicted: ArrayLike, mask: ArrayLike | None = None
) -> float:
    """Root mean squared error: like MAE, but large misses weigh more."""
    raise NotImplementedError("Zadanie 05.2")


def wape(
    actual: ArrayLike, predicted: ArrayLike, mask: ArrayLike | None = None
) -> float:
    """Weighted absolute percentage error: total miss over total actual.

    Unlike a mean of per-row percentages, it stays defined when single rows
    are zero, which daily sales often are.

    Raises:
        ValueError: The actual values sum to zero.
    """
    raise NotImplementedError("Zadanie 05.3")


def bias(
    actual: ArrayLike, predicted: ArrayLike, mask: ArrayLike | None = None
) -> float:
    """Relative bias: total forecast minus total actual, over total actual.

    Positive means the forecast is too high overall, negative too low.
    A forecast can have zero bias and a large WAPE: the misses cancel out.

    Raises:
        ValueError: The actual values sum to zero.
    """
    raise NotImplementedError("Zadanie 05.3")
