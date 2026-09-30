"""Checks for module 08: time splits, gradient descent, panel forecasters."""

from collections.abc import Callable, Sequence
from typing import Any, Self, cast

import numpy as np
import pandas as pd

from coursekit.checking import CheckFailed, expect, task

ROW_KEY = ["store_id", "product_id", "dt"]


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


def _panel(days: int = 10) -> pd.DataFrame:
    """Two series over ``days`` consecutive days, rows in random order."""
    dates = pd.date_range("2024-04-01", periods=days)
    frame = pd.DataFrame(
        {
            "store_id": [1] * days + [2] * days,
            "product_id": [7] * (2 * days),
            "dt": [*dates, *dates],
            "sale_amount": [*np.arange(1.0, days + 1), *np.arange(10.0, 10.0 + days)],
        }
    )
    return frame.sample(frac=1.0, random_state=3)


class _LastValue:
    """Stand-in local forecaster, so this check does not depend on module 04."""

    def fit(self, history: Sequence[float]) -> Self:
        self.history = list(history)
        return self

    def predict(self, horizon: int) -> list[float]:
        return [self.history[-1] + step for step in range(1, horizon + 1)]


@task("08.1", "last_days_start i split_by_date: podział po czasie")
def check_split(_target: object) -> None:
    from freshcast import split

    frame = _panel()
    start = split.last_days_start(frame, 3)
    expect(
        start == pd.Timestamp("2024-04-08"),
        "Dla danych z dni 2024-04-01..2024-04-10 ostatnie 3 dni zaczynają się "
        f"2024-04-08. last_days_start zwróciło {start}.",
    )
    _raises(lambda: split.last_days_start(frame, 0), ValueError, "days wynosi 0")
    _raises(
        lambda: split.last_days_start(frame, 10),
        ValueError,
        "days obejmuje cały zakres danych (na trening nic nie zostaje)",
    )

    before, after = split.split_by_date(frame, pd.Timestamp("2024-04-08"))
    expect(
        len(before) == 14 and len(after) == 6,
        "Przy podziale w dniu 2024-04-08 dwie serie po 10 dni dają 14 wierszy "
        f"przed i 6 od tej daty. Dostałem {len(before)} i {len(after)}.",
    )
    expect(
        bool((before["dt"] < pd.Timestamp("2024-04-08")).all())
        and bool((after["dt"] >= pd.Timestamp("2024-04-08")).all()),
        "Pierwsza część ma zawierać tylko daty wcześniejsze niż cutoff, druga "
        "cutoff i późniejsze.",
    )
    expect(
        set(before.index) | set(after.index) == set(frame.index)
        and before.loc[before.index[0]].equals(frame.loc[before.index[0]]),
        "Obie części mają zachować indeks ramki wejściowej (bez reset_index).",
    )
    _raises(
        lambda: split.split_by_date(frame, pd.Timestamp("2024-03-01")),
        ValueError,
        "cutoff leży przed wszystkimi danymi",
    )
    _raises(
        lambda: split.split_by_date(frame, pd.Timestamp("2025-01-01")),
        ValueError,
        "cutoff leży po wszystkich danych",
    )


@task("08.2", "PerSeriesForecaster: prognoza lokalna na każdej serii panelu")
def check_per_series(_target: object) -> None:
    from freshcast.models import panel

    frame = _panel()
    cutoff = pd.Timestamp("2024-04-08")
    train, future = frame[frame["dt"] < cutoff], frame[frame["dt"] >= cutoff]

    model = panel.PerSeriesForecaster(cast(Any, _LastValue))
    expect(
        model.fit(train[ROW_KEY], train["sale_amount"]) is model,
        "fit ma zwracać self.",
    )
    forecast = model.predict(future[ROW_KEY])
    expect(
        isinstance(forecast, np.ndarray) and forecast.shape == (len(future),),
        "predict ma zwrócić tablicę NumPy z jedną wartością na wiersz X.",
    )
    result = future.assign(forecast=forecast).sort_values(ROW_KEY)
    got = result["forecast"].tolist()
    expect(
        got == [8.0, 9.0, 10.0, 17.0, 18.0, 19.0],
        "Testowy model lokalny zwraca ostatnią wartość historii plus numer "
        "kroku. Seria 1 kończy historię na 7, seria 2 na 16, więc po "
        "posortowaniu po serii i dacie prognozy to [8, 9, 10, 17, 18, 19]. "
        f"Dostałem {got}. Wiersze X i historii przychodzą w losowej kolejności.",
    )
    unknown = future[ROW_KEY].assign(store_id=99)
    _raises(lambda: model.predict(unknown), ValueError, "w X jest seria nieznana z fit")


