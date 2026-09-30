"""Checks for module 15: object storage through S3 and SQL with DuckDB.

Storage runs against moto, an in-process fake of S3, so the checks need
neither the network nor a server. SQL runs on parquet files in a temporary
directory, built from the sample with the learner's module 07 code.
"""

import contextlib
import os
import tempfile
from collections.abc import Callable, Iterator
from datetime import date
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from coursekit import paths
from coursekit.checking import CheckFailed, expect, task
from coursekit.checks.m04 import check_tests

SAMPLE = paths.FIXTURES_DIR / "frn_sample.parquet"
TESTS = paths.ROOT / "tests" / "storage" / "test_s3.py"
BUCKET = "check-bucket"


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
def _fake_s3() -> Iterator[Any]:
    """A moto S3 with one bucket and fake credentials; yields a client."""
    import boto3
    from moto import mock_aws

    saved = {
        name: os.environ.get(name)
        for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")
    }
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # noqa: S105 - moto's fake key
    try:
        with mock_aws():
            client = boto3.client("s3", region_name="us-east-1")
            client.create_bucket(Bucket=BUCKET)
            yield client
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _client_error(code: str, status: int) -> Any:
    from botocore.exceptions import ClientError

    response: Any = {
        "Error": {"Code": code},
        "ResponseMetadata": {"HTTPStatusCode": status},
    }
    return ClientError(response, "Op")


@task("15.1", "StorageSettings: nazwa bucketu, prefiks, adres serwera")
def check_settings(_target: object) -> None:
    from pydantic import ValidationError

    from freshcast.config import StorageSettings

    good = StorageSettings(
        bucket="freshcast-models",
        prefix="/models/v1/",
        endpoint_url="http://localhost:9000",
    )
    expect(
        good.prefix == "models/v1",
        f"Ukośniki na końcach prefiksu mają zniknąć: '/models/v1/' to 'models/v1'. Dostałem {good.prefix!r}.",
    )
    expect(
        StorageSettings(bucket="abc", prefix="").prefix == "",
        "Pusty prefiks oznacza korzeń bucketu.",
    )
    for bucket in ("Freshcast", "ab", "my_bucket", "-models", "a.b.c"):
        _raises(
            partial(StorageSettings, bucket=bucket),
            ValidationError,
            f"nazwa bucketu to {bucket!r}",
        )
    _raises(
        lambda: StorageSettings(bucket="abc", prefix="models/../x"),
        ValidationError,
        "prefiks zawiera '..'",
    )
    for url in ("localhost:9000", "ftp://host:21", "http://"):
        _raises(
            partial(StorageSettings, bucket="abc", endpoint_url=url),
            ValidationError,
            f"adres serwera to {url!r}",
        )


@task("15.2", "retry i is_transient: ponawianie tylko tego, co może przejść")
def check_retry(_target: object) -> None:
    from botocore.exceptions import EndpointConnectionError

    from freshcast.storage import retry, s3

    expect(
        s3.is_transient(EndpointConnectionError(endpoint_url="http://x"))
        and s3.is_transient(_client_error("InternalError", 503))
        and s3.is_transient(_client_error("SlowDown", 200)),
        "Zerwane połączenie, status 503 i kod SlowDown to błędy przejściowe.",
    )
    expect(
        not s3.is_transient(_client_error("NoSuchKey", 404))
        and not s3.is_transient(_client_error("AccessDenied", 403))
        and not s3.is_transient(ValueError("x")),
        "Brak klucza, brak dostępu i błędy spoza botocore nie są przejściowe.",
    )

    waits: list[float] = []
    calls: list[int] = []

    @retry.retry(
        retry_if=lambda error: True,
        attempts=4,
        base_delay=0.5,
        factor=2.0,
        max_delay=1.5,
        sleep=waits.append,
    )
    def flaky() -> str:
        """Fails three times."""
        calls.append(1)
        if len(calls) < 4:
            raise ConnectionError("down")
        return "ok"

    expect(
        flaky() == "ok" and len(calls) == 4,
        "Funkcja, która udaje się za czwartym razem, ma zwrócić wynik po 4 wywołaniach.",
    )
    expect(
        waits == [0.5, 1.0, 1.5],
        "Przerwy rosną wykładniczo od base_delay i nie przekraczają max_delay: "
        f"oczekiwano [0.5, 1.0, 1.5], dostałem {waits}.",
    )
    expect(
        flaky.__name__ == "flaky" and flaky.__doc__ == "Fails three times.",
        "Dekorowana funkcja ma zachować nazwę i docstring.",
    )

    calls.clear()
    waits.clear()

    @retry.retry(
        retry_if=lambda error: isinstance(error, ConnectionError),
        attempts=3,
        sleep=waits.append,
    )
    def broken() -> None:
        calls.append(1)
        raise KeyError("permanent")

    _raises(broken, KeyError, "błąd nie spełnia retry_if")
    expect(
        len(calls) == 1 and waits == [],
        "Błędu, którego retry_if nie uznaje, nie wolno ponawiać ani na niego czekać.",
    )

    calls.clear()

    @retry.retry(retry_if=lambda error: True, attempts=3, sleep=lambda _: None)
    def always_down() -> None:
        calls.append(1)
        raise ConnectionError(f"attempt {len(calls)}")

    try:
        always_down()
    except ConnectionError as error:
        expect(
            str(error) == "attempt 3" and len(calls) == 3,
            "Po ostatniej próbie ma polecieć błąd tej ostatniej próby.",
        )
    else:
        raise CheckFailed(
            "Po wyczerpaniu prób błąd ma zostać zgłoszony, a nie połknięty."
        )
    _raises(
        lambda: retry.retry(retry_if=lambda error: True, attempts=0),
        ValueError,
        "attempts wynosi 0",
    )


