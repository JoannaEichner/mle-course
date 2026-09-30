"""Checks for module 03: classes in ``labs/03-classes/demand.py``.

The notebook imports the learner's module and passes it to the check:
``check("03.1", demand)``.
"""

import dataclasses
import inspect
import types
from datetime import date
from typing import Any

from coursekit.checking import CheckFailed, expect, task
from coursekit.checks._quality import expect_clean, need


def _raises(call: Any, error: type[Exception], when: str) -> None:
    try:
        call()
    except error:
        return
    except Exception as other:  # noqa: BLE001 - the wrong exception type is the finding
        raise CheckFailed(
            f"Gdy {when}, oczekiwano {error.__name__}, a poleciał {type(other).__name__}: {other}"
        ) from other
    raise CheckFailed(f"Gdy {when}, oczekiwano {error.__name__}.")


def _series(
    module: types.ModuleType, values: list[float | None], name: str = "A"
) -> Any:
    return module.DemandSeries.from_record((name, "1998-01-01", values))


@task("03.1", "DemandSeries: zamrożony dataclass z właściwościami", notebook=True)
def check_demand_series(module: types.ModuleType) -> None:
    need(module, "DemandSeries")
    cls = module.DemandSeries
    if not dataclasses.is_dataclass(cls) or not dataclasses.fields(cls):
        raise NotImplementedError
    names = [f.name for f in dataclasses.fields(cls)]
    expect(
        names == ["name", "start", "values"],
        f"Pola DemandSeries to name, start, values, w tej kolejności. Są: {names}.",
    )
    series = _series(module, [0.0, 2.0, None, 0.0, 6.0])
    expect(
        series.name == "A" and series.start == date(1998, 1, 1),
        f"from_record(('A', '1998-01-01', ...)) ma dać name 'A' i start date(1998, 1, 1). Dostałem {series.name!r}, {series.start!r}.",
    )
    expect(
        series.values == (0.0, 2.0, None, 0.0, 6.0)
        and isinstance(series.values, tuple),
        f"values ma być krotką wartości z rekordu. Dostałem {series.values!r}.",
    )
    expect(
        isinstance(inspect.getattr_static(cls, "from_record"), classmethod),
        "from_record ma być metodą klasy (@classmethod): tworzy obiekt, zanim jakikolwiek istnieje.",
    )
    _raises(
        lambda: setattr(series, "name", "B"),
        dataclasses.FrozenInstanceError,
        "zmieniasz pole obiektu",
    )
    expect(
        series == _series(module, [0.0, 2.0, None, 0.0, 6.0])
        and len({series, series}) == 1,
        "Dwie serie z tych samych danych mają być równe i dać się włożyć do zbioru.",
    )
    for prop in ("known", "is_complete", "adi", "cv2"):
        expect(
            isinstance(inspect.getattr_static(cls, prop, None), property),
            f"{prop} ma być właściwością (@property): series.{prop}, bez nawiasów.",
        )
    got = (series.known, series.is_complete, series.adi, series.cv2)
    wanted = ([0.0, 2.0, 0.0, 6.0], False, 2.0, 0.25)
    expect(
        got == wanted,
        f"Dla [0, 2, None, 0, 6] oczekiwano known, is_complete, adi, cv2 = {wanted}. Dostałem {got}. "
        "cv2 liczysz z niezerowych wartości 2 i 6: średnia 4, wariancja 4.",
    )
    quiet = _series(module, [0.0, 0.0, 0.0])
    expect(
        quiet.is_complete and quiet.adi is None and quiet.cv2 is None,
        f"Seria samych zer: is_complete True, adi i cv2 None. Dostałem {quiet.is_complete}, {quiet.adi}, {quiet.cv2}.",
    )
    _raises(lambda: _series(module, [1.0, -2.0]), ValueError, "seria ma wartość ujemną")
    _raises(lambda: _series(module, []), ValueError, "seria nie ma żadnych wartości")


@task("03.2", "DemandType i classify: typ popytu przez match", notebook=True)
def check_classify(module: types.ModuleType) -> None:
    need(module, "DemandType", "classify")
    kind = module.DemandType
    wanted = {
        "SMOOTH": "smooth",
        "ERRATIC": "erratic",
        "INTERMITTENT": "intermittent",
        "LUMPY": "lumpy",
        "INSUFFICIENT": "insufficient",
    }
    got = {member.name: str(member) for member in kind}
    expect(got == wanted, f"DemandType ma mieć członków {wanted}. Ma {got}.")
    expect(
        kind.LUMPY == "lumpy",
        "DemandType ma być StrEnum: członek równa się swojej nazwie tekstowej.",
    )
    cases = [
        ((1.0, 0.1), "smooth"),
        ((1.0, 0.8), "erratic"),
        ((2.0, 0.1), "intermittent"),
        ((2.0, 0.8), "lumpy"),
        ((1.32, 0.49), "smooth"),
        ((None, 0.1), "insufficient"),
        ((2.0, None), "insufficient"),
        ((1, 0), "smooth"),
    ]
    for (adi, cv2), expected in cases:
        result = module.classify(adi, cv2)
        expect(
            isinstance(result, kind) and result == expected,
            f"classify({adi}, {cv2}) ma dać DemandType.{expected.upper()}. Dostałem {result!r}. "
            "Progi 1.32 i 0.49 należą jeszcze do niższej klasy, a liczby całkowite liczą się jak każde inne.",
        )


def _forecast(model: Any, history: list[float], horizon: int) -> list[float]:
    return list(model.fit(history).predict(horizon))


