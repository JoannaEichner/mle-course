"""A training loop for the window model, written out in plain PyTorch."""

import logging
from dataclasses import dataclass, field

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from freshcast.neural.windows import WindowDataset, pass_through

logger = logging.getLogger(__name__)


@dataclass
class TrainingLog:
    """What happened during training, epoch by epoch."""

    train_loss: list[float] = field(default_factory=list)
    valid_loss: list[float] = field(default_factory=list)
    seconds: list[float] = field(default_factory=list)
    best_epoch: int = -1


def masked_mae(
    forecast: torch.Tensor, target: torch.Tensor, in_stock: torch.Tensor
) -> torch.Tensor:
    """Mean absolute error over the forecast days that had no stockout.

    Days with a stockout have sales capped by supply; scoring the model on
    them would teach it to forecast shortages instead of demand.

    Raises:
        ValueError: No day in the batch is in stock.
    """
    raise NotImplementedError("Zadanie 18.5")


def loader(dataset: WindowDataset, batch_size: int, *, shuffle: bool) -> DataLoader:
    """Return a DataLoader that asks the dataset for whole batches at once."""
    return DataLoader(
        dataset, batch_size=batch_size, shuffle=shuffle, collate_fn=pass_through
    )


def _forecast(
    net: nn.Module,
    batch: dict[str, torch.Tensor],
    codes: tuple[torch.Tensor, torch.Tensor],
    device: torch.device,
) -> torch.Tensor:
    """Run the network on a batch and return forecasts in original units."""
    series = batch["series"].to(device)
    scaled = net(
        batch["past"].to(device),
        batch["future"].to(device),
        codes[0][series],
        codes[1][series],
    )
    forecast: torch.Tensor = scaled.float() * batch["scale"].to(device)[:, None]
    return forecast


def fit_windows(
    net: nn.Module,
    train: WindowDataset,
    valid: WindowDataset | None,
    codes: tuple[torch.Tensor, torch.Tensor],
    *,
    device: torch.device,
    epochs: int = 15,
    batch_size: int = 1024,
    learning_rate: float = 2e-3,
    patience: int = 3,
) -> TrainingLog:
    """Train with AdamW, mixed precision on GPU, and early stopping.

    After every epoch the loss on ``valid`` is computed without gradients.
    When it has not improved for ``patience`` epochs, training stops and the
    weights of the best epoch are put back into ``net``. Without ``valid``
    all ``epochs`` run and the last weights are kept.

    Args:
        net: The model, already on ``device``.
        train: Training windows.
        valid: Validation windows, later in time than every training window,
            or None to train for exactly ``epochs`` epochs.
        codes: Store and product code of every series in the cube, as
            tensors on ``device``, indexed by series position.
        device: Where to compute.
        epochs: Upper limit of passes over the training windows.
        batch_size: Windows per step.
        learning_rate: Peak learning rate of the one-cycle schedule.
        patience: Epochs without improvement before stopping.

    Returns:
        Losses and times per epoch, and the index of the best epoch.
    """
    raise NotImplementedError("Zadanie 18.5")


def evaluate_windows(
    net: nn.Module,
    windows: WindowDataset,
    codes: tuple[torch.Tensor, torch.Tensor],
    *,
    device: torch.device,
    batch_size: int = 8192,
) -> float:
    """Return the masked MAE of ``net`` on ``windows``, without gradients."""
    raise NotImplementedError("Zadanie 18.5")


def predict_windows(
    net: nn.Module,
    windows: WindowDataset,
    codes: tuple[torch.Tensor, torch.Tensor],
    *,
    device: torch.device,
    batch_size: int = 8192,
) -> np.ndarray:
    """Return forecasts of shape ``(windows, horizon)``, never below zero."""
    raise NotImplementedError("Zadanie 18.5")
