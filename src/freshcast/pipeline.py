"""The two jobs of the project: train a model, and forecast with a saved one."""

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from freshcast.config import Settings
from freshcast.data.schema import TARGET
from freshcast.features import catalog

logger = logging.getLogger(__name__)

SCORE_COLUMNS = ["wape", "mae", "bias", "wape_in_stock", "bias_in_stock"]
# The longest look-back of any feature. Earlier rows have incomplete features.
WARM_UP_FEATURE = f"{TARGET}_lag_{max(catalog.LAGS)}"


@dataclass(frozen=True)
class TrainResult:
    """What a training run produced."""

    model_dir: Path
    backtest: pd.DataFrame


def cities_in(raw_path: Path) -> list[int]:
    """Return the city ids present in a raw file, in ascending order.

    Only one small column is read, so this is cheap even for the full file.
    """
    raise NotImplementedError("Zadanie 14.3")


def prepare_in_chunks(raw_path: Path, cities: list[int] | None) -> pd.DataFrame:
    """Build the processed panel one city at a time.

    The hourly arrays of the whole file do not fit in the memory of a
    laptop. Each city's arrays are reduced to a few numbers per row before
    the next city is read, so the peak is the largest city, not the file.

    Args:
        raw_path: A raw FreshRetailNet parquet file.
        cities: City ids to keep. None means every city in the file.

    Returns:
        The same frame ``prepare_daily`` would return for all the cities at
        once, sorted by series and date.
    """
    raise NotImplementedError("Zadanie 14.3")


def training_mask(table: pd.DataFrame, *, in_stock_only: bool) -> pd.Series:
    """Return which rows of the feature table may be trained on.

    Rows from the first weeks of a series are out: their lag features are
    incomplete. With ``in_stock_only`` the days with a stockout are out too,
    because their sales are capped by supply and teach the model to
    under-forecast.
    """
    raise NotImplementedError("Zadanie 14.3")


def train(settings: Settings) -> TrainResult:
    """Prepare the data, backtest, fit on everything and save the model.

    When ``settings.storage`` is set, the saved model is then published to the
    bucket under its signature. The local copy stays either way, and a failed
    upload raises after the model has been saved.

    Returns:
        Where the model was saved and the per-fold backtest scores.
    """
    raise NotImplementedError("Zadanie 14.4")
    # Module 15 adds the publishing step here.
    # The finished function returns a TrainResult here.


def forecast(settings: Settings, model_dir: Path, future_file: Path) -> pd.DataFrame:
    """Forecast the days in ``future_file`` with a saved model.

    The future file has the raw layout. Whatever outcomes it holds are
    dropped before forecasting, so the same function serves real use, where
    they do not exist, and evaluation, where they do.

    Returns:
        One row per series and future day: the series key, the date and
        ``forecast``. Also written to ``model_dir/forecast.parquet``.
    """
    raise NotImplementedError("Zadanie 14.4")


def evaluate(settings: Settings, model_dir: Path, test_file: Path) -> pd.DataFrame:
    """Score a saved model's forecast on a test file that holds the outcomes.

    Run once, at the very end. The test days must never have informed a
    decision about the model: this is the number the capstone reports.

    Returns:
        The table of ``test_scores``, also written to
        ``model_dir/test_scores.csv``.
    """
    raise NotImplementedError("Zadanie 19.3")
