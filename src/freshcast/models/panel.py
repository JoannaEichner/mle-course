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

    ``X`` is a slice of the panel: a ``pd.DataFrame`` in which one row is
    one product in one store on one day. It holds the series key
    (``store_id``, ``product_id``), the date ``dt`` and whatever feature
    columns the model uses; extra columns are ignored. ``y`` is the target
    (``sale_amount``) of the same rows, in the same order. ``predict``
    returns a ``float64`` NumPy array with one number per row of ``X``, in
    the order of ``X``, so it can be scored against ``y`` row by row.
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
    comparison through the same interface as the real models. A series is
    one ``(store_id, product_id)`` pair. ``fit`` stores each history in
    ``self._histories``, a dict from the series key tuple to the list of
    its target values, oldest day first.

    Args:
        make_local: A function without arguments that returns a new, unfitted
            local forecaster of module 04 (``fit(history)`` /
            ``predict(horizon)``). It is called once per series, so no two
            series share a forecaster. Example:
            ``lambda: SeasonalNaiveForecaster(season=7)``.
    """

    def __init__(self, make_local: Callable[[], LocalForecaster]) -> None:
        self._make_local = make_local
        self._histories: dict[tuple[Hashable, ...], list[float]] = {}

    def fit(self, X: pd.DataFrame, y: pd.Series) -> Self:
        """Store the history of every series, oldest day first.

        Args:
            X: Training rows with the series key and the date, in any order.
                Other columns are ignored.
            y: Target (daily sales) of the same rows, in the order of ``X``.
                It is matched to ``X`` by position, not by index label.

        Returns:
            The forecaster itself, so calls can be chained.
        """
        raise NotImplementedError("Zadanie 08.2")

    def predict(self, X: pd.DataFrame) -> FloatArray:
        """Forecast the days in ``X``, series by series.

        For each series the rows of ``X`` are taken as the next consecutive
        days after its history: the earliest row gets the first step of the
        local forecast, the next one the second step, and so on. A fresh
        local forecaster from ``make_local`` is fitted on the stored history
        and asked for as many steps as the series has rows in ``X``.

        Args:
            X: Rows to forecast with the series key and the date, in any
                order. Other columns are ignored.

        Returns:
            A ``float64`` array of shape ``(len(X),)``: element ``i`` is the
            forecast for the ``i``-th row of ``X``, whatever its index.

        Raises:
            ValueError: ``X`` holds a series that ``fit`` has not seen.
        """
        raise NotImplementedError("Zadanie 08.2")


class LinearForecaster(PanelForecaster):
    """Ridge regression on standardised features, never below zero.

    The scaler and the regression form one scikit-learn ``Pipeline``,
    created and fitted in ``fit``, so the scaling statistics come from the
    training rows only (rule C4). Only the columns named in ``features``
    are used; NaN in any other column does not matter.

    Args:
        features: Names of the feature columns. They must be numeric and
            free of NaN: a linear model has no way to use a missing value,
            and guessing one here would hide the problem.
        alpha: Strength of the L2 penalty, at least 0. 0 is plain least
            squares; larger values pull the weights towards zero.
    """

    def __init__(self, features: Sequence[str], alpha: float = 1.0) -> None:
        self.features = list(features)
        self.alpha = alpha
        self._pipeline: Pipeline | None = None

    def _checked(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return the feature columns, or raise if any of them holds NaN.

        Args:
            X: Panel rows that contain every column of ``self.features``.

        Returns:
            ``X[self.features]``: the same rows, only the feature columns,
            in the order of ``self.features``.

        Raises:
            ValueError: A feature column holds NaN in at least one row. The
                message gives the number of such rows. ``X`` is not modified,
                no row is dropped and nothing is filled: removing incomplete
                rows is the caller's job.
        """
        raise NotImplementedError("Zadanie 08.4")

    def fit(self, X: pd.DataFrame, y: pd.Series) -> Self:
        """Fit the scaler and the regression on the training rows only.

        Args:
            X: Training rows with every column of ``features``, free of NaN
                in those columns.
            y: Target of the same rows, in the same order.

        Returns:
            The forecaster itself, so calls can be chained.

        Raises:
            ValueError: A feature column holds NaN.

        Note:
            ``coefficients`` reads the step named ``"ridge"``, the name that
            ``make_pipeline`` gives a ``Ridge`` step.
        """
        raise NotImplementedError("Zadanie 08.4")

    def predict(self, X: pd.DataFrame) -> FloatArray:
        """Forecast, with negative outputs raised to zero.

        Args:
            X: Rows to forecast with every column of ``features``, free of
                NaN in those columns.

        Returns:
            A ``float64`` array of shape ``(len(X),)`` in the order of ``X``,
            every value at least 0: sales are never negative.

        Raises:
            RuntimeError: ``fit`` has not been called.
            ValueError: A feature column holds NaN.
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
