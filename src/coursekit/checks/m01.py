"""Checks for module 01: parsing Monash Car Parts in plain Python.

The tasks are functions written in the lab notebook, so every check takes
the learner's function as its target: ``check("01.2", parse_series_line)``.
"""

import json
import tempfile
import types
from collections.abc import Callable
from pathlib import Path
from typing import Any

from coursekit.checking import CheckFailed, expect, task

TSF = """# Dataset Information
# A tiny sample in the Monash format.
@relation Sample
@attribute series_name string
@attribute start_timestamp date
@frequency monthly
@missing true
@data
A:1998-01-01 00-00-00:0,2,?,0,5
B:1998-01-01 00-00-00:1,1,1,1,1

C:1998-01-01 00-00-00:0,0,0,?,?
"""


def _raises(call: Callable[[], object], error: type[Exception], when: str) -> None:
    try:
        call()
    except error:
        return
    except Exception as other:  # noqa: BLE001 - the wrong exception type is the finding
        raise CheckFailed(
            f"Gdy {when}, oczekiwano {error.__name__}, a poleciał {type(other).__name__}."
        ) from other
    raise CheckFailed(f"Gdy {when}, funkcja powinna zgłosić {error.__name__}.")


@task("01.1", "parse_value: liczba, brak (?) albo błąd", notebook=True)
def check_parse_value(parse_value: Any) -> None:
    got = [parse_value(text) for text in ["0", "3", " 12 ", "?", "2.5"]]
    expect(
        got == [0.0, 3.0, 12.0, None, 2.5],
        "Dla '0', '3', ' 12 ', '?', '2.5' oczekiwano [0.0, 3.0, 12.0, None, 2.5]. "
        f"Dostałem {got}.",
    )
    expect(
        all(isinstance(value, float) for value in got if value is not None),
        "Liczby mają być typu float, także gdy w tekście są całkowite.",
    )
    _raises(lambda: parse_value("abc"), ValueError, "tekst nie jest liczbą")
    _raises(lambda: parse_value("-1"), ValueError, "popyt jest ujemny")


@task("01.2", "parse_series_line: nazwa, data startu, wartości", notebook=True)
def check_parse_series_line(parse_series_line: Any) -> None:
    got = parse_series_line("T7:1998-01-01 00-00-00:0,2,?,1\n")
    expect(
        got == ("T7", "1998-01-01", [0.0, 2.0, None, 1.0]),
        "Dla 'T7:1998-01-01 00-00-00:0,2,?,1' oczekiwano "
        f"('T7', '1998-01-01', [0.0, 2.0, None, 1.0]). Dostałem {got!r}.",
    )
    expect(isinstance(got, tuple), "Wynik ma być krotką: trzy pola o stałym znaczeniu.")
    _raises(
        lambda: parse_series_line("T7 0,1,2"),
        ValueError,
        "linia nie ma dwóch dwukropków",
    )


@task("01.3", "read_series: generator serii z pliku .tsf", notebook=True)
def check_read_series(read_series: Any) -> None:
    with tempfile.TemporaryDirectory() as scratch:
        path = Path(scratch) / "sample.tsf"
        path.write_text(TSF, encoding="utf-8")
        series = read_series(path)
        expect(
            isinstance(series, types.GeneratorType),
            "read_series ma być generatorem (yield), a nie budować listy od razu.",
        )
        first = next(series)
        expect(
            first == ("A", "1998-01-01", [0.0, 2.0, None, 0.0, 5.0]),
            f"Pierwsza seria w pliku to A z wartościami [0, 2, None, 0, 5]. Dostałem {first!r}.",
        )
        rest = list(series)
    names = [name for name, _, _ in rest]
    expect(
        names == ["B", "C"],
        "Po A w pliku są serie B i C. Linie komentarzy, nagłówka i puste mają "
        f"być pominięte. Dostałem nazwy {names}.",
    )


@task("01.4", "demand_stats: statystyki popytu jednej serii", notebook=True)
def check_demand_stats(demand_stats: Any) -> None:
    got = demand_stats([0.0, 2.0, None, 0.0, 6.0])
    wanted = {"months": 4, "missing": 1, "total": 8.0, "zero_share": 0.5, "adi": 2.0}
    expect(
        got == wanted,
        f"Dla [0, 2, None, 0, 6] oczekiwano {wanted}. Dostałem {got}. ADI to liczba "
        "znanych miesięcy podzielona przez liczbę miesięcy z popytem większym od zera.",
    )
    quiet = demand_stats([0.0, None, 0.0])
    expect(
        quiet["adi"] is None and quiet["zero_share"] == 1.0,
        "Seria bez żadnego popytu ma adi None (nie ma przerw między popytami do zmierzenia), "
        f"a zero_share 1.0. Dostałem {quiet}.",
    )
    empty = demand_stats([None, None])
    expect(
        empty["months"] == 0 and empty["zero_share"] is None and empty["adi"] is None,
        "Seria z samymi brakami ma months 0, a zero_share i adi None, bez dzielenia przez zero.",
    )


@task("01.5", "top_series: najlepsze serie według statystyki", notebook=True)
def check_top_series(top_series: Any) -> None:
    stats: dict[str, dict[str, float | None]] = {
        "T1": {"total": 5.0, "adi": 2.0},
        "T2": {"total": 9.0, "adi": None},
        "T3": {"total": 9.0, "adi": 1.0},
        "T4": {"total": 1.0, "adi": 4.0},
    }
    got = top_series(stats, "total", 2)
    expect(
        got == [("T2", 9.0), ("T3", 9.0)],
        "Dwie serie z największym total to T2 i T3 (po 9). Remisy rozstrzyga nazwa, "
        f"rosnąco. Dostałem {got}.",
    )
    got = top_series(stats, "adi", 10)
    expect(
        got == [("T4", 4.0), ("T1", 2.0), ("T3", 1.0)],
        f"Serie z adi None pomijasz, reszta malejąco. Dostałem {got}.",
    )
    expect(
        list(stats) == ["T1", "T2", "T3", "T4"] and stats["T2"]["adi"] is None,
        "top_series zmieniło słownik, który dostało.",
    )


@task("01.6", "save_summary: zapis statystyk do JSON", notebook=True)
def check_save_summary(save_summary: Any) -> None:
    stats = {"T2": {"total": 9.0, "adi": None}, "T1": {"total": 5.0, "adi": 2.0}}
    with tempfile.TemporaryDirectory() as scratch:
        target = Path(scratch) / "out" / "summary.json"
        returned = save_summary(stats, target)
        expect(
            returned == target and target.is_file(),
            "save_summary ma utworzyć brakujący katalog, zapisać plik i zwrócić jego ścieżkę.",
        )
        text = target.read_text(encoding="utf-8")
    expect(json.loads(text) == stats, "Po wczytaniu JSON ma dać ten sam słownik.")
    expect(
        text.index('"T1"') < text.index('"T2"') and "\n  " in text,
        "Plik ma mieć klucze posortowane i wcięcia, żeby dało się go czytać i porównywać w gicie.",
    )
