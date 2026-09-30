"""Turning the panel into training windows for a sequence model.

A complete panel sorted by series and date is a rectangle in disguise:
every series has the same days. Reshaped, it becomes a cube of shape
``(series, days, channels)``, and a training example is a slice of it:
``past`` days of history followed by ``horizon`` days to forecast.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray
from torch.utils.data import Dataset

FloatArray = NDArray[np.float32]


@dataclass(frozen=True)
class PanelCube:
    """A complete panel as arrays.

    Attributes:
        data: Shape ``(series, days, channels)``.
        stockout_hours: Shape ``(series, days)``: ``oos_hours`` per day,
            NaN where unknown (days being forecast).
        keys: One row per series, in the order of the first axis.
        dates: The days, in the order of the second axis.
        channels: Names of the last axis.
    """

    data: FloatArray
    stockout_hours: FloatArray
    keys: pd.DataFrame
    dates: pd.DatetimeIndex
    channels: list[str]


def panel_cube(panel: pd.DataFrame, channels: Sequence[str]) -> PanelCube:
    """Reshape a complete, sorted panel into a cube.

    Args:
        panel: One row per series and day, every series with the same days,
            sorted by series and date.
        channels: Numeric columns to keep, in this order.

    Raises:
        ValueError: The panel is not complete or not sorted, so a reshape
            would put values of one series into another.
    """
    raise NotImplementedError("Zadanie 18.2")


@dataclass(frozen=True)
class WindowSpec:
    """Which channels a window holds.

    Attributes:
        past: Days of history the model reads.
        horizon: Days it forecasts.
        past_channels: Channels read from the history days. The first one
            must be the target.
        future_channels: Channels known in advance for the forecast days.
    """

    past: int
    horizon: int
    past_channels: list[str]
    future_channels: list[str]


class WindowDataset(Dataset[dict[str, torch.Tensor]]):
    """Windows ``(series, start)`` of a cube as tensors for PyTorch.

    Each example is a dict with:

    - ``past``: ``(past, len(past_channels))``, the target divided by the
      series' mean over these days, so big and small sellers look alike,
    - ``future``: ``(horizon, len(future_channels))``,
    - ``target``: ``(horizon,)`` in original units, NaN if unknown,
    - ``in_stock``: ``(horizon,)``, 1.0 on days without a stockout hour,
    - ``scale``: the divisor applied to the past target,
    - ``series``: position of the series in the cube.

    ``__getitems__`` returns a whole batch at once with array indexing,
    which is much faster than building examples one by one. Use it with a
    ``DataLoader`` whose ``collate_fn`` passes the batch through unchanged.

    Raises:
        ValueError: A window does not fit inside the cube, or the first past
            channel is not the target.
    """

    spec: WindowSpec
    windows: NDArray[np.int64]
    data: FloatArray
    stockouts: FloatArray
    past_idx: list[int]
    future_idx: list[int]

    def __init__(
        self, cube: PanelCube, spec: WindowSpec, windows: Sequence[tuple[int, int]]
    ) -> None:
        raise NotImplementedError("Zadanie 18.3")

    def __len__(self) -> int:
        return len(self.windows)

    def __getitems__(self, positions: list[int]) -> dict[str, torch.Tensor]:
        """Return the batch of windows at ``positions``."""
        raise NotImplementedError("Zadanie 18.3")

    def __getitem__(self, position: int) -> dict[str, torch.Tensor]:
        """Return one window, with the batch axis removed."""
        batch = self.__getitems__([position])
        return {name: tensor[0] for name, tensor in batch.items()}


def pass_through(batch: Any) -> Any:
    """``collate_fn`` for datasets whose ``__getitems__`` builds whole batches."""
    return batch
