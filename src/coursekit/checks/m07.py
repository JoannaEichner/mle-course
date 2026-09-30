"""Checks for module 07: pandas on a panel.

Every check runs on ``fixtures/frn_sample.parquet``: 8 real series, 90 days,
raw schema. Expected numbers are constants measured on that file, so the
checks do not contain a second implementation of the tasks.
"""

import tempfile
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from coursekit import paths
from coursekit.checking import CheckFailed, expect, task

SAMPLE = paths.FIXTURES_DIR / "frn_sample.parquet"
N_ROWS = 720
N_SERIES = 8
N_DAYS = 90
KEY = ["store_id", "product_id"]
ROW_KEY = [*KEY, "dt"]


def _raises(call: Callable[[], object], error: type[Exception], when: str) -> None:
    """Fail unless ``call`` raises ``error``. ``when`` describes the input."""
    try:
        call()
    except error:
        return
    except NotImplementedError:
        raise
    except Exception as other:  # noqa: BLE001 - the wrong exception type is the finding
        raise CheckFailed(
            f"Dla danych, w których {when}, oczekiwano {error.__name__}, "
            f"a poleciał {type(other).__name__}."
        ) from other
    raise CheckFailed(
        f"Dla danych, w których {when}, funkcja powinna zgłosić {error.__name__}, "
        "a zakończyła się bez błędu."
    )


def _is_sorted(df: pd.DataFrame) -> bool:
    return bool(df[ROW_KEY].equals(df[ROW_KEY].sort_values(ROW_KEY)))


def _tiny_panel() -> pd.DataFrame:
    """Two series, five days, values that make cross-series leaks visible."""
    days = pd.date_range("2024-04-01", periods=5)
    return pd.DataFrame(
        {
            "store_id": [1] * 5 + [2] * 5,
            "product_id": [7] * 10,
            "dt": [*days, *days],
            "sale_amount": [1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 20.0, 30.0, 40.0, 50.0],
        }
    )


@task("07.1", "load_sales: tylko potrzebne kolumny i miasta, małe typy, sortowanie")
def check_load(_target: object) -> None:
    from freshcast.data import load
    from freshcast.data.schema import DAILY_COLUMNS

    frame = pd.DataFrame(
        {
            "small": np.array([1, 2, 3], dtype="int64"),
            "big": np.array([1, 2, 3_000_000_000], dtype="int64"),
            "ratio": np.array([0.1, 0.2, 0.3], dtype="float64"),
        }
    )
    shrunk = load.shrink_integers(frame)
    expect(
        isinstance(shrunk, pd.DataFrame)
        and list(shrunk.columns) == list(frame.columns),
        "shrink_integers ma zwrócić DataFrame z tymi samymi kolumnami w tej samej "
        "kolejności.",
    )
    expect(
        shrunk["small"].dtype == "int8",
        f"Kolumna z wartościami 1, 2, 3 mieści się w int8, a ma typ "
        f"{shrunk['small'].dtype}.",
    )
    expect(
        shrunk["big"].dtype == "int64",
        "Kolumna z wartością 3 000 000 000 nie mieści się w int32. Zmniejszenie "
        "typu nie może zmienić wartości.",
    )
    expect(
        shrunk["ratio"].dtype == "float64",
        "shrink_integers ma zostawić kolumny zmiennoprzecinkowe bez zmian.",
    )
    expect(
        frame["small"].dtype == "int64",
        "shrink_integers zmieniło ramkę wejściową. Zwróć nową ramkę.",
    )

    daily = load.load_sales(SAMPLE)
    expect(
        list(daily.columns) == DAILY_COLUMNS,
        "load_sales bez argumentu columns ma zwrócić dokładnie DAILY_COLUMNS, "
        f"w tej kolejności. Dostałem: {list(daily.columns)}",
    )
    expect(len(daily) == N_ROWS, f"Oczekiwano {N_ROWS} wierszy, jest {len(daily)}.")
    expect(
        pd.api.types.is_datetime64_any_dtype(daily["dt"]),
        f"Kolumna dt ma typ {daily['dt'].dtype}, a powinna być datą (datetime64).",
    )
    expect(
        _is_sorted(daily),
        "Wynik nie jest posortowany po store_id, product_id, dt.",
    )
    expect(
        daily.index.equals(pd.RangeIndex(len(daily))),
        "Po sortowaniu indeks powinien biec od 0 do n-1. Teraz niesie stare "
        "pozycje wierszy.",
    )
    expect(
        daily["store_id"].dtype == "int16" and daily["city_id"].dtype == "int8",
        "Kolumny całkowite nie zostały zmniejszone (store_id ma "
        f"{daily['store_id'].dtype}, city_id ma {daily['city_id'].dtype}).",
    )

    one_city = load.load_sales(SAMPLE, cities=[3])
    expect(
        len(one_city) == 540 and set(one_city["city_id"]) == {3},
        "load_sales(cities=[3]) ma zwrócić tylko wiersze miasta 3 (540 wierszy "
        f"w próbce). Dostałem {len(one_city)} wierszy.",
    )
    narrow = load.load_sales(SAMPLE, cities=[11], columns=[*ROW_KEY, "sale_amount"])
    expect(
        list(narrow.columns) == [*ROW_KEY, "sale_amount"] and len(narrow) == 180,
        "Filtr miast ma działać także wtedy, gdy city_id nie ma wśród "
        "wczytywanych kolumn. Oczekiwano 180 wierszy i 4 kolumn, jest "
        f"{len(narrow)} wierszy i kolumny {list(narrow.columns)}.",
    )


