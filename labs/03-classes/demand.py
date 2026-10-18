"""Car Parts demand series as objects: demand types and local forecasts."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Protocol, Self


MISSING = "?"
# Syntetos-Boylan cut-offs: above ADI_CUTOFF demand is intermittent, above
# CV2_CUTOFF the sizes of the orders vary a lot.
ADI_CUTOFF = 1.32
CV2_CUTOFF = 0.49


def read_tsf(path: str | Path) -> Iterator[tuple[str, str, list[float | None]]]:
    """Yield (name, start, values) for every series of a .tsf file.

    The same job as ``read_series`` from labs 01 and 02, kept short here.
    """
    in_data = False
    with Path(path).open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower() == "@data":
                in_data = True
            elif in_data:
                name, start, values = line.split(":", 2)
                parsed = [None if v == MISSING else float(v) for v in values.split(",")]
                yield name, start.split(" ")[0], parsed


@dataclass(frozen=True)
class DemandSeries:
    """One monthly demand series, oldest value first; None marks a missing month.

    03.1: fields name, start, values; from_record, known, is_complete, adi
    and cv2. The notebook describes each of them.
    """
    name: str
    start: date
    values: tuple[float | None, ...]

    def __post_init__(self):
        if not self.values: 
            raise ValueError("Values cannot be empty")
        for value in self.values:
            if value is not None and value < 0:
                raise ValueError("Negative demand")

    @classmethod
    def from_record(cls, record):
        name, start, values = record
        start = date.fromisoformat(start)
        values = tuple(values)
        return cls(name, start, values)

    @property
    def known(self):
        result = []
        for value in self.values:
            if value is not None:
                result.append(value)
        return result

    @property
    def is_complete(self) -> bool:
        for value in self.values:
            if value is None:
                return False
        return True

    @property
    def adi(self) ->float | None:
        positive_months = 0
        for value in self.known:
            if value > 0:
                positive_months +=1
        if positive_months == 0:
            return None
        return len(self.known)/positive_months

    @property
    def cv2(self) -> float | None:
        positive = []

        for value in self.known:
            if value > 0:
                positive.append(value)
        
        if len(positive) <2:
            return None

        average = sum(positive)/len(positive)

        variance_sum = 0

        for value in positive:
            variance_sum += (value - average) ** 2

        variance = variance_sum / len(positive)

        return variance/(average ** 2)

class DemandType(StrEnum):
    SMOOTH = "smooth"
    INTERMITTENT = "intermittent"
    ERRATIC = "erratic"
    LUMPY = "lumpy"
    INSUFFICIENT = "insufficient"

def classify(adi: float | None, cv2: float | None) -> DemandType: 
    match (adi, cv2):
        case (None, _):
            return  DemandType.INSUFFICIENT
        case (_, None):
            return  DemandType.INSUFFICIENT
        case (adi, cv2) if adi <= ADI_CUTOFF and cv2 <= CV2_CUTOFF:
            return  DemandType.SMOOTH
        case (adi, cv2) if adi > ADI_CUTOFF and cv2 <= CV2_CUTOFF:
            return  DemandType.INTERMITTENT
        case (adi, cv2) if adi <= ADI_CUTOFF and cv2 > CV2_CUTOFF:
            return DemandType.ERRATIC
        case (adi, cv2) if adi > ADI_CUTOFF and cv2 > CV2_CUTOFF:
            return DemandType.LUMPY
        
class LocalForecaster(ABC):
    def __init__(self):
        self._history = None

    def fit(self, history):
        if not history:
            raise ValueError("History cannot be empty")
        self._history = [float(x) for x in history]
        return self

    def predict(self, horizon):
        if self._history is None:
            raise RuntimeError("Call fit before predict")
        if horizon < 1:
            raise ValueError("Horizon must be positive")
        return self._forecast(self._history, horizon)

    @abstractmethod
    def _forecast(self, history, horizon):
        ...

class NaiveForecaster(LocalForecaster):
    def _forecast(self, history, horizon):
        return [history[-1]] * horizon
    

class SeasonalNaiveForecaster(LocalForecaster):
    def __init__(self, season=7):
        super().__init__()

        if season < 1:
            raise ValueError("Season must be positive")

        self.season = season

    def fit(self, history):
        if len(history) < self.season:
            raise ValueError("History shorter than season")
        return super().fit(history)

    def _forecast(self, history, horizon):
        last_season = history[-self.season:]
        return [last_season[i % self.season] for i in range(horizon)]

class MovingAverageForecaster(LocalForecaster):
    def __init__(self, window = 7):
        super().__init__()

        if window < 1:
            raise ValueError("Window must be positive")
        self.window = window

    def _forecast(self, history, horizon):
        last_values = history[-self.window:]
        average = sum(last_values)/len(last_values)
        return [average] * horizon

class Forecaster(Protocol):
    def fit(history) -> Self:
        ...

    def predict(horizon) -> list[float]:
        ...

    def mae(actual, forecast):
        ...

    def evaluate(make_model, series, holdout=6):
        errors = []

        for one in series:
            if not one.is_complete or len(one.values) <= holdout:
                continue
            history, actual = one.known[:-holdout], one.known[-holdout:]

            forecast = make_model().fit(history).predict(holdout)

            errors.append(mae(actual, forecast))

        if not errors:
            raise ValueError("")