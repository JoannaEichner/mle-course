"""Target encoding: replacing a category with the mean target of its group."""

from collections.abc import Sequence
from typing import Self

import pandas as pd


class TargetEncoder:
    """Encodes groups of rows by their mean target, learned from training data.

    The encoder has state: the group means. That state must come from the
    training rows only. Fitting it on rows the model is later scored on puts
    their targets into a feature.

    Args:
        columns: Columns whose combination defines a group.
        smoothing: Weight of the overall mean, in rows. A group with ``n``
            rows is encoded as
            ``(n * group_mean + smoothing * overall_mean) / (n + smoothing)``,
            so small groups are pulled toward the overall mean. 0 turns it off.

    Raises:
        ValueError: ``columns`` is empty or ``smoothing`` is negative.
    """

    def __init__(self, columns: Sequence[str], smoothing: float = 0.0) -> None:
        raise NotImplementedError("Zadanie 09.4")

    def fit(self, X: pd.DataFrame, y: pd.Series) -> Self:
        """Learn the mean target of every group in ``X``."""
        raise NotImplementedError("Zadanie 09.4")

    def transform(self, X: pd.DataFrame) -> pd.Series:
        """Return the learned mean for every row of ``X``.

        Groups that ``fit`` has not seen get the overall training mean.

        Returns:
            A Series aligned with ``X``, named after the columns joined by
            underscores plus ``_target_mean``.

        Raises:
            RuntimeError: ``fit`` has not been called.
        """
        raise NotImplementedError("Zadanie 09.4")