@task("07.2", "check_panel i clean_discount: reguły panelu, zero rabatu poza skalą")
def check_validate(_target: object) -> None:
    from freshcast.data import validate

    raw = pd.read_parquet(SAMPLE, columns=[*ROW_KEY, "sale_amount", "discount"])
    good = raw.assign(dt=pd.to_datetime(raw["dt"])).sort_values(ROW_KEY)
    good = good.reset_index(drop=True)

    try:
        validate.check_panel(good)
    except ValueError as error:
        raise CheckFailed(
            f"check_panel odrzuciło poprawny panel z komunikatem: {error}"
        ) from error

    _raises(
        lambda: validate.check_panel(pd.concat([good, good.iloc[[5]]])),
        ValueError,
        "jeden wiersz jest powtórzony",
    )
    _raises(
        lambda: validate.check_panel(good.drop(index=40)),
        ValueError,
        "jednej serii brakuje jednego dnia w środku",
    )
    with_nan = good.copy()
    with_nan.loc[3, "sale_amount"] = np.nan
    _raises(
        lambda: validate.check_panel(with_nan), ValueError, "sprzedaż ma brak (NaN)"
    )
    negative = good.copy()
    negative.loc[3, "sale_amount"] = -0.5
    _raises(lambda: validate.check_panel(negative), ValueError, "sprzedaż jest ujemna")

    cleaned = validate.clean_discount(good)
    expect(
        "discount_is_zero" in cleaned.columns
        and cleaned["discount_is_zero"].dtype == bool,
        "clean_discount ma dodać kolumnę discount_is_zero typu bool.",
    )
    expect(
        int(cleaned["discount_is_zero"].sum()) == 3,
        "W próbce są 3 wiersze z discount == 0. discount_is_zero wskazuje "
        f"{int(cleaned['discount_is_zero'].sum())}.",
    )
    expect(
        int(cleaned["discount"].isna().sum()) == 3
        and bool(cleaned.loc[cleaned["discount_is_zero"], "discount"].isna().all()),
        "Zero ma stać się NaN dokładnie w wierszach, w których discount_is_zero "
        "jest True.",
    )
    kept = good["discount"] != 0
    expect(
        bool((cleaned.loc[kept, "discount"] == good.loc[kept, "discount"]).all()),
        "Wszystkie rabaty różne od 0 mają zostać bez zmian, także te powyżej 1. "
        f"W próbce największy to 1.088, u Ciebie {cleaned['discount'].max()}.",
    )
    expect(
        int((good["discount"] == 0).sum()) == 3 and "discount_is_zero" not in good,
        "clean_discount zmieniło ramkę wejściową. Zwróć nową ramkę.",
    )
    below_zero = good.copy()
    below_zero.loc[0, "discount"] = -0.2
    _raises(
        lambda: validate.clean_discount(below_zero), ValueError, "rabat jest ujemny"
    )
    already_nan = good.copy()
    already_nan.loc[0, "discount"] = np.nan
    _raises(
        lambda: validate.clean_discount(already_nan),
        ValueError,
        "rabat ma brak (NaN) już na wejściu",
    )


