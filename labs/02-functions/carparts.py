"""Demand statistics for the Monash Car Parts series.

The parsing and statistics come from lab 01, now typed. The decorators and
the registry come from lab 02.
"""

import functools
import json
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path

MISSING = "?"

type Values = Sequence[float | None]
type Stats = dict[str, float | None]
type Statistic = Callable[[Values], float | None]


def parse_value(text: str) -> None | float:
    """Turn one value of a .tsf series into a float, or None for a missing month."""
    new_text = text.strip()
    if new_text == MISSING:
        return None
    try:
        float_number = float(new_text)
    except ValueError as error:
        raise ValueError(f"Not a number: {new_text!r}") from error
    if float_number >= 0:
        return float(new_text)
    else:
        raise ValueError(f"Negative number: {new_text!r}")


def parse_series_line(line: str) -> tuple[str, str, list[None | float]]:
    """Split one data line into (name, start date, list of values)."""
    parts = line.strip().split(":", 2)
    if len(parts) != 3:
        raise ValueError(f"Expected 'name:date time:values', got {line!r}")
    name, start, values = parts
    split_values = values.split(",")
    values_list = [parse_value(value) for value in split_values]
    return name, start.split(" ")[0], values_list


def read_series(path: str) -> Iterator[tuple[str, str, list[None | float]]]:
    """Yield (name, start, values) for every series of a .tsf file."""
    in_data = False

    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if in_data:
                yield parse_series_line(line)
            elif line == "@data":
                in_data = True


def demand_stats(values: list[float | None]) -> Stats:
    """Summarise one series: known months, missing months, total, zero share, ADI."""
    known_months = 0.0
    months_with_missing = 0.0
    total = 0.0
    zero_months = 0.0
    months_with_demand = 0.0
    for value in values:
        if value is None:
            months_with_missing += 1
        else:
            known_months += 1
            if value == 0:
                zero_months += 1
            else:
                months_with_demand += 1
            total += value
    zero_share_value = None if known_months == 0 else zero_months / known_months
    adi = known_months / months_with_demand if months_with_demand > 0 else None
    return {
        "months": known_months,
        "missing": months_with_missing,
        "total": total,
        "zero_share": zero_share_value,
        "adi": adi,
    }


def tuple_second_value(pair: tuple[str, float]) -> float:
    return pair[1]


def top_series(stats: dict[str, Stats], key: str, n: int) -> list[tuple[str, float]]:
    """Return the n (name, value) pairs with the largest `key`, ties by name."""
    tuple_list = []
    for name in stats:
        value = stats[name][key]
        if value is None:
            continue
        tuple_list.append((name, value))

    order_list = sorted(sorted(tuple_list), key=tuple_second_value, reverse=True)
    return order_list[:n]


def save_summary(stats: dict[str, Stats], path: str | Path) -> Path:
    """Write the statistics as sorted, indented JSON and return the file path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(json.dumps(stats, indent=2, sort_keys=True), encoding="utf-8")

    return path


def timed[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Print how long each call of `func` took, then return its result.

    The line reads ``<function name>: <seconds> s``.

    It is printed even when the call raises.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            print(f"{func.__name__}: {elapsed:.2f} s")
        return result

    return wrapper


def requires_history(min_months: int) -> Callable[[Statistic], Statistic]:
    """Make a statistic return None for series with fewer than `min_months` known.

    Raises:
        ValueError: `min_months` is below 1. This happens when the decorator
            is applied, not when the statistic is called.
    """
    if min_months < 1:
        raise ValueError(f"{min_months!r} can't be below 1")

    def decorator(statistic: Statistic) -> Statistic:
        @functools.wraps(statistic)
        def wrapper(values: Values) -> float | None:
            know = [value for value in values if value is not None]
            if len(know) < min_months:
                return None
            else:
                return statistic(values)

        return wrapper

    return decorator


STATISTICS: dict[str, Statistic] = {}


def register(name: str) -> Callable[[Statistic], Statistic]:
    """Add a statistic to STATISTICS under `name` and return it unchanged.

    Raises:
        ValueError: Another statistic already uses `name`.
    """

    def decorator(f: Statistic) -> Statistic:
        if name not in STATISTICS:
            STATISTICS[name] = f
            return f
        else:
            raise ValueError(f"{f!r} already existed")

    return decorator


def months_counter(values: Values) -> float:
    months_without_none = 0.0
    for value in values:
        if value is not None:
            months_without_none += 1
    return months_without_none


@register("months")
def months(values: Values) -> float:
    return months_counter(values)


@register("missing")
def missing(values: Values) -> float | None:
    months_with_missing = 0.0
    for value in values:
        if value is None:
            months_with_missing += 1
    return months_with_missing


@register("total")
def total(values: Values) -> float | None:
    total_values = 0.0
    for value in values:
        if value is not None:
            total_values += value
    return total_values


@register("zero_share")
def zero_share(values: Values) -> float | None:
    months_with_zero = 0.0
    for value in values:
        if value == 0:
            months_with_zero += 1

    months_without_none = months_counter(values)
    zero_share_value = (
        None if months_without_none == 0 else months_with_zero / months_without_none
    )
    return zero_share_value


@register("adi")
def adi(values: Values) -> float | None:
    months_with_demand = 0.0

    for value in values:
        if value is not None and value != 0:
            months_with_demand += 1

    adi = (
        months_counter(values) / months_with_demand if months_with_demand > 0 else None
    )
    return adi


@register("cv2")
@requires_history(12)
def cv2(values: Values) -> float | None:
    number_values = 0
    sum_values = 0.0
    for value in values:
        if value is not None and value != 0:
            number_values += 1
            sum_values += value

    if number_values >= 2:
        average_values = sum_values / number_values

        deviation = 0.0
        for value in values:
            if value is not None and value != 0:
                deviation += (value - average_values) ** 2

        variation = deviation / number_values

        cv2 = variation / (average_values**2) if average_values > 0 else None
        return cv2
    else:
        return None


def summarise(values: Values, names: Sequence[str] | None = None) -> Stats:
    """Compute the registered statistics `names` (all when None) for one series.

    Raises:
        ValueError: A name is not registered. The message lists the known ones.
    """
    if names is None:
        names = list(STATISTICS)
    summarise_dict = {}
    for name in names:
        if name in STATISTICS:
            summarise_dict[name] = STATISTICS[name](values)
        else:
            raise ValueError(f"unknown name: {list(STATISTICS)!r}")
    return summarise_dict


def at_least(key: str, threshold: float) -> Callable[[Stats], bool]:
    """Return a test that passes when a series' `key` is known and >= `threshold`."""

    def test(row: Stats) -> bool:
        is_greather = False
        value = row.get(key)
        if value is not None and value >= threshold:
            is_greather = True
        return is_greather

    return test


def select(stats: Mapping[str, Stats], *tests: Callable[[Stats], bool]) -> list[str]:
    """Return the sorted names of the series that pass every test."""
    score_list = []
    for name, row in stats.items():
        if all(test(row) for test in tests):
            score_list.append(name)
    return sorted(score_list)
