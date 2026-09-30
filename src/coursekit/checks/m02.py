"""Checks for module 02: functions, decorators and types in ``carparts.py``.

The lab's code lives in ``labs/02-functions/carparts.py``. The notebook
imports it and passes the module, or one of its functions, to the check:
``check("02.1", carparts)``.
"""

import contextlib
import inspect
import io
import re
import time
import types
from typing import Any

from coursekit.checking import CheckFailed, expect, task
from coursekit.checks import m01
from coursekit.checks._quality import expect_clean

LAB_01 = {
    "parse_value": m01.check_parse_value,
    "parse_series_line": m01.check_parse_series_line,
    "read_series": m01.check_read_series,
    "demand_stats": m01.check_demand_stats,
    "top_series": m01.check_top_series,
    "save_summary": m01.check_save_summary,
}


def _missing_types(func: Any) -> list[str]:
    signature = inspect.signature(func)
    missing = [
        name
        for name, parameter in signature.parameters.items()
        if parameter.annotation is inspect.Parameter.empty
    ]
    if signature.return_annotation is inspect.Signature.empty:
        missing.append("wynik (->)")
    return missing


@task(
    "02.1",
    "carparts.py: funkcje z labu 01 z typami, czyste dla ruff i mypy",
    notebook=True,
)
def check_typed_module(module: types.ModuleType) -> None:
    absent = [name for name in LAB_01 if not callable(getattr(module, name, None))]
    if len(absent) == len(LAB_01):
        raise NotImplementedError
    expect(not absent, f"W carparts.py brakuje funkcji: {', '.join(absent)}.")
    for name, check_lab_01 in LAB_01.items():
        try:
            check_lab_01(getattr(module, name))
        except CheckFailed as failure:
            raise CheckFailed(f"{name}: {failure}") from failure
    untyped = {
        name: missing
        for name in LAB_01
        if (missing := _missing_types(getattr(module, name)))
    }
    expect(
        not untyped,
        "Brakuje typów: "
        + "; ".join(
            f"{name}: {', '.join(missing)}" for name, missing in untyped.items()
        ),
    )
    undocumented = [
        name for name in LAB_01 if not inspect.getdoc(getattr(module, name))
    ]
    expect(not undocumented, f"Brakuje docstringów: {', '.join(undocumented)}.")
    expect_clean(module)


def _add(a: int, b: int = 0, *, c: int = 0) -> int:
    """Add three numbers."""
    return a + b + c


def _fail() -> None:
    raise KeyError("expected")


def _nap() -> None:
    time.sleep(0.05)


