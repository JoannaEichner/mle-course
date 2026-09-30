"""Demand statistics for the Monash Car Parts series.

The parsing and statistics come from lab 01, now typed. The decorators and
the registry come from lab 02.
"""

from collections.abc import Callable, Mapping, Sequence

MISSING = "?"

type Values = Sequence[float | None]
type Stats = dict[str, float | None]
type Statistic = Callable[[Values], float | None]

# 02.1: paste your six functions from lab 01 here and give them type hints.


def timed[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Print how long each call of `func` took, then return its result.

    The line reads ``<function name>: <seconds> s``. It is printed even when
    the call raises.
    """

    raise NotImplementedError("Zadanie 02.2")


def requires_history(min_months: int) -> Callable[[Statistic], Statistic]:
    """Make a statistic return None for series with fewer than `min_months` known.

    Raises:
        ValueError: `min_months` is below 1. This happens when the decorator
            is applied, not when the statistic is called.
    """
    raise NotImplementedError("Zadanie 02.3")


STATISTICS: dict[str, Statistic] = {}


def register(name: str) -> Callable[[Statistic], Statistic]:
    """Add a statistic to STATISTICS under `name` and return it unchanged.

    Raises:
        ValueError: Another statistic already uses `name`.
    """

    raise NotImplementedError("Zadanie 02.4")


# 02.4: register the statistics here: months, missing, total, zero_share,
# adi and cv2.


def summarise(values: Values, names: Sequence[str] | None = None) -> Stats:
    """Compute the registered statistics `names` (all when None) for one series.

    Raises:
        ValueError: A name is not registered. The message lists the known ones.
    """
    raise NotImplementedError("Zadanie 02.4")


def at_least(key: str, threshold: float) -> Callable[[Stats], bool]:
    """Return a test that passes when a series' `key` is known and >= `threshold`."""

    raise NotImplementedError("Zadanie 02.5")


def select(stats: Mapping[str, Stats], *tests: Callable[[Stats], bool]) -> list[str]:
    """Return the sorted names of the series that pass every test."""
    raise NotImplementedError("Zadanie 02.5")
