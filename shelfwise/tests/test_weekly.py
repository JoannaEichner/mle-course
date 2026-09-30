import pandas as pd

from shelfwise import cleaning, io, weekly


def test_weekly_demand_fills_weeks_without_sales(lines):
    clean = cleaning.clean(lines)
    clean.loc[clean["invoice_date"] > "2011-03-10", "invoice_date"] += pd.Timedelta(weeks=1)
    demand = weekly.weekly_demand(clean)
    cake = demand[demand["stock_code"] == "21212"]
    assert len(cake) == 3
    assert cake["units"].tolist()[1] == 0


def test_current_prices_is_a_median(lines):
    clean = cleaning.clean(lines)
    prices = weekly.current_prices(clean, lookback_weeks=13).set_index("stock_code")["price"]
    assert prices["21212"] == 0.55


def test_catalogue_has_categories(lines):
    catalogue = io.build_catalogue(lines)
    assert set(catalogue["category"]) >= {"KITCHEN", "BAGS"}
