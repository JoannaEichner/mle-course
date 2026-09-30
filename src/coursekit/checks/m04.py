"""Checks for module 04: the local forecasters as a package, with tests."""

from collections.abc import Callable
from pathlib import Path

from coursekit import mutation, paths
from coursekit.checking import CheckFailed, expect, task

TESTS = paths.ROOT / "tests" / "models" / "test_local.py"
_MIN_TESTS = 6


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
            f"{type(other).__name__}."
        ) from other
    raise CheckFailed(f"Gdy {when}, kod powinien zgłosić {error.__name__}.")


def check_tests(test_path: Path, group: str, minimum: int) -> None:
    """Shared by modules 04 and 05: the tests exist, pass and kill mutants."""
    found = mutation.count_tests(test_path)
    expect(
        found >= minimum,
        f"W {test_path.relative_to(paths.ROOT)} jest {found} testów (licząc "
        f"przypadki parametryzacji). Napisz co najmniej {minimum}.",
    )
    expect(
        mutation.suite_passes(test_path),
        "Twoje testy nie przechodzą na Twoim własnym kodzie. Uruchom "
        f"`uv run pytest {test_path.relative_to(paths.ROOT)}` i zobacz które.",
    )
    alive = mutation.survivors(test_path, group)
    if alive:
        listing = "\n".join(f"        - {mutant.description}" for mutant in alive)
        raise CheckFailed(
            "Twoje testy przechodzą, mimo że kod został celowo zepsuty. "
            f"Nie wykryły {len(alive)} z {len(mutation.load_group(group))} błędów:\n"
            f"{listing}"
        )


@task("04.1", "LocalForecaster i trzy prognozy: naiwna, sezonowa, średnia krocząca")
def check_local(_target: object) -> None:
    from freshcast.models import local

    naive = local.NaiveForecaster()
    expect(
        naive.fit([3.0, 5.0, 4.0]) is naive,
        "fit ma zwracać ten sam obiekt (self), żeby dało się pisać "
        ".fit(...).predict(...).",
    )
    got = naive.predict(3)
    expect(
        got == [4.0, 4.0, 4.0],
        f"NaiveForecaster po historii [3, 5, 4] ma dać [4.0, 4.0, 4.0]. Dał {got}.",
    )
    expect(
        all(isinstance(value, float) for value in got),
        "predict ma zwracać listę liczb typu float, także gdy historia zawierała int.",
    )

    seasonal = local.SeasonalNaiveForecaster(season=3)
    got = seasonal.fit([1, 2, 3, 10, 20, 30]).predict(5)
    expect(
        got == [10.0, 20.0, 30.0, 10.0, 20.0],
        "SeasonalNaiveForecaster(season=3) po historii [1, 2, 3, 10, 20, 30] ma "
        f"dla horyzontu 5 dać [10, 20, 30, 10, 20]. Dał {got}.",
    )

    average = local.MovingAverageForecaster(window=3)
    got = average.fit([100, 1, 2, 3]).predict(2)
    expect(
        got == [2.0, 2.0],
        "MovingAverageForecaster(window=3) po historii [100, 1, 2, 3] ma dać "
        f"[2.0, 2.0]. Dał {got}.",
    )
    got = local.MovingAverageForecaster(window=7).fit([2, 4]).predict(1)
    expect(
        got == [3.0],
        "Historię krótszą niż okno MovingAverageForecaster uśrednia w całości: "
        f"dla [2, 4] i window=7 ma dać [3.0]. Dał {got}.",
    )

    history = [1.0, 2.0]
    local.NaiveForecaster().fit(history)
    expect(history == [1.0, 2.0], "fit zmienił listę, którą dostał.")

    _raises(lambda: local.NaiveForecaster().fit([]), ValueError, "historia jest pusta")
    _raises(
        lambda: local.NaiveForecaster().predict(1),
        RuntimeError,
        "predict jest wołany przed fit",
    )
    _raises(
        lambda: local.NaiveForecaster().fit([1.0]).predict(0),
        ValueError,
        "horizon wynosi 0",
    )
    _raises(
        lambda: local.SeasonalNaiveForecaster(season=7).fit([1.0, 2.0]),
        ValueError,
        "historia jest krótsza niż sezon",
    )
    _raises(
        lambda: local.SeasonalNaiveForecaster(season=0), ValueError, "season wynosi 0"
    )
    _raises(
        lambda: local.MovingAverageForecaster(window=0), ValueError, "window wynosi 0"
    )


@task("04.2", "testy prognoz lokalnych wykrywają celowo zepsuty kod")
def check_local_tests(_target: object) -> None:
    from freshcast.models import local

    local.NaiveForecaster().fit([1.0]).predict(1)  # not implemented yet -> todo
    check_tests(TESTS, "local", _MIN_TESTS)
