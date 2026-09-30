import numpy as np
import pandas as pd

from shelfwise import features, model


def _frame(products: int = 5, weeks: int = 40) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    rows = []
    for number in range(products):
        for week in pd.date_range("2010-01-04", periods=weeks, freq="7D"):
            rows.append((f"2{number:04d}", week, float(rng.poisson(5 + number))))
    return pd.DataFrame(rows, columns=["stock_code", "week", "units"])


def test_lags_stay_within_a_product():
    built = features.add_history(_frame(products=2, weeks=5))
    firsts = built.groupby("stock_code").head(1)
    assert firsts["units_lag_1"].isna().all()


def test_split_weeks_holds_out_the_last_weeks():
    train, valid = model.split_weeks(_frame(), validation_weeks=8)
    assert valid["week"].nunique() == 8
    assert train["week"].max() < valid["week"].min()


def test_train_and_validate_returns_forecasts():
    frame = features.build(_frame())
    fitted, valid = model.train_and_validate(frame, validation_weeks=8)
    assert (valid["forecast"] >= 0).all()
    assert len(model.predict_next(frame, fitted)) == 5
