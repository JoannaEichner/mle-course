"""Turning invoice lines into sales and returns of real products."""

import pandas as pd

# Codes like POST, M, D, DOT, BANK CHARGES are not products.
PRODUCT_CODE = r"^\d{5}[A-Z]{0,2}$"


def keep_products(lines: pd.DataFrame) -> pd.DataFrame:
    is_product = lines["stock_code"].str.match(PRODUCT_CODE)
    return lines[is_product].copy()


def split_returns(lines: pd.DataFrame) -> pd.DataFrame:
    """Add qty_sold and qty_returned.

    Cancellation invoices start with C and carry negative quantities. Lines
    with a negative quantity that are not cancellations are stock write-offs
    and are not customer returns, so they count as neither.
    """
    out = lines.copy()
    cancelled = out["invoice"].str.startswith("C")
    out["qty_sold"] = out["quantity"].where(~cancelled & (out["quantity"] > 0), 0)
    out["qty_returned"] = (-out["quantity"]).where(cancelled & (out["quantity"] < 0), 0)
    return out


def net_units(lines: pd.DataFrame) -> pd.Series:
    """Units that stayed with customers, per line."""
    # quantity is already negative on returns
    return lines["quantity"].clip(lower=None) - lines["qty_returned"]


def clean(lines: pd.DataFrame) -> pd.DataFrame:
    products = keep_products(lines)
    products = split_returns(products)
    products["net_qty"] = net_units(products)
    return products
