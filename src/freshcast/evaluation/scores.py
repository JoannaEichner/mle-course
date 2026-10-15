"""One scoring function for every model of the course."""

from numpy.typing import ArrayLike


def score_forecast(
    actual: ArrayLike, predicted: ArrayLike, in_stock: ArrayLike
) -> dict[str, float]:
    """Score a forecast on all rows and on the rows without a stockout.

    Sales on a stockout day are capped by supply, so they say little about
    how well demand was forecast. The in-stock rows are the honest test.

    Every number comes from the metrics of module 05 (``freshcast.metrics``);
    the in-stock ones use their ``mask`` argument.

    Args:
        actual: Observed daily sales, one value per row (array or Series).
        predicted: Forecasts for the same rows, in the same order.
        in_stock: Booleans of the same length, True where the row counts as
            in stock. The caller chooses the definition; the course uses
            ``oos_hours == 0``, i.e. no stockout hour between 06:00 and
            22:00.

    Returns:
        A dict of five floats with the keys, in this order: ``wape``,
        ``mae`` and ``bias`` on all rows, then ``wape_in_stock`` and
        ``bias_in_stock`` on the in-stock rows. WAPE and bias are fractions
        (0.25 means 25 %), MAE is in units of sales.

    Raises:
        ValueError: Raised by the metrics: lengths differ, a value is NaN,
            or the actual sales of the scored rows sum to zero.
    """
    raise NotImplementedError("Zadanie 08.5")
