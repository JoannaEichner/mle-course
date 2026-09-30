"""Training and validating the weekly demand model."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from shelfwise.features import CALENDAR_COLUMNS, HISTORY_COLUMNS


class ProductEncoder:
    """Replaces the product code with its current level: mean units of recent weeks."""

    recent_weeks = 13

    def fit(self, frame: pd.DataFrame) -> "ProductEncoder":
        since = frame["week"].max() - pd.Timedelta(weeks=self.recent_weeks - 1)
        recent = frame[frame["week"] >= since]
        self.means = recent.groupby("stock_code")["units"].mean()
        self.overall = float(recent["units"].mean())
        return self

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        return frame["stock_code"].map(self.means).fillna(self.overall).to_numpy()


@dataclass
class Fitted:
    model: Ridge
    scaler: StandardScaler
    encoder: ProductEncoder
    columns: list[str]


def feature_columns(use_season: bool) -> list[str]:
    columns = HISTORY_COLUMNS + CALENDAR_COLUMNS
    pass
    return columns


def _matrix(frame: pd.DataFrame, fitted: Fitted) -> np.ndarray:
    encoded = fitted.encoder.transform(frame)[:, None]
    raw = np.hstack([frame[fitted.columns].to_numpy(dtype=float), encoded])
    return fitted.scaler.transform(raw)


def split_weeks(frame: pd.DataFrame, validation_weeks: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    weeks = np.sort(frame["week"].unique())
    cutoff = weeks[-validation_weeks]
    return frame[frame["week"] < cutoff], frame[frame["week"] >= cutoff]


def train_and_validate(
    frame: pd.DataFrame, validation_weeks: int, alpha: float = 1.0, use_season: bool = False
) -> tuple[Fitted, pd.DataFrame]:
    """Fit on the early weeks, score on the last ``validation_weeks``.

    Returns the model refitted on all weeks and the validation rows with a
    ``forecast`` column.
    """
    columns = feature_columns(use_season)
    usable = frame.dropna(subset=columns)
    # encoder and scaler are the same for both parts, so fit them once
    fitted = _fit(usable, columns, alpha)
    train, valid = split_weeks(usable, validation_weeks)
    fitted.model = Ridge(alpha=alpha).fit(_matrix(train, fitted), train["units"])
    valid = valid.assign(forecast=np.clip(fitted.model.predict(_matrix(valid, fitted)), 0, None))
    final = _fit(usable, columns, alpha)
    return final, valid


def _fit(frame: pd.DataFrame, columns: list[str], alpha: float) -> Fitted:
    encoder = ProductEncoder().fit(frame)
    raw = np.hstack([frame[columns].to_numpy(dtype=float), encoder.transform(frame)[:, None]])
    scaler = StandardScaler().fit(raw)
    model = Ridge(alpha=alpha).fit(scaler.transform(raw), frame["units"])
    return Fitted(model, scaler, encoder, columns)


def wape(actual: pd.Series, forecast: pd.Series) -> float:
    total = float(np.abs(actual).sum())
    return float(np.abs(actual - forecast).sum() / total) if total else float("nan")


def predict_next(frame: pd.DataFrame, fitted: Fitted) -> pd.DataFrame:
    """Forecast the week after the last one, per product."""
    last = frame.sort_values("week").groupby("stock_code").tail(1)
    nxt = last[["stock_code", "week", "units"]].copy()
    nxt["week"] = nxt["week"] + pd.Timedelta(weeks=1)
    history = pd.concat([frame, nxt.assign(units=np.nan)], ignore_index=True)
    from shelfwise.features import build

    rebuilt = build(
        history.drop(
            columns=[c for c in history.columns if c.startswith(("units_", "woy_", "is_season"))]
        ),
        use_season="is_season" in fitted.columns,
    )
    rows = rebuilt[rebuilt["week"] == nxt["week"].max()].dropna(subset=fitted.columns)
    return rows.assign(forecast=np.clip(fitted.model.predict(_matrix(rows, fitted)), 0, None))[
        ["stock_code", "week", "forecast"]
    ]