@task("08.3", "regresja liniowa od zera: predykcja, strata, gradient, uczenie")
def check_gradient(_target: object) -> None:
    from freshcast.models import gradient

    rng = np.random.default_rng(8)
    features = rng.normal(size=(200, 2))
    true_weights, true_intercept = np.array([2.0, -1.0]), 0.5
    target = features @ true_weights + true_intercept

    predicted = gradient.predict_linear(features, true_weights, true_intercept)
    expect(
        predicted.shape == (200,) and bool(np.allclose(predicted, target)),
        "predict_linear ma zwrócić X @ weights + intercept, jedną liczbę na wiersz.",
    )
    got = gradient.mse(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 6.0]))
    expect(
        isinstance(got, float) and bool(np.isclose(got, 3.0)),
        f"mse dla błędów [0, 0, 3] to 9 / 3 = 3.0. Dostałem {got!r}.",
    )

    weights, intercept = np.array([0.3, 0.1]), -0.2
    weight_gradient, intercept_gradient = gradient.mse_gradient(
        features, target, weights, intercept
    )
    step = 1e-6
    numeric = []
    for index in range(2):
        shifted = weights.copy()
        shifted[index] += step
        up = gradient.mse(target, gradient.predict_linear(features, shifted, intercept))
        shifted[index] -= 2 * step
        down = gradient.mse(
            target, gradient.predict_linear(features, shifted, intercept)
        )
        numeric.append((up - down) / (2 * step))
    expect(
        bool(np.allclose(weight_gradient, numeric, rtol=1e-4)),
        "Gradient po wagach nie zgadza się z przybliżeniem różnicowym straty. "
        f"Twój: {np.round(weight_gradient, 4).tolist()}, "
        f"numeryczny: {np.round(numeric, 4).tolist()}.",
    )
    up = gradient.mse(
        target, gradient.predict_linear(features, weights, intercept + step)
    )
    down = gradient.mse(
        target, gradient.predict_linear(features, weights, intercept - step)
    )
    expect(
        bool(np.isclose(intercept_gradient, (up - down) / (2 * step), rtol=1e-4)),
        "Gradient po wyrazie wolnym nie zgadza się z przybliżeniem różnicowym.",
    )

    fitted_weights, fitted_intercept, losses = gradient.fit_linear_gd(
        features, target, learning_rate=0.1, steps=300
    )
    expect(
        len(losses) == 300 and bool(np.isclose(losses[0], np.mean(target**2))),
        "losses ma mieć jedną wartość na krok, a losses[0] to strata modelu "
        "z samych zer, czyli średnia z y².",
    )
    expect(
        all(
            later <= earlier for earlier, later in zip(losses, losses[1:], strict=False)
        ),
        "Przy learning_rate=0.1 na tych danych strata powinna maleć w każdym kroku.",
    )
    expect(
        bool(np.allclose(fitted_weights, true_weights, atol=1e-3))
        and bool(np.isclose(fitted_intercept, true_intercept, atol=1e-3)),
        "Po 300 krokach na danych bez szumu wagi powinny dojść do [2, -1], "
        f"a wyraz wolny do 0.5. Dostałem {np.round(fitted_weights, 3).tolist()} "
        f"i {fitted_intercept:.3f}.",
    )
    _raises(
        lambda: gradient.fit_linear_gd(features, target, learning_rate=50.0, steps=500),
        ValueError,
        "learning_rate jest tak duży, że strata ucieka do nieskończoności",
    )
    _raises(
        lambda: gradient.fit_linear_gd(features, target, learning_rate=0.1, steps=0),
        ValueError,
        "steps wynosi 0",
    )


@task("08.4", "LinearForecaster: Ridge na cechach bez NaN, prognoza nieujemna")
def check_linear(_target: object) -> None:
    from freshcast.models import panel

    rng = np.random.default_rng(4)
    frame = pd.DataFrame(
        {"a": rng.normal(size=300), "b": rng.normal(size=300), "noise": 1.0}
    )
    target = pd.Series(50.0 + 2.0 * frame["a"] - 1.0 * frame["b"])

    model = panel.LinearForecaster(features=["a", "b"], alpha=0.0)
    _raises(lambda: model.predict(frame), RuntimeError, "predict jest wołany przed fit")
    expect(model.fit(frame, target) is model, "fit ma zwracać self.")
    forecast = model.predict(frame)
    expect(
        isinstance(forecast, np.ndarray)
        and bool(np.allclose(forecast, target.to_numpy(), atol=1e-6)),
        "Na danych bez szumu i z alpha=0 model liniowy powinien odtworzyć cel "
        "dokładnie. Sprawdź, czy używasz tylko kolumn z `features`.",
    )

    low = pd.Series(-5.0 + 0.0 * frame["a"])
    forecast = panel.LinearForecaster(["a", "b"]).fit(frame, low).predict(frame)
    expect(
        float(forecast.min()) == 0.0,
        "Sprzedaż nie bywa ujemna. Prognozy poniżej zera mają być podniesione "
        f"do 0. Najmniejsza prognoza: {forecast.min():.3f}.",
    )

    holes = frame.copy()
    holes.loc[0, "a"] = np.nan
    _raises(
        lambda: panel.LinearForecaster(["a", "b"]).fit(holes, target),
        ValueError,
        "cecha ma NaN przy fit",
    )
    _raises(lambda: model.predict(holes), ValueError, "cecha ma NaN przy predict")
    ignored = frame.assign(noise=np.nan)
    try:
        model.predict(ignored)
    except ValueError as error:
        raise CheckFailed(
            "NaN w kolumnie, której nie ma w `features`, nie powinien być błędem."
        ) from error


@task("08.5", "score_forecast: metryki na wszystkich wierszach i bez braków towaru")
def check_scores(_target: object) -> None:
    from freshcast.evaluation import scores

    actual = np.array([10.0, 10.0, 0.0, 20.0])
    predicted = np.array([12.0, 9.0, 1.0, 14.0])
    in_stock = np.array([True, True, False, False])
    got = scores.score_forecast(actual, predicted, in_stock)
    wanted = {
        "wape": 0.25,
        "mae": 2.5,
        "bias": -0.1,
        "wape_in_stock": 0.15,
        "bias_in_stock": 0.05,
    }
    expect(
        list(got) == list(wanted),
        f"score_forecast ma zwrócić słownik z kluczami {list(wanted)}, w tej "
        f"kolejności. Dostałem {list(got)}.",
    )
    for name, value in wanted.items():
        expect(
            bool(np.isclose(got[name], value)),
            f"{name} powinno wynosić {value}, a wynosi {got[name]:.4f}.",
        )
