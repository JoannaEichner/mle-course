"""SQL over parquet files with DuckDB: the same questions, asked to the file.

DuckDB runs inside the Python process and reads a parquet file directly, from
the disk or, through its ``httpfs`` extension, from a bucket. There is no
server and no loading step: ``FROM read_parquet(?)`` is the table.

Every query here is a function that takes a connection and returns a
DataFrame. The SQL is one readable string, and every value that changes from
call to call (a path, a date, a number) is a ``?`` placeholder filled in by
DuckDB, never pasted into the text. A value pasted into SQL is a bug waiting
for the first quote character, and for anybody who controls the value, an
attack. Only names of tables and columns cannot be placeholders, so they are
written out in the query. That is why column names appear here as text
instead of constants from ``schema.py``: a query is meant to be read as SQL.
"""

from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import boto3
import duckdb
import pandas as pd

from freshcast.config import StorageSettings

# A local path, or an ``s3://bucket/key`` address as text.
Location = str | Path


def connect(storage: StorageSettings | None = None) -> duckdb.DuckDBPyConnection:
    """Open an in-memory DuckDB connection.

    With ``storage``, the connection can also read ``s3://`` addresses from
    the bucket's server. That takes the ``httpfs`` extension, which DuckDB
    downloads the first time (once per machine, so this needs the internet
    once), and a secret that tells DuckDB where the server is and how to
    sign in. The settings needed for a local server are the ones below:

    - ``ENDPOINT`` is ``host:port``, without ``http://``.
    - ``URL_STYLE 'path'`` puts the bucket in the path (``host/bucket/key``).
      The default puts it in the host name (``bucket.host``), which a local
      server does not answer to.
    - ``USE_SSL`` is false for a plain ``http://`` endpoint.

    The keys are the ones boto3 finds, so the service class and the queries
    always sign in as the same user.

    Raises:
        RuntimeError: ``storage`` is given but boto3 finds no credentials.
    """
    con = duckdb.connect()
    if storage is None:
        return con

    credentials = boto3.Session().get_credentials()
    if credentials is None:
        raise RuntimeError(
            "No credentials: set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
        )
    keys = credentials.get_frozen_credentials()

    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    if storage.endpoint_url is None:
        con.execute(
            """
            CREATE OR REPLACE SECRET freshcast (
                TYPE s3, KEY_ID ?, SECRET ?, REGION ?
            )
            """,
            [keys.access_key, keys.secret_key, storage.region],
        )
    else:
        server = urlparse(storage.endpoint_url)
        con.execute(
            """
            CREATE OR REPLACE SECRET freshcast (
                TYPE s3, KEY_ID ?, SECRET ?, REGION ?,
                ENDPOINT ?, URL_STYLE 'path', USE_SSL ?
            )
            """,
            [
                keys.access_key,
                keys.secret_key,
                storage.region,
                server.netloc,
                server.scheme == "https",
            ],
        )
    return con


def city_sales(
    con: duckdb.DuckDBPyConnection,
    daily: Location,
    city_id: int,
    start: date,
    end: date,
) -> pd.DataFrame:
    """Select the rows of one city between two dates, both days included.

    In pandas this is a boolean mask on ``city_id`` and ``dt``. The rows are
    filtered while the file is read, so only what is asked for reaches Python.

    Args:
        con: An open connection.
        daily: The processed daily dataset, a parquet file.
        city_id: The city to keep.
        start: First day wanted.
        end: Last day wanted.

    Returns:
        The columns ``store_id``, ``product_id``, ``dt``, ``sale_amount`` and
        ``oos_hours``, sorted by those three keys in that order.

    Raises:
        ValueError: ``end`` is before ``start``.
    """
    raise NotImplementedError("Zadanie 15.7")


def store_summary(con: duckdb.DuckDBPyConnection, daily: Location) -> pd.DataFrame:
    """Summarise every store: its city, its products and its mean sales.

    Mirrors ``build_store_dim``: the same columns in the same order, one row
    per store, and the same error. The lab compares the two results.

    Args:
        con: An open connection.
        daily: The processed daily dataset, a parquet file.

    Returns:
        The columns ``store_id``, ``city_id``, ``n_products`` (distinct
        products sold in the store) and ``mean_sales`` (mean of
        ``sale_amount`` over the store's rows), sorted by ``store_id``.

    Raises:
        ValueError: A store appears in more than one city. Grouping by the
            store alone would hide it, so the query has to count the cities.
    """
    raise NotImplementedError("Zadanie 15.7")


