"""Checks for module 10: tree splits, LightGBM, direct and recursive forecasts."""

from collections.abc import Callable
from typing import Any, cast

import numpy as np
import pandas as pd

from coursekit.checking import CheckFailed, expect, task

KEY = ["store_id", "product_id"]


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


def _shops(rows: int = 600, seed: int = 10) -> tuple[pd.DataFrame, pd.Series]:
    """Synthetic data: a numeric effect, a shop effect and a useless column."""
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(
        {
            "a": rng.uniform(0, 10, rows),
            "junk": rng.normal(size=rows),
            "shop": rng.choice(["north", "south", "west"], rows),
        }
    )
    effect = frame["shop"].map({"north": 0.0, "south": 20.0, "west": 40.0})
    target = 100 + 3 * frame["a"] + effect + rng.normal(scale=0.5, size=rows)
    return frame, target


@task("10.1", "sum_of_squares i best_split: jak drzewo wybiera podział")
def check_tree(_target: object) -> None:
    from freshcast.models import tree

    got = tree.sum_of_squares(np.array([1.0, 2.0, 3.0]))
    expect(
        isinstance(got, float) and bool(np.isclose(got, 2.0)),
        "Dla [1, 2, 3] średnia to 2, a suma kwadratów odchyleń to 2.0. "
        f"Dostałem {got!r}.",
    )
    expect(
        tree.sum_of_squares(np.array([])) == 0.0,
        "Pusta grupa ma błąd 0, a nie NaN.",
    )

    feature = np.array([11.0, 1.0, 12.0, 2.0, 3.0, 10.0])
    target = np.array([5.0, 1.0, 5.0, 1.0, 1.0, 5.0])
    threshold, gain = tree.best_split(feature, target)
    expect(
        bool(np.isclose(threshold, 6.5)) and bool(np.isclose(gain, 24.0)),
        "Cecha [1, 2, 3, 10, 11, 12] (podana w losowej kolejności) z celem "
        "[1, 1, 1, 5, 5, 5] dzieli się idealnie w punkcie 6.5 z zyskiem 24. "
        f"Dostałem próg {threshold} i zysk {gain:.3f}.",
    )
    threshold, gain = tree.best_split(
        np.array([1.0, 1.0, 1.0, 2.0]), np.array([0.0, 5.0, 1.0, 3.0])
    )
    expect(
        bool(np.isclose(threshold, 1.5)),
        "Progi leżą tylko między różnymi wartościami cechy. Dla cechy "
        f"[1, 1, 1, 2] jedyny możliwy próg to 1.5. Dostałem {threshold}.",
    )
    threshold, _ = tree.best_split(
        np.array([1.0, 2.0, 3.0, 4.0]), np.array([0.0, 1.0, 0.0, 1.0])
    )
    expect(
        bool(np.isclose(threshold, 1.5)),
        "Gdy kilka progów daje ten sam zysk, zwracasz najniższy. Dla celu "
        f"[0, 1, 0, 1] progi 1.5 i 3.5 są równie dobre. Dostałem {threshold}.",
    )
    _raises(
        lambda: tree.best_split(np.array([3.0, 3.0]), np.array([1.0, 2.0])),
        ValueError,
        "cecha ma jedną wartość",
    )


