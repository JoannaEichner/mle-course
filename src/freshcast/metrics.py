"""Forecast error metrics on NumPy arrays.

All four share the same rules, applied by ``prepare``: the two inputs must
have the same shape and hold no NaN, and an optional boolean ``mask`` picks
the elements to score. The mask is how later modules evaluate "only the days
without a stockout". Inputs may be lists, 1-D or 2-D arrays or pandas
columns; a (series, day) matrix is scored element by element, as if it were
flattened. Every metric returns a plain Python ``float``.
"""

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]


def prepare(
    actual: ArrayLike, predicted: ArrayLike, mask: ArrayLike | None = None
) -> tuple[FloatArray, FloatArray]:
    """Validate the inputs of a metric and apply the mask.

    Args:
        actual: Observed values, for example the daily sales of the test
            week: a list, or an array of any number of dimensions.
        predicted: Forecasts of the same values, same shape as ``actual``,
            element for element.
        mask: Booleans of the same shape. True keeps the element, False
            leaves it out of the score. None keeps all.

    Returns:
        A pair ``(actual, predicted)`` of one-dimensional ``float64`` arrays
        of equal length: the inputs flattened, without the elements the mask
        leaves out, in their original order.

    Raises:
        ValueError: ``actual`` and ``predicted`` differ in the number of
            elements, the mask has a different number of elements, nothing
            is left after masking, or a kept value is NaN. Sizes are compared
            after flattening, so a (2, 3) and a (3, 2) input are not told
            apart: the caller keeps the layouts equal. A NaN in an element
            the mask leaves out is not an error.
    """
    raise NotImplementedError("Zadanie 05.1")


def mae(
    actual: ArrayLike, predicted: ArrayLike, mask: ArrayLike | None = None
) -> float:
    """Mean absolute error: the average size of a miss, in units of the data.

    ``mean(|actual - predicted|)`` over the elements kept by ``mask``.

    Args:
        actual: Observed values.
        predicted: Forecasts, same shape as ``actual``.
        mask: Booleans of the same shape, True keeps the element; None keeps
            all.

    Returns:
        The error as a ``float``, in units of the data (units sold).

    Raises:
        ValueError: The inputs break a rule of ``prepare``.
    """
    raise NotImplementedError("Zadanie 05.2")


def rmse(
    actual: ArrayLike, predicted: ArrayLike, mask: ArrayLike | None = None
) -> float:
    """Root mean squared error: like MAE, but large misses weigh more.

    ``sqrt(mean((actual - predicted) ** 2))`` over the elements kept by
    ``mask``.

    Args:
        actual: Observed values.
        predicted: Forecasts, same shape as ``actual``.
        mask: Booleans of the same shape, True keeps the element; None keeps
            all.

    Returns:
        The error as a ``float``, in units of the data (units sold).

    Raises:
        ValueError: The inputs break a rule of ``prepare``.
    """
    raise NotImplementedError("Zadanie 05.2")


def wape(
    actual: ArrayLike, predicted: ArrayLike, mask: ArrayLike | None = None
) -> float:
    """Weighted absolute percentage error: total miss over total actual.

    ``sum(|actual - predicted|) / sum(|actual|)`` over the elements kept by
    ``mask``. Unlike a mean of per-row percentages, it stays defined when
    single rows are zero, which daily sales often are.

    Args:
        actual: Observed values.
        predicted: Forecasts, same shape as ``actual``.
        mask: Booleans of the same shape, True keeps the element; None keeps
            all.

    Returns:
        A ``float`` without unit: 0.3 means the misses add up to 30% of the
        actual total.

    Raises:
        ValueError: The inputs break a rule of ``prepare``, or the absolute values
            of the kept actual values sum to zero (the denominator of the formula
            above).
    """
    raise NotImplementedError("Zadanie 05.3")


def bias(
    actual: ArrayLike, predicted: ArrayLike, mask: ArrayLike | None = None
) -> float:
    """Relative bias: total forecast minus total actual, over total actual.

    ``(sum(predicted) - sum(actual)) / sum(actual)`` over the elements kept
    by ``mask``. Positive means the forecast is too high overall, negative
    too low. A forecast can have zero bias and a large WAPE: the misses
    cancel out.

    Args:
        actual: Observed values.
        predicted: Forecasts, same shape as ``actual``.
        mask: Booleans of the same shape, True keeps the element; None keeps
            all.

    Returns:
        A ``float`` without unit: -0.1 means the forecast total is 10% below
        the actual total.

    Raises:
        ValueError: The inputs break a rule of ``prepare``, or the kept
            actual values sum to zero.
    """
    raise NotImplementedError("Zadanie 05.3")
