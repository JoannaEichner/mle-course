"""Checks for module 19: the capstone."""

import contextlib
import io
import re
from typing import Any, cast

import numpy as np
import pandas as pd

from coursekit import paths
from coursekit.checking import CheckFailed, expect, task
from coursekit.checks.m11 import _Spy, _table
from coursekit.checks.m14 import _raises, _workspace

REPORT = paths.ROOT / "reports" / "capstone.md"
REPORT_SECTIONS = ["Dane", "Walidacja", "Wyniki", "Wybór modelu", "Ograniczenia"]


class _Constant(_Spy):
    """Stand-in model that forecasts a fixed number."""

    value = 0.0

    def predict(self, X: pd.DataFrame) -> Any:
        return np.full(len(X), self.value)


class _Near(_Constant):
    value = 25.0


class _Far(_Constant):
    value = 100.0


@task("19.1", "compare_models: kilka modeli w jednym backteście")
def check_compare(_target: object) -> None:
    from freshcast import split
    from freshcast.evaluation import final

    table = _table()
    folds = split.rolling_origin_folds(table["dt"].max(), n_folds=2, horizon=7)
    candidates = cast(Any, {"near": _Near, "far": _Far})
    results = final.compare_models(
        candidates, table, folds, {"far": table["oos_hours"] == 0}
    )
    expect(
        list(results.columns[:2]) == ["model", "valid_start"] and len(results) == 4,
        "compare_models ma zwrócić po wierszu na model i fold (tu 2 × 2), z kolumną "
        f"model na początku. Dostałem {len(results)} wierszy i kolumny {list(results.columns)}.",
    )
    rows = results.set_index(["model", "valid_start"])
    expect(
        results.groupby("model")["mae"].mean()["near"]
        < results.groupby("model")["mae"].mean()["far"],
        "Model stale prognozujący 25 (blisko średniej sprzedaży) ma mieć mniejszy błąd niż model prognozujący 100. Wyniki modeli są pomieszane.",
    )
    trained = results.groupby("model")["train_rows"].first()
    expect(
        trained["far"] < trained["near"] and len(rows) == 4,
        "fit_masks ma ograniczać wiersze treningowe tylko wskazanego modelu.",
    )
    _raises(
        lambda: final.compare_models({}, table, folds, {}),
        ValueError,
        "nie podano żadnego modelu",
    )
    _raises(
        lambda: final.compare_models(candidates, table, folds, {"naer": None}),
        ValueError,
        "fit_masks zawiera nazwę modelu, którego nie ma wśród kandydatów",
    )


@task("19.2", "seasonal_naive_forecast i test_scores: model obok baseline'u")
def check_test_scores(_target: object) -> None:
    from freshcast.evaluation import final

    days = pd.date_range("2024-06-01", periods=14)
    history = pd.DataFrame(
        {
            "store_id": 1,
            "product_id": 7,
            "dt": days,
            "sale_amount": np.arange(1.0, 15.0),
        }
    )
    ahead = pd.DataFrame(
        {"store_id": 1, "product_id": 7, "dt": pd.date_range("2024-06-15", periods=3)},
        index=[7, 8, 9],
    )
    naive = final.seasonal_naive_forecast(history, ahead)
    expect(
        naive.tolist() == [8.0, 9.0, 10.0] and naive.index.equals(ahead.index),
        "Prognoza naiwna sezonowa na 15-17 czerwca to sprzedaż z 8-10 czerwca: [8, 9, 10], "
        f"z indeksem ramki wejściowej. Dostałem {naive.tolist()}.",
    )
    _raises(
        lambda: final.seasonal_naive_forecast(
            history, ahead.assign(dt=pd.Timestamp("2024-06-25"))
        ),
        ValueError,
        "dzień leży dalej niż 7 dni po historii",
    )

    actuals = ahead.assign(sale_amount=[8.0, 12.0, 10.0], oos_hours=[0, 0, 5])
    forecasts = ahead.assign(forecast=[8.0, 10.0, 10.0])
    scores = final.test_scores(forecasts, actuals, history)
    expect(
        list(scores.index) == ["model", "seasonal_naive"]
        and "wape_in_stock" in scores.columns,
        "test_scores ma zwrócić dwa wiersze, model i seasonal_naive, z kolumnami score_forecast.",
    )
    expect(
        bool(np.isclose(scores["wape_in_stock"].astype(float)["model"], 0.1))
        and bool(
            np.isclose(scores["wape_in_stock"].astype(float)["seasonal_naive"], 0.15)
        ),
        "Na dniach bez braków (pierwsze dwa) model myli się o 2 na 20 sztukach (WAPE 0.1), a "
        f"baseline o 3 (0.15). Dostałem {scores['wape_in_stock'].round(3).to_dict()}.",
    )
    _raises(
        lambda: final.test_scores(forecasts.iloc[:2], actuals, history),
        ValueError,
        "prognozy nie obejmują wszystkich dni testowych",
    )


@task("19.3", "freshcast evaluate: jedna ocena na zamkniętym zbiorze testowym")
def check_evaluate(_target: object) -> None:
    from freshcast import cli

    with _workspace() as root, contextlib.redirect_stdout(io.StringIO()) as out:
        settings = str(root / "settings.yaml")
        expect(
            cli.main(["train", "--config", settings]) == 0,
            "Trening na próbce się nie udał.",
        )
        model_dir = out.getvalue().strip().splitlines()[-1]
        future = str(root / "future.parquet")
        cli.main(
            ["forecast", "--config", settings, "--model", model_dir, "--future", future]
        )
        try:
            code = cli.main(
                [
                    "evaluate",
                    "--config",
                    settings,
                    "--model",
                    model_dir,
                    "--test",
                    future,
                ]
            )
        except SystemExit as error:  # argparse: the command does not exist yet
            raise NotImplementedError from error
        expect(
            code == 0,
            f"`freshcast evaluate` ma zakończyć się kodem 0. Dostałem {code}.",
        )
        written = pd.read_csv(f"{model_dir}/test_scores.csv", index_col=0)
    expect(
        list(written.index) == ["model", "seasonal_naive"],
        "evaluate ma zapisać test_scores.csv z wierszami model i seasonal_naive.",
    )


@task("19.4", "raport capstone ma wszystkie sekcje", graded=False)
def check_report(_target: object) -> None:
    if not REPORT.is_file():
        raise NotImplementedError
    text = REPORT.read_text(encoding="utf-8")
    headings = re.findall(r"^#{1,3}\s+(.+)$", text, flags=re.MULTILINE)
    missing = [name for name in REPORT_SECTIONS if not any(name in h for h in headings)]
    expect(not missing, f"W reports/capstone.md brakuje sekcji: {', '.join(missing)}.")
    expect(
        len(re.findall(r"\d+[.,]\d+", text)) >= 6,
        "Raport ma podawać wyniki liczbami: WAPE i bias modelu i baseline'u, w backteście i na teście.",
    )
    if "wape" not in text.lower():
        raise CheckFailed(
            "Raport nie wspomina o WAPE, metryce, którą kurs ocenia modele."
        )
