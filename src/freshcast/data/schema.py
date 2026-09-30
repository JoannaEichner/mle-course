"""Column names of the raw FreshRetailNet-50K files and of the processed dataset.

This file is given. Import the names from here instead of typing column
strings by hand, so a typo fails at import time and not halfway through a run.
"""

SERIES_KEY = ["store_id", "product_id"]
DATE = "dt"
TARGET = "sale_amount"
CITY = "city_id"
DISCOUNT = "discount"

HIERARCHY = [
    "management_group_id",
    "first_category_id",
    "second_category_id",
    "third_category_id",
]
FLAGS = ["holiday_flag", "activity_flag"]
WEATHER = ["precpt", "avg_temperature", "avg_humidity", "avg_wind_level"]

# Raw names of the three stockout columns. Status 1 means "out of stock".
RAW_OOS_HOURS = "stock_hour6_22_cnt"
HOURLY_SALES = "hours_sale"
HOURLY_STOCKOUT = "hours_stock_status"
HOURS_PER_DAY = 24
# The raw count covers the hours 06:00-21:59, i.e. array positions 6..21.
OOS_WINDOW = slice(6, 22)

# Scalar columns: cheap to load. The two hourly columns are 24-element arrays
# per row and cost about ten times more memory than everything else together.
DAILY_COLUMNS = [
    *SERIES_KEY,
    CITY,
    DATE,
    TARGET,
    DISCOUNT,
    RAW_OOS_HOURS,
    *FLAGS,
    *WEATHER,
]
HOURLY_COLUMNS = [*SERIES_KEY, DATE, HOURLY_SALES, HOURLY_STOCKOUT]

# Contract of data/processed/daily.parquet, written in module 07 and read by
# every later module.
DISCOUNT_IS_ZERO = "discount_is_zero"
OOS_HOURS = "oos_hours"
OOS_HOURS_TOTAL = "oos_hours_total"
SALES_IN_STOCK = "sales_in_stock"
SALES_WHILE_OOS = "sales_while_oos"
PROCESSED_COLUMNS = [
    *SERIES_KEY,
    CITY,
    DATE,
    TARGET,
    DISCOUNT,
    DISCOUNT_IS_ZERO,
    *FLAGS,
    *WEATHER,
    OOS_HOURS,
    OOS_HOURS_TOTAL,
    SALES_IN_STOCK,
    SALES_WHILE_OOS,
]
