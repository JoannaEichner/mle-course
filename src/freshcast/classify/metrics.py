"""Classification metrics on NumPy arrays, thresholds and calibration.

Labels are 0 and 1 (or False and True), 1 being the positive class: the event
we want to catch. A classifier gives a score per row. A threshold turns the
score into a decision: predict 1 when ``score >= threshold``.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


def binary_array(name: str, values: ArrayLike) -> IntArray:
    """Return ``values`` as a flat array of 0 and 1.

    This is the gate every metric passes its labels through. A label that is
    NaN (a row whose tomorrow is unknown) or anything but 0 and 1 is not
    silently turned into a class.

    Args:
        name: Argument name, used in the error message.
        values: Booleans, or numbers that are all 0 or 1.

    Raises:
        ValueError: A value is NaN or different from 0 and 1.
    """
    numbers = np.asarray(values, dtype=np.float64).ravel()
    missing = int(np.isnan(numbers).sum())
    if missing:
        raise ValueError(f"{name} has {missing} NaN values.")
    other = int(((numbers != 0) & (numbers != 1)).sum())
    if other:
        raise ValueError(f"{name} has {other} values that are neither 0 nor 1.")
    return numbers.astype(np.int64)


def score_array(scores: ArrayLike) -> FloatArray:
    """Return ``scores`` as a flat float array, refusing NaN.

    Raises:
        ValueError: A score is NaN.
    """
    numbers = np.asarray(scores, dtype=np.float64).ravel()
    missing = int(np.isnan(numbers).sum())
    if missing:
        raise ValueError(f"scores has {missing} NaN values.")
    return numbers


@dataclass(frozen=True)
class Confusion:
    """The four outcomes of yes/no predictions.

    ``tp`` true positives (alarm, and it happened), ``fp`` false positives
    (alarm, nothing happened), ``fn`` false negatives (no alarm, it
    happened), ``tn`` true negatives (no alarm, nothing happened).
    """

    tp: int
    fp: int
    fn: int
    tn: int


def confusion_counts(y_true: ArrayLike, y_pred: ArrayLike) -> Confusion:
    """Count true and false positives and negatives.

    Args:
        y_true: Observed labels, 0 or 1.
        y_pred: Predicted labels, 0 or 1, same length.

    Returns:
        The four counts. They add up to the number of rows.

    Raises:
        ValueError: A label is NaN or not 0 or 1, or the lengths differ.
    """
    raise NotImplementedError("Zadanie 12.3")


def precision(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Of the alarms raised, the share that were right: ``tp / (tp + fp)``.

    Returns 0.0 when no alarm was raised, because the ratio is then 0 / 0 and
    a model that never speaks has earned no credit.

    Raises:
        ValueError: As ``confusion_counts``.
    """
    raise NotImplementedError("Zadanie 12.3")