@task("07.3", "wymiary sklepu i produktu, attach_dim bez gubienia i mnożenia wierszy")
def check_dims(_target: object) -> None:
    from freshcast.data import dims

    raw = pd.read_parquet(SAMPLE).drop(columns=["hours_sale", "hours_stock_status"])
    fact = raw.sort_values(ROW_KEY).reset_index(drop=True)

    stores = dims.build_store_dim(fact)
    expect(
        list(stores.columns) == ["store_id", "city_id", "n_products", "mean_sales"],
        "build_store_dim ma zwrócić kolumny store_id, city_id, n_products, "
        f"mean_sales. Dostałem: {list(stores.columns)}",
    )
    expect(
        list(stores["store_id"]) == [70, 107, 293],
        "Wymiar sklepu ma mieć jeden wiersz na sklep, posortowany po store_id. "
        f"Dostałem store_id: {list(stores['store_id'])}",
    )
    expect(
        list(stores["city_id"]) == [3, 3, 11]
        and list(stores["n_products"]) == [5, 1, 2],
        "Sklep 70 leży w mieście 3 i sprzedaje 5 produktów, sklep 293 w mieście 11 "
        "i sprzedaje 2. Twoje city_id lub n_products się różnią.",
    )
    expect(
        bool(np.isclose(float(stores["mean_sales"].iloc[0]), 0.643889, atol=1e-5)),
        "mean_sales sklepu 70 to średnia sale_amount po wszystkich jego wierszach, "
        f"czyli 0.6439. Dostałem {float(stores['mean_sales'].iloc[0]):.4f}.",
    )
    moved = fact.copy()
    moved.loc[0, "city_id"] = 99
    _raises(
        lambda: dims.build_store_dim(moved),
        ValueError,
        "jeden sklep występuje w dwóch miastach",
    )

    products = dims.build_product_dim(fact)
    expect(
        list(products["product_id"]) == [4, 37, 92, 116, 129, 860],
        "Wymiar produktu ma mieć jeden wiersz na produkt, posortowany po "
        f"product_id. Dostałem: {list(products['product_id'])}",
    )
    expect(
        list(products["n_stores"]) == [2, 1, 1, 1, 1, 2],
        "n_stores to liczba różnych sklepów sprzedających produkt. Produkty 4 "
        "i 860 są w dwóch sklepach, pozostałe w jednym.",
    )
    expect(
        {
            "management_group_id",
            "first_category_id",
            "second_category_id",
            "third_category_id",
        }
        <= set(products.columns)
        and int(products["third_category_id"].iloc[1]) == 67,
        "Wymiar produktu ma zawierać cztery kolumny hierarchii. Produkt 37 ma "
        "third_category_id równe 67.",
    )
    relabelled = fact.copy()
    relabelled.loc[0, "third_category_id"] = 999
    _raises(
        lambda: dims.build_product_dim(relabelled),
        ValueError,
        "jeden produkt ma dwie różne ścieżki w hierarchii",
    )

    slim = fact[[*ROW_KEY, "sale_amount"]]
    joined = dims.attach_dim(slim, products, on="product_id")
    expect(
        len(joined) == len(slim) and joined[ROW_KEY].equals(slim[ROW_KEY]),
        "attach_dim ma zachować liczbę i kolejność wierszy tabeli faktów.",
    )
    expect(
        "n_stores" in joined.columns and "_merge" not in joined.columns,
        "attach_dim ma dołożyć kolumny wymiaru i nie zostawiać kolumn pomocniczych.",
    )
    doubled = pd.concat([products, products.iloc[[0]]], ignore_index=True)
    _raises(
        lambda: dims.attach_dim(slim, doubled, on="product_id"),
        pd.errors.MergeError,
        "klucz w wymiarze się powtarza",
    )
    _raises(
        lambda: dims.attach_dim(slim, products.iloc[1:], on="product_id"),
        ValueError,
        "w wymiarze brakuje produktu obecnego w faktach",
    )


