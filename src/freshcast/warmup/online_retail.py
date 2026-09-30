"""The raw UCI Online Retail II table: names, contracts, reading and validation.

The workbook ``online_retail_II.xlsx`` has two sheets, "Year 2009-2010" and
"Year 2010-2011", with one invoice line per row. Module 06 turns it into the
daily product table below, which later modules read. The constants in this
file are given; the functions are written in tasks 06.1 and 06.2.

Contract of ``data/processed/online_retail_daily.parquet`` (built by
``daily.build_daily``, one row per product and day with at least one sale or
return line):

    stock_code      str       product key: five digits and up to two letters
    date            datetime  the day, at midnight
    units_sold      int64     units on sale lines
    units_returned  int64     units on cancellation lines, as a positive number
    revenue         float64   sum of quantity * price over sale lines, in pounds

The table is sparse: a missing product-day means no line was booked, not that
demand was zero. 604 of the 739 calendar days from 2009-12-01 to 2011-12-09
have at least one line. The shop books nothing on Saturdays (one exception,
2009-12-05), nothing from Christmas Eve to 3 January (two gaps of eleven days,
so two whole weeks are absent) and nothing over Easter. The first day starts
at 07:45 and the last day, 2011-12-09, ends at 12:50, so the first and the last
week are partial. A weekly step has to fill the gaps knowingly.
"""

from pathlib import Path

import pandas as pd

# Header in the workbook -> column name used everywhere else.
SHEET_HEADERS = {
    "Invoice": "invoice",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "price",
    "Customer ID": "customer_id",
    "Country": "country",
}
SHEET = "sheet"
# The typed raw table and the parquet cache: the eight columns, then the
# name of the sheet each row came from.
RAW_COLUMNS = [*SHEET_HEADERS.values(), SHEET]
# Columns that are never missing in the file. ``description`` and
# ``customer_id`` may be.
REQUIRED_COLUMNS = [
    "invoice",
    "stock_code",
    "quantity",
    "invoice_date",
    "price",
    "country",
]

# Invoice numbers: six digits, with a letter prefix for two special kinds.
CANCELLATION_PREFIX = "C"
ADJUSTMENT_PREFIX = "A"
INVOICE_PATTERN = r"[CA]?\d{6}"
# A product code: five digits and up to two letters (85123A, 79323LP).
PRODUCT_CODE_PATTERN = r"\d{5}[A-Z]{0,2}"

# Columns added by ``lines.add_flags`` and ``lines.flag_repeat_lines``.
FLAG_COLUMNS = [
    "is_cancellation",
    "is_non_product",
    "is_missing_customer",
    "is_bad_price",
]
REPEAT_FLAG = "is_repeat_line"

# The processed daily dataset.
PRODUCT_KEY = ["stock_code", "date"]
MEASURE_COLUMNS = ["units_sold", "units_returned", "revenue"]
DAILY_COLUMNS = [*PRODUCT_KEY, *MEASURE_COLUMNS]


def read_sheets(path: Path) -> pd.DataFrame:
    """Read every sheet of the workbook into one typed table.

    Reading the workbook is slow (about half a minute for 1,067,371 rows,
    525,461 in the first sheet and 541,910 in the second) and reading the
    parquet cache written from it takes a few hundredths of a second, so
    this function is meant to run once (see ``build_cache``).

    Types matter because of what the workbook stores. Invoice numbers are
    numbers in 1,047,871 cells and text in 19,500 ("C489449", "A506401");
    stock codes are numbers in 932,385 cells and text in 134,986. Read as they
    come, both columns mix ``int`` and ``str``, and ``.str`` methods on such a
    column silently return NaN for every numeric cell: ``startswith("C")``
    would say nothing about 98% of the invoices. Customer ids are whole
    numbers (all 5,942 of them) but 243,007 cells are empty, so they arrive as
    floats. 4,382 descriptions are empty and 4 hold a number.

    Stock codes are also tidied, because the same product appears under two
    spellings: 3,471 rows use lowercase letters (183 codes; 173 of those also
    occur in upper case, 161 of them with the same description: ``85123a`` next
    to ``85123A``), and one row has a trailing space (``"47503J "``). The file
    has 5,305 distinct codes; after tidying, 5,131.

    Args:
        path: The ``.xlsx`` workbook.

    Returns:
        A frame with exactly the columns of ``RAW_COLUMNS``, in that order,
        and a fresh 0..n-1 index. Rows are in file order, the first sheet
        first. The eight headers are renamed as in ``SHEET_HEADERS`` and
        ``sheet`` holds the name of the sheet a row came from. Types:
        ``invoice``, ``stock_code``, ``description`` and ``country`` are
        strings, with missing descriptions left missing (not the text
        "nan"); ``customer_id`` is a nullable integer; ``invoice_date`` is a
        datetime; ``quantity`` is an integer and ``price`` a float.
        ``stock_code`` has no surrounding spaces and no lowercase letters.

    Raises:
        ValueError: A sheet lacks one of the headers of ``SHEET_HEADERS``.
    """
    raise NotImplementedError("Zadanie 06.1")


def build_cache(xlsx: Path, cache: Path) -> Path:
    """Read the workbook once and store the typed table as a parquet file.

    Args:
        xlsx: The ``.xlsx`` workbook.
        cache: Where to write the parquet file. Missing parent directories are
            created, an existing file is overwritten.

    Returns:
        ``cache``.

    Raises:
        ValueError: A sheet lacks one of the expected headers.
    """
    raise NotImplementedError("Zadanie 06.1")


def load_raw(cache: Path) -> pd.DataFrame:
    """Read the typed raw table written by ``build_cache``.

    Args:
        cache: The parquet file.

    Returns:
        The table exactly as ``read_sheets`` returned it: same columns, same
        types, same order.

    Raises:
        FileNotFoundError: The cache has not been built yet.
        ValueError: The file's columns differ from ``RAW_COLUMNS``, which
            means it was written by an older version of the code.
    """
    raise NotImplementedError("Zadanie 06.1")


def check_raw(raw: pd.DataFrame) -> None:
    """Raise unless ``raw`` satisfies the rules every later step relies on.

    The rules, in the order they are checked. On the real file every one of
    them holds, so a violation means the data or the code changed.

    1. The columns are exactly ``RAW_COLUMNS``.
    2. No missing value in ``REQUIRED_COLUMNS``. (Descriptions are missing in
       4,382 rows and customer ids in 243,007; both are allowed.)
    3. Every invoice number matches ``INVOICE_PATTERN``: six digits, with a
       ``C`` prefix for cancellations (8,292 invoices) or an ``A`` prefix for
       adjustments (6 invoices). A new prefix would change what the
       cancellation flag means.
    4. Every stock code is tidy: it equals itself stripped and upper-cased.
    5. Quantity is never 0.
    6. A negative quantity has a reason: the invoice is a cancellation
       (19,493 rows) or the price is 0 (3,457 rows, stock written off without
       a customer). No row is negative for any other reason.
    7. A negative price only occurs on an adjustment invoice (5 rows, all
       "Adjust bad debt").
    8. An invoice has one country and at most one customer id (53,628
       invoices).

    Args:
        raw: The typed raw table, as returned by ``load_raw``.

    Raises:
        ValueError: A rule is broken. The message names the rule and says how
            many rows or invoices break it.
    """
    raise NotImplementedError("Zadanie 06.2")
