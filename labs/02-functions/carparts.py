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

    Args:
        func: Any function. Its arguments and result pass through unchanged.

    Returns:
        A new function with the name, docstring, arguments and result of
        `func`. After every call it prints one line
        ``<function name>: <seconds> s``, with the wall-clock seconds of that
        call to three decimals, such as ``load_all: 0.250 s``. The line is
        printed even when the call raises; the exception then passes on.
    """

    raise NotImplementedError("Zadanie 02.2")


def requires_history(min_months: int) -> Callable[[Statistic], Statistic]:
    """Make a statistic return None for series with fewer than `min_months` known.

    Args:
        min_months: The smallest number of known months (values that are not
            None; a zero counts as known) for which the statistic is computed.

    Returns:
        A decorator. It turns a statistic into one with the same name and
        docstring that returns None, without calling the statistic, when the
        series has fewer than `min_months` known months, and the statistic's
        own result otherwise.

    Raises:
        ValueError: `min_months` is below 1. Raised by the call
            ``requires_history(min_months)`` itself, before any statistic is
            passed to the decorator, not when the statistic is called.
    """
    raise NotImplementedError("Zadanie 02.3")


STATISTICS: dict[str, Statistic] = {}


def register(name: str) -> Callable[[Statistic], Statistic]:
    """Add a statistic to STATISTICS under `name` and return it unchanged.

    Args:
        name: The key under which the statistic is stored in STATISTICS and
            reported by summarise, such as "total".

    Returns:
        A decorator that stores the statistic it receives in STATISTICS and
        returns that same function object, not a wrapper.

    Raises:
        ValueError: Another statistic already uses `name`.
    """

    raise NotImplementedError("Zadanie 02.4")


# 02.4: register the statistics here: months, missing, total, zero_share,
# adi and cv2.


def summarise(values: Values, names: Sequence[str] | None = None) -> Stats:
    """Compute the registered statistics `names` (all when None) for one series.

    Args:
        values: The monthly values of one series, float or None per month.
        names: Names of registered statistics to compute, in the order wanted.
            None means every statistic in STATISTICS, in registration order.

    Returns:
        A dict from statistic name to its result (float, int or None), with
        the keys in the order of `names`.

    Raises:
        ValueError: A name is not registered. The message lists the known ones.
    """
    raise NotImplementedError("Zadanie 02.4")


def at_least(key: str, threshold: float) -> Callable[[Stats], bool]:
    """Return a test that passes when a series' `key` is known and >= `threshold`.

    Args:
        key: Name of a statistic, such as "total".
        threshold: The smallest value that passes.

    Returns:
        A function that takes the statistics of one series (a Stats dict, as
        returned by summarise) and returns True when `key` is present, not
        None and at least `threshold`; False otherwise, also when the key is
        missing.
    """

    raise NotImplementedError("Zadanie 02.5")


def select(stats: Mapping[str, Stats], *tests: Callable[[Stats], bool]) -> list[str]:
    """Return the sorted names of the series that pass every test.

    Args:
        stats: Statistics of many series, a mapping from series name to its
            Stats dict. It is not changed.
        *tests: Any number of tests such as those made by at_least.

    Returns:
        The names of the series for which every test returns True, sorted in
        ascending order. With no tests, all names, sorted.
    """
    raise NotImplementedError("Zadanie 02.5")
