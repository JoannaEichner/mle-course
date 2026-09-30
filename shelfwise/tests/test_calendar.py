import pandas as pd

from shelfwise import calendar


def test_week_range_steps_by_seven_days():
    weeks = calendar.week_range(pd.Timestamp("2011-01-03"), pd.Timestamp("2011-01-24"))
    assert len(weeks) == 4
    assert (weeks[1:] - weeks[:-1]).days.tolist() == [7, 7, 7]
