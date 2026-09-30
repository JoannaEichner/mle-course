"""Checks for module 05: NumPy, metrics, row shares."""

from collections.abc import Callable

import numpy as np

from coursekit import paths
from coursekit.checking import CheckFailed, expect, task
from coursekit.checks.m04 import check_tests

TESTS = paths.ROOT / "tests" / "test_metrics.py"
_MIN_TESTS = 6


def _raises(call: Callable[[], object], when: str) -> None:
    try:
        call()
    except ValueError:
        return
    except NotImplementedError:
        raise
    except Exception as other:  # noqa: BLE001 - the wrong exception type is the finding
        raise CheckFailed(
            f"Gdy {when}, oczekiwano ValueError, a poleciał {type(other).__name__}."
        ) from other
    raise CheckFailed(f"Gdy {when}, funkcja powinna zgłosić ValueError.")


@task("05.1", "prepare: wspólna walidacja wejść metryk i maska")
def check_prepare(_target: object) -> None:
    from freshcast import metrics

    actual, predicted = metrics.prepare([1, 2, 3], [1.5, 2.5, 3.5])
    expect(
        isinstance(actual, np.ndarray) and actual.dtype == np.float64,
        "prepare ma zwracać tablice NumPy typu float64, także dla list liczb "
        "całkowitych.",
    )
    expect(
        actual.tolist() == [1.0, 2.0, 3.0] and predicted.tolist() == [1.5, 2.5, 3.5],
        "Bez maski prepare zwraca wszystkie wartości, w tej samej kolejności.",
    )
    actual, predicted = metrics.prepare(
        [1.0, 2.0, 3.0], [9.0, 8.0, 7.0], [True, False, True]
    )
    expect(
        actual.tolist() == [1.0, 3.0] and predicted.tolist() == [9.0, 7.0],
        "Maska [True, False, True] ma zostawić pierwszy i trzeci element obu "
        f"tablic. Zostało: {actual.tolist()} i {predicted.tolist()}.",
    )
    kept, _ = metrics.prepare([1.0, np.nan], [1.0, 2.0], [True, False])
    expect(
        kept.tolist() == [1.0],
        "NaN w wierszu odrzuconym przez maskę nie jest błędem: ten wiersz nie "
        "bierze udziału w ocenie.",
    )
    _raises(lambda: metrics.prepare([1.0, 2.0], [1.0]), "wejścia mają różną długość")
    _raises(lambda: metrics.prepare([1.0, np.nan], [1.0, 2.0]), "w danych jest NaN")
    _raises(
        lambda: metrics.prepare([1.0, 2.0], [1.0, 2.0], [False, False]),
        "maska odrzuca wszystkie wiersze",
    )
    _raises(
        lambda: metrics.prepare([1.0, 2.0], [1.0, 2.0], [True]),
        "maska ma inną długość niż dane",
    )


@task("05.2", "mae i rmse")
def check_mae_rmse(_target: object) -> None:
    from freshcast import metrics

    actual = np.array([0.0, 0.0, 0.0, 0.0])
    predicted = np.array([0.0, 0.0, 0.0, 4.0])
    got = metrics.mae(actual, predicted)
    expect(
        isinstance(got, float) and bool(np.isclose(got, 1.0)),
        f"mae dla błędów [0, 0, 0, 4] to 1.0. Dostałem {got!r}. Wynik ma być "
        "zwykłym floatem, nie skalarem NumPy.",
    )
    got = metrics.rmse(actual, predicted)
    expect(
        isinstance(got, float) and bool(np.isclose(got, 2.0)),
        f"rmse dla błędów [0, 0, 0, 4] to 2.0. Dostałem {got!r}.",
    )
    got = metrics.mae([1.0, 100.0, 3.0], [2.0, 0.0, 3.0], [True, False, True])
    expect(
        bool(np.isclose(got, 0.5)),
        f"Z maską [True, False, True] mae liczy się z dwóch wierszy i wynosi 0.5. "
        f"Dostałem {got}.",
    )


@task("05.3", "wape i bias")
def check_wape_bias(_target: object) -> None:
    from freshcast import metrics

    actual = np.array([0.0, 10.0, 10.0])
    predicted = np.array([1.0, 8.0, 13.0])
    got = metrics.wape(actual, predicted)
    expect(
        isinstance(got, float) and bool(np.isclose(got, 0.3)),
        "wape to suma błędów bezwzględnych (1 + 2 + 3) przez sumę wartości "
        f"rzeczywistych (20), czyli 0.3. Dostałem {got!r}.",
    )
    got = metrics.bias(actual, predicted)
    expect(
        isinstance(got, float) and bool(np.isclose(got, 0.1)),
        "bias to (suma prognoz - suma rzeczywistych) / suma rzeczywistych, tutaj "
        f"(22 - 20) / 20 = 0.1. Dostałem {got!r}.",
    )
    got = metrics.bias([10.0, 10.0], [8.0, 9.0])
    expect(
        bool(np.isclose(got, -0.15)),
        f"Prognoza za niska daje bias ujemny: dla [8, 9] wobec [10, 10] to -0.15. "
        f"Dostałem {got}.",
    )
    _raises(
        lambda: metrics.wape(np.zeros(3), np.ones(3)),
        "wartości rzeczywiste sumują się do zera (wape)",
    )
    _raises(
        lambda: metrics.bias(np.zeros(3), np.ones(3)),
        "wartości rzeczywiste sumują się do zera (bias)",
    )


@task("05.4", "row_shares: każdy wiersz tablicy sumuje się do 1")
def check_row_shares(_target: object) -> None:
    from freshcast import numeric

    matrix = np.array([[1.0, 1.0, 2.0], [0.0, 0.0, 0.0], [5.0, 0.0, 0.0]])
    before = matrix.copy()
    shares = numeric.row_shares(matrix)
    expect(
        isinstance(shares, np.ndarray) and shares.shape == matrix.shape,
        "row_shares ma zwrócić tablicę o tym samym kształcie co wejście.",
    )
    expect(
        bool(np.allclose(shares[0], [0.25, 0.25, 0.5]))
        and bool(np.allclose(shares[2], [1.0, 0.0, 0.0])),
        "Wiersz [1, 1, 2] ma dać [0.25, 0.25, 0.5], a [5, 0, 0] ma dać [1, 0, 0]. "
        f"Dostałem {shares[0].tolist()} i {shares[2].tolist()}.",
    )
    expect(
        bool(np.isnan(shares[1]).all()),
        "Wiersz samych zer nie ma profilu. Ma stać się wierszem NaN, a nie zer "
        f"ani nieskończoności. Dostałem {shares[1].tolist()}.",
    )
    expect(
        bool(np.array_equal(matrix, before)), "row_shares zmieniło tablicę wejściową."
    )
    _raises(lambda: numeric.row_shares(np.array([1.0, 2.0])), "tablica jest 1-D")
    _raises(
        lambda: numeric.row_shares(np.array([[1.0, -1.0]])), "w tablicy jest ujemna"
    )


@task("05.5", "testy metryk wykrywają celowo zepsuty kod")
def check_metric_tests(_target: object) -> None:
    from freshcast import metrics

    metrics.mae([1.0], [1.0])  # not implemented yet -> todo
    metrics.wape([1.0], [1.0])
    check_tests(TESTS, "metrics", _MIN_TESTS)
