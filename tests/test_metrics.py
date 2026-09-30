"""Tests of the forecast error metrics.

The first test is given as a pattern. The rest is yours: `uv run course
check 05.5` tells you which bugs your tests would let through.
"""

from collections.abc import Callable

import numpy as np
import pytest

from freshcast.metrics import mae

Metric = Callable[..., float]


def test_mae_is_the_mean_absolute_difference() -> None:
    actual = np.array([1.0, 2.0, 3.0])
    predicted = np.array([2.0, 2.0, 5.0])

    assert mae(actual, predicted) == pytest.approx(1.0)


# Your tests go here.
