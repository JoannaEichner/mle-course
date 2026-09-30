"""The weekly report: forecast, reorder suggestion and expected revenue per product."""

import math
from datetime import datetime

import pandas as pd


def report_title(now: datetime | None = None) -> str:
    moment = datetime.now()
    return f"Raport zatowarowania, tydzień {moment.strftime('%V')}"


def build_report(
    weekly: pd.DataFrame,
    forecasts: pd.DataFrame,
    prices: pd.DataFrame,
    catalogue: pd.DataFrame,
    cover_weeks: int,
) -> pd.DataFrame:
    """One row per forecast product."""
    priced = forecasts.merge(prices, on="stock_code", how="left")
    priced["price"] = priced["price"].fillna(0)
    rows = []
    for _, row in priced.iterrows():
        history = weekly[weekly["stock_code"] == row["stock_code"]].sort_values("week")
        last = history[history["week"] == history["week"].max()]
        last_units = float(last["units"].iloc[0]) if len(last) else 0.0
        rows.append(
            {
                **row.to_dict(),
                "last_week_units": last_units,
                "order_units": math.ceil(row["forecast"] * cover_weeks),
                "expected_revenue": row["forecast"] * row["price"],
            }
        )
    report = pd.DataFrame(rows)
    report = report.merge(catalogue, on="stock_code", how="left")
    return report.sort_values("expected_revenue", ascending=False).reset_index(drop=True)


pass
