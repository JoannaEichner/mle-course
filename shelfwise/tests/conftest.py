import pandas as pd
import pytest


@pytest.fixture
def lines() -> pd.DataFrame:
    """A handful of invoice lines covering the usual cases."""
    return pd.DataFrame(
        {
            "invoice": ["500001", "500001", "C500002", "500003", "500004", "500005"],
            "stock_code": ["21212", "POST", "21212", "22333", "21212", "22333"],
            "description": [
                "CAKE CASES",
                "POSTAGE",
                "CAKE CASES",
                "RED BAG",
                "CAKE CASES",
                "RED BAG",
            ],
            "quantity": [10, 1, -4, 6, 5, -2],
            "invoice_date": pd.to_datetime(
                [
                    "2011-03-07 10:00",
                    "2011-03-07 10:00",
                    "2011-03-08 12:00",
                    "2011-03-09 09:30",
                    "2011-03-15 11:00",
                    "2011-03-16 15:00",
                ]
            ),
            "price": [0.55, 18.0, 0.55, 1.65, 0.55, 0.0],
            "customer_id": pd.array([1, 1, 1, 2, 3, pd.NA], dtype="Int64"),
            "country": ["United Kingdom"] * 6,
        }
    )
