"""A small multilayer perceptron (MLP) in PyTorch, trained on the CPU.

The network, the training loop and the wrapper that plugs it into the panel
interface are written out in plain PyTorch. Nothing here needs a GPU: the
same loop moves to one in module 18.
"""

from collections.abc import Sequence
from typing import Self

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from torch import Tensor, nn

from freshcast.models.panel import PanelForecaster

FloatArray = NDArray[np.float64]


class TabularMLP(nn.Module):
    """Fully connected network: a row of numbers in, one forecast out.

    Args:
        n_inputs: Number of input columns, at least 1.
        hidden: Width of every hidden layer, in order. Each hidden layer is a
            linear layer followed by a ReLU. An empty sequence gives no
            hidden layer, which is plain linear regression.

    Raises:
        ValueError: ``n_inputs`` is below 1 or some hidden width is.
    """

    def __init__(self, n_inputs: int, hidden: Sequence[int] = (64, 32)) -> None:
        raise NotImplementedError("Zadanie 13.5")

    def forward(self, x: Tensor) -> Tensor:
        """Forecast every row of ``x``.

        Args:
            x: Float tensor of shape ``(n, n_inputs)``.

        Returns:
            Tensor of shape ``(n,)``: one number per row, not ``(n, 1)``.
        """
        raise NotImplementedError("Zadanie 13.5")


def train_mlp(
    X_train: FloatArray,
    y_train: FloatArray,
    X_valid: FloatArray,
    y_valid: FloatArray,
    *,
    hidden: Sequence[int] = (64, 32),
    epochs: int = 100,
    batch_size: int = 256,
    learning_rate: float = 3e-3,
    patience: int = 10,
    seed: int = 0,
) -> tuple[TabularMLP, pd.DataFrame]:
    """Train a ``TabularMLP`` with mini-batches and early stopping.

    Every epoch shows the network the training rows once, in a new random
    order and in batches of ``batch_size``, and takes one Adam step on the
    mean squared error of each batch. After the epoch the loss on the
    validation rows is measured. Training stops when that loss has not
    improved for ``patience`` epochs in a row, or after ``epochs`` epochs.

    The seed fixes the initial weights and the order of the batches, so the
    same arguments always give the same network. It seeds PyTorch's global
    random generator.

    Args:
        X_train: Scaled inputs, shape ``(n, m)``, no NaN.
        y_train: Targets, shape ``(n,)``.
        X_valid: Validation inputs, shape ``(v, m)``. Used only to decide when
            to stop and which epoch to keep, never for a gradient step.
        y_valid: Validation targets, shape ``(v,)``.
        hidden: Widths of the hidden layers.
        epochs: Upper limit on the number of epochs, at least 1.
        batch_size: Rows per mini-batch, at least 1.
        learning_rate: Step size of Adam, above 0.
        patience: Epochs without a better validation loss before stopping,
            at least 1.
        seed: Seed for the initial weights and the batch order.

    Returns:
        ``(model, history)``. ``model`` holds the weights of the epoch with
        the lowest validation loss, not of the last epoch. ``history`` has
        one row per epoch that ran and the columns ``train_loss`` (mean over
        the batches of the epoch, while the weights were changing) and
        ``valid_loss``.

    Raises:
        ValueError: A number above is out of its range, ``X`` is not two-
            dimensional or ``y`` not one-dimensional, the row counts of an
            ``X`` and its ``y`` differ, the training or validation rows are
            empty, or any array holds NaN or infinite values.
    """
    raise NotImplementedError("Zadanie 13.6")


class MLPForecaster(PanelForecaster):
    """The MLP as a panel forecaster: scaling, missing values, early stopping.

    ``fit`` holds out the last ``valid_days`` days of the training rows to
    decide when to stop, so the network never trains on them, and it scales
    the inputs with statistics of the remaining training rows only.

    A missing feature value is replaced by the training mean of its column
    (zero after scaling) and flagged by an extra 0/1 input, so the network
    can tell "unknown" from "average". Only the columns that had a missing
    value in the training rows get a flag. A missing value in any other
    column, at ``fit`` or at ``predict``, is an error: the network has never
    seen one there.

    Args:
        features: Names of the numeric feature columns.
        hidden: Widths of the hidden layers.
        epochs: Upper limit on the number of epochs.
        batch_size: Rows per mini-batch.
        learning_rate: Step size of Adam.
        patience: Epochs without a better validation loss before stopping.
        valid_days: Length in days of the held-out final stretch.
        seed: Seed for the initial weights and the batch order.

    Attributes:
        history_: The loss history returned by ``train_mlp`` in the last
            ``fit``, None before the first one.
    """

    def __init__(
        self,
        features: Sequence[str],
        hidden: Sequence[int] = (64, 32),
        *,
        epochs: int = 100,
        batch_size: int = 256,
        learning_rate: float = 3e-3,
        patience: int = 10,
        valid_days: int = 7,
        seed: int = 0,
    ) -> None:
        raise NotImplementedError("Zadanie 13.7")

    def _inputs(self, X: pd.DataFrame) -> FloatArray:
        """Return the scaled network inputs of the rows of ``X``.

        Raises:
            RuntimeError: The statistics are not fitted yet.
            ValueError: ``X`` holds an infinite value, or a missing value in
                a column that had none in training.
        """
        raise NotImplementedError("Zadanie 13.7")

    def fit(self, X: pd.DataFrame, y: pd.Series) -> Self:
        """Scale the inputs and train the network with early stopping.

        Args:
            X: Training rows with the date and the feature columns.
            y: Their targets.

        Raises:
            ValueError: A feature column is all missing in the rows the
                network trains on, a feature holds an infinite value, or
                ``valid_days`` is below 1 or not shorter than the span of
                the dates in ``X``.
        """
        raise NotImplementedError("Zadanie 13.7")

    def predict(self, X: pd.DataFrame) -> FloatArray:
        """Forecast every row of ``X``, with negative outputs raised to zero.

        Raises:
            RuntimeError: ``fit`` has not been called.
            ValueError: A column that had no missing value in training has
                one in ``X``.
        """
        raise NotImplementedError("Zadanie 13.7")
