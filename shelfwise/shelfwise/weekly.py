"""Weekly demand per product."""

import pandas as pd

from shelfwise.calendar import week_range, week_start


def weekly_demand(clean_lines: pd.DataFrame, first_day: int = 0) -> pd.DataFrame:
    """Sum net units and revenue per product and week.

    Weeks without sales are filled with zero demand, so every product has an
    unbroken row per week from its first sale to the end of the data.
    """
    frame = clean_lines.assign(week=week_start(clean_lines["invoice_date"], first_day))
    frame["revenue"] = frame["qty_sold"] * frame["price"]
    sums = frame.groupby(["stock_code", "week"], as_index=False).agg(
        units=("net_qty", "sum"), revenue=("revenue", "sum")
    )

    all_weeks = week_range(sums["week"].min(), sums["week"].max())
    first_sale = sums.groupby("stock_code")["week"].min()
    rows = []
    for code, start in first_sale.items():
        for wk in all_weeks[all_weeks >= start]:
            rows.append((code, wk))
    grid = pd.DataFrame(rows, columns=["stock_code", "week"])
    weekly = grid.merge(sums, on=["stock_code", "week"], how="left")
    weekly[["units", "revenue"]] = weekly[["units", "revenue"]].fillna(0)
    return weekly.sort_values(["stock_code", "week"]).reset_index(drop=True)


def add_catalogue(weekly: pd.DataFrame, catalogue: pd.DataFrame) -> pd.DataFrame:
    return weekly.merge(catalogue, on="stock_code", how="left")


def active_products(weekly: pd.DataFrame, min_weeks: int) -> list[str]:
    selling = weekly[weekly["units"] > 0].groupby("stock_code")["week"].nunique()
    return sorted(selling[selling >= min_weeks].index)


def current_prices(clean_lines: pd.DataFrame, lookback_weeks: int) -> pd.DataFrame:
    """Median selling price per product."""
    sold = clean_lines[clean_lines["qty_sold"] > 0]
    since = sold["invoice_date"].max() - pd.Timedelta(weeks=lookback_weeks)
    prices = sold[sold["invoice_date"] >= since].groupby("stock_code")["price"].median()
    return prices.rename("price").reset_index()
