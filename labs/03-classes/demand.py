"""Car Parts demand series as objects: demand types and local forecasts."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

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
    """One monthly demand series of one car part, oldest month first.

    03.1, the contract (the notebook explains each step in Polish):

    Fields, in this order:
        name (str): name of the series in the .tsf file, for example "T1".
        start (date): date of the first month of the series.
        values (tuple of float or None): units sold in each month, oldest
            first; None marks a month without a record.

    __post_init__: ValueError when values is empty or holds a negative number.
    from_record(record) (classmethod): build a series from one
        (name, "YYYY-MM-DD", list of values) record yielded by read_tsf.
    known (property): list of the known values, missing months left out.
    is_complete (property): True when no month is missing.
    adi (property): known months / months with demand above zero;
        None when no month has demand.
    cv2 (property): population variance of the values above zero divided
        by the square of their mean; None when fewer than two months have
        demand.
    """


# 03.2: DemandType and classify.
#
# DemandType: a StrEnum with members SMOOTH, ERRATIC, INTERMITTENT, LUMPY
# and INSUFFICIENT; each value is the member name in lower case.
#
# classify(adi, cv2) -> DemandType: adi and cv2 are floats or None, as
# DemandSeries.adi and DemandSeries.cv2 return them. INSUFFICIENT when
# either is None; otherwise the class from the table in the notebook, with
# ADI_CUTOFF and CV2_CUTOFF above. A value equal to a cut-off belongs to the
# lower class. Write it with a match statement.


# 03.3: LocalForecaster and NaiveForecaster.
#
# LocalForecaster: abstract base class (ABC) of every forecaster.
#   __init__(): sets self._history to None (not fitted yet).
#   fit(history) -> Self: history is a sequence of floats, oldest first.
#     Stores a copy as a list of floats and returns self.
#     ValueError when history is empty.
#   predict(horizon) -> list[float]: RuntimeError before fit, ValueError
#     when horizon is below 1; otherwise returns
#     self._forecast(self._history, horizon).
#   _forecast(history, horizon) -> list[float]: abstract method; returns
#     horizon forecasts, nearest first.
#
# NaiveForecaster(LocalForecaster): _forecast repeats the last value of
# the history horizon times.


# 03.4: SeasonalNaiveForecaster and MovingAverageForecaster, both
# subclasses of LocalForecaster.
#
# SeasonalNaiveForecaster(season=7): ValueError when season is below 1.
#   fit(history): ValueError when history is shorter than one season,
#   otherwise as LocalForecaster.fit. The forecast repeats the last
#   `season` values in order and wraps around for longer horizons.
#
# MovingAverageForecaster(window=7): ValueError when window is below 1.
#   The forecast repeats the mean of the last `window` values, or of the
#   whole history when it is shorter than the window.


# 03.5: Forecaster, mae and evaluate.
#
# Forecaster: a Protocol with fit(history) -> Self and
#   predict(horizon) -> list[float].
#
# mae(actual, forecast) -> float: mean of the absolute differences of two
#   sequences of floats. ValueError when the lengths differ or both are
#   empty.
#
# evaluate(make_model, series, holdout=6) -> float: make_model is a
#   function without arguments that returns a new model; holdout is a
#   positive integer (not validated); series is an
#   iterable of DemandSeries. For every complete series longer than
#   holdout: a new model from make_model(), fitted on all months but the
#   last holdout, forecasts holdout months; mae against those months.
#   Returns the mean of these MAE values. ValueError when no series
#   qualifies.