@task("15.3", "S3Storage i make_client: podstawowe operacje na buckecie")
def check_storage(_target: object) -> None:
    from freshcast.storage import s3

    _raises(
        lambda: s3.make_client(access_key="only-one"),
        ValueError,
        "podano tylko access_key",
    )
    with _fake_s3() as client, tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        storage = s3.S3Storage(client, BUCKET, sleep=lambda _: None)
        source = root / "a.txt"
        source.write_text("hello", encoding="utf-8")
        storage.upload_file(source, "models/a.txt")
        storage.upload_file(source, "models/b.txt")
        storage.upload_file(source, "other.txt")
        storage.download_file("models/a.txt", root / "deep" / "copy.txt")
        expect(
            (root / "deep" / "copy.txt").read_text(encoding="utf-8") == "hello",
            "download_file ma odtworzyć plik, tworząc brakujące katalogi.",
        )
        expect(
            storage.exists("models/a.txt")
            and not storage.exists("models")
            and not storage.exists("nope"),
            "exists ma rozpoznawać tylko pełne klucze: 'models' nie istnieje, choć istnieje 'models/a.txt'.",
        )
        expect(
            storage.list_keys("models/") == ["models/a.txt", "models/b.txt"]
            and storage.list_keys() == ["models/a.txt", "models/b.txt", "other.txt"],
            f"list_keys ma zwracać posortowane klucze z prefiksem. Dostałem {storage.list_keys()}.",
        )
        storage.delete("other.txt")
        storage.delete("other.txt")
        expect(
            not storage.exists("other.txt"),
            "delete ma usunąć obiekt i nie narzekać, gdy go już nie ma.",
        )
        _raises(
            lambda: storage.download_file("nope", root / "x"),
            FileNotFoundError,
            "klucza nie ma w buckecie",
        )
        _raises(
            lambda: storage.upload_file(root / "nope.txt", "x"),
            FileNotFoundError,
            "plik lokalny nie istnieje",
        )


@task("15.4", "fetch: lokalna kopia pobierana tylko wtedy, gdy trzeba")
def check_fetch(_target: object) -> None:
    from freshcast.storage import s3

    with _fake_s3() as client, tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        storage = s3.S3Storage(
            client, BUCKET, cache_dir=root / "cache", sleep=lambda _: None
        )
        source = root / "data.parquet"
        source.write_text("first", encoding="utf-8")
        storage.upload_file(source, "data/data.parquet")

        downloads: list[str] = []
        original = storage.download_file

        def counting(key: str, path: Path) -> None:
            downloads.append(key)
            original(key, path)

        storage.download_file = counting  # type: ignore[method-assign]
        first = storage.fetch("data/data.parquet")
        second = storage.fetch("data/data.parquet")
        expect(
            first == second and len(downloads) == 1,
            f"Drugi fetch tego samego obiektu nie może go pobierać. Pobrań: {len(downloads)}.",
        )
        expect(
            first.name == "data.parquet" and root / "cache" in first.parents,
            "Kopia ma leżeć w cache_dir i nazywać się jak ostatnia część klucza.",
        )
        source.write_text("second", encoding="utf-8")
        storage.upload_file(source, "data/data.parquet")
        third = storage.fetch("data/data.parquet")
        expect(
            third.read_text(encoding="utf-8") == "second"
            and first.read_text(encoding="utf-8") == "first",
            "Po podmianie obiektu fetch ma zwrócić nową treść i nie nadpisywać starej kopii.",
        )
        _raises(
            lambda: storage.fetch("missing.txt"),
            FileNotFoundError,
            "klucza nie ma w buckecie",
        )
        _raises(
            lambda: storage.fetch("../escape.txt"),
            ValueError,
            "klucz wychodzi poza cache ('..')",
        )
        plain = s3.S3Storage(client, BUCKET)
        _raises(
            lambda: plain.fetch("data/data.parquet"),
            RuntimeError,
            "serwis nie ma cache_dir",
        )


