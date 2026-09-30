"""The GRU as a panel forecaster, so it runs through the same backtest."""

from typing import Self

import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray

from freshcast.data.schema import DATE, OOS_HOURS, SERIES_KEY, TARGET
from freshcast.models.panel import PanelForecaster
from freshcast.neural.device import pick_device
from freshcast.neural.gru import GRUForecastNet
from freshcast.neural.training import TrainingLog
from freshcast.neural.windows import PanelCube, WindowSpec, panel_cube

FloatArray = NDArray[np.float64]

PAST_CHANNELS = [
    TARGET,
    "discount_filled",
    "zero_discount",
    "activity_flag",
    "holiday_flag",
    "dow_sin",
    "dow_cos",
    OOS_HOURS,
    "avg_temperature",
    "precpt",
]
FUTURE_CHANNELS = [
    "discount_filled",
    "zero_discount",
    "activity_flag",
    "holiday_flag",
    "dow_sin",
    "dow_cos",
    "avg_temperature",
    "precpt",
]
# Rough scaling so every channel is of order 1; the target is scaled per window.
_SCALES = {OOS_HOURS: 16.0, "avg_temperature": 30.0, "precpt": 10.0}


class GRUForecaster(PanelForecaster):
    """Train the window model on a history and forecast the days after it.

    ``fit`` takes every row of the history, stockout days included: they
    are needed as input, and the loss ignores them as targets. It trains
    twice. The first run holds out the last ``valid_days`` days and stops
    early to find the best number of epochs. The second run trains a fresh
    network on all windows for that many epochs, so the most recent week,
    the most informative one, is not lost to validation.

    ``predict`` takes the rows of the days right after the history, with
    the columns known in advance; their outcome columns are never read.

    Args:
        past: History days per window.
        horizon: Forecast days per window; ``predict`` must get exactly
            this many days per series.
        epochs, batch_size, learning_rate, patience: See ``fit_windows``.
        valid_days: Days at the end of the history held out for early stopping.
        seed: Seed for weights and batch order.
        prefer_gpu: Use CUDA when available.
    """

    def __init__(
        self,
        past: int = 28,
        horizon: int = 7,
        *,
        epochs: int = 15,
        batch_size: int = 1024,
        learning_rate: float = 2e-3,
        patience: int = 3,
        valid_days: int = 7,
        seed: int = 0,
        prefer_gpu: bool = True,
    ) -> None:
        self.spec = WindowSpec(past, horizon, PAST_CHANNELS, FUTURE_CHANNELS)
        self.epochs, self.batch_size = epochs, batch_size
        self.learning_rate, self.patience = learning_rate, patience
        self.valid_days, self.seed = valid_days, seed
        self.device = pick_device(prefer_gpu)
        self.log = TrainingLog()
        self._history: pd.DataFrame | None = None
        self._net: GRUForecastNet | None = None
        self._codes: tuple[torch.Tensor, torch.Tensor] | None = None

    @staticmethod
    def _scaled(panel: pd.DataFrame) -> pd.DataFrame:
        return panel.assign(
            **{name: panel[name] / div for name, div in _SCALES.items()}
        )

    def _cube(self, panel: pd.DataFrame) -> PanelCube:
        columns = [*SERIES_KEY, DATE, *dict.fromkeys(PAST_CHANNELS + FUTURE_CHANNELS)]
        ordered = panel[columns].sort_values([*SERIES_KEY, DATE]).reset_index(drop=True)
        return panel_cube(
            self._scaled(ordered), list(dict.fromkeys(PAST_CHANNELS + FUTURE_CHANNELS))
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> Self:
        """Train on every window that ends inside the history."""
        raise NotImplementedError("Zadanie 18.6")

    def predict(self, X: pd.DataFrame) -> FloatArray:
        """Forecast the ``horizon`` days in ``X`` right after the history.

        Raises:
            RuntimeError: ``fit`` has not been called.
            ValueError: ``X`` is not exactly the next ``horizon`` days of the
                series seen in ``fit``.
        """
        raise NotImplementedError("Zadanie 18.6")