@task("07.4", "summarise_hours: z tablic godzinowych do liczb na dzień")
def check_hourly(_target: object) -> None:
    from freshcast.data import hourly
    from freshcast.data.schema import HOURLY_COLUMNS

    frame = hourly.load_hourly(SAMPLE)
    expect(
        list(frame.columns) == HOURLY_COLUMNS and len(frame) == N_ROWS,
        f"load_hourly ma zwrócić kolumny {HOURLY_COLUMNS} i {N_ROWS} wierszy.",
    )
    expect(
        pd.api.types.is_datetime64_any_dtype(frame["dt"]) and _is_sorted(frame),
        "load_hourly ma zwrócić dt jako datę i wiersze posortowane po serii i dacie.",
    )
    expect(
        len(hourly.load_hourly(SAMPLE, cities=[11])) == 180,
        "load_hourly(cities=[11]) ma zwrócić 180 wierszy z próbki.",
    )

    matrix = hourly.to_matrix(frame["hours_sale"])
    expect(
        isinstance(matrix, np.ndarray) and matrix.shape == (N_ROWS, 24),
        "to_matrix ma zwrócić tablicę NumPy o kształcie (liczba wierszy, 24). "
        f"Dostałem {type(matrix).__name__}, kształt {getattr(matrix, 'shape', '?')}.",
    )
    ragged = pd.Series([np.zeros(24), np.zeros(23)])
    _raises(lambda: hourly.to_matrix(ragged), ValueError, "jeden wiersz ma 23 wartości")

    summary = hourly.summarise_hours(frame)
    wanted = [
        *ROW_KEY,
        "oos_hours",
        "oos_hours_total",
        "sales_in_stock",
        "sales_while_oos",
    ]
    expect(
        list(summary.columns) == wanted and len(summary) == N_ROWS,
        f"summarise_hours ma zwrócić kolumny {wanted}, po jednym wierszu na wejściowy.",
    )
    raw = pd.read_parquet(
        SAMPLE, columns=[*ROW_KEY, "stock_hour6_22_cnt", "sale_amount"]
    )
    raw = raw.assign(dt=pd.to_datetime(raw["dt"])).sort_values(ROW_KEY)
    raw = raw.reset_index(drop=True)
    expect(
        bool(
            (
                summary["oos_hours"].to_numpy() == raw["stock_hour6_22_cnt"].to_numpy()
            ).all()
        ),
        "oos_hours ma się zgadzać z kolumną stock_hour6_22_cnt z surowych danych. "
        "Sprawdź, które pozycje tablicy odpowiadają godzinom 6:00-22:00.",
    )
    expect(
        int(summary["oos_hours_total"].sum()) == 4741,
        "Suma oos_hours_total w próbce to 4741 godzin. Dostałem "
        f"{int(summary['oos_hours_total'].sum())}.",
    )
    total = summary["sales_in_stock"] + summary["sales_while_oos"]
    expect(
        bool(np.allclose(total.to_numpy(), raw["sale_amount"].to_numpy())),
        "sales_in_stock + sales_while_oos ma dawać dzienną sprzedaż sale_amount.",
    )
    expect(
        bool(np.isclose(summary["sales_while_oos"].sum(), 19.2)),
        "Sprzedaż w godzinach oznaczonych jako brak towaru wynosi w próbce 19.2. "
        f"Dostałem {summary['sales_while_oos'].sum():.2f}.",
    )


