"""Checks for module 14: settings, artifacts, the pipeline and its command line."""

import contextlib
import io
import json
import os
import tempfile
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Any, Self, cast

import numpy as np
import pandas as pd

from coursekit import paths
from coursekit.checking import CheckFailed, expect, task

SAMPLE = paths.FIXTURES_DIR / "frn_sample.parquet"
LAST_HISTORY_DAY = "2024-06-18"


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


@contextlib.contextmanager
def _workspace() -> Iterator[Path]:
    """A scratch directory with raw history and future files and a settings file."""
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        raw = pd.read_parquet(SAMPLE)
        is_history = raw["dt"] <= LAST_HISTORY_DAY
        raw[is_history].to_parquet(root / "train.parquet", index=False)
        raw[~is_history].to_parquet(root / "future.parquet", index=False)
        (root / "settings.yaml").write_text(
            "data:\n"
            f"  train_file: {root / 'train.parquet'}\n"
            f"  processed_dir: {root / 'processed'}\n"
            "model:\n"
            "  rounds: 30\n"
            "  params:\n"
            "    min_child_samples: 5\n"
            "backtest:\n"
            "  folds: 2\n"
            f"artifacts_dir: {root / 'artifacts'}\n",
            encoding="utf-8",
        )
        yield root


class Constant:
    """A picklable stand-in model."""

    def __init__(self, value: float) -> None:
        self.value = value

    def fit(self, X: pd.DataFrame, y: pd.Series) -> Self:
        return self

    def predict(self, X: pd.DataFrame) -> Any:
        return np.full(len(X), self.value)


@task("14.1", "Settings i load_settings: YAML, zmienne środowiskowe, walidacja")
def check_config(_target: object) -> None:
    from pydantic import ValidationError

    from freshcast import config

    with _workspace() as root:
        file = root / "settings.yaml"
        settings = config.load_settings(file)
        expect(
            isinstance(settings, config.Settings)
            and settings.model.rounds == 30
            and settings.backtest.folds == 2,
            "load_settings ma zwrócić obiekt Settings z wartościami z pliku YAML.",
        )
        expect(
            settings.backtest.horizon == 7 and settings.data.cities is None,
            "Wartości, których nie ma w pliku, biorą się z domyślnych w klasach.",
        )
        expect(
            isinstance(settings.data.train_file, Path),
            "Ścieżki z pliku YAML mają stać się obiektami Path.",
        )

        os.environ["FRESHCAST_MODEL__ROUNDS"] = "123"
        try:
            overridden = config.load_settings(file)
        finally:
            del os.environ["FRESHCAST_MODEL__ROUNDS"]
        expect(
            overridden.model.rounds == 123 and overridden.backtest.folds == 2,
            "Zmienna FRESHCAST_MODEL__ROUNDS=123 ma wygrać z wartością z pliku, "
            "a reszta ustawień ma zostać z pliku. Dostałem rounds="
            f"{overridden.model.rounds}.",
        )

        text = file.read_text(encoding="utf-8")
        typo = root / "typo.yaml"
        typo.write_text(text.replace("rounds: 30", "roundz: 30"), encoding="utf-8")
        _raises(
            lambda: config.load_settings(typo),
            ValidationError,
            "w pliku jest klucz z literówką (roundz)",
        )
        empty = root / "empty.yaml"
        empty.write_text(
            text.replace("model:", "  cities: []\nmodel:"), encoding="utf-8"
        )
        _raises(
            lambda: config.load_settings(empty),
            ValidationError,
            "cities to pusta lista",
        )
        _raises(
            lambda: config.load_settings(root / "missing.yaml"),
            FileNotFoundError,
            "plik ustawień nie istnieje",
        )


