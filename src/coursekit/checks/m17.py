"""Checks for module 17: tickets in shelfwise, someone else's codebase.

Each check is the hidden acceptance test of one ticket. It fails on the code
as the learner receives it and passes once the ticket is done. Messages
restate the symptom, never the cause.
"""

import importlib
import importlib.util
import sys
import time
from collections.abc import Callable
from types import ModuleType
from typing import cast

import numpy as np
import pandas as pd

from coursekit import paths
from coursekit.checking import CheckFailed, expect, task

SHELFWISE = paths.ROOT / "shelfwise"
SAMPLE = paths.FIXTURES_DIR / "shelfwise_lines.parquet"
NET_UNITS = {
    "20713": 22833,
    "21034": 4214,
    "21181": 25427,
    "22088": 4335,
    "22138": 8537,
    "22423": 26126,
    "46000M": 4204,
    "82494L": 15725,
    "85123A": 97111,
}
STALE_PRODUCT = "22088"


def _shelfwise(module: str) -> ModuleType:
    """Import a shelfwise module from the repository, fresh."""
    if str(SHELFWISE) not in sys.path:
        sys.path.insert(0, str(SHELFWISE))
    for name in list(sys.modules):
        if name == "shelfwise" or name.startswith("shelfwise."):
            del sys.modules[name]
    return importlib.import_module(f"shelfwise.{module}")


def _lines() -> pd.DataFrame:
    lines = pd.read_parquet(SAMPLE)
    lines["stock_code"] = lines["stock_code"].str.strip().str.upper()
    return lines


def _needs(module: ModuleType, name: str, ticket: str) -> Callable[..., object]:
    found = getattr(module, name, None)
    if found is None:
        raise CheckFailed(f"{ticket}: w {module.__name__} nie ma jeszcze {name}.")
    return found  # type: ignore[no-any-return]


@task("17.1", "T1: sumy sprzedaży zgodne z fakturami", starts_as="fail")
def check_t1(_target: object) -> None:
    cleaning = _shelfwise("cleaning")
    clean = cleaning.clean(_lines())
    got = {
        code: int(units)
        for code, units in clean.groupby("stock_code")["net_qty"].sum().items()
    }
    wrong = {
        code: (got.get(code), units)
        for code, units in NET_UNITS.items()
        if got.get(code) != units
    }
    expect(
        not wrong,
        "Sprzedaż netto (sprzedane minus zwrócone przez klientów) nadal nie zgadza się z "
        f"fakturami dla {len(wrong)} z {len(NET_UNITS)} produktów próbki, na przykład "
        f"{next(iter(wrong.items())) if wrong else ''} (raport, faktury).",
    )


@task("17.2", "T2: WAPE per kategoria w raporcie", starts_as="fail")
def check_t2(_target: object) -> None:
    report = _shelfwise("report")
    by_category = _needs(report, "wape_by_category", "T2")
    valid = pd.DataFrame(
        {
            "stock_code": ["A", "A", "B", "C"],
            "category": ["X", "X", "Y", "Y"],
            "units": [10.0, 10.0, 5.0, 15.0],
            "forecast": [8.0, 12.0, 5.0, 10.0],
        }
    )
    table = cast(pd.DataFrame, by_category(valid))
    expect(
        isinstance(table, pd.DataFrame)
        and {"category", "products", "units", "wape"} <= set(table.columns),
        "T2: tabela ma mieć kolumny category, products, units i wape.",
    )
    rows = table.set_index("category")
    wapes = rows["wape"].astype(float)
    expect(
        bool(np.isclose(wapes["X"], 0.2))
        and bool(np.isclose(wapes["Y"], 0.25))
        and int(rows["products"].astype(int)["Y"]) == 2,
        "T2: WAPE kategorii to suma błędów bezwzględnych przez sumę sprzedaży w tej "
        f"kategorii. Dla danych testowych X = 0.2, Y = 0.25. Dostałem {rows['wape'].to_dict()}.",
    )


@task(
    "17.3", "T3: cecha sezonu z ustawieniem, testami i dokumentacją", starts_as="fail"
)
def check_t3(_target: object) -> None:
    config = _shelfwise("config")
    features = _shelfwise("features")
    model = _shelfwise("model")
    expect(
        getattr(config.ModelConfig(), "use_season", None) is False,
        "T3: ustawienie model.use_season ma istnieć i domyślnie być wyłączone.",
    )
    add_season = _needs(features, "add_season", "T3")
    weeks = pd.DataFrame(
        {"week": pd.to_datetime(["2010-09-27", "2010-10-04", "2010-12-27"])}
    )
    expect(
        cast(pd.DataFrame, add_season(weeks))["is_season"].tolist() == [0, 1, 1],
        "T3: tygodnie od października do grudnia mają mieć is_season = 1, pozostałe 0.",
    )
    expect(
        "is_season" in model.feature_columns(use_season=True)
        and "is_season" not in model.feature_columns(use_season=False),
        "T3: model ma używać cechy sezonu tylko wtedy, gdy ustawienie jest włączone.",
    )
    reference = paths.ROOT / "reference" / "17" / "shelfwise" / "README.md"
    readme_path = reference if reference.is_file() else SHELFWISE / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    expect("use_season" in readme, "T3: README ma opisywać nowe ustawienie use_season.")


