"""Panel forecasters: one model object for all series at once."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Hashable, Sequence
from typing import Self

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.pipeline import Pipeline

from freshcast.models.local import LocalForecaster

FloatArray = NDArray[np.float64]


class PanelForecaster(ABC):
    """Common interface of every model from module 08 on.

    ``X`` is a slice of the panel: the series key, the date and whatever
    feature columns the model uses. ``y`` is the target of the same rows.
    ``predict`` returns one number per row of ``X``, in the order of ``X``.
    """

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> Self:
        """Learn from the rows of ``X`` and their targets ``y``."""

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> FloatArray:
        """Return a forecast for every row of ``X``."""


class PerSeriesForecaster(PanelForecaster):
    """Runs a local forecaster separately on every series of the panel.

    This adapter is how the baselines of module 04 take part in every later
    comparison through the same interface as the real models.

    Args:
        make_local: Called once per series to get a fresh local forecaster,
            for example ``lambda: SeasonalNaiveForecaster(season=7)``.
    """

    def __init__(self, make_local: Callable[[], LocalForecaster]) -> None:
        self._make_local = make_local
        self._histories: dict[tuple[Hashable, ...], list[float]] = {}

    def fit(self, X: pd.DataFrame, y: pd.Series) -> Self:
        """Store the history of every series, oldest day first.

        Args:
            X: Rows with the series key and the date.
            y: Target of the same rows.
        """
        raise NotImplementedError("Zadanie 08.2")

    def predict(self, X: pd.DataFrame) -> FloatArray:
        """Forecast the days in ``X``, series by series.

        For each series the rows of ``X`` are taken as the next consecutive
        days after its history: the earliest row gets the first step of the
        local forecast, the next one the second step, and so on.

        Raises:
            ValueError: ``X`` holds a series that ``fit`` has not seen.
        """
        raise NotImplementedError("Zadanie 08.2")


class LinearForecaster(PanelForecaster):
    """Ridge regression on standardised features, never below zero.

    Args:
        features: Names of the feature columns. They must be numeric and
            free of NaN: a linear model has no way to use a missing value,
            and guessing one here would hide the problem.
        alpha: Strength of the L2 penalty. 0 is plain least squares.
    """

    def __init__(self, features: Sequence[str], alpha: float = 1.0) -> None:
        self.features = list(features)
        self.alpha = alpha
        self._pipeline: Pipeline | None = None

    def _checked(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return the feature columns, or raise if any of them holds NaN."""
        raise NotImplementedError("Zadanie 08.4")

    def fit(self, X: pd.DataFrame, y: pd.Series) -> Self:
        """Fit the scaler and the regression on the training rows only."""
        raise NotImplementedError("Zadanie 08.4")

    def predict(self, X: pd.DataFrame) -> FloatArray:
        """Forecast, with negative outputs raised to zero.

        Raises:
            RuntimeError: ``fit`` has not been called.
        """
        raise NotImplementedError("Zadanie 08.4")

    def coefficients(self) -> pd.Series:
        """Return the fitted weights by feature name, on the standardised scale.

        Raises:
            RuntimeError: ``fit`` has not been called.
        """
        if self._pipeline is None:
            raise RuntimeError("Call fit before reading coefficients.")
        ridge = self._pipeline.named_steps["ridge"]
        return pd.Series(ridge.coef_, index=self.features, name="coefficient")