def _model_dir(root: Path) -> Path:
    directory = root / "local" / "lightgbm_20240625-143005"
    (directory / "extra").mkdir(parents=True)
    (directory / "model.joblib").write_bytes(b"model")
    (directory / "metadata.json").write_text("{}", encoding="utf-8")
    (directory / "extra" / "backtest.csv").write_text("a\n1\n", encoding="utf-8")
    return directory


@task("15.5", "publish_model i fetch_model, publikacja w pipeline")
def check_publish(_target: object) -> None:
    from freshcast.storage import s3

    with _fake_s3() as client, tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        storage = s3.S3Storage(client, BUCKET, sleep=lambda _: None)
        uploaded: list[str] = []
        original = storage.upload_file

        def recording(path: Path, key: str) -> None:
            uploaded.append(key)
            original(path, key)

        storage.upload_file = recording  # type: ignore[method-assign]
        base = s3.publish_model(storage, _model_dir(root), "/models/")
        expect(
            base == "models/lightgbm_20240625-143005",
            f"publish_model ma zwrócić prefiks 'models/<sygnatura>'. Dostałem {base!r}.",
        )
        expect(
            sorted(uploaded)
            == [
                f"{base}/extra/backtest.csv",
                f"{base}/metadata.json",
                f"{base}/model.joblib",
            ]
            and uploaded[-1] == f"{base}/metadata.json",
            "Wszystkie pliki katalogu (także w podkatalogach) mają trafić pod prefiks, "
            f"a metadata.json na końcu. Kolejność wysyłki: {uploaded}.",
        )
        _raises(
            lambda: s3.publish_model(storage, _model_dir(root / "again"), "models"),
            FileExistsError,
            "model o tej sygnaturze jest już opublikowany",
        )
        fetched = s3.fetch_model(
            storage, "lightgbm_20240625-143005", root / "download", "models"
        )
        expect(
            fetched == root / "download" / "lightgbm_20240625-143005"
            and (fetched / "extra" / "backtest.csv").read_text(encoding="utf-8")
            == "a\n1\n",
            "fetch_model ma odtworzyć katalog modelu z podkatalogami pod target_dir/<sygnatura>.",
        )
        _raises(
            lambda: s3.fetch_model(
                storage, "lightgbm_20240625-143005", root / "download", "models"
            ),
            FileExistsError,
            "katalog docelowy już istnieje",
        )
        _raises(
            lambda: s3.fetch_model(
                storage, "lightgbm_20240625", root / "other", "models"
            ),
            FileNotFoundError,
            "pod tą sygnaturą nie ma kompletnego modelu",
        )

        from freshcast import config, pipeline

        raw = pd.read_parquet(SAMPLE)
        raw[raw["dt"] <= "2024-06-18"].to_parquet(root / "train.parquet", index=False)
        settings = config.Settings(
            data=config.DataSettings(
                train_file=root / "train.parquet", processed_dir=root / "p"
            ),
            model=config.ModelSettings(rounds=20, params={"min_child_samples": 5}),
            backtest=config.BacktestSettings(folds=1),
            storage=config.StorageSettings(bucket=BUCKET, prefix="runs"),
            artifacts_dir=root / "artifacts",
        )
        result = pipeline.train(settings)
        expect(
            s3.S3Storage(client, BUCKET).exists(
                f"runs/{result.model_dir.name}/metadata.json"
            ),
            "Gdy ustawienia mają sekcję storage, train ma opublikować model w buckecie pod runs/<sygnatura>/.",
        )


@task("15.6", "testy serwisu S3 wykrywają celowo zepsuty kod")
def check_storage_tests(_target: object) -> None:
    from freshcast.storage import s3

    with _fake_s3() as client:
        s3.S3Storage(client, BUCKET).exists("x")  # not implemented yet -> todo
    check_tests(TESTS, "s3", 6)


@contextlib.contextmanager
def _warehouse() -> Iterator[tuple[Any, Path, Path, Path, pd.DataFrame]]:
    """Parquet files of the sample: daily facts and the two dimensions."""
    import duckdb

    from freshcast.data.dims import build_product_dim, build_store_dim
    from freshcast.data.load import load_sales
    from freshcast.data.prepare import prepare_daily
    from freshcast.data.schema import DATE, HIERARCHY, SERIES_KEY

    daily = prepare_daily(SAMPLE)
    hierarchy = load_sales(SAMPLE, columns=[*SERIES_KEY, DATE, *HIERARCHY])
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        daily.to_parquet(root / "daily.parquet", index=False)
        build_store_dim(daily).to_parquet(root / "stores.parquet", index=False)
        build_product_dim(hierarchy).to_parquet(root / "products.parquet", index=False)
        with duckdb.connect() as con:
            yield (
                con,
                root / "daily.parquet",
                root / "stores.parquet",
                root / "products.parquet",
                daily,
            )