def _weekly_frame() -> pd.DataFrame:
    cleaning = _shelfwise("cleaning")
    weekly = _shelfwise("weekly")
    features = _shelfwise("features")
    built: pd.DataFrame = features.build(weekly.weekly_demand(cleaning.clean(_lines())))
    return built


@task("17.4", "T4: walidacja nie widzi tygodni walidacyjnych", starts_as="fail")
def check_t4(_target: object) -> None:
    model = _shelfwise("model")
    frame = _weekly_frame()
    _, first = model.train_and_validate(frame, validation_weeks=8)
    changed = frame.copy()
    last = changed["week"] >= np.sort(changed["week"].unique())[-8]
    changed.loc[last, "units"] *= 100
    _, second = model.train_and_validate(changed, validation_weeks=8)
    week = first["week"].min()
    same = np.allclose(
        first.loc[first["week"] == week, "forecast"],
        second.loc[second["week"] == week, "forecast"],
    )
    expect(
        same,
        "T4: prognoza pierwszego tygodnia walidacji zmienia się, gdy zmieniamy sprzedaż "
        "w tygodniach walidacyjnych. Wynik walidacji zależy więc od danych, których model "
        "w produkcji nie zna.",
    )


@task("17.5", "T5: test tytułu raportu przechodzi każdego dnia", starts_as="fail")
def check_t5(_target: object) -> None:
    from freezegun import freeze_time

    path = SHELFWISE / "tests" / "test_report.py"
    spec = importlib.util.spec_from_file_location("check_test_report", path)
    if spec is None or spec.loader is None:
        raise CheckFailed("T5: nie udało się wczytać tests/test_report.py.")
    _shelfwise("report")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    tests = [
        getattr(module, name)
        for name in dir(module)
        if name.startswith("test") and "title" in name
    ]
    expect(bool(tests), "T5: w tests/test_report.py nie ma testu tytułu raportu.")
    for day in ("2026-01-05", "2026-03-02", "2026-09-30", "2027-01-01"):
        with freeze_time(day):
            for test in tests:
                try:
                    test()
                except AssertionError as error:
                    raise CheckFailed(
                        f"T5: test {test.__name__} nie przechodzi, gdy jest {day}."
                    ) from error


@task("17.6", "T6: raport liczy się szybko także dla wielu produktów", starts_as="fail")
def check_t6(_target: object) -> None:
    report = _shelfwise("report")
    products, weeks = 3000, 60
    codes = [f"P{number:05d}" for number in range(products)]
    starts = pd.date_range("2010-01-04", periods=weeks, freq="7D")
    weekly = pd.DataFrame(
        {
            "stock_code": np.repeat(codes, weeks),
            "week": np.tile(starts, products),
            "units": np.tile(np.arange(weeks, dtype=float), products),
        }
    )
    forecasts = pd.DataFrame({"stock_code": codes, "forecast": 3.3})
    prices = pd.DataFrame({"stock_code": codes, "price": 2.0})
    catalogue = pd.DataFrame(
        {"stock_code": codes, "description": "x", "category": "OTHER"}
    )
    started = time.perf_counter()
    table = report.build_report(weekly, forecasts, prices, catalogue, cover_weeks=2)
    seconds = time.perf_counter() - started
    expect(
        len(table) == products and bool((table["last_week_units"] == weeks - 1).all()),
        "T6: raport ma nadal zawierać ostatni tydzień sprzedaży każdego produktu.",
    )
    expect(
        seconds < 2.0,
        f"T6: raport dla {products} produktów liczy się {seconds:.1f} s. Cel: poniżej 2 s.",
    )


@task("17.7", "przychód liczony dla każdego produktu z prognozą", starts_as="fail")
def check_prices(_target: object) -> None:
    cleaning = _shelfwise("cleaning")
    weekly = _shelfwise("weekly")
    prices = weekly.current_prices(cleaning.clean(_lines()), 13).set_index(
        "stock_code"
    )["price"]
    expect(
        STALE_PRODUCT in prices.index and prices[STALE_PRODUCT] > 0,
        f"Produkt {STALE_PRODUCT} nie sprzedawał się w ostatnich 13 tygodniach, ale ma prognozę. "
        "Jego przychód w raporcie wychodzi zerowy.",
    )


@task("17.8", "katalog produktów nie mnoży wierszy", starts_as="fail")
def check_catalogue(_target: object) -> None:
    io = _shelfwise("io")
    catalogue = io.build_catalogue(_lines())
    expect(
        catalogue["stock_code"].is_unique and len(catalogue) == len(NET_UNITS),
        f"Katalog ma {len(catalogue)} wierszy dla {len(NET_UNITS)} produktów próbki. Raport "
        "pokazuje część produktów kilka razy.",
    )


@task("17.9", "tydzień od poniedziałku do niedzieli", starts_as="fail")
def check_weeks(_target: object) -> None:
    calendar = _shelfwise("calendar")
    days = pd.Series(pd.date_range("2011-03-07 13:00", periods=7, freq="D"))
    starts = calendar.week_start(days)
    expect(
        bool((starts == pd.Timestamp("2011-03-07")).all()),
        "Sprzedaż z 7-13 marca 2011 (poniedziałek-niedziela) nie trafia w całości do tygodnia "
        f"zaczynającego się 7 marca. Dostałem początki: {sorted({str(d.date()) for d in starts})}.",
    )
