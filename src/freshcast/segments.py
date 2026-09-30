"""Segments of series: describe each series, cluster, look in two dimensions.

Clustering has no target to score against. Every choice here (what to
describe, how to scale, how many clusters) is judged by evidence you read
yourself, and the final test is whether the segment helps a forecast.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Self

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from freshcast.data.schema import (
    DATE,
    HOURS_PER_DAY,
    OOS_WINDOW,
    SERIES_KEY,
)
from freshcast.models.gbm import LightGBMForecaster
from freshcast.models.panel import PanelForecaster

FloatArray = NDArray[np.float64]

PROFILE_FEATURES = [
    "log_mean_sales",
    "cv",
    "weekend_uplift",
    "discounted_share",
    "stockout_rate",
    "zero_share",
]
HOUR_COLUMNS = [f"h{hour:02d}" for hour in range(HOURS_PER_DAY)]
SEGMENT = "segment"

# Days of the week count from 0 (Monday), so Saturday is 5 and Sunday is 6.
FIRST_WEEKEND_DAY = 5
# Hours per day that ``oos_hours`` can count: 06:00 to 22:00.
OPEN_HOURS = OOS_WINDOW.stop - OOS_WINDOW.start
# k-means starts from random centres and can end in a poor spot. Keeping the
# best of several starts makes the result stable, and it must be the same
# number everywhere so the functions below agree with each other.
N_INIT = 10


@dataclass(frozen=True)
class Segmentation:
    """What ``fit_segments`` returns.

    Attributes:
        labels: The segment of every row of the profile, named ``segment``
            and indexed like the profile. Numbers are arbitrary names: two
            runs may call the same group 0 and 3.
        scaler: The scaler fitted on the profile, to scale further series
            the same way.
        kmeans: The fitted clustering, with the cluster centres in scaled
            units.
    """

    labels: pd.Series
    scaler: StandardScaler
    kmeans: KMeans


def series_profile(daily: pd.DataFrame) -> pd.DataFrame:
    """Describe every series by six numbers of its behaviour.

    Args:
        daily: The processed daily panel, in any row order, with the series
            key, the date, sales, the discount and the stockout hours.

    Returns:
        One row per series, indexed by the series key and sorted by it, with
        the columns of ``PROFILE_FEATURES``:

        - ``log_mean_sales``: natural logarithm of the mean daily sales.
          Levels differ by a factor of 40 between series. On the raw scale a
          few giants would decide the clusters.
        - ``cv``: standard deviation of daily sales (``ddof=0``) divided by
          their mean.
        - ``weekend_uplift``: mean sales on Saturdays and Sundays divided by
          the mean of all days, minus 1. 0.25 means a quarter more at
          weekends.
        - ``discounted_share``: share of days with a discount below 1. A
          day with an unknown discount (NaN) counts as not discounted.
        - ``stockout_rate``: mean ``oos_hours`` divided by the 16 hours it
          counts.
        - ``zero_share``: share of days with no sales at all.

        Every number is computed from the rows of its own series alone.

    Raises:
        ValueError: A series has no sales on any day, so its level has no
            logarithm and its variability no scale, or a series has no
            Saturday or Sunday among its days.
    """
    raise NotImplementedError("Zadanie 13.1")


def standardise(features: pd.DataFrame) -> tuple[FloatArray, StandardScaler]:
    """Scale every column to mean 0 and standard deviation 1.

    k-means measures distances, so a column measured in thousands would
    decide everything and a column measured in fractions nothing.

    Args:
        features: Numeric columns, one row per series.

    Returns:
        ``(scaled, scaler)``. ``scaled`` is an array of shape ``(n, k)`` in
        the column order of ``features``. ``scaler`` is fitted on exactly
        these rows and scales other rows the same way. A column that is
        constant becomes all zeros.

    Raises:
        ValueError: ``features`` has no rows, or holds NaN or infinite
            values (the message says how many).
    """
    raise NotImplementedError("Zadanie 13.2")


def fit_segments(profile: pd.DataFrame, k: int, seed: int = 0) -> Segmentation:
    """Scale a profile and cut the series into ``k`` segments with k-means.

    The run starts from ``N_INIT`` random initialisations and keeps the best,
    all seeded from ``seed``: the same profile, ``k`` and ``seed`` always
    give the same labels.

    Args:
        profile: One row per series, only numeric columns, for example the
            output of ``series_profile``.
        k: Number of segments, from 2 up to the number of rows.
        seed: Seed of the random initialisations.

    Returns:
        A ``Segmentation`` with one label per row of ``profile``.

    Raises:
        ValueError: ``k`` is outside 2..number of rows, or ``profile`` holds
            NaN or infinite values.
    """
    raise NotImplementedError("Zadanie 13.2")


def inertia_by_k(scaled: FloatArray, ks: Sequence[int], seed: int = 0) -> pd.Series:
    """Return the k-means inertia for every k in ``ks``.

    Inertia is the sum of squared distances from every point to the centre
    of its cluster. It only falls as k grows, so the useful signal is where
    it stops falling fast: the bend of the curve.

    Args:
        scaled: Scaled features, shape ``(n, m)``.
        ks: The numbers of clusters to try, each from 1 to ``n``.
        seed: Seed of the random initialisations, as in ``fit_segments``.

    Returns:
        A Series named ``inertia``, indexed by k in the order of ``ks``.

    Raises:
        ValueError: Some k is outside 1..n.
    """
    raise NotImplementedError("Zadanie 13.3")


def silhouette_by_k(scaled: FloatArray, ks: Sequence[int], seed: int = 0) -> pd.Series:
    """Return the mean silhouette of the k-means clustering for every k.

    The silhouette of a point compares ``a``, its mean distance to the other
    points of its own cluster, with ``b``, its mean distance to the points of
    the nearest other cluster: ``(b - a) / max(a, b)``. It is near 1 for a
    point deep inside a well separated cluster, near 0 on a border and
    negative for a point that sits closer to another cluster. The result is
    the mean over all points.

    Args:
        scaled: Scaled features, shape ``(n, m)``.
        ks: The numbers of clusters to try, each from 2 to ``n - 1``.
        seed: Seed of the random initialisations, as in ``fit_segments``.

    Returns:
        A Series named ``silhouette``, indexed by k in the order of ``ks``.

    Raises:
        ValueError: Some k is outside 2..n-1.
    """
    raise NotImplementedError("Zadanie 13.3")


def hour_profiles(hourly: pd.DataFrame) -> pd.DataFrame:
    """Return, per series, the share of its sales that falls in each hour.

    Sales are added up over all days first and turned into shares after, so
    a busy day counts more than a quiet one. Hours without stock are taken as
    recorded: no sales.

    Args:
        hourly: Output of ``load_hourly``: the series key, the date and the
            column of 24-hour sales arrays.

    Returns:
        One row per series, indexed by the series key and sorted by it, with
        the 24 columns of ``HOUR_COLUMNS``. Every row adds up to 1.

    Raises:
        ValueError: A series has no sales in any hour, so it has no profile.
    """
    raise NotImplementedError("Zadanie 13.4")


def project_2d(matrix: FloatArray) -> tuple[FloatArray, FloatArray]:
    """Project the rows onto their first two principal components (PCA).

    The components are the two directions along which the rows vary most.
    The columns are centred but not scaled, which is right when they share a
    unit (hourly shares); scale them first when they do not.

    Args:
        matrix: Array of shape ``(n, m)`` with ``n >= 2`` and ``m >= 2``.

    Returns:
        ``(coordinates, explained)``. ``coordinates`` has shape ``(n, 2)``:
        the first column is the position along the first component.
        ``explained`` holds the share of the total variance each of the two
        components carries, largest first. The shares add up to less than 1:
        the rest is what the picture leaves out.

    Raises:
        ValueError: ``matrix`` has fewer than two rows or two columns, or
            holds NaN or infinite values.
    """
    raise NotImplementedError("Zadanie 13.4")


class SegmentedForecaster(PanelForecaster):
    """LightGBM with the series' segment as one more categorical feature.

    Given code. It shows how to test a cluster-based feature honestly. A
    segment built from the whole panel before the backtest describes each
    series by days that lie in the validation weeks, so the feature knows
    the future and the score looks better than the model really is. Here the
    segments are learned inside ``fit``, from the history up to the last
    training day, and a series that ``fit`` never saw gets no segment.

    Args:
        history: The whole panel with the columns ``series_profile`` needs.
            Rows after the last day of the training rows are ignored. It
            includes the days the training rows leave out, for example days
            with stockouts, which are part of how a series behaves.
        features: Feature columns of the trees, categorical ones included.
        categorical: The features to treat as categories.
        k: Number of segments.
        rounds: Number of trees.
        params: LightGBM parameters that override the defaults.
        seed: Seed of k-means.
    """

    def __init__(
        self,
        history: pd.DataFrame,
        features: Sequence[str],
        categorical: Sequence[str],
        k: int,
        *,
        rounds: int = 400,
        params: Mapping[str, Any] | None = None,
        seed: int = 0,
    ) -> None:
        self.history = history
        self.features = [*features, SEGMENT]
        self.categorical = [*categorical, SEGMENT]
        self.k = k
        self.rounds = rounds
        self.params = params
        self.seed = seed
        self._segments: pd.DataFrame | None = None
        self._model: LightGBMForecaster | None = None

    def _with_segment(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return ``X`` with a ``segment`` column, missing for unknown series."""
        if self._segments is None:
            raise RuntimeError("Call fit first.")
        merged = X[SERIES_KEY].merge(
            self._segments, on=SERIES_KEY, how="left", validate="many_to_one"
        )
        return X.assign(**{SEGMENT: merged[SEGMENT].set_axis(X.index)})

    def fit(self, X: pd.DataFrame, y: pd.Series) -> Self:
        """Learn the segments from the past of the training rows, then the trees."""
        last_day = X[DATE].max()
        past = self.history.loc[self.history[DATE] <= last_day]
        segmentation = fit_segments(series_profile(past), self.k, self.seed)
        # Int64 (not int64) so that a series without a segment can be missing.
        self._segments = segmentation.labels.astype("Int64").reset_index()
        self._model = LightGBMForecaster(
            self.features, self.categorical, self.params, self.rounds
        ).fit(self._with_segment(X), y)
        return self

    def predict(self, X: pd.DataFrame) -> FloatArray:
        """Forecast with the segments learned in ``fit``.

        Raises:
            RuntimeError: ``fit`` has not been called.
        """
        if self._model is None:
            raise RuntimeError("Call fit first.")
        return self._model.predict(self._with_segment(X))