@task("14.2", "save_model i load_model: model z metadanymi i sygnaturą")
def check_artifacts(_target: object) -> None:
    from freshcast import artifacts

    moment = datetime(2024, 6, 25, 14, 30, 5)
    got = artifacts.model_signature("lightgbm", moment)
    expect(
        got == "lightgbm_20240625-143005",
        "Sygnatura dla 2024-06-25 14:30:05 to lightgbm_20240625-143005. "
        f"Dostałem {got!r}.",
    )
    with tempfile.TemporaryDirectory() as scratch:
        directory = Path(scratch) / "artifacts"
        metadata = {"features": ["a", "b"], "trained_until": pd.Timestamp("2024-06-18")}
        stand_in = cast(Any, Constant(4.0))
        target = artifacts.save_model(
            stand_in,
            directory,
            "constant",
            metadata,
            moment=moment,
        )
        expect(
            target == directory / "constant_20240625-143005" and target.is_dir(),
            "save_model ma utworzyć katalog o nazwie równej sygnaturze i zwrócić "
            "jego ścieżkę.",
        )
        expect(
            (target / "model.joblib").is_file()
            and (target / "metadata.json").is_file(),
            "W katalogu modelu mają być pliki model.joblib i metadata.json.",
        )
        saved = json.loads((target / "metadata.json").read_text(encoding="utf-8"))
        expect(
            saved.get("signature") == "constant_20240625-143005"
            and saved.get("name") == "constant"
            and saved.get("features") == ["a", "b"],
            "metadata.json ma zawierać sygnaturę, nazwę i wszystko, co podano "
            f"w metadata. Dostałem klucze {sorted(saved)}.",
        )
        _raises(
            lambda: artifacts.save_model(
                stand_in,
                directory,
                "constant",
                metadata,
                moment=moment,
            ),
            FileExistsError,
            "model o tej samej sygnaturze już istnieje",
        )

        model, loaded = artifacts.load_model(target)
        expect(
            loaded == saved
            and model.predict(pd.DataFrame({"x": [1, 2]})).tolist() == [4.0, 4.0],
            "load_model ma zwrócić model, który prognozuje tak jak zapisany, "
            "i jego metadane.",
        )
        (target / "metadata.json").unlink()
        _raises(
            lambda: artifacts.load_model(target),
            FileNotFoundError,
            "w katalogu modelu brakuje metadata.json",
        )


@task("14.3", "cities_in, prepare_in_chunks, training_mask")
def check_chunks(_target: object) -> None:
    from freshcast import pipeline
    from freshcast.data.prepare import prepare_daily

    got = pipeline.cities_in(SAMPLE)
    expect(
        got == [3, 11] and all(isinstance(city, int) for city in got),
        "W próbce są miasta 3 i 11. cities_in ma zwrócić [3, 11] jako zwykłe int. "
        f"Dostałem {got!r}.",
    )
    whole = prepare_daily(SAMPLE)
    chunked = pipeline.prepare_in_chunks(SAMPLE, None)
    try:
        pd.testing.assert_frame_equal(chunked, whole)
    except AssertionError as error:
        raise CheckFailed(
            "prepare_in_chunks dla wszystkich miast ma dać tę samą ramkę co "
            f"prepare_daily na całym pliku. Różnica: {str(error).splitlines()[0]}"
        ) from error
    expect(
        len(pipeline.prepare_in_chunks(SAMPLE, [11])) == 180,
        "prepare_in_chunks(plik, [11]) ma zwrócić 180 wierszy z próbki.",
    )

    table = pd.DataFrame(
        {
            pipeline.WARM_UP_FEATURE: [np.nan, 1.0, 2.0, 3.0],
            "oos_hours": [0, 0, 5, 0],
        }
    )
    mask = pipeline.training_mask(table, in_stock_only=True)
    expect(
        mask.tolist() == [False, True, False, True],
        "Z in_stock_only=True odpadają wiersze bez kompletnych lagów i dni "
        "z brakiem towaru. Oczekiwano [False, True, False, True], dostałem "
        f"{mask.tolist()}.",
    )
    mask = pipeline.training_mask(table, in_stock_only=False)
    expect(
        mask.tolist() == [False, True, True, True],
        "Z in_stock_only=False odpadają tylko wiersze bez kompletnych lagów.",
    )


