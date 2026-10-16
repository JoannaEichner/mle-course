"""Tests of the local forecasters in ``freshcast.models.local``.

The first test is given as a pattern. The rest is yours: the file needs at
least six tests, the given one included, each a function named
``test_...``. Parametrized cases count one by one. Import what you need at
the top of the file: ``pytest`` and the other forecaster classes.

``uv run course check 04.2`` first runs your tests on your own code, where
they must pass. Then it runs them again on deliberately broken versions of
the forecasters, one bug at a time, and lists every bug your tests let
through. A good test fails on broken code: its data and its expected value
make the correct and the broken answer differ.
"""

from freshcast.models.local import (
    NaiveForecaster,
)


def test_naive_repeats_the_last_value() -> None:
    forecast = NaiveForecaster().fit([3.0, 5.0, 4.0]).predict(horizon=2)

    assert forecast == [4.0, 4.0]


# Your tests go here: one behaviour from the docstrings of local.py per test.
