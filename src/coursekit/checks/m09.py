"""Checks for module 09: feature engineering."""

from collections.abc import Callable

import numpy as np
import pandas as pd

from coursekit.checking import CheckFailed, expect, task


def _raises(call: Callable[[], object], error: type[Exception], when: str) -> None:
    try:
        call()
    except error:
        return
    except NotImplementedError:
        raise
    except Exception as other:  # noqa: BLE001 - the wrong exception type is the finding
        raise CheckFailed(
            f"Gdy {when}, oczekiwano {error.__name__}, a poleciał "
            f"{type(other).__name__}: {other}"
        ) from other
    raise CheckFailed(f"Gdy {when}, kod powinien zgłosić {error.__name__}.")


def _dates(*days: str) -> pd.DataFrame:
    return pd.DataFrame({"dt": pd.to_datetime(list(days))})


def _tiny_panel(days: int = 10) -> pd.DataFrame:
    dates = pd.date_range("2024-04-01", periods=days)
    return pd.DataFrame(
        {
            "store_id": [1] * days + [2] * days,
            "product_id": [7] * (2 * days),
            "dt": [*dates, *dates],
            "sale_amount": [
                *np.arange(1.0, days + 1),
                *np.arange(10.0, 10.0 * days + 1, 10.0),
            ],
        }
    )


def _hourly(rows: list[tuple[dict[int, float], list[int]]]) -> pd.DataFrame:
    """Build an hourly frame from (sales by hour, out-of-stock hours) pairs."""
    sales, status = [], []
    for sold, missing in rows:
        day = np.zeros(24)
        for hour, amount in sold.items():
            day[hour] = amount
        flags = np.zeros(24, dtype="int64")
        flags[missing] = 1
        sales.append(day)
        status.append(flags)
    return pd.DataFrame({"hours_sale": sales, "hours_stock_status": status})


@task("09.1", "cechy kalendarzowe: dzień tygodnia, kodowanie cykliczne, święta")
def check_calendar(_target: object) -> None:
    from freshcast.features import calendar

    week = pd.DataFrame({"dt": pd.date_range("2024-04-01", periods=7)})
    got = calendar.day_of_week(week).tolist()
    expect(
        got == [0, 1, 2, 3, 4, 5, 6],
        f"2024-04-01 to poniedziałek, więc kolejne dni to 0..6. Dostałem {got}.",
    )

    sine, cosine = calendar.cyclical(pd.Series([0, 7, 1, 6]), 7)
    expect(
        bool(np.isclose(sine.iloc[0], 0.0)) and bool(np.isclose(cosine.iloc[0], 1.0)),
        "Pozycja 0 cyklu leży w punkcie (sin, cos) = (0, 1).",
    )
    expect(
        bool(np.isclose(sine.iloc[0], sine.iloc[1]))
        and bool(np.isclose(cosine.iloc[0], cosine.iloc[1])),
        "Pozycje 0 i 7 w cyklu o długości 7 to ten sam punkt na okręgu.",
    )
    expect(
        bool(np.isclose(cosine.iloc[2], cosine.iloc[3]))
        and bool(np.isclose(sine.iloc[2], -sine.iloc[3])),
        "Dni 1 i 6 leżą symetrycznie po obu stronach dnia 0: ten sam cosinus, "
        "sinusy przeciwnego znaku.",
    )

    days = calendar.public_holidays(
        pd.Timestamp("2024-03-28"), pd.Timestamp("2024-06-25")
    )
    wanted = [
        "2024-04-04",
        "2024-04-05",
        "2024-05-01",
        "2024-05-02",
        "2024-05-03",
        "2024-06-10",
    ]
    expect(
        [str(day.date()) for day in days] == wanted,
        f"Między 2024-03-28 a 2024-06-25 pakiet holidays zna dla Chin dni: {wanted}. "
        f"Dostałem: {[str(day.date()) for day in days]}.",
    )

    frame = _dates("2024-04-03", "2024-04-04", "2024-04-05", "2024-04-06")
    got = calendar.is_public_holiday(frame).tolist()
    expect(
        got == [0, 1, 1, 0],
        f"Dla dni 3-6 kwietnia 2024 is_public_holiday to [0, 1, 1, 0]. Dostałem {got}.",
    )

    frame = _dates(
        "2024-04-01",
        "2024-04-02",
        "2024-04-04",
        "2024-04-20",
        "2024-04-10",
        "2024-06-20",
    )
    got = calendar.days_to_next_holiday(frame).tolist()
    expect(
        got == [3, 2, 0, 11, 14, 14],
        "Do święta 4 kwietnia z 1 kwietnia są 3 dni, w samo święto 0, z 20 "
        "kwietnia do 1 maja 11. Odległości powyżej 14 i brak kolejnego święta "
        f"dają 14. Oczekiwano [3, 2, 0, 11, 14, 14], dostałem {got}.",
    )
    shuffled = frame.sample(frac=1.0, random_state=1)
    expect(
        calendar.days_to_next_holiday(shuffled).index.equals(shuffled.index),
        "Wynik ma mieć ten sam indeks co ramka wejściowa, także gdy wiersze nie "
        "są posortowane.",
    )


