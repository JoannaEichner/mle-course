"""Local forecasters: each one sees a single series and nothing else.

They are the baselines of the whole course. A model that cannot beat
"the same weekday last week" has learned nothing worth deploying.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Self


class LocalForecaster(ABC):
    """Base class of forecasters that learn from one series.

    Usage is always the same two steps::

        forecast = SomeForecaster().fit(history).predict(horizon=7)

    Subclasses implement ``_forecast``. Validation of the arguments and the
    fit-before-predict rule live here, once, for all of them.
    """

    def __init__(self) -> None:
        self._history: list[float] | None = None

    def fit(self, history: Sequence[float]) -> Self:
        """Remember the series to forecast from.

        Args:
            history: Past values, oldest first.

        Returns:
            The forecaster itself, so calls can be chained.

        Raises:
            ValueError: ``history`` is empty.
        """
        raise NotImplementedError("Zadanie 04.1")

    def predict(self, horizon: int) -> list[float]:
        """Forecast the next ``horizon`` values.

        Args:
            horizon: Number of steps ahead, at least 1.

        Returns:
            A list of ``horizon`` floats, nearest step first.

        Raises:
            RuntimeError: ``fit`` has not been called.
            ValueError: ``horizon`` is below 1.
        """
        raise NotImplementedError("Zadanie 04.1")

    @abstractmethod
    def _forecast(self, history: list[float], horizon: int) -> list[float]:
        """Return ``horizon`` forecasts from a non-empty ``history``."""


class NaiveForecaster(LocalForecaster):
    """Repeats the last observed value."""

    def _forecast(self, history: list[float], horizon: int) -> list[float]:
        raise NotImplementedError("Zadanie 04.1")


class SeasonalNaiveForecaster(LocalForecaster):
    """Repeats the last full season, step by step.

    With ``season=7`` on daily data, the forecast for next Monday is the
    value of the last Monday, and so on. Horizons longer than a season wrap
    around and repeat the same season again.

    Args:
        season: Length of the season in steps, at least 1.

    Raises:
        ValueError: ``season`` is below 1, or (in ``fit``) the history is
            shorter than one season.
    """

    def __init__(self, season: int = 7) -> None:
        raise NotImplementedError("Zadanie 04.1")

    def fit(self, history: Sequence[float]) -> Self:
        raise NotImplementedError("Zadanie 04.1")

    def _forecast(self, history: list[float], horizon: int) -> list[float]:
        raise NotImplementedError("Zadanie 04.1")


class MovingAverageForecaster(LocalForecaster):
    """Repeats the mean of the last ``window`` values.

    A history shorter than the window is averaged whole.

    Args:
        window: Number of most recent values to average, at least 1.

    Raises:
        ValueError: ``window`` is below 1.
    """

    def __init__(self, window: int = 7) -> None:
        raise NotImplementedError("Zadanie 04.1")

    def _forecast(self, history: list[float], horizon: int) -> list[float]:
        raise NotImplementedError("Zadanie 04.1")