@task("14.4", "train i forecast: od surowego pliku do zapisanej prognozy")
def check_pipeline(_target: object) -> None:
    from freshcast import config, pipeline

    with _workspace() as root:
        settings = config.load_settings(root / "settings.yaml")
        result = pipeline.train(settings)
        model_dir = result.model_dir
        expect(
            model_dir.parent == root / "artifacts"
            and model_dir.name.startswith("lightgbm_"),
            "train ma zapisać model w katalogu artifacts_dir z ustawień, pod "
            "sygnaturą zaczynającą się od lightgbm_.",
        )
        for name in (
            "model.joblib",
            "metadata.json",
            "history.parquet",
            "backtest.csv",
        ):
            expect(
                (model_dir / name).is_file(), f"W katalogu modelu brakuje pliku {name}."
            )
        expect(
            len(result.backtest) == 2 and "wape_in_stock" in result.backtest.columns,
            "TrainResult.backtest ma mieć po jednym wierszu na fold (tu 2).",
        )
        saved = json.loads((model_dir / "metadata.json").read_text(encoding="utf-8"))
        expect(
            "backtest" in saved
            and "features" in saved
            and saved.get("train_rows", 0) > 0,
            "metadata.json ma zawierać między innymi features, train_rows i "
            f"średnie wyniki backtestu. Dostałem klucze {sorted(saved)}.",
        )

        forecasts = pipeline.forecast(settings, model_dir, root / "future.parquet")
        expect(
            list(forecasts.columns) == ["store_id", "product_id", "dt", "forecast"]
            and len(forecasts) == 56,
            "forecast ma zwrócić kolumny store_id, product_id, dt, forecast, po "
            f"jednym wierszu na serię i dzień (8 × 7 = 56). Dostałem {len(forecasts)} "
            f"wierszy i kolumny {list(forecasts.columns)}.",
        )
        expect(
            bool(forecasts["forecast"].notna().all())
            and float(forecasts["forecast"].min()) >= 0,
            "Prognozy nie mogą być puste ani ujemne.",
        )
        expect(
            (model_dir / "forecast.parquet").is_file(),
            "Prognoza ma zostać zapisana jako forecast.parquet w katalogu modelu.",
        )

        tampered = pd.read_parquet(root / "future.parquet").assign(sale_amount=999.0)
        tampered.to_parquet(root / "tampered.parquet", index=False)
        again = pipeline.forecast(settings, model_dir, root / "tampered.parquet")
        expect(
            bool(np.allclose(again["forecast"], forecasts["forecast"])),
            "Prognoza nie może zależeć od sprzedaży zapisanej w pliku przyszłości. "
            "Po podmianie sale_amount na 999 wynik się zmienił, więc wartości "
            "z prognozowanych dni przeciekają do cech.",
        )


@task("14.5", "CLI: freshcast train i freshcast forecast, kody wyjścia")
def check_cli(_target: object) -> None:
    from freshcast import cli

    parser = cli.build_parser()
    args = parser.parse_args(["train", "--config", "x.yaml"])
    expect(
        args.command == "train" and args.config == Path("x.yaml"),
        "`freshcast train --config x.yaml` ma dać args.command == 'train' "
        "i args.config jako Path.",
    )

    with _workspace() as root, contextlib.redirect_stdout(io.StringIO()) as out:
        code = cli.main(["train", "--config", str(root / "nope.yaml")])
        expect(code == 2, f"Brak pliku ustawień ma dać kod wyjścia 2. Dostałem {code}.")

        code = cli.main(["train", "--config", str(root / "settings.yaml")])
        expect(code == 0, f"Udany trening ma dać kod wyjścia 0. Dostałem {code}.")
        printed = out.getvalue().strip().splitlines()
        expect(
            bool(printed) and Path(printed[-1]).is_dir(),
            "Po treningu CLI ma wypisać na standardowe wyjście ścieżkę katalogu "
            "modelu, żeby dało się ją przekazać do następnego polecenia.",
        )
        model_dir = printed[-1]
        code = cli.main(
            [
                "forecast",
                "--config",
                str(root / "settings.yaml"),
                "--model",
                model_dir,
                "--future",
                str(root / "future.parquet"),
            ]
        )
        expect(
            code == 0 and (Path(model_dir) / "forecast.parquet").is_file(),
            f"Udana prognoza ma dać kod 0 i plik forecast.parquet. Kod: {code}.",
        )
        code = cli.main(
            [
                "forecast",
                "--config",
                str(root / "settings.yaml"),
                "--model",
                str(root / "no-such-model"),
                "--future",
                str(root / "future.parquet"),
            ]
        )
        expect(
            code == 1,
            "Błąd w trakcie działania (tu: brak katalogu modelu) ma dać kod "
            f"wyjścia 1, a nie nieobsłużony wyjątek. Dostałem {code}.",
        )