@task("03.3", "LocalForecaster (ABC) i NaiveForecaster", notebook=True)
def check_naive(module: types.ModuleType) -> None:
    need(module, "LocalForecaster", "NaiveForecaster")
    base, naive = module.LocalForecaster, module.NaiveForecaster
    expect(
        inspect.isabstract(base),
        "LocalForecaster ma być klasą abstrakcyjną (ABC) z metodą abstrakcyjną _forecast.",
    )
    _raises(base, TypeError, "tworzysz LocalForecaster() bezpośrednio")
    expect(
        issubclass(naive, base), "NaiveForecaster ma dziedziczyć po LocalForecaster."
    )
    model = naive()
    _raises(lambda: model.predict(3), RuntimeError, "wywołujesz predict przed fit")
    expect(
        model.fit([1.0, 2.0, 5.0]) is model,
        "fit ma zwrócić sam model, żeby dało się pisać model.fit(h).predict(n).",
    )
    expect(
        model.predict(3) == [5.0, 5.0, 5.0],
        f"Naiwna prognoza z [1, 2, 5] na 3 kroki to [5, 5, 5]. Dostałem {model.predict(3)}.",
    )
    _raises(lambda: model.predict(0), ValueError, "horyzont jest mniejszy od 1")
    _raises(lambda: naive().fit([]), ValueError, "historia jest pusta")
    history = [1.0, 4.0]
    model = naive().fit(history)
    history.append(100.0)
    expect(
        model.predict(1) == [4.0],
        "Model zmienił prognozę, gdy ktoś dopisał wartość do listy po fit. fit ma zapamiętać kopię.",
    )


@task("03.4", "SeasonalNaiveForecaster i MovingAverageForecaster", notebook=True)
def check_seasonal_and_average(module: types.ModuleType) -> None:
    need(module, "SeasonalNaiveForecaster", "MovingAverageForecaster")
    seasonal, average = module.SeasonalNaiveForecaster, module.MovingAverageForecaster
    for cls in (seasonal, average):
        expect(
            issubclass(cls, module.LocalForecaster),
            f"{cls.__name__} ma dziedziczyć po LocalForecaster.",
        )
    got = _forecast(seasonal(season=3), [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], 5)
    expect(
        got == [4.0, 5.0, 6.0, 4.0, 5.0],
        f"Sezon 3, historia 1..6, horyzont 5: oczekiwano [4, 5, 6, 4, 5]. Dostałem {got}.",
    )
    _raises(lambda: seasonal(season=0), ValueError, "season jest mniejsze od 1")
    _raises(
        lambda: seasonal(season=4).fit([1.0, 2.0]),
        ValueError,
        "historia jest krótsza niż sezon",
    )
    got = _forecast(average(window=2), [1.0, 2.0, 3.0, 5.0], 2)
    expect(
        got == [4.0, 4.0],
        f"Średnia z 2 ostatnich wartości [.., 3, 5] to 4. Dostałem {got}.",
    )
    got = _forecast(average(window=10), [1.0, 3.0], 1)
    expect(
        got == [2.0],
        f"Okno dłuższe niż historia: średnia z całej historii. Dostałem {got}.",
    )
    _raises(lambda: average(window=0), ValueError, "window jest mniejsze od 1")
    _raises(lambda: seasonal().predict(1), RuntimeError, "wywołujesz predict przed fit")


class _Zero:
    """A forecaster that does not inherit from LocalForecaster."""

    def fit(self, history: Any) -> "_Zero":
        return self

    def predict(self, horizon: int) -> list[float]:
        return [0.0] * horizon


@task(
    "03.5",
    "Forecaster (Protocol), mae, evaluate; plik czysty dla ruff i mypy",
    notebook=True,
)
def check_evaluate(module: types.ModuleType) -> None:
    need(module, "Forecaster", "mae", "evaluate")
    expect(
        getattr(module.Forecaster, "_is_protocol", False),
        "Forecaster ma być Protocol: opisuje, co model umie, a nie po czym dziedziczy.",
    )
    expect(
        module.mae([1.0, 2.0], [2.0, 4.0]) == 1.5,
        "mae([1, 2], [2, 4]) to (1 + 2) / 2 = 1.5.",
    )
    _raises(
        lambda: module.mae([1.0], [1.0, 2.0]), ValueError, "ciągi mają różne długości"
    )
    series = [
        _series(module, [1.0, 1.0, 3.0, 5.0], "A"),
        _series(module, [2.0, 2.0, 4.0, 2.0], "B"),
        _series(module, [9.0, None, 9.0, 9.0], "C"),
    ]
    got = module.evaluate(module.NaiveForecaster, series, holdout=2)
    expect(
        got == 2.0,
        "Naiwna prognoza, holdout 2: seria A ma MAE 3 ([3, 5] wobec [1, 1]), seria B ma MAE 1 "
        f"([4, 2] wobec [2, 2]), seria C z brakiem odpada. Średnia to 2.0. Dostałem {got}.",
    )
    got = module.evaluate(_Zero, series, holdout=2)
    expect(
        got == 3.5,
        "evaluate ma działać z każdym obiektem, który ma fit i predict, także bez dziedziczenia. "
        f"Prognoza zerowa daje MAE 4 i 3, średnio 3.5. Dostałem {got}.",
    )
    _raises(
        lambda: module.evaluate(module.NaiveForecaster, series[2:], holdout=2),
        ValueError,
        "żadna seria nie jest kompletna",
    )
    expect_clean(module)
