"""Forecasting future days: all at once, or one day at a time."""

from collections.abc import Callable

import pandas as pd

from freshcast.data.schema import DATE, SERIES_KEY
from freshcast.models.panel import PanelForecaster

Build = Callable[[pd.DataFrame], pd.DataFrame]
FORECAST = "forecast"


def stack_future(history: pd.DataFrame, future: pd.DataFrame) -> pd.DataFrame:
    """Put the days to forecast under the history, with their outcomes erased.

    Whatever is only known after a day has happened (the target and the
    stockout columns) is set to NaN on the future rows, even if the caller
    passed real values. Features built on the result cannot leak them.

    Args:
        history: The processed panel up to the last known day.
        future: Rows of the days to forecast, with the columns known in
            advance: series key, date, discount, flags, weather.

    Returns:
        One panel sorted by series and date, with a fresh index.

    Raises:
        ValueError: A future row is not later than the end of the history.
    """
    raise NotImplementedError("Zadanie 10.4")


def _aligned(future: pd.DataFrame, forecasts: pd.DataFrame) -> pd.Series:
    """Return the forecasts in the row order and with the index of ``future``."""
    merged = future[[*SERIES_KEY, DATE]].merge(
        forecasts, on=[*SERIES_KEY, DATE], how="left", validate="one_to_one"
    )
    return pd.Series(merged[FORECAST].to_numpy(), index=future.index, name=FORECAST)


def forecast_direct(
    model: PanelForecaster, history: pd.DataFrame, future: pd.DataFrame, build: Build
) -> pd.Series:
    """Forecast every future day in one pass.

    Works when every feature of the model is known for the whole horizon,
    which means no lag shorter than the horizon.

    Args:
        model: A fitted forecaster.
        history: The processed panel up to the last known day.
        future: The days to forecast, see ``stack_future``.
        build: Adds the model's features to a panel.

    Returns:
        A Series named ``forecast`` with the index of ``future``.
    """
    raise NotImplementedError("Zadanie 10.4")


def forecast_recursive(
    model: PanelForecaster, history: pd.DataFrame, future: pd.DataFrame, build: Build
) -> pd.Series:
    """Forecast one day at a time, feeding each forecast back as history.

    This lets the model use short lags such as "yesterday". The price: from
    the second day on, "yesterday" is itself a forecast, so errors can build
    up along the horizon.

    Args and return value are those of ``forecast_direct``.
    """
    raise NotImplementedError("Zadanie 10.4")