@task("09.2", "lagi i okna świadome horyzontu prognozy")
def check_lags(_target: object) -> None:
    from freshcast.features import lags

    try:
        lags.check_horizon(7, 7)
    except ValueError as error:
        raise CheckFailed(
            "Lag równy horyzontowi jest dozwolony: dla prognozy na 7 dni wartość "
            "sprzed 7 dni jest już znana."
        ) from error
    _raises(
        lambda: lags.check_horizon(6, 7), ValueError, "lag jest krótszy niż horyzont"
    )
    _raises(lambda: lags.check_horizon(7, 0), ValueError, "horyzont wynosi 0")

    panel = _tiny_panel()
    feature = lags.lag_feature(panel, "sale_amount", 3, horizon=2)
    expect(
        isinstance(feature, pd.Series) and feature.name == "sale_amount_lag_3",
        "lag_feature ma zwrócić Series o nazwie sale_amount_lag_3.",
    )
    expect(
        bool(
            np.allclose(
                feature.iloc[:5], [np.nan, np.nan, np.nan, 1.0, 2.0], equal_nan=True
            )
        )
        and bool(
            np.allclose(
                feature.iloc[10:15],
                [np.nan, np.nan, np.nan, 10.0, 20.0],
                equal_nan=True,
            )
        ),
        "Lag 3 ma dać w każdej serii trzy NaN, a potem wartości sprzed trzech dni.",
    )
    _raises(
        lambda: lags.lag_feature(panel, "sale_amount", 1, horizon=2),
        ValueError,
        "lag 1 przy horyzoncie 2",
    )

    feature = lags.window_mean_feature(panel, "sale_amount", 2, horizon=2)
    expect(
        feature.name == "sale_amount_mean_2_lag_2",
        "window_mean_feature(df, 'sale_amount', 2, horizon=2) ma zwrócić Series "
        f"o nazwie sale_amount_mean_2_lag_2. Dostałem {feature.name!r}.",
    )
    expect(
        bool(
            np.allclose(
                feature.iloc[:5], [np.nan, np.nan, np.nan, 1.5, 2.5], equal_nan=True
            )
        ),
        "Okno 2 dni kończące się 2 dni przed wierszem: dla serii [1, 2, 3, 4, 5] "
        "czwarty dzień dostaje średnią z dni 1 i 2, czyli 1.5. Dostałem "
        f"{feature.iloc[:5].tolist()}.",
    )


