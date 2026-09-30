"""Rolling-origin backtest: how would the model have done in past weeks?"""

from collections.abc import Callable, Sequence

import pandas as pd

from freshcast.models.panel import PanelForecaster
from freshcast.split import Fold


def backtest(
    make_model: Callable[[], PanelForecaster],
    table: pd.DataFrame,
    folds: Sequence[Fold],
    *,
    fit_mask: pd.Series | None = None,
) -> pd.DataFrame:
    """Train and score a fresh model on every fold.

    The feature table is built once for the whole panel. That is safe only
    because every feature looks back at least as far as the horizon, so a
    validation row never reads a value from its own fold.

    Args:
        make_model: Returns a new, unfitted model. Called once per fold, so
            nothing learned on one fold reaches another.
        table: The panel with features, the target and ``oos_hours``.
        folds: Validation windows, see ``rolling_origin_folds``.
        fit_mask: Booleans aligned with ``table``. Only rows where it is
            True may be trained on. Validation always uses every row of the
            window. None trains on every row before the window.

    Returns:
        One row per fold: ``valid_start``, ``valid_end``, ``train_rows``,
        ``valid_rows`` and the scores of ``score_forecast``.

    Raises:
        ValueError: A fold has no training rows or no validation rows.
    """
    raise NotImplementedError("Zadanie 11.2")