@task(
    "10.2", "LightGBMForecaster: kategorie, early stopping, ograniczenia monotoniczne"
)
def check_gbm(_target: object) -> None:
    from freshcast.models import gbm

    frame, target = _shops()
    features = ["a", "junk", "shop"]
    model = gbm.LightGBMForecaster(features, categorical=["shop"], rounds=200)
    _raises(lambda: model.predict(frame), RuntimeError, "predict jest wołany przed fit")
    expect(model.fit(frame, target) is model, "fit ma zwracać self.")
    forecast = model.predict(frame)
    error = float(np.mean(np.abs(forecast - target.to_numpy())))
    expect(
        isinstance(forecast, np.ndarray) and error < 2.0,
        "Na prostych danych syntetycznych (efekt liniowy plus efekt sklepu) "
        f"średni błąd na zbiorze treningowym powinien być poniżej 2. Jest {error:.2f}.",
    )

    south = frame[frame["shop"] == "south"]
    together = pd.Series(forecast, index=frame.index).loc[south.index].to_numpy()
    alone = model.predict(south)
    expect(
        bool(np.allclose(alone, together)),
        "Prognoza dla wierszy jednego sklepu ma być taka sama, gdy podasz je "
        "osobno i gdy podasz je razem z innymi. Jeśli kody kategorii powstają "
        "od nowa przy każdym predict, ten sam sklep dostaje inny kod niż w "
        "treningu.",
    )
    stranger = frame.head(3).assign(shop="east")
    try:
        model.predict(stranger)
    except Exception as error_:  # noqa: BLE001 - any crash here is the finding
        raise CheckFailed(
            "Kategoria nieznana z treningu nie powinna wywracać predict. Ma "
            f"stać się brakiem. Poleciał {type(error_).__name__}."
        ) from error_

    below = gbm.LightGBMForecaster(["a"], rounds=50).fit(frame, target - 200)
    expect(
        float(below.predict(frame).min()) == 0.0,
        "Prognozy ujemne mają być podniesione do zera.",
    )

    rng = np.random.default_rng(3)
    noisy = pd.DataFrame({"a": rng.uniform(0, 10, 800)})
    noisy_target = pd.Series(noisy["a"] + rng.normal(scale=3.0, size=800))
    stopper = gbm.LightGBMForecaster(["a"], params={"learning_rate": 0.3}, rounds=300)
    stopper.fit(
        noisy.iloc[:600],
        noisy_target.iloc[:600],
        valid=(noisy.iloc[600:], noisy_target.iloc[600:]),
        patience=10,
    )
    expect(
        stopper.rounds_used < 300,
        "Z podanym zbiorem walidacyjnym trening ma się zatrzymać, gdy błąd na "
        f"nim przestaje maleć. Model użył {stopper.rounds_used} z 300 rund.",
    )

    wave = pd.DataFrame({"a": np.linspace(0, 10, 500)})
    wave_target = pd.Series(10 + 3 * np.sin(wave["a"]))
    rising = gbm.LightGBMForecaster(["a"], monotone={"a": 1}, rounds=100)
    curve = rising.fit(wave, wave_target).predict(wave)
    expect(
        bool((np.diff(curve) >= -1e-9).all()),
        "Z monotone={'a': 1} prognoza nie może maleć, gdy rośnie a, nawet na "
        "danych w kształcie fali.",
    )
    _raises(
        lambda: gbm.LightGBMForecaster(["a"], categorical=["shop"]),
        ValueError,
        "kolumna kategoryczna nie jest wśród cech",
    )
    _raises(
        lambda: gbm.LightGBMForecaster(["a"], monotone={"b": 1}),
        ValueError,
        "ograniczenie monotoniczne dotyczy kolumny spoza cech",
    )


@task("10.3", "importance i contributions: co model wykorzystał")
def check_explain(_target: object) -> None:
    from freshcast.models import gbm

    frame, target = _shops()
    features = ["junk", "a", "shop"]
    model = gbm.LightGBMForecaster(features, categorical=["shop"], rounds=100)
    model.fit(frame, target)

    shares = model.importance()
    expect(
        isinstance(shares, pd.Series) and set(shares.index) == set(features),
        "importance ma zwrócić Series z indeksem równym nazwom cech.",
    )
    expect(
        bool(np.isclose(shares.sum(), 1.0)) and bool(shares.is_monotonic_decreasing),
        "Udziały zysku mają sumować się do 1 i być posortowane malejąco.",
    )
    expect(
        shares.index[-1] == "junk",
        "Kolumna junk to czysty szum i powinna mieć najmniejszy udział. Na końcu "
        f"jest {shares.index[-1]!r}.",
    )

    sample = frame.iloc[:20]
    parts = model.contributions(sample)
    expect(
        list(parts.columns) == [*features, "baseline"]
        and parts.index.equals(sample.index),
        "contributions ma zwrócić ramkę z kolumną na cechę i ostatnią kolumną "
        "baseline, z indeksem ramki X.",
    )
    expect(
        bool(np.allclose(parts.sum(axis=1).to_numpy(), model.predict(sample))),
        "Wkłady cech i baseline w każdym wierszu mają sumować się do prognozy.",
    )


class _FromColumn:
    """Stand-in model: the forecast is a function of one feature column."""

    def __init__(self, column: str, scale: float, shift: float) -> None:
        self.column, self.scale, self.shift = column, scale, shift

    def predict(self, X: pd.DataFrame) -> Any:
        return (X[self.column] * self.scale + self.shift).to_numpy()


