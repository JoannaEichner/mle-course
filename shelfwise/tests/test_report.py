import pandas as pd

from shelfwise import report


def _inputs():
    weekly = pd.DataFrame(
        {
            "stock_code": ["A", "A", "B"],
            "week": pd.to_datetime(["2011-03-07", "2011-03-14", "2011-03-14"]),
            "units": [4.0, 6.0, 2.0],
        }
    )
    forecasts = pd.DataFrame({"stock_code": ["A", "B"], "forecast": [5.0, 1.2]})
    prices = pd.DataFrame({"stock_code": ["A", "B"], "price": [2.0, 10.0]})
    catalogue = pd.DataFrame(
        {"stock_code": ["A", "B"], "description": ["a", "b"], "category": ["X", "Y"]}
    )
    return weekly, forecasts, prices, catalogue


def test_report_orders_by_expected_revenue():
    table = report.build_report(*_inputs(), cover_weeks=2)
    assert table["stock_code"].tolist() == ["B", "A"]
    assert table["order_units"].tolist() == [3, 10]
    assert table["last_week_units"].tolist() == [2.0, 6.0]


def test_report_title_uses_the_iso_week():
    from datetime import date

    week = date.today().isocalendar().week
    assert report.report_title() == f"Raport zatowarowania, tydzień {week}"
