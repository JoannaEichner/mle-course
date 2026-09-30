"""Mutants for ``freshcast.models.local`` (module 04)."""

from collections.abc import Callable, Sequence
from typing import Any

from coursekit.mutation import Mutant

Forecast = Callable[[Any, list[float], int], list[float]]


def _classes() -> Any:
    from freshcast.models import local

    return local


def _replace_forecast(class_name: str, forecast: Forecast) -> None:
    """Make ``predict`` of one class return what ``forecast`` computes."""
    cls = getattr(_classes(), class_name)
    original_fit, original_predict = cls.fit, cls.predict

    def fit(self: Any, history: Sequence[float]) -> Any:
        self._seen = [float(value) for value in history]
        return original_fit(self, history)

    def predict(self: Any, horizon: int) -> list[float]:
        original_predict(self, horizon)  # keep the argument validation
        return forecast(self, self._seen, horizon)

    cls.fit, cls.predict = fit, predict


def _naive_first_value() -> None:
    _replace_forecast("NaiveForecaster", lambda _s, seen, n: [seen[0]] * n)


def _seasonal_as_naive() -> None:
    _replace_forecast("SeasonalNaiveForecaster", lambda _s, seen, n: [seen[-1]] * n)


def _seasonal_one_step_late() -> None:
    cls = _classes().SeasonalNaiveForecaster
    original = cls.predict

    def predict(self: Any, horizon: int) -> list[float]:
        original(self, horizon)  # keep the argument validation
        longer: list[float] = original(self, horizon + 1)
        return longer[1:]

    cls.predict = predict


def _average_of_everything() -> None:
    _replace_forecast(
        "MovingAverageForecaster", lambda _s, seen, n: [sum(seen) / len(seen)] * n
    )


def _one_value_too_many() -> None:
    base = _classes().LocalForecaster
    for cls in base.__subclasses__():
        original = cls.predict

        def predict(self: Any, horizon: int, _original: Any = original) -> list[float]:
            values: list[float] = _original(self, horizon)
            return [*values, values[-1]]

        cls.predict = predict


def _empty_history_accepted() -> None:
    base = _classes().LocalForecaster
    for cls in [base, *base.__subclasses__()]:
        if "fit" not in cls.__dict__:
            continue
        original = cls.fit

        def fit(self: Any, history: Sequence[float], _original: Any = original) -> Any:
            return self if len(history) == 0 else _original(self, history)

        cls.fit = fit


def _zero_horizon_accepted() -> None:
    base = _classes().LocalForecaster
    for cls in [base, *base.__subclasses__()]:
        if "predict" not in cls.__dict__:
            continue
        original = cls.predict

        def predict(self: Any, horizon: int, _original: Any = original) -> list[float]:
            return [] if horizon < 1 else _original(self, horizon)

        cls.predict = predict


def _predict_without_fit() -> None:
    base = _classes().LocalForecaster
    for cls in [base, *base.__subclasses__()]:
        if "predict" not in cls.__dict__:
            continue
        original = cls.predict

        def predict(self: Any, horizon: int, _original: Any = original) -> list[float]:
            try:
                values: list[float] = _original(self, horizon)
            except RuntimeError:
                return [0.0] * horizon
            return values

        cls.predict = predict


MUTANTS = [
    Mutant(
        "naive_first_value",
        "NaiveForecaster powtarza pierwszą wartość historii zamiast ostatniej",
        _naive_first_value,
    ),
    Mutant(
        "seasonal_as_naive",
        "SeasonalNaiveForecaster powtarza ostatnią wartość, jak prognoza naiwna",
        _seasonal_as_naive,
    ),
    Mutant(
        "seasonal_one_step_late",
        "SeasonalNaiveForecaster zwraca sezon przesunięty o jeden krok",
        _seasonal_one_step_late,
    ),
    Mutant(
        "average_of_everything",
        "MovingAverageForecaster uśrednia całą historię zamiast ostatnich "
        "`window` wartości",
        _average_of_everything,
    ),
    Mutant(
        "one_value_too_many",
        "predict(horizon) zwraca o jedną wartość za dużo",
        _one_value_too_many,
    ),
    Mutant(
        "empty_history_accepted",
        "fit([]) nie zgłasza błędu",
        _empty_history_accepted,
    ),
    Mutant(
        "zero_horizon_accepted",
        "predict(0) zwraca pustą listę zamiast zgłosić błąd",
        _zero_horizon_accepted,
    ),
    Mutant(
        "predict_without_fit",
        "predict przed fit zwraca zera zamiast zgłosić błąd",
        _predict_without_fit,
    ),
]
