"""Invoice lines: flags, the sheet overlap, repeated lines, product lines.

Tasks 06.3 to 06.5. Every function takes the frame produced by the step
before it (the typed raw table, see ``online_retail``) and returns a new
frame; none changes its input.
"""

import pandas as pd

from freshcast.warmup.online_retail import (
    RAW_COLUMNS,
    SHEET,
)

# The eight columns of an invoice line, without the sheet it was read from.
LINE_COLUMNS = [column for column in RAW_COLUMNS if column != SHEET]


def add_flags(raw: pd.DataFrame) -> pd.DataFrame:
    """Describe every line with four boolean flags, without dropping any.

    A flag says what a line is. What to do with it is decided later, in
    ``product_lines``. What the real file (1,067,371 lines) says about each:

    - ``is_cancellation``: the invoice number starts with ``C``. 19,494 lines
      (1.8%) on 8,292 of 53,628 invoices. All but one have a negative
      quantity; the exception is a "Manual" line with quantity 1.
    - ``is_non_product``: the stock code is not five digits followed by up to
      two letters. 6,093 lines (0.6%) in 61 codes; the other 5,070 codes
      match. They are postage (POST 2,122 lines, DOT 1,446), manual entries
      (M 1,426), carriage, discounts, samples, bank charges, adjustments,
      fees, gift vouchers, test products and 158 lines of dotcom-shop codes
      (``DCGS...``) that do sell real goods, but only 266 units on 125 sale
      lines in two years.
    - ``is_missing_customer``: the customer id is missing. 243,007 lines
      (22.8%). It is a property of the invoice: 8,752 invoices have no id on
      any line, 44,876 have one on every line, none is mixed.
    - ``is_bad_price``: the price is 0 or negative. 6,207 lines: 5 negative
      (the "Adjust bad debt" adjustment invoices) and 6,202 at zero. Of the
      zero-price lines 3,457 have a negative quantity, no customer and no
      cancellation invoice: stock written off ("damages", "check"). The other
      2,745 have a positive quantity and mostly no customer (2,674): samples,
      found stock, manual corrections. Neither kind is a sale.

    Args:
        raw: The typed raw table with tidy stock codes (``read_sheets``).

    Returns:
        A new frame with the columns of ``raw`` plus the four flags of
        ``FLAG_COLUMNS`` as ``bool`` columns, same rows, same order, same
        index.
    """
    raise NotImplementedError("Zadanie 06.3")


def drop_sheet_overlap(raw: pd.DataFrame) -> pd.DataFrame:
    """Drop the second copy of every invoice that occurs in both sheets.

    The sheets overlap: 1,088 invoices, all dated between 2010-12-01 and
    2010-12-09, are in "Year 2009-2010" and again in "Year 2010-2011". The
    copies are identical line for line (22,523 lines in each sheet, compared
    after sorting), so keeping both would count nine days of sales twice.
    This is not the same as dropping exact duplicates, see
    ``flag_repeat_lines``.

    Args:
        raw: The typed raw table with a ``sheet`` column.

    Returns:
        A new frame without the lines of the later copies, in the original
        order, with a fresh 0..n-1 index. For an invoice that occurs in
        several sheets the copy from the first sheet in name order is kept.
        A frame without such invoices comes back with all its rows.

    Raises:
        ValueError: Copies of an invoice differ in the number of lines or in
            the total quantity, so they are not copies. The message says how
            many invoices.
    """
    raise NotImplementedError("Zadanie 06.4")


def flag_repeat_lines(raw: pd.DataFrame) -> pd.DataFrame:
    """Mark lines that repeat an earlier line of the table exactly.

    Two lines are the same when all eight ``LINE_COLUMNS`` agree, a missing
    value counting as equal to a missing value. The lines are marked, not
    dropped, and the daily dataset keeps them. What the real file says, after
    ``drop_sheet_overlap``:

    - 11,812 of 1,044,848 lines (1.1%) repeat an earlier one, on 4,387
      invoices. They are in the source, not made by the export: the overlap
      between the sheets contains 321 of them in each copy.
    - Only 1,685 stand directly under their twin, so most are not a double
      keystroke. Among the 20,955 invoice and product pairs booked on two
      or more sale lines, 48% have identical quantities. Drawing quantities
      independently from each product's own distribution would give 22%. So
      some repeats are probably re-keyed lines, but not most of the lines
      that look like repeats.
    - The evidence does not point to billing errors. Customers who bought a
      product on a repeated line returned some of it later in 2.5% of the
      cases, against 4.1% for a product on a single line.
    - The effect is small: the repeats in sale lines carry 0.30% of the units
      and 0.29% of the revenue.

    The file cannot settle whether they are errors, and the cost is at most
    0.30% of the units either way. Marking is reversible and dropping is not,
    so the repeats stay and this flag lets anyone measure what dropping them
    would change. ``DataFrame.drop_duplicates`` would have removed 34,335
    lines at once: the 22,523 sheet copies, which are certainly wrong, and
    these 11,812, which are not certainly anything.

    Args:
        raw: A typed raw table.

    Returns:
        A new frame with the columns of ``raw`` plus a ``bool`` column
        ``is_repeat_line``, True for every occurrence after the first, same
        rows, same order, same index.
    """
    raise NotImplementedError("Zadanie 06.4")


def product_lines(flagged: pd.DataFrame) -> pd.DataFrame:
    """Reduce flagged lines to product sale lines and product return lines.

    A line is kept when its stock code is a product and either

    - it is a sale: not a cancellation and the price is above 0, or
    - it is a return: a cancellation. Their prices are all above 0.

    Everything else goes. Counted after ``drop_sheet_overlap``, on 1,044,848
    lines: 1,014,945 sale lines and 17,973 return lines are kept; 11,930 are
    dropped, 5,992 for a non-product code and 5,938 product lines with price
    0 (2,576 giveaways with a positive quantity and 3,362 write-offs with a
    negative one). Write-offs are not returns: taking every negative quantity
    as a return would give 1,033,911 returned units instead of 469,881.

    Lines without a customer id are kept. They are 22.3% of the sale lines
    (226,758) but only 6.1% of the units and 13.1% of the revenue: a median
    of 1 unit per line against 5, at a median price of 3.29 pounds against
    1.95. That is a different kind of buyer, not a random hole in the data,
    and dropping the lines would remove a real part of demand. Nothing in the
    daily table needs the customer.

    Args:
        flagged: Output of ``add_flags``, after ``drop_sheet_overlap``.

    Returns:
        One row per kept line, in the original order, with a fresh index and
        the columns ``stock_code``, ``date`` (the invoice day at midnight),
        ``units_sold``, ``units_returned`` (a positive number) and
        ``revenue`` (quantity times price for a sale line, in pounds). A sale
        line has ``units_returned`` 0, a return line has ``units_sold`` 0 and
        ``revenue`` 0.0.

    Raises:
        ValueError: A kept sale line has a quantity of 0 or less, or a kept
            return line a quantity of 0 or more. The message says how many.
    """
    raise NotImplementedError("Zadanie 06.5")