def recall(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Of the events that happened, the share that were caught: ``tp / (tp + fn)``.

    Returns 0.0 when no event happened, because the ratio is then 0 / 0.

    Raises:
        ValueError: As ``confusion_counts``.
    """
    raise NotImplementedError("Zadanie 12.3")


def f1(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Harmonic mean of precision and recall.

    The harmonic mean is low when either part is low, so a model cannot hide
    a missing recall behind a good precision. Returns 0.0 when precision and
    recall are both 0 (this includes the case of no alarms and no events).

    Raises:
        ValueError: As ``confusion_counts``.
    """
    raise NotImplementedError("Zadanie 12.3")


def counts_by_threshold(
    y_true: ArrayLike, scores: ArrayLike
) -> tuple[FloatArray, IntArray, IntArray]:
    """Count true and false positives at every threshold that changes anything.

    The candidate thresholds are the distinct score values. At the threshold
    ``t`` the model raises an alarm on every row with ``score >= t``. Rows
    with equal scores always enter together: no threshold can split them.

    Args:
        y_true: Observed labels, 0 or 1.
        scores: A score per row, higher meaning more likely positive.

    Returns:
        ``(thresholds, tp, fp)``, three arrays of one length, in order of
        falling threshold. ``tp[k]`` and ``fp[k]`` are the true and false
        alarms raised at ``thresholds[k]``. Both never decrease.

    Raises:
        ValueError: A label is not 0 or 1, a value is NaN, the lengths differ,
            or there are no rows.
    """
    raise NotImplementedError("Zadanie 12.4")


def precision_recall_curve(
    y_true: ArrayLike, scores: ArrayLike
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Precision and recall at every threshold, from strictest to most lenient.

    Args:
        y_true: Observed labels, 0 or 1, with at least one 1.
        scores: A score per row, higher meaning more likely positive.

    Returns:
        ``(precision, recall, thresholds)``, three arrays of one length, in
        order of falling threshold, so recall never decreases. This differs
        from scikit-learn, whose arrays are in rising threshold order and
        whose precision and recall carry one extra final point.

    Raises:
        ValueError: As ``counts_by_threshold``, or ``y_true`` has no 1.
    """
    raise NotImplementedError("Zadanie 12.4")


def average_precision(y_true: ArrayLike, scores: ArrayLike) -> float:
    """Area under the precision-recall curve, summed step by step.

    Walk the thresholds from strictest to most lenient. Each step that raises
    recall from ``r_prev`` to ``r`` counts ``(r - r_prev) * precision`` at that
    threshold. There is no interpolation between points. A random ranking
    scores about the share of positives; a perfect one scores 1.

    Raises:
        ValueError: As ``precision_recall_curve``.
    """
    raise NotImplementedError("Zadanie 12.4")


@dataclass(frozen=True)
class ThresholdChoice:
    """A threshold and the total cost it brings on the rows it was chosen on.

    ``threshold`` is ``inf`` when the cheapest policy is to raise no alarm.
    """

    threshold: float
    cost: float


def best_threshold(
    y_true: ArrayLike,
    scores: ArrayLike,
    cost_false_alarm: float,
    cost_missed: float,
) -> ThresholdChoice:
    """Find the threshold with the lowest total cost.

    Every false alarm costs ``cost_false_alarm`` and every missed event costs
    ``cost_missed``; correct decisions are free. The candidates are the
    distinct score values and, in addition, "raise no alarm at all"
    (threshold ``inf``), which costs ``cost_missed`` per event.

    On equal cost the higher threshold wins, that is, the one with fewer
    alarms.

    Args:
        y_true: Observed labels, 0 or 1.
        scores: A score per row, higher meaning more likely positive.
        cost_false_alarm: Cost of one false alarm, not negative.
        cost_missed: Cost of one missed event, not negative.

    Returns:
        The best threshold and its total cost.

    Raises:
        ValueError: A cost is negative, or as ``counts_by_threshold``.
    """
    raise NotImplementedError("Zadanie 12.5")


def calibration_table(
    y_true: ArrayLike, probabilities: ArrayLike, bins: int = 10
) -> pd.DataFrame:
    """Compare predicted probabilities with observed frequencies, bin by bin.

    A model is calibrated when, among the rows it gives probability 0.3, about
    30% are positive. The range 0 to 1 is cut into ``bins`` bins of equal
    width. A bin includes its lower edge and excludes its upper edge, except
    the last bin, which includes 1.0.

    Args:
        y_true: Observed labels, 0 or 1.
        probabilities: Predicted probabilities of the positive class.
        bins: Number of equal-width bins, at least 1.

    Returns:
        One row per bin that holds at least one row, in order, with the
        columns ``bin_low``, ``bin_high``, ``rows``, ``mean_predicted`` (mean
        probability in the bin) and ``observed_rate`` (share of positives).

    Raises:
        ValueError: ``bins`` is below 1, a probability is NaN or outside
            [0, 1], a label is not 0 or 1, or the lengths differ.
    """
    raise NotImplementedError("Zadanie 12.6")
