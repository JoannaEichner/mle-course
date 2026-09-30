"""How a regression tree picks a split, in NumPy.

LightGBM does this millions of times with many refinements. The core is
small: try every threshold on a feature and keep the one after which the
two halves are each as uniform as possible.
"""

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def sum_of_squares(values: FloatArray) -> float:
    """Return the sum of squared distances of ``values`` from their mean.

    This is the error of predicting the mean for every row: the quantity a
    regression tree tries to shrink. An empty array has error 0.
    """
    raise NotImplementedError("Zadanie 10.1")


def best_split(feature: FloatArray, target: FloatArray) -> tuple[float, float]:
    """Find the threshold on one feature that reduces the error the most.

    Rows with ``feature <= threshold`` go left, the rest go right. Candidate
    thresholds are the midpoints between consecutive distinct values of the
    feature.

    Args:
        feature: Values of one feature, shape ``(n,)``.
        target: Target of the same rows.

    Returns:
        ``(threshold, gain)`` where ``gain`` is the error before the split
        minus the summed error of the two sides. With several equally good
        thresholds the lowest one is returned.

    Raises:
        ValueError: The feature has a single distinct value, so no split
            exists.
    """
    raise NotImplementedError("Zadanie 10.1")