@task("07.5", "add_lag, add_rolling_mean, dow_profile: obliczenia wewnątrz serii")
def check_panel_ops(_target: object) -> None:
    from freshcast.data import panel

    tiny = _tiny_panel()
    shuffled = tiny.sample(frac=1.0, random_state=1)
    expect(
        panel.is_sorted_panel(tiny) is True
        and panel.is_sorted_panel(shuffled) is False,
        "is_sorted_panel ma zwracać True dla panelu posortowanego po serii i dacie "
        "oraz False dla tych samych wierszy w losowej kolejności.",
    )

    lagged = panel.add_lag(tiny, "sale_amount", 2)
    expect(
        "sale_amount_lag_2" in lagged.columns,
        "add_lag(df, 'sale_amount', 2) ma dodać kolumnę sale_amount_lag_2.",
    )
    wanted = [np.nan, np.nan, 1.0, 2.0, 3.0, np.nan, np.nan, 10.0, 20.0, 30.0]
    expect(
        bool(np.allclose(lagged["sale_amount_lag_2"], wanted, equal_nan=True)),
        "Lag 2 na dwóch seriach [1..5] i [10..50] ma dać [NaN, NaN, 1, 2, 3] oraz "
        "[NaN, NaN, 10, 20, 30]. Pierwsze dni drugiej serii nie mogą dostać "
        f"wartości z pierwszej. Dostałem: {lagged['sale_amount_lag_2'].tolist()}",
    )
    expect(
        "sale_amount_lag_2" not in tiny.columns,
        "add_lag zmieniło ramkę wejściową. Zwróć nową ramkę.",
    )
    _raises(
        lambda: panel.add_lag(shuffled, "sale_amount", 1),
        ValueError,
        "wiersze nie są posortowane",
    )
    _raises(lambda: panel.add_lag(tiny, "sale_amount", 0), ValueError, "lag wynosi 0")

    rolled = panel.add_rolling_mean(tiny, "sale_amount", window=2)
    expect(
        "sale_amount_mean_2_lag_1" in rolled.columns,
        "add_rolling_mean(df, 'sale_amount', window=2) ma dodać kolumnę "
        "sale_amount_mean_2_lag_1.",
    )
    wanted = [np.nan, np.nan, 1.5, 2.5, 3.5, np.nan, np.nan, 15.0, 25.0, 35.0]
    expect(
        bool(np.allclose(rolled["sale_amount_mean_2_lag_1"], wanted, equal_nan=True)),
        "Średnia z okna 2 dni kończącego się wczoraj ma dać [NaN, NaN, 1.5, 2.5, "
        "3.5] i [NaN, NaN, 15, 25, 35]. Jeśli trzeci wynik to 2.5, okno obejmuje "
        f"bieżący dzień. Dostałem: {rolled['sale_amount_mean_2_lag_1'].tolist()}",
    )
    further = panel.add_rolling_mean(tiny, "sale_amount", window=2, lag=2)
    wanted = [np.nan, np.nan, np.nan, 1.5, 2.5, np.nan, np.nan, np.nan, 15.0, 25.0]
    expect(
        bool(np.allclose(further["sale_amount_mean_2_lag_2"], wanted, equal_nan=True)),
        "Z lag=2 okno ma kończyć się przedwczoraj: [NaN, NaN, NaN, 1.5, 2.5].",
    )
    _raises(
        lambda: panel.add_rolling_mean(shuffled, "sale_amount", window=2),
        ValueError,
        "wiersze nie są posortowane",
    )

    days = pd.date_range("2024-04-01", periods=14)  # starts on a Monday
    weekend = days.dayofweek >= 5
    two_shapes = pd.DataFrame(
        {
            "store_id": [1] * 14 + [2] * 14,
            "product_id": [7] * 28,
            "dt": [*days, *days],
            "sale_amount": [*np.where(weekend, 2.0, 1.0), *([10.0] * 14)],
        }
    )
    profile = panel.dow_profile(two_shapes)
    expect(
        isinstance(profile, pd.Series) and list(profile.index) == list(range(7)),
        "dow_profile ma zwrócić Series z indeksem 0..6 (poniedziałek..niedziela).",
    )
    wanted = [8 / 9] * 5 + [23 / 18] * 2
    expect(
        bool(np.allclose(profile.to_numpy(), wanted)),
        "Każdą serię trzeba najpierw podzielić przez jej własną średnią. Dla "
        "serii z podwójną sprzedażą w weekend i serii płaskiej, dziesięć razy "
        "większej, profil to 0.889 w dni robocze i 1.278 w weekend. Dostałem: "
        f"{profile.round(3).tolist()}",
    )
    dead = two_shapes.assign(sale_amount=0.0)
    _raises(lambda: panel.dow_profile(dead), ValueError, "seria ma średnią sprzedaż 0")