@task("09.3", "popyt ocenzurowany: profil godzinowy, pokrycie, korekta")
def check_demand(_target: object) -> None:
    from freshcast.features import demand

    hourly = _hourly(
        [
            ({8: 1.0, 18: 3.0}, []),
            ({8: 1.0, 18: 1.0}, []),
            ({8: 5.0}, [18, 19]),
            ({}, []),
        ]
    )
    profile = demand.hourly_profile(hourly)
    expect(
        isinstance(profile, np.ndarray) and profile.shape == (24,),
        "hourly_profile ma zwrócić tablicę 24 udziałów.",
    )
    expect(
        bool(np.isclose(profile.sum(), 1.0)),
        f"Udziały mają sumować się do 1. Sumują się do {profile.sum():.3f}.",
    )
    expect(
        bool(np.isclose(profile[8], 0.375)) and bool(np.isclose(profile[18], 0.625)),
        "Profil to średnia udziałów z dni bez braków i ze sprzedażą. Dwa takie "
        "dni mają udziały godziny 8 równe 0.25 i 0.5, więc profil[8] = 0.375. "
        f"Dostałem {profile[8]:.3f}. Dzień z brakiem towaru i dzień bez "
        "sprzedaży nie biorą udziału.",
    )
    _raises(
        lambda: demand.hourly_profile(_hourly([({8: 1.0}, [3])])),
        ValueError,
        "żaden dzień nie nadaje się do zbudowania profilu",
    )

    covered = demand.coverage(hourly, profile)
    expect(
        bool(np.allclose(covered, [1.0, 1.0, 0.375, 1.0])),
        "Pokrycie to suma udziałów profilu w godzinach z towarem. Dzień bez "
        "towaru w godzinie 18 ma pokrycie 0.375, dni bez braków 1.0. Dostałem "
        f"{np.round(covered, 3).tolist()}.",
    )

    estimate = demand.corrected_demand(
        np.array([3.0, 3.0, 0.0]), np.array([0.375, 1.0, 0.0])
    )
    expect(
        bool(np.allclose(estimate, [8.0, 3.0, np.nan], equal_nan=True)),
        "Sprzedaż 3 przy pokryciu 0.375 daje popyt 8. Przy pokryciu 1.0 popyt "
        "równa się sprzedaży. Pokrycie 0 to popyt nieznany (NaN). Dostałem "
        f"{estimate.tolist()}.",
    )
    estimate = demand.corrected_demand(
        np.array([3.0, 3.0]), np.array([0.375, 1.0]), min_coverage=0.5
    )
    expect(
        bool(np.isnan(estimate[0])) and estimate[1] == 3.0,
        "Poniżej min_coverage wynik ma być NaN.",
    )
    _raises(
        lambda: demand.corrected_demand(
            np.array([1.0]), np.array([1.0]), min_coverage=0.0
        ),
        ValueError,
        "min_coverage wynosi 0",
    )


@task("09.4", "TargetEncoder: średnia celu w grupie, dopasowana tylko na train")
def check_encoding(_target: object) -> None:
    from freshcast.features import encoding

    train = pd.DataFrame(
        {"g": ["a", "a", "a", "b"], "h": [1, 1, 2, 1]}, index=[10, 11, 12, 13]
    )
    target = pd.Series([1.0, 2.0, 6.0, 10.0], index=train.index)

    encoder = encoding.TargetEncoder(["g"])
    _raises(
        lambda: encoder.transform(train),
        RuntimeError,
        "transform jest wołany przed fit",
    )
    expect(encoder.fit(train, target) is encoder, "fit ma zwracać self.")
    encoded = encoder.transform(train)
    expect(
        encoded.name == "g_target_mean" and encoded.index.equals(train.index),
        "transform ma zwrócić Series o nazwie g_target_mean i indeksie ramki X.",
    )
    expect(
        encoded.tolist() == [3.0, 3.0, 3.0, 10.0],
        f"Średnia celu w grupie a to 3, w grupie b to 10. Dostałem {encoded.tolist()}.",
    )

    later = pd.DataFrame({"g": ["b", "a", "zzz"], "h": [1, 1, 1]})
    got = encoder.transform(later).tolist()
    expect(
        got == [10.0, 3.0, 4.75],
        "Nowe wiersze dostają średnie wyuczone na danych z fit. Grupa, której "
        "fit nie widział, dostaje średnią całego zbioru treningowego (4.75). "
        f"Dostałem {got}.",
    )

    smooth = encoding.TargetEncoder(["g"], smoothing=1.0).fit(train, target)
    got = smooth.transform(later).tolist()
    expect(
        bool(np.allclose(got, [7.375, 3.4375, 4.75])),
        "Z smoothing=1 grupa b (1 wiersz, średnia 10) to (10 + 4.75) / 2 = 7.375, "
        "a grupa a (3 wiersze, suma 9) to (9 + 4.75) / 4 = 3.4375. Dostałem "
        f"{np.round(got, 4).tolist()}.",
    )

    pair = encoding.TargetEncoder(["g", "h"]).fit(train, target)
    encoded = pair.transform(train)
    expect(
        encoded.name == "g_h_target_mean" and encoded.tolist() == [1.5, 1.5, 6.0, 10.0],
        "Dla kolumn ['g', 'h'] grupą jest para wartości. Oczekiwano nazwy "
        f"g_h_target_mean i wartości [1.5, 1.5, 6, 10]. Dostałem {encoded.name!r}, "
        f"{encoded.tolist()}.",
    )
    expect(list(train.columns) == ["g", "h"], "fit albo transform zmieniło ramkę X.")
    _raises(lambda: encoding.TargetEncoder([]), ValueError, "lista kolumn jest pusta")
    _raises(
        lambda: encoding.TargetEncoder(["g"], smoothing=-1.0),
        ValueError,
        "smoothing jest ujemny",
    )


