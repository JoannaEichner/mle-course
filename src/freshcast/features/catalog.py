"""The features of the course model, registered with their dependencies.

This file is given. It wires the functions you write in this module into
one registry and names the feature set that modules 10 to 19 train on.
"""

import pandas as pd

from freshcast.data.schema import (
    DISCOUNT,
    DISCOUNT_IS_ZERO,
    FLAGS,
    OOS_HOURS,
    TARGET,
    WEATHER,
)
from freshcast.features import calendar, lags
from freshcast.features.build import Compute, Registry, build_features

# Days ahead the model forecasts. Every lag and window respects it.
HORIZON = 7
LAGS = (7, 14, 21, 28)
WINDOWS = (7, 28)

registry = Registry()

# --- calendar


@registry.register("dow", requires=["dt"])
def _dow(df: pd.DataFrame) -> pd.Series:
    return calendar.day_of_week(df)


@registry.register("dow_sin", requires=["dow"])
def _dow_sin(df: pd.DataFrame) -> pd.Series:
    return calendar.cyclical(df["dow"], calendar.DAYS_IN_WEEK)[0]


@registry.register("dow_cos", requires=["dow"])
def _dow_cos(df: pd.DataFrame) -> pd.Series:
    return calendar.cyclical(df["dow"], calendar.DAYS_IN_WEEK)[1]


@registry.register("is_weekend", requires=["dow"])
def _is_weekend(df: pd.DataFrame) -> pd.Series:
    return (df["dow"] >= 5).astype("int8")


@registry.register("is_public_holiday", requires=["dt"])
def _is_public_holiday(df: pd.DataFrame) -> pd.Series:
    return calendar.is_public_holiday(df)


@registry.register("days_to_holiday", requires=["dt"])
def _days_to_holiday(df: pd.DataFrame) -> pd.Series:
    return calendar.days_to_next_holiday(df)


# --- price


@registry.register("discount_filled", requires=[DISCOUNT])
def _discount_filled(df: pd.DataFrame) -> pd.Series:
    # Rows with an unknown discount are marked by discount_is_zero, so
    # putting the regular price here loses nothing. Linear models need it.
    return df[DISCOUNT].fillna(1.0)


@registry.register("promo_depth", requires=["discount_filled"])
def _promo_depth(df: pd.DataFrame) -> pd.Series:
    return 1.0 - df["discount_filled"]


@registry.register("zero_discount", requires=[DISCOUNT_IS_ZERO])
def _zero_discount(df: pd.DataFrame) -> pd.Series:
    return df[DISCOUNT_IS_ZERO].astype("int8")


# --- history of the target and of stockouts


def _lag(column: str, lag: int) -> Compute:
    def compute(df: pd.DataFrame) -> pd.Series:
        return lags.lag_feature(df, column, lag, horizon=HORIZON)

    return compute


def _window_mean(column: str, window: int) -> Compute:
    def compute(df: pd.DataFrame) -> pd.Series:
        return lags.window_mean_feature(df, column, window, horizon=HORIZON)

    return compute


for _lag_days in LAGS:
    registry.register(f"{TARGET}_lag_{_lag_days}", requires=[TARGET])(
        _lag(TARGET, _lag_days)
    )
for _window_days in WINDOWS:
    registry.register(f"{TARGET}_mean_{_window_days}_lag_{HORIZON}", requires=[TARGET])(
        _window_mean(TARGET, _window_days)
    )
registry.register(f"{OOS_HOURS}_lag_{HORIZON}", requires=[OOS_HOURS])(
    _lag(OOS_HOURS, HORIZON)
)
registry.register(f"{OOS_HOURS}_mean_28_lag_{HORIZON}", requires=[OOS_HOURS])(
    _window_mean(OOS_HOURS, 28)
)

SAME_WEEKDAY_LAGS = [f"{TARGET}_lag_{lag}" for lag in LAGS]


@registry.register("same_weekday_mean", requires=SAME_WEEKDAY_LAGS)
def _same_weekday_mean(df: pd.DataFrame) -> pd.Series:
    # Mean of the same weekday over the last four weeks. NaN until all four exist.
    return df[SAME_WEEKDAY_LAGS].mean(axis=1, skipna=False)


# Short lags for one-day-ahead models used in recursive forecasting (module 10).
SHORT_LAGS = (1, 2, 3)
SHORT_WINDOWS = (7, 28)


def _short_lag(lag: int) -> Compute:
    def compute(df: pd.DataFrame) -> pd.Series:
        return lags.lag_feature(df, TARGET, lag, horizon=1)

    return compute


def _short_window(window: int) -> Compute:
    def compute(df: pd.DataFrame) -> pd.Series:
        return lags.window_mean_feature(df, TARGET, window, horizon=1)

    return compute


for _lag_days in SHORT_LAGS:
    registry.register(f"{TARGET}_lag_{_lag_days}", requires=[TARGET])(
        _short_lag(_lag_days)
    )
for _window_days in SHORT_WINDOWS:
    registry.register(f"{TARGET}_mean_{_window_days}_lag_1", requires=[TARGET])(
        _short_window(_window_days)
    )

SHORT_FEATURES = [
    *(f"{TARGET}_lag_{lag}" for lag in SHORT_LAGS),
    *(f"{TARGET}_mean_{window}_lag_1" for window in SHORT_WINDOWS),
]

# --- the feature set of the course model

CALENDAR_FEATURES = [
    "dow",
    "dow_sin",
    "dow_cos",
    "is_weekend",
    "is_public_holiday",
    "days_to_holiday",
]
PRICE_FEATURES = ["discount_filled", "promo_depth", "zero_discount"]
HISTORY_FEATURES = [
    *SAME_WEEKDAY_LAGS,
    f"{TARGET}_mean_7_lag_{HORIZON}",
    f"{TARGET}_mean_28_lag_{HORIZON}",
    "same_weekday_mean",
    f"{OOS_HOURS}_lag_{HORIZON}",
    f"{OOS_HOURS}_mean_28_lag_{HORIZON}",
]
NUMERIC_FEATURES = [
    *CALENDAR_FEATURES,
    *PRICE_FEATURES,
    *FLAGS,
    *WEATHER,
    *HISTORY_FEATURES,
]
CATEGORICAL_FEATURES = ["store_id", "product_id"]
MODEL_FEATURES = [*NUMERIC_FEATURES, *CATEGORICAL_FEATURES]

FEATURES_FILE = "features.parquet"


def build_feature_table(daily: pd.DataFrame) -> pd.DataFrame:
    """Return the processed daily panel with every numeric model feature added."""
    return build_features(daily, NUMERIC_FEATURES, registry.features)


def build_recursive_table(daily: pd.DataFrame) -> pd.DataFrame:
    """Return the panel with the model features plus the short lags."""
    names = [*NUMERIC_FEATURES, *SHORT_FEATURES]
    return build_features(daily, names, registry.features)
