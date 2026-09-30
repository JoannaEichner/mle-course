"""Checks for module 11: rolling-origin folds, backtest, tuning with MLflow."""

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, Self, cast

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


def _table(days: int = 42, seed: int = 11) -> pd.DataFrame:
    """Three series with a weekly pattern and one informative feature."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-04-01", periods=days)
    frames = []
    for store in (1, 2, 3):
        signal = rng.uniform(0, 5, days)
        frames.append(
            pd.DataFrame(
                {
                    "store_id": store,
                    "product_id": 7,
                    "dt": dates,
                    "signal": signal,
                    "sale_amount": 10 * store + 2 * signal + rng.normal(0, 0.2, days),
                    "oos_hours": rng.choice([0, 0, 3], days),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


class _Spy:
    """Stand-in model that records what it was trained on."""

    seen: list[pd.DataFrame] = []

    def fit(self, X: pd.DataFrame, y: pd.Series) -> Self:
        type(self).seen.append(X)
        self.level = float(y.mean())
        return self

    def predict(self, X: pd.DataFrame) -> Any:
        return np.full(len(X), self.level)


@task("11.1", "Fold i rolling_origin_folds: okna walidacyjne krok po kroku")
def check_folds(_target: object) -> None:
    from freshcast import split

    last = pd.Timestamp("2024-06-25")
    folds = split.rolling_origin_folds(last, n_folds=3, horizon=7)
    got = [(str(f.valid_start.date()), str(f.valid_end.date())) for f in folds]
    wanted = [
        ("2024-06-05", "2024-06-11"),
        ("2024-06-12", "2024-06-18"),
        ("2024-06-19", "2024-06-25"),
    ]
    expect(
        got == wanted,
        "Dla ostatniej daty 2024-06-25, trzech foldów i horyzontu 7 okna "
        f"walidacyjne to {wanted}, od najstarszego. Dostałem {got}.",
    )
    _raises(
        lambda: split.rolling_origin_folds(last, n_folds=0, horizon=7),
        ValueError,
        "n_folds wynosi 0",
    )
    _raises(
        lambda: split.rolling_origin_folds(last, n_folds=2, horizon=0),
        ValueError,
        "horizon wynosi 0",
    )

    table = _table()
    fold = split.Fold(pd.Timestamp("2024-04-29"), pd.Timestamp("2024-05-05"))
    train, valid = fold.split(table)
    expect(
        len(train) == 3 * 28 and len(valid) == 3 * 7,
        "Fold z oknem 2024-04-29..2024-05-05 na trzech seriach od 2024-04-01 "
        f"daje 84 wiersze treningowe i 21 walidacyjnych. Dostałem {len(train)} "
        f"i {len(valid)}. Dni po końcu okna nie należą do żadnej części.",
    )
    expect(
        bool((train["dt"] < fold.valid_start).all())
        and bool(train.index.isin(table.index).all()),
        "Trening to wyłącznie dni przed valid_start, z indeksem ramki wejściowej.",
    )


@task("11.2", "backtest: świeży model na każdym foldzie, wynik per fold")
def check_backtest(_target: object) -> None:
    from freshcast import split
    from freshcast.evaluation import backtest

    table = _table()
    folds = split.rolling_origin_folds(table["dt"].max(), n_folds=2, horizon=7)
    _Spy.seen = []
    results = backtest.backtest(_Spy, table, folds)  # type: ignore[arg-type]
    wanted = [
        "valid_start",
        "valid_end",
        "train_rows",
        "valid_rows",
        "wape",
        "mae",
        "bias",
        "wape_in_stock",
        "bias_in_stock",
    ]
    expect(
        list(results.columns) == wanted and len(results) == 2,
        f"backtest ma zwrócić po jednym wierszu na fold z kolumnami {wanted}. "
        f"Dostałem {len(results)} wierszy i kolumny {list(results.columns)}.",
    )
    expect(
        results["train_rows"].tolist() == [84, 105]
        and results["valid_rows"].tolist() == [21, 21],
        "Trening rośnie z foldu na fold (84, potem 105 wierszy), walidacja ma "
        f"stale 21. Dostałem {results['train_rows'].tolist()} i "
        f"{results['valid_rows'].tolist()}.",
    )
    expect(
        len(_Spy.seen) == 2 and bool((_Spy.seen[0]["dt"] < folds[0].valid_start).all()),
        "Każdy fold ma dostać nowy model wytrenowany tylko na dniach sprzed "
        "swojego okna walidacyjnego.",
    )

    _Spy.seen = []
    in_stock = table["oos_hours"] == 0
    masked = backtest.backtest(_Spy, table, folds, fit_mask=in_stock)  # type: ignore[arg-type]
    expect(
        bool((_Spy.seen[0]["oos_hours"] == 0).all())
        and masked["valid_rows"].tolist() == [21, 21],
        "fit_mask ogranicza tylko wiersze treningowe. Walidacja zawsze używa "
        "wszystkich wierszy okna.",
    )
    expect(
        masked["train_rows"].tolist()
        == [int(in_stock[table["dt"] < f.valid_start].sum()) for f in folds],
        "train_rows ma liczyć wiersze po zastosowaniu fit_mask.",
    )
    nothing = pd.Series(False, index=table.index)
    _raises(
        lambda: backtest.backtest(_Spy, table, folds, fit_mask=nothing),  # type: ignore[arg-type]
        ValueError,
        "fit_mask nie zostawia żadnego wiersza treningowego",
    )


@task("11.3", "suggest_params i tune: Optuna z logowaniem prób do MLflow")
def check_tuning(_target: object) -> None:
    import mlflow
    import optuna

    from freshcast import split, tracking, tuning

    trial = optuna.trial.FixedTrial(
        {
            "learning_rate": 0.1,
            "num_leaves": 31,
            "min_child_samples": 20,
            "feature_fraction": 0.8,
            "lambda_l2": 1.0,
        }
    )
    params = tuning.suggest_params(cast(Any, trial))
    expect(
        params
        == {
            "learning_rate": 0.1,
            "num_leaves": 31,
            "min_child_samples": 20,
            "feature_fraction": 0.8,
            "lambda_l2": 1.0,
        },
        "suggest_params ma zwrócić słownik z pięcioma parametrami z tabeli "
        f"w docstringu, pod tymi samymi nazwami. Dostałem {params}.",
    )
    for name, low, high in [("learning_rate", 0.02, 0.2), ("lambda_l2", 1e-3, 10.0)]:
        distribution: Any = trial.distributions[name]
        expect(
            bool(np.isclose(distribution.low, low))
            and bool(np.isclose(distribution.high, high))
            and distribution.log,
            f"{name} ma być losowany z zakresu {low}..{high} w skali logarytmicznej.",
        )

    table = _table()
    folds = split.rolling_origin_folds(table["dt"].max(), n_folds=2, horizon=7)
    previous = mlflow.get_tracking_uri()
    with tempfile.TemporaryDirectory() as scratch:
        tracking.use_local_tracking(Path(scratch), "check-11")
        try:
            study = tuning.tune(
                table,
                folds,
                ["signal", "store_id"],
                ["store_id"],
                n_trials=3,
                rounds=20,
                experiment="check-11",
            )
            runs = mlflow.search_runs(experiment_names=["check-11"])
        finally:
            mlflow.set_tracking_uri(previous)

    expect(
        len(study.trials) == 3
        and study.direction == optuna.study.StudyDirection.MINIMIZE,
        "tune ma uruchomić n_trials prób w studium, które minimalizuje wynik.",
    )
    expect(
        len(runs) == 3,
        "Każda próba ma mieć własny przebieg w MLflow. Prób było 3, przebiegów "
        f"{len(runs)}.",
    )
    for column in (
        "params.num_leaves",
        "params.rounds",
        "metrics.wape_in_stock",
        "metrics.bias",
    ):
        expect(
            column in runs.columns and bool(runs[column].notna().all()),
            f"W każdym przebiegu MLflow ma być zapisane {column.split('.')[1]}.",
        )
    logged = sorted(runs["metrics.wape_in_stock"].round(9).tolist())
    returned = sorted(round(t.value, 9) for t in study.trials if t.value is not None)
    expect(
        logged == returned,
        "Wartość zwracana przez próbę do Optuny ma być tą samą średnią "
        "wape_in_stock, która trafia do MLflow.",
    )