def category_sales(
    con: duckdb.DuckDBPyConnection,
    daily: Location,
    store_dim: Location,
    product_dim: Location,
    *,
    min_products: int,
) -> pd.DataFrame:
    """Total sales by first category, for stores with enough products.

    Joins the fact table to two dimensions: ``store_dim`` says how many
    products a store sells (``n_products``), ``product_dim`` gives the
    category of a product (``first_category_id``). An inner join silently
    drops fact rows whose key is missing from a dimension, and the totals
    would then be too low without any sign of it. So the function counts
    those rows first and refuses to go on.

    Args:
        con: An open connection.
        daily: The processed daily dataset, a parquet file.
        store_dim: The store dimension, see ``build_store_dim``.
        product_dim: The product dimension, see ``build_product_dim``.
        min_products: Keep only stores with at least this many products.

    Returns:
        The columns ``first_category_id``, ``n_series`` (distinct store and
        product pairs), ``total_sales`` and ``mean_sales`` (mean of
        ``sale_amount`` per row), sorted by ``total_sales`` from the largest,
        then by ``first_category_id``.

    Raises:
        ValueError: Some fact rows have a store missing from ``store_dim`` or
            a product missing from ``product_dim``.
    """
    raise NotImplementedError("Zadanie 15.7")


def top_products_per_store(
    con: duckdb.DuckDBPyConnection, daily: Location, *, top: int
) -> pd.DataFrame:
    """Pick the best-selling products of every store.

    A product's total is the sum of ``sale_amount`` over all its days in the
    store. Products are ranked inside each store, so a small store still gets
    its own best products. In pandas this is ``groupby`` followed by ``rank``
    on the groups.

    Args:
        con: An open connection.
        daily: The processed daily dataset, a parquet file.
        top: How many products to keep per store, at least 1.

    Returns:
        The columns ``store_id``, ``product_id``, ``total_sales`` and
        ``rank_in_store`` (1 is the best), sorted by ``store_id`` and rank.
        Equal totals are ordered by the lower ``product_id``, so a store
        with at least ``top`` products returns exactly ``top`` rows.

    Raises:
        ValueError: ``top`` is below 1.
    """
    raise NotImplementedError("Zadanie 15.8")


def sales_lag(
    con: duckdb.DuckDBPyConnection, daily: Location, lag: int
) -> pd.DataFrame:
    """Add to every row the sales from ``lag`` days earlier in the same series.

    Mirrors ``add_lag(panel, "sale_amount", lag)``. The lab compares the two.
    Like it, the query steps back by rows, not by calendar days, so it is
    right only for a complete panel: a series with a missing day would get the
    value of the wrong day.

    Args:
        con: An open connection.
        daily: The processed daily dataset, a parquet file.
        lag: How many days back, at least 1.

    Returns:
        The columns ``store_id``, ``product_id``, ``dt``, ``sale_amount`` and
        ``sale_amount_lag_<lag>``, sorted by the first three. The first
        ``lag`` days of every series have no earlier value, and their lag is
        NaN: a value of another series never fills the gap.

    Raises:
        ValueError: ``lag`` is below 1.
    """
    raise NotImplementedError("Zadanie 15.8")


def rolling_mean_7(con: duckdb.DuckDBPyConnection, daily: Location) -> pd.DataFrame:
    """Add the mean sales of the previous 7 days to every row, per series.

    Mirrors ``add_rolling_mean(panel, "sale_amount", window=7, lag=1)``. The
    lab compares the two. The window is yesterday and the six days before
    it, never the day of the row itself, so the value could have been known
    when that day was forecast. Like the pandas function, it steps back by
    rows, which is right only for a complete panel.

    Args:
        con: An open connection.
        daily: The processed daily dataset, a parquet file.

    Returns:
        The columns ``store_id``, ``product_id``, ``dt``, ``sale_amount`` and
        ``sale_amount_mean_7_lag_1``, sorted by the first three. A row with
        fewer than 7 earlier days has NaN, not the mean of the few it has.
    """
    raise NotImplementedError("Zadanie 15.8")