def _history_and_future() -> tuple[pd.DataFrame, pd.DataFrame]:
    past = pd.date_range("2024-04-01", periods=10)
    ahead = pd.date_range("2024-04-11", periods=3)
    history = pd.DataFrame(
        {
            "store_id": [1] * 10 + [2] * 10,
            "product_id": [7] * 20,
            "dt": [*past, *past],
            "sale_amount": [*np.arange(1.0, 11.0), *np.arange(10.0, 101.0, 10.0)],
            "oos_hours": 0.0,
            "discount": 1.0,
        }
    )
    future = pd.DataFrame(
        {
            "store_id": [1] * 3 + [2] * 3,
            "product_id": [7] * 6,
            "dt": [*ahead, *ahead],
            "sale_amount": 999.0,
            "oos_hours": 5.0,
            "discount": 0.8,
        },
        index=[50, 51, 52, 60, 61, 62],
    )
    return history, future.sample(frac=1.0, random_state=2)


def _lag_builder(lag: int) -> Callable[[pd.DataFrame], pd.DataFrame]:
    def build(panel: pd.DataFrame) -> pd.DataFrame:
        lagged = panel.groupby(KEY, sort=False)["sale_amount"].shift(lag)
        return panel.assign(past=lagged)

    return build


@task("10.4", "stack_future, forecast_direct, forecast_recursive")
def check_forecast(_target: object) -> None:
    from freshcast import forecast

    history, future = _history_and_future()
    panel = forecast.stack_future(history, future)
    expect(
        len(panel) == 26 and panel.index.equals(pd.RangeIndex(26)),
        "stack_future ma zwrócić wszystkie wiersze historii i przyszłości "
        "z nowym indeksem 0..n-1.",
    )
    expect(
        panel[[*KEY, "dt"]].equals(panel[[*KEY, "dt"]].sort_values([*KEY, "dt"])),
        "Wynik stack_future ma być posortowany po serii i dacie.",
    )
    ahead = panel[panel["dt"] > pd.Timestamp("2024-04-10")]
    expect(
        bool(ahead["sale_amount"].isna().all())
        and bool(ahead["oos_hours"].isna().all()),
        "Na wierszach przyszłości cel i kolumny o brakach towaru mają być NaN, "
        "nawet jeśli wywołujący podał w nich wartości. W teście podano "
        "sale_amount = 999 i oos_hours = 5.",
    )
    expect(
        bool((ahead["discount"] == 0.8).all()),
        "Kolumny znane z góry (tu discount) mają zostać nietknięte.",
    )
    _raises(
        lambda: forecast.stack_future(history, history.tail(2)),
        ValueError,
        "wiersz przyszłości nie jest późniejszy niż koniec historii",
    )

    direct = forecast.forecast_direct(
        cast(Any, _FromColumn("past", 2.0, 0.0)), history, future, _lag_builder(3)
    )
    expect(
        isinstance(direct, pd.Series) and direct.index.equals(future.index),
        "forecast_direct ma zwrócić Series z indeksem ramki future, w jej "
        "kolejności wierszy.",
    )
    got = direct.sort_index().tolist()
    expect(
        got == [16.0, 18.0, 20.0, 160.0, 180.0, 200.0],
        "Model testowy zwraca dwukrotność wartości sprzed 3 dni. Seria 1 kończy "
        "się na 8, 9, 10, więc prognozy to 16, 18, 20, a dla serii 2 to 160, "
        f"180, 200. Dostałem {got}.",
    )

    recursive = forecast.forecast_recursive(
        cast(Any, _FromColumn("past", 1.0, 1.0)), history, future, _lag_builder(1)
    )
    expect(
        recursive.index.equals(future.index),
        "forecast_recursive ma zwrócić Series z indeksem ramki future.",
    )
    got = recursive.sort_index().tolist()
    expect(
        got == [11.0, 12.0, 13.0, 101.0, 102.0, 103.0],
        "Model testowy zwraca wczorajszą wartość plus 1. Drugi dzień prognozy "
        "musi więc korzystać z prognozy pierwszego: 11, 12, 13 dla serii 1 oraz "
        f"101, 102, 103 dla serii 2. Dostałem {got}.",
    )
