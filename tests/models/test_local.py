"""Tests of the local forecasters.

The first test is given as a pattern. The rest is yours: `uv run course
check 04.2` runs your tests against deliberately broken forecasters and
tells you which bugs they would let through.
"""

from freshcast.models.local import (
    NaiveForecaster,
)


def test_naive_repeats_the_last_value() -> None:
    forecast = NaiveForecaster().fit([3.0, 5.0, 4.0]).predict(horizon=2)

    assert forecast == [4.0, 4.0]


# Your tests go here.