@task("07.6", "prepare_daily i zapis: zbiór przetworzony zgodny z kontraktem")
def check_prepare(_target: object) -> None:
    from freshcast.data import prepare
    from freshcast.data.schema import PROCESSED_COLUMNS

    daily = prepare.prepare_daily(SAMPLE)
    expect(
        list(daily.columns) == PROCESSED_COLUMNS,
        "prepare_daily ma zwrócić dokładnie PROCESSED_COLUMNS, w tej kolejności. "
        f"Dostałem: {list(daily.columns)}",
    )
    expect(
        len(daily) == N_ROWS and _is_sorted(daily),
        f"Oczekiwano {N_ROWS} wierszy posortowanych po serii i dacie.",
    )
    expect(
        int(daily["discount"].isna().sum()) == 3
        and int(daily["oos_hours"].sum()) == 2789,
        "Zbiór przetworzony ma mieć wyczyszczony rabat (3 wartości NaN w próbce) "
        "i oos_hours policzone z tablic godzinowych (suma 2789).",
    )
    expect(
        len(prepare.prepare_daily(SAMPLE, cities=[11])) == 180,
        "prepare_daily(cities=[11]) ma zwrócić 180 wierszy z próbki.",
    )

    with tempfile.TemporaryDirectory() as scratch:
        directory = Path(scratch) / "processed"
        written = prepare.save_processed(daily, directory)
        expect(
            isinstance(written, Path) and written.is_file(),
            "save_processed ma utworzyć katalog, zapisać plik i zwrócić jego ścieżkę.",
        )
        restored = prepare.load_processed(directory)
        try:
            pd.testing.assert_frame_equal(restored, daily)
        except AssertionError as error:
            raise CheckFailed(
                "Zbiór po zapisie i odczycie różni się od oryginału: "
                f"{str(error).splitlines()[0]}"
            ) from error

        _raises(
            lambda: prepare.load_processed(Path(scratch) / "missing"),
            FileNotFoundError,
            "katalog nie zawiera jeszcze zbioru",
        )
        _raises(
            lambda: prepare.save_processed(daily.drop(columns="oos_hours"), directory),
            ValueError,
            "ramka nie ma kolumny z kontraktu",
        )
        daily.drop(columns="oos_hours").to_parquet(written, index=False)
        _raises(
            lambda: prepare.load_processed(directory),
            ValueError,
            "plik na dysku ma inne kolumny niż kontrakt",
        )