@task("09.5", "rejestr cech: kolejność z grafu zależności, build_features")
def check_build(_target: object) -> None:
    from freshcast.features import build

    registry = build.Registry()

    @registry.register("double", requires=["x"])
    def _double(df: pd.DataFrame) -> pd.Series:
        return df["x"] * 2

    @registry.register("plus_one", requires=["double"])
    def _plus_one(df: pd.DataFrame) -> pd.Series:
        return df["double"] + 1

    @registry.register("total", requires=["double", "plus_one"])
    def _total(df: pd.DataFrame) -> pd.Series:
        return df["double"] + df["plus_one"]

    @registry.register("orphan", requires=["missing_column"])
    def _orphan(df: pd.DataFrame) -> pd.Series:
        return df["missing_column"]

    known = registry.features
    order = build.resolve_order(["total"], known, available=["x"])
    expect(
        order == ["double", "plus_one", "total"],
        "Dla cechy total, która wymaga double i plus_one (a plus_one wymaga "
        f"double), kolejność to ['double', 'plus_one', 'total']. Dostałem {order}.",
    )
    order = build.resolve_order(
        ["plus_one", "double", "plus_one"], known, available=["x"]
    )
    expect(
        order == ["double", "plus_one"],
        "Każda cecha ma wystąpić raz, po swoich zależnościach, niezależnie od "
        f"kolejności i powtórzeń na liście. Dostałem {order}.",
    )
    expect(
        build.resolve_order(["x"], known, available=["x"]) == [],
        "Kolumna, która już jest w ramce, nie trafia na listę do policzenia.",
    )
    _raises(
        lambda: build.resolve_order(["orphan"], known, available=["x"]),
        ValueError,
        "cecha wymaga kolumny, której nie ma ani w ramce, ani w rejestrze",
    )
    _raises(
        lambda: build.resolve_order(["nope"], known, available=["x"]),
        ValueError,
        "poproszono o nieznaną cechę",
    )

    loop = build.Registry()
    loop.register("first", requires=["second"])(lambda df: df["second"])
    loop.register("second", requires=["first"])(lambda df: df["first"])
    _raises(
        lambda: build.resolve_order(["first"], loop.features, available=[]),
        ValueError,
        "dwie cechy wymagają siebie nawzajem",
    )

    frame = pd.DataFrame({"x": [1.0, 2.0]}, index=[5, 6])
    built = build.build_features(frame, ["total"], known)
    expect(
        list(built.columns) == ["x", "double", "plus_one", "total"]
        and built["total"].tolist() == [5.0, 9.0],
        "build_features ma dodać cechy w kolejności z resolve_order. Dla x = [1, 2] "
        f"total to [5, 9]. Dostałem kolumny {list(built.columns)}.",
    )
    expect(list(frame.columns) == ["x"], "build_features zmieniło ramkę wejściową.")

    broken = build.Registry()
    broken.register("shifted", requires=["x"])(
        lambda df: df["x"].reset_index(drop=True)
    )
    _raises(
        lambda: build.build_features(frame, ["shifted"], broken.features),
        ValueError,
        "cecha zwraca Series o innym indeksie niż ramka",
    )
