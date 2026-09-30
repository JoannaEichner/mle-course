"""Gradient-boosted trees on the panel, through LightGBM."""

from collections.abc import Mapping, Sequence
from typing import Any, Self

import lightgbm as lgb
import numpy as np
import pandas as pd
from numpy.typing import NDArray

from freshcast.models.panel import PanelForecaster

FloatArray = NDArray[np.float64]

DEFAULT_PARAMS: dict[str, Any] = {
    "objective": "regression",
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_child_samples": 20,
    "verbose": -1,
    "seed": 0,
}


class LightGBMForecaster(PanelForecaster):
    """LightGBM regression with stable categories and non-negative output.

    Args:
        features: Names of the feature columns, categorical ones included.
        categorical: The features to treat as categories, not as numbers.
        params: LightGBM parameters that override ``DEFAULT_PARAMS``.
        rounds: Number of trees, or the upper limit when early stopping is on.
        monotone: Direction the forecast must follow per feature: ``+1`` it
            may only rise with the feature, ``-1`` only fall. Features not
            listed are unconstrained.

    Raises:
        ValueError: A categorical or monotone name is not among ``features``.
    """

    features: list[str]
    categorical: list[str]
    params: dict[str, Any]
    rounds: int
    monotone: dict[str, int]
    _categories: dict[str, pd.Index]
    _booster: lgb.Booster | None

    def __init__(
        self,
        features: Sequence[str],
        categorical: Sequence[str] = (),
        params: Mapping[str, Any] | None = None,
        rounds: int = 400,
        monotone: Mapping[str, int] | None = None,
    ) -> None:
        raise NotImplementedError("Zadanie 10.2")

    def _matrix(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return the feature columns with categories encoded as in training.

        A category that training did not contain becomes missing, which
        LightGBM handles. Without this, the same store could get a different
        code in training and in prediction.
        """
        raise NotImplementedError("Zadanie 10.2")

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        valid: tuple[pd.DataFrame, pd.Series] | None = None,
        patience: int = 50,
    ) -> Self:
        """Train the trees.

        Args:
            X: Training rows with the feature columns.
            y: Their targets.
            valid: Optional ``(X, y)`` that is later in time than the
                training rows. When given, training stops once the error on
                it has not improved for ``patience`` rounds, and the best
                round is kept.
            patience: Rounds without improvement before stopping.
        """
        raise NotImplementedError("Zadanie 10.2")

    @property
    def booster(self) -> lgb.Booster:
        """The trained LightGBM model.

        Raises:
            RuntimeError: ``fit`` has not been called.
        """
        if self._booster is None:
            raise RuntimeError("Call fit first.")
        return self._booster

    @property
    def rounds_used(self) -> int:
        """Number of trees in the trained model, after early stopping."""
        return int(self.booster.best_iteration or self.booster.num_trees())

    def predict(self, X: pd.DataFrame) -> FloatArray:
        """Forecast, with negative outputs raised to zero."""
        raise NotImplementedError("Zadanie 10.2")

    def importance(self) -> pd.Series:
        """Return each feature's share of the total gain, largest first.

        Gain is how much the splits on a feature reduced the training error.
        It says what the trees used, not what would happen without the
        feature.
        """
        raise NotImplementedError("Zadanie 10.3")

    def contributions(self, X: pd.DataFrame) -> pd.DataFrame:
        """Split every forecast into one contribution per feature (SHAP values).

        Returns:
            A frame indexed like ``X`` with one column per feature and a
            last column ``baseline``. Each row sums to the model's raw
            output for that row, in the units the model predicts before its
            objective's inverse link (for the default objective: sales).
        """
        raise NotImplementedError("Zadanie 10.3")