@task("15.7", "SQL: filtr, grupowanie, złączenia z wymiarami")
def check_sql_basics(_target: object) -> None:
    from freshcast.data.dims import build_store_dim
    from freshcast.storage import sql

    with _warehouse() as (con, daily_file, stores, products, daily):
        rows = sql.city_sales(con, daily_file, 3, date(2024, 4, 1), date(2024, 4, 7))
        expect(
            list(rows.columns)
            == ["store_id", "product_id", "dt", "sale_amount", "oos_hours"]
            and len(rows) == 6 * 7,
            f"Miasto 3 ma w próbce 6 serii, więc tydzień to 42 wiersze. Dostałem {len(rows)}.",
        )
        _raises(
            lambda: sql.city_sales(
                con, daily_file, 3, date(2024, 4, 7), date(2024, 4, 1)
            ),
            ValueError,
            "end jest przed start",
        )
        summary = sql.store_summary(con, daily_file)
        try:
            pd.testing.assert_frame_equal(
                summary, build_store_dim(daily), check_dtype=False
            )
        except AssertionError as error:
            raise CheckFailed(
                "store_summary ma dać to samo co build_store_dim z modułu 07. "
                f"Różnica: {str(error).splitlines()[0]}"
            ) from error
        by_category = sql.category_sales(
            con, daily_file, stores, products, min_products=2
        )
        expect(
            list(by_category.columns)
            == ["first_category_id", "n_series", "total_sales", "mean_sales"]
            and int(by_category["n_series"].sum()) == 7,
            "Sklepy z co najmniej 2 produktami to w próbce 70 (5 serii) i 293 (2 serie): "
            f"razem 7 serii w kategoriach. Dostałem {int(by_category['n_series'].sum())}.",
        )
        expect(
            bool(by_category["total_sales"].is_monotonic_decreasing),
            "Wynik ma być posortowany malejąco po total_sales.",
        )
        pd.read_parquet(products).iloc[1:].to_parquet(products, index=False)
        _raises(
            lambda: sql.category_sales(
                con, daily_file, stores, products, min_products=1
            ),
            ValueError,
            "w wymiarze produktu brakuje produktu obecnego w faktach",
        )


@task("15.8", "SQL: funkcje okna zamiast groupby, shift i rolling")
def check_sql_windows(_target: object) -> None:
    from freshcast.data.panel import add_lag, add_rolling_mean
    from freshcast.storage import sql

    with _warehouse() as (con, daily_file, _stores, _products, daily):
        top = sql.top_products_per_store(con, daily_file, top=2)
        expect(
            list(top.columns)
            == ["store_id", "product_id", "total_sales", "rank_in_store"]
            and top.groupby("store_id").size().tolist() == [2, 1, 2],
            "Dla top=2 sklep 70 ma 2 produkty w wyniku, sklep 107 (1 produkt) jeden, sklep 293 dwa.",
        )
        expect(
            top["rank_in_store"].tolist()[:2] == [1, 2]
            and bool(top.iloc[0]["total_sales"] >= top.iloc[1]["total_sales"]),
            "Ranga 1 to produkt o największej sprzedaży w sklepie.",
        )
        _raises(
            lambda: sql.top_products_per_store(con, daily_file, top=0),
            ValueError,
            "top wynosi 0",
        )

        lagged = sql.sales_lag(con, daily_file, 7)
        wanted = add_lag(daily, "sale_amount", 7)["sale_amount_lag_7"].to_numpy()
        expect(
            bool(
                np.allclose(
                    lagged["sale_amount_lag_7"].to_numpy(dtype=float),
                    wanted,
                    equal_nan=True,
                )
            ),
            "sales_lag ma dać te same wartości co add_lag z modułu 07, z NaN na początku każdej serii.",
        )
        rolled = sql.rolling_mean_7(con, daily_file)
        wanted = add_rolling_mean(daily, "sale_amount", 7)[
            "sale_amount_mean_7_lag_1"
        ].to_numpy()
        expect(
            bool(
                np.allclose(
                    rolled["sale_amount_mean_7_lag_1"].to_numpy(dtype=float),
                    wanted,
                    equal_nan=True,
                )
            ),
            "rolling_mean_7 ma dać to samo co add_rolling_mean(window=7, lag=1): bez dnia "
            "bieżącego i NaN, gdy wcześniejszych dni jest mniej niż 7.",
        )