def _printed(call: Any) -> tuple[Any, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = call()
    return result, buffer.getvalue()


@task("02.2", "timed: dekorator mierzący czas wywołania", notebook=True)
def check_timed(timed: Any) -> None:
    wrapped = timed(_add)
    expect(
        wrapped is not _add, "timed ma zwrócić nową funkcję, która opakowuje oryginał."
    )
    result, out = _printed(lambda: wrapped(1, 2, c=3))
    expect(
        result == 6,
        f"_add(1, 2, c=3) daje 6, po opakowaniu {result!r}. Czy przekazujesz *args i **kwargs?",
    )
    expect(
        re.fullmatch(r"_add: \d+(\.\d+)? s\n", out) is not None,
        f"Po wywołaniu oczekiwano jednej linii w postaci '_add: 0.000 s'. Wypisano {out!r}.",
    )
    expect(
        wrapped.__name__ == "_add" and wrapped.__doc__ == _add.__doc__,
        "Opakowana funkcja zgubiła nazwę albo docstring. Tu pomaga functools.wraps.",
    )
    _, out = _printed(lambda: timed(_nap)())
    seconds = float(out.split(": ")[1].split(" ")[0]) if ": " in out else -1.0
    expect(
        0.04 <= seconds < 1.0,
        f"Funkcja śpiąca 0,05 s wypisała {out.strip()!r}. Czas mierzysz od startu do końca wywołania.",
    )
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            timed(_fail)()
    except KeyError:
        pass
    else:
        raise CheckFailed("Wyjątek z opakowanej funkcji ma przejść dalej, a zniknął.")
    expect(
        buffer.getvalue().startswith("_fail: "),
        "Gdy funkcja rzuca wyjątek, linia z czasem też ma się pojawić. Pomyśl o try/finally.",
    )


def _answer(values: Any) -> float | None:
    """Always 42."""
    return 42.0


@task("02.3", "requires_history: fabryka dekoratorów z walidacją", notebook=True)
def check_requires_history(requires_history: Any) -> None:
    try:
        requires_history(0)
    except ValueError:
        pass
    else:
        raise CheckFailed(
            "requires_history(0) ma zgłosić ValueError od razu, przy nakładaniu dekoratora."
        )
    guarded = requires_history(3)(_answer)
    expect(
        guarded([1.0, None, 2.0]) is None,
        "Seria z 2 znanymi miesiącami przy min_months=3 ma dać None.",
    )
    got = guarded([1.0, 0.0, None, 2.0])
    expect(
        got == 42.0,
        f"Seria [1, 0, None, 2] ma 3 znane miesiące (zero to znana wartość), więc statystyka ma się policzyć. Dostałem {got!r}.",
    )
    expect(
        guarded.__name__ == "_answer",
        "Opakowana statystyka zgubiła nazwę. Użyj functools.wraps.",
    )


def _probe(values: Any) -> float | None:
    """A statistic registered by the check and removed afterwards."""
    return 0.0


@task("02.4", "register i summarise: rejestr statystyk", notebook=True)
def check_registry(module: types.ModuleType) -> None:
    sample = [0.0, 2.0, None, 0.0, 6.0]
    summary = module.summarise(sample)
    registry = module.STATISTICS
    snapshot = dict(registry)
    try:
        expect(
            module.register("__check__")(_probe) is _probe,
            "register ma zwrócić tę samą funkcję, którą dostał.",
        )
        expect(
            registry.get("__check__") is _probe,
            "Po register('__check__') funkcji nie ma w STATISTICS.",
        )
        try:
            module.register("__check__")(_answer)
        except ValueError:
            pass
        else:
            raise CheckFailed("Druga statystyka pod tą samą nazwą ma dać ValueError.")
    finally:
        registry.clear()
        registry.update(snapshot)
    wanted = {"months", "missing", "total", "zero_share", "adi", "cv2"}
    expect(
        wanted <= set(registry),
        f"W STATISTICS brakuje: {sorted(wanted - set(registry))}.",
    )
    year = [0.0, 2.0, 0.0, 4.0] * 3
    cv2 = registry["cv2"](year)
    expect(
        cv2 is not None and abs(cv2 - 1 / 9) < 1e-9,
        f"cv2 dla 12 miesięcy [0, 2, 0, 4] * 3: rozmiary popytu 2 i 4, średnia 3, wariancja 1, więc 1/9. Dostałem {cv2!r}.",
    )
    expect(
        registry["cv2"](year[:11]) is None,
        "cv2 zarejestrowane w STATISTICS policzyło się dla 11 miesięcy. Czy requires_history(12) "
        "działa na funkcji, którą widzi rejestr? Sprawdź kolejność dekoratorów.",
    )
    expected = {
        "months": 4,
        "missing": 1,
        "total": 8.0,
        "zero_share": 0.5,
        "adi": 2.0,
        "cv2": None,
    }
    got = {name: summary.get(name) for name in expected}
    expect(
        got == expected,
        f"summarise([0, 2, None, 0, 6]) powinno dać {expected}. Dostałem {got}.",
    )
    expect(
        module.summarise(sample, ["total"]) == {"total": 8.0},
        "summarise(values, ['total']) ma zwrócić tylko tę statystykę.",
    )
    try:
        module.summarise(sample, ["no_such_statistic"])
    except ValueError:
        pass
    else:
        raise CheckFailed(
            "Nieznana nazwa statystyki ma dać ValueError z listą znanych nazw."
        )


@task("02.5", "at_least i select: domknięcia i *args", notebook=True)
def check_selection(module: types.ModuleType) -> None:
    big = module.at_least("total", 9)
    small = module.at_least("total", 1)
    expect(
        [big({"total": 9.0}), big({"total": 5.0}), small({"total": 5.0})]
        == [True, False, True],
        "at_least('total', 9) ma przepuścić 9 i odrzucić 5, a at_least('total', 1) przepuścić 5. "
        "Każdy test pamięta własny próg.",
    )
    expect(
        big({"total": None}) is False and big({}) is False,
        "Brak wartości (None albo brak klucza) nie spełnia progu.",
    )
    stats = {
        "T3": {"total": 9.0, "adi": 1.0},
        "T1": {"total": 12.0, "adi": 4.0},
        "T2": {"total": 2.0, "adi": 6.0},
    }
    expect(
        module.select(stats) == ["T1", "T2", "T3"],
        "select bez testów zwraca wszystkie nazwy, posortowane.",
    )
    got = module.select(stats, big, module.at_least("adi", 2))
    expect(got == ["T1"], f"Tylko T1 ma total >= 9 i adi >= 2. Dostałem {got}.")
