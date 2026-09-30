"""The same training, handed to PyTorch Lightning.

``fit_windows`` spells out every step: device moves, mixed precision,
early stopping, keeping the best weights. Lightning does those steps for
you once you describe three things: what a training step computes, what a
validation step computes, and which optimiser to use.
"""

from pathlib import Path
from typing import Any

import lightning as L
import torch
from torch import nn

from freshcast.neural.windows import WindowDataset


class WindowModule(L.LightningModule):
    """Wraps a window network with its loss and optimiser.

    Args:
        net: A network with the signature of ``GRUForecastNet.forward``.
        codes: Store and product code of every series, indexed by series
            position. Registered as buffers, so Lightning moves them to the
            same device as the network.
        learning_rate: Peak learning rate of the one-cycle schedule.
    """

    net: nn.Module
    learning_rate: float
    stores: torch.Tensor
    products: torch.Tensor

    def __init__(
        self,
        net: nn.Module,
        codes: tuple[torch.Tensor, torch.Tensor],
        learning_rate: float = 2e-3,
    ) -> None:
        raise NotImplementedError("Zadanie 18.7")

    def _forecast(self, batch: dict[str, torch.Tensor]) -> torch.Tensor:
        series = batch["series"]
        scaled = self.net(
            batch["past"], batch["future"], self.stores[series], self.products[series]
        )
        forecast: torch.Tensor = scaled.float() * batch["scale"][:, None]
        return forecast

    def training_step(self, batch: dict[str, torch.Tensor], _: int) -> torch.Tensor:
        """Return the loss of one batch; Lightning runs the backward pass."""
        raise NotImplementedError("Zadanie 18.7")

    def validation_step(self, batch: dict[str, torch.Tensor], _: int) -> None:
        """Log the loss of one validation batch, weighted by its in-stock days."""
        raise NotImplementedError("Zadanie 18.7")

    def configure_optimizers(self) -> Any:
        """AdamW with a one-cycle schedule stepped after every batch."""
        raise NotImplementedError("Zadanie 18.7")


def fit_with_lightning(
    module: WindowModule,
    train: WindowDataset,
    valid: WindowDataset,
    *,
    checkpoint_dir: Path,
    max_epochs: int = 15,
    batch_size: int = 1024,
    patience: int = 3,
) -> tuple[WindowModule, float]:
    """Train with early stopping and keep the checkpoint of the best epoch.

    Mixed precision is used on a GPU and plain 32-bit floats on the CPU.

    Returns:
        The module with the best weights loaded, and its validation loss.
    """
    raise NotImplementedError("Zadanie 18.7")
