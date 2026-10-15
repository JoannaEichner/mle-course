"""Dimension tables: one row per store or product, joined back to the facts."""

import pandas as pd


def build_store_dim(df: pd.DataFrame) -> pd.DataFrame:
    """Build the store dimension: one row per store.

    Args:
        df: Daily sales, one row per series and day, e.g. the result of
            ``load_sales``. Columns used: ``store_id``, ``city_id``,
            ``product_id`` and ``sale_amount``.

    Returns:
        A new frame with the columns ``store_id``, ``city_id`` (the store's
        city), ``n_products`` (distinct products sold in the store) and
        ``mean_sales`` (mean ``sale_amount`` over all rows of the store, i.e.
        mean daily sales of one of its series), in that order, sorted by
        ``store_id``, with a fresh 0..n-1 index.

    Raises:
        ValueError: A store appears in more than one city. The message gives
            the number of such stores.
    """
    raise NotImplementedError("Zadanie 07.3")


def build_product_dim(df: pd.DataFrame) -> pd.DataFrame:
    """Build the product dimension: one row per product.

    The four hierarchy columns are the product's path in the catalogue, from
    the broadest group (``management_group_id``) to the narrowest category
    (``third_category_id``).

    Args:
        df: Rows with ``product_id``, ``store_id`` and the four hierarchy
            columns (``HIERARCHY`` in ``schema.py``), e.g. ``load_sales``
            called with ``columns=[*SERIES_KEY, DATE, *HIERARCHY]``.

    Returns:
        A new frame with ``product_id``, the four hierarchy columns and
        ``n_stores`` (distinct stores selling the product), in that order,
        sorted by ``product_id``, with a fresh 0..n-1 index.

    Raises:
        ValueError: A product appears under more than one hierarchy path. The
            message gives the number of such products.
    """
    raise NotImplementedError("Zadanie 07.3")


def attach_dim(fact: pd.DataFrame, dim: pd.DataFrame, on: str) -> pd.DataFrame:
    """Add the columns of a dimension to a fact table.

    The join can neither add nor drop fact rows: a key repeated in ``dim``
    or a fact key missing from ``dim`` is an error, not something to work
    around later.

    Args:
        fact: The table to extend, many rows per key, e.g. daily sales.
        dim: The dimension, exactly one row per key, e.g. the result of
            ``build_product_dim``.
        on: Name of the key column, present in both, e.g. ``"product_id"``.

    Returns:
        A new frame: every column of ``fact`` followed by the other columns
        of ``dim``, one row per fact row, rows in the original order, with a
        fresh 0..n-1 index. No helper column is left behind.

    Raises:
        pandas.errors.MergeError: ``dim`` has a repeated key.
        ValueError: Some fact rows have a key that ``dim`` lacks. The message
            gives the number of such rows.
    """
    raise NotImplementedError("Zadanie 07.3")
