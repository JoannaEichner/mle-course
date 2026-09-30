"""Dimension tables: one row per store or product, joined back to the facts."""

import pandas as pd


def build_store_dim(df: pd.DataFrame) -> pd.DataFrame:
    """Build the store dimension: one row per store.

    Args:
        df: Daily sales with ``store_id``, ``city_id``, ``product_id`` and
            the target.

    Returns:
        A frame with ``store_id``, ``city_id``, ``n_products`` (distinct
        products sold in the store) and ``mean_sales`` (mean daily sales per
        series row), sorted by ``store_id``.

    Raises:
        ValueError: A store appears in more than one city.
    """
    raise NotImplementedError("Zadanie 07.3")


def build_product_dim(df: pd.DataFrame) -> pd.DataFrame:
    """Build the product dimension: one row per product.

    Args:
        df: Rows with ``product_id``, ``store_id`` and the four hierarchy
            columns.

    Returns:
        A frame with ``product_id``, the four hierarchy columns and
        ``n_stores`` (distinct stores selling the product), sorted by
        ``product_id``.

    Raises:
        ValueError: A product appears under more than one hierarchy path.
    """
    raise NotImplementedError("Zadanie 07.3")


def attach_dim(fact: pd.DataFrame, dim: pd.DataFrame, on: str) -> pd.DataFrame:
    """Add the columns of a dimension to a fact table.

    The join can neither add nor drop fact rows: a key repeated in ``dim``
    or a fact key missing from ``dim`` is an error, not something to work
    around later.

    Args:
        fact: The table to extend, many rows per key.
        dim: The dimension, exactly one row per key.
        on: Name of the key column, present in both.

    Returns:
        ``fact`` with the dimension's other columns appended, rows in the
        original order.

    Raises:
        pandas.errors.MergeError: ``dim`` has a repeated key.
        ValueError: Some fact rows have a key that ``dim`` lacks.
    """
    raise NotImplementedError("Zadanie 07.3")
