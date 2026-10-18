"""Rules the data must satisfy before anything is computed from it."""

import pandas as pd


def check_panel(df: pd.DataFrame) -> None:
    """Raise unless ``df`` is a complete daily panel.

    A panel is many daily time series stacked in one frame; a series is one
    product in one store (``store_id``, ``product_id``). The rules, in the
    order they are checked:

    1. No missing value in the series key, the date or the target.
    2. At most one row per series and day. Rows after the first occurrence
       of a (series, day) pair are counted: two identical keys count as 1.
    3. Every series has a row for every day between the first and the last
       date of the whole frame (both included).
    4. The target is never negative.

    Row order is not checked, and other columns are ignored.

    Args:
        df: Daily sales, one row per series and day, e.g. the result of
            ``load_sales``. Columns used: ``store_id``, ``product_id``,
            ``dt`` (``datetime64``) and ``sale_amount``.

    Returns:
        None. The function only raises; it never changes ``df``.

    Raises:
        ValueError: A rule is broken. The message names the rule and says
            how many rows or series break it.
    """
    raise NotImplementedError("Zadanie 07.2")


def clean_discount(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy in which a zero discount is off the numeric scale.

    ``discount`` is a price multiplier: 1.0 is the regular price, 0.8 is 20%
    off. The documentation does not say what exactly 0 means. It may be a
    product given away for free or a placeholder for "not recorded". Either
    way it does not behave like the low end of the same scale, so:

    - rows with a discount of exactly 0 get ``discount_is_zero`` True and
      their ``discount`` becomes NaN,
    - every other row gets ``discount_is_zero`` False, and every other
      value, including the few above 1, stays as it is.

    No information is lost: the flag says where the zeros were.

    Args:
        df: Daily sales with a float ``discount`` column, e.g. the result of
            ``load_sales``.

    Returns:
        A new frame with the same rows, index and order, ``discount`` cleaned
        and a boolean ``discount_is_zero`` column added as the last column.
        The input is not modified.

    Raises:
        ValueError: A discount is negative or missing on input. Neither can
            be explained, so neither is handled. The message gives the number
            of such rows.
    """
    raise NotImplementedError("Zadanie 07.2")
