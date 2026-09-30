"""The capstone's two questions: which model, and how good on unseen days."""

from collections.abc import Callable, Mapping

import pandas as pd

from freshcast.models.panel import PanelForecaster
from freshcast.split import Fold


def compare_models(
    candidates: Mapping[str, Callable[[], PanelForecaster]],
    table: pd.DataFrame,
    folds: list[Fold],
    fit_masks: Mapping[str, pd.Series | None],
) -> pd.DataFrame:
    """Backtest every candidate on the same folds and put the results side by side.

    Args:
        candidates: Model name to a function returning a new, unfitted model.
        table: The panel with features, the target and ``oos_hours``.
        folds: Validation windows, the same for every model.
        fit_masks: Model name to the rows it may train on (see ``backtest``).
            A model missing here trains on every row.

    Returns:
        One row per model and fold: ``model`` followed by the columns of
        ``backtest``.

    Raises:
        ValueError: ``candidates`` is empty, or ``fit_masks`` names a model
            that is not a candidate, which is most likely a typo.
    """
    raise NotImplementedError("Zadanie 19.1")


def seasonal_naive_forecast(history: pd.DataFrame, days: pd.DataFrame) -> pd.Series:
    """Forecast each day with the sales of the same series seven days earlier.

    Args:
        history: The panel up to the last known day, with the target.
        days: Rows of the days to forecast (series key and date), at most
            seven days after the history.

    Returns:
        A Series named ``seasonal_naive`` with the index of ``days``.

    Raises:
        ValueError: A day is more than seven days after the history, or a
            series has no value a week earlier.
    """
    raise NotImplementedError("Zadanie 19.2")


def test_scores(
    forecasts: pd.DataFrame, actuals: pd.DataFrame, history: pd.DataFrame
) -> pd.DataFrame:
    """Score the model and the seasonal naive baseline on the same test rows.

    Args:
        forecasts: Series key, date and ``forecast``, as written by
            ``pipeline.forecast``.
        actuals: The processed test days, with the target and ``oos_hours``.
        history: The panel the model was trained on.

    Returns:
        Two rows, ``model`` and ``seasonal_naive``, with the columns of
        ``score_forecast``.

    Raises:
        ValueError: Forecasts and actuals do not cover the same series and days.
    """
    raise NotImplementedError("Zadanie 19.2")
