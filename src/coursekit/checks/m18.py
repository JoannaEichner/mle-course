"""Checks for module 18: neural forecasting with PyTorch and Lightning.

They run on the CPU in a few seconds, on tiny synthetic panels, so they
pass on a machine without a GPU. Training on the GPU is the lab's job.
"""

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from coursekit.checking import CheckFailed, expect, task


def _torch() -> Any:
    try:
        import torch
    except ImportError as error:
        raise CheckFailed(
            "Brakuje PyTorch. Moduł 18 wymaga grupy zależności neural: "
            "uruchom `uv sync --group neural`."
        ) from error
    return torch


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


def _toy_panel(series: int = 4, days: int = 60, seed: int = 5) -> pd.DataFrame:
    """A panel with every channel the GRU forecaster reads, and a weekly rhythm."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-04-01", periods=days)
    frames = []
    for number in range(series):
        weekday = dates.dayofweek.to_numpy()
        level = 1.0 + number
        frames.append(
            pd.DataFrame(
                {
                    "store_id": number // 2,
                    "product_id": number % 2,
                    "dt": dates,
                    "sale_amount": level * (1 + 0.5 * (weekday >= 5))
                    + rng.normal(0, 0.05, days),
                    "discount_filled": 1.0,
                    "zero_discount": 0,
                    "activity_flag": 0,
                    "holiday_flag": (weekday >= 5).astype(int),
                    "dow_sin": np.sin(2 * np.pi * weekday / 7),
                    "dow_cos": np.cos(2 * np.pi * weekday / 7),
                    "oos_hours": rng.choice([0, 0, 0, 4], days),
                    "avg_temperature": 20.0,
                    "precpt": 1.0,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


@task("18.1", "pick_device i seed_everything")
def check_device(_target: object) -> None:
    torch = _torch()
    from freshcast.neural import device

    expect(
        device.pick_device(prefer_gpu=False).type == "cpu",
        "pick_device(prefer_gpu=False) ma zwrócić CPU.",
    )
    wanted = "cuda" if torch.cuda.is_available() else "cpu"
    got = device.pick_device(prefer_gpu=True).type
    expect(
        got == wanted,
        f"Na tej maszynie pick_device(prefer_gpu=True) powinno wybrać {wanted}, "
        f"a wybrało {got}.",
    )
    device.seed_everything(7)
    first = (torch.rand(3).tolist(), np.random.rand(3).tolist())  # noqa: NPY002
    device.seed_everything(7)
    second = (torch.rand(3).tolist(), np.random.rand(3).tolist())  # noqa: NPY002
    expect(
        first == second,
        "Po ponownym seed_everything(7) losowania PyTorch i NumPy mają się powtórzyć.",
    )


@task("18.2", "panel_cube: panel jako tablica (serie, dni, kanały)")
def check_cube(_target: object) -> None:
    from freshcast.neural import windows

    panel = _toy_panel(series=3, days=10)
    cube = windows.panel_cube(panel, ["sale_amount", "holiday_flag"])
    expect(
        cube.data.shape == (3, 10, 2) and cube.stockout_hours.shape == (3, 10),
        "Dla 3 serii po 10 dni i 2 kanałów kostka ma kształt (3, 10, 2), a "
        f"godziny braków (3, 10). Dostałem {cube.data.shape} i "
        f"{cube.stockout_hours.shape}.",
    )
    expect(
        cube.data.dtype == np.float32
        and bool(np.allclose(cube.data[1, :, 0], panel["sale_amount"].iloc[10:20])),
        "Kostka ma być typu float32, a cube.data[1, :, 0] to sprzedaż drugiej serii.",
    )
    expect(
        list(cube.keys.columns) == ["store_id", "product_id"] and len(cube.keys) == 3,
        "keys ma zawierać po jednym wierszu (store_id, product_id) na serię.",
    )
    expect(
        len(cube.dates) == 10 and cube.channels == ["sale_amount", "holiday_flag"],
        "dates ma mieć 10 dni, a channels nazwy kanałów w podanej kolejności.",
    )
    _raises(
        lambda: windows.panel_cube(
            panel.sample(frac=1.0, random_state=1), ["sale_amount"]
        ),
        ValueError,
        "panel nie jest posortowany",
    )
    _raises(
        lambda: windows.panel_cube(
            panel.drop(index=3).reset_index(drop=True), ["sale_amount"]
        ),
        ValueError,
        "jednej serii brakuje dnia",
    )


def _dataset(starts: list[int] | None = None) -> Any:
    from freshcast.neural import windows

    panel = _toy_panel(series=2, days=20)
    channels = ["sale_amount", "holiday_flag", "dow_sin"]
    cube = windows.panel_cube(panel, channels)
    spec = windows.WindowSpec(
        past=5, horizon=3, past_channels=channels, future_channels=["holiday_flag"]
    )
    pairs = [(series, start) for series in (0, 1) for start in (starts or [0, 4])]
    return windows.WindowDataset(cube, spec, pairs), cube, spec


@task("18.3", "WindowDataset: okna historii i horyzontu jako tensory")
def check_windows(_target: object) -> None:
    _torch()
    from freshcast.neural import windows

    dataset, cube, spec = _dataset()
    expect(len(dataset) == 4, f"Zbiór z 4 oknami ma mieć długość 4. Ma {len(dataset)}.")
    batch = dataset.__getitems__([0, 3])
    shapes = {name: tuple(tensor.shape) for name, tensor in batch.items()}
    wanted = {
        "past": (2, 5, 3),
        "future": (2, 3, 1),
        "target": (2, 3),
        "in_stock": (2, 3),
        "scale": (2,),
        "series": (2,),
    }
    expect(
        shapes == wanted,
        f"Kształty tensorów partii dwóch okien mają być {wanted}. Dostałem {shapes}.",
    )
    history = cube.data[1, 4:9, 0]
    expect(
        bool(np.isclose(batch["scale"][1], history.mean(), atol=1e-5))
        and bool(
            np.allclose(batch["past"][1, :, 0], history / history.mean(), atol=1e-5)
        ),
        "Sprzedaż w oknie historii ma być podzielona przez jej średnią w tym "
        "oknie, a scale ma przechowywać tę średnią.",
    )
    expect(
        bool(np.allclose(batch["target"][1], cube.data[1, 9:12, 0], atol=1e-6)),
        "target to sprzedaż 3 dni po oknie historii, w oryginalnych jednostkach.",
    )
    expect(
        bool(
            np.array_equal(
                batch["in_stock"][1],
                (cube.stockout_hours[1, 9:12] == 0).astype(np.float32),
            )
        ),
        "in_stock ma wynosić 1 w dniach horyzontu bez godzin braku i 0 w pozostałych.",
    )
    single = dataset[0]
    expect(
        tuple(single["past"].shape) == (5, 3),
        "dataset[i] ma zwrócić jedno okno, bez osi partii.",
    )
    _raises(
        lambda: windows.WindowDataset(cube, spec, [(0, 15)]),
        ValueError,
        "okno wychodzi poza koniec danych",
    )
    wrong = windows.WindowSpec(5, 3, ["holiday_flag", "sale_amount"], ["holiday_flag"])
    _raises(
        lambda: windows.WindowDataset(cube, wrong, [(0, 0)]),
        ValueError,
        "pierwszym kanałem historii nie jest sprzedaż",
    )


@task("18.4", "GRUForecastNet: GRU czyta historię, głowica pisze tydzień")
def check_network(_target: object) -> None:
    torch = _torch()
    from freshcast.neural import gru

    torch.manual_seed(0)
    net = gru.GRUForecastNet(3, 1, horizon=7, n_stores=2, n_products=3, hidden=8)
    past, future = torch.randn(4, 28, 3), torch.randn(4, 7, 1)
    stores, products = torch.tensor([0, 1, 0, 1]), torch.tensor([0, 1, 2, 0])
    out = net(past, future, stores, products)
    expect(
        tuple(out.shape) == (4, 7),
        "Dla partii 4 okien i horyzontu 7 wynik ma kształt (4, 7). "
        f"Dostałem {tuple(out.shape)}.",
    )
    other = net(past, future, 1 - stores, products)
    expect(
        not torch.allclose(out, other),
        "Zmiana kodu sklepu nie zmienia prognozy, więc embedding sklepu nie "
        "trafia do głowicy.",
    )
    shifted = net(past, future + 1.0, stores, products)
    expect(
        not torch.allclose(out, shifted),
        "Zmiana cech dni prognozowanych nie zmienia prognozy, więc future nie "
        "trafia do głowicy.",
    )


@task("18.5", "masked_mae, fit_windows, predict_windows: pętla treningowa")
def check_training(_target: object) -> None:
    torch = _torch()
    from freshcast.neural import gru, training

    forecast = torch.tensor([[1.0, 2.0, 3.0]])
    target = torch.tensor([[2.0, 2.0, 7.0]])
    loss = training.masked_mae(forecast, target, torch.tensor([[1.0, 1.0, 0.0]]))
    expect(
        bool(torch.isclose(loss, torch.tensor(0.5))),
        "Strata liczy się tylko z dni w stanie: błędy 1 i 0 dają 0.5, a dzień "
        f"z brakiem towaru (błąd 4) jest pominięty. Dostałem {float(loss):.3f}.",
    )
    _raises(
        lambda: training.masked_mae(forecast, target, torch.zeros(1, 3)),
        ValueError,
        "w partii nie ma ani jednego dnia w stanie",
    )

    dataset, cube, spec = _dataset(starts=list(range(0, 10)))
    valid, _, _ = _dataset(starts=[11, 12])
    codes = (torch.tensor([0, 1]), torch.tensor([0, 0]))
    cpu = torch.device("cpu")
    torch.manual_seed(0)
    net = gru.GRUForecastNet(3, 1, horizon=3, n_stores=2, n_products=1, hidden=8)
    before = training.evaluate_windows(net, valid, codes, device=cpu)
    log = training.fit_windows(
        net, dataset, valid, codes, device=cpu, epochs=30, batch_size=8, patience=5
    )
    after = training.evaluate_windows(net, valid, codes, device=cpu)
    expect(
        after < before and len(log.valid_loss) >= 1,
        "Po treningu błąd walidacyjny ma być niższy niż przed nim. Przed: "
        f"{before:.3f}, po: {after:.3f}.",
    )
    expect(
        0 <= log.best_epoch < len(log.valid_loss)
        and bool(np.isclose(after, min(log.valid_loss), rtol=1e-4)),
        "Po treningu w sieci mają zostać wagi najlepszej epoki: błąd walidacyjny "
        "sieci ma równać się najmniejszemu w historii.",
    )
    log = training.fit_windows(
        net, dataset, None, codes, device=cpu, epochs=2, batch_size=8
    )
    expect(
        len(log.train_loss) == 2 and not log.valid_loss,
        "Bez zbioru walidacyjnego fit_windows ma przejść dokładnie `epochs` epok.",
    )
    predicted = training.predict_windows(net, valid, codes, device=cpu)
    expect(
        isinstance(predicted, np.ndarray)
        and predicted.shape == (4, 3)
        and float(predicted.min()) >= 0,
        "predict_windows ma zwrócić tablicę (liczba okien, horyzont) bez "
        "wartości ujemnych.",
    )


@task("18.6", "GRUForecaster: sieć w tym samym backteście co LightGBM")
def check_forecaster(_target: object) -> None:
    _torch()
    from freshcast.models import neural

    panel = _toy_panel(series=4, days=60)
    history, future = (
        panel[panel["dt"] < "2024-05-24"],
        panel[panel["dt"] >= "2024-05-24"],
    )
    model = neural.GRUForecaster(
        past=14, horizon=7, epochs=3, batch_size=16, prefer_gpu=False
    )
    _raises(
        lambda: model.predict(future), RuntimeError, "predict jest wołany przed fit"
    )
    model.fit(history, history["sale_amount"])
    shuffled = future.sample(frac=1.0, random_state=2)
    got = model.predict(shuffled)
    expect(
        isinstance(got, np.ndarray)
        and got.shape == (len(future),)
        and bool(np.isfinite(got).all()),
        "predict ma zwrócić jedną skończoną prognozę na wiersz X.",
    )
    ordered = pd.Series(got, index=shuffled.index).sort_index().to_numpy()
    again = model.predict(future.assign(sale_amount=999.0, oos_hours=16))
    expect(
        bool(np.allclose(ordered, again, atol=1e-5)),
        "Prognoza nie może zależeć od kolejności wierszy X ani od sprzedaży "
        "i braków zapisanych w wierszach przyszłości.",
    )
    _raises(
        lambda: model.predict(future.iloc[:-4]),
        ValueError,
        "X nie zawiera pełnych 7 dni dla każdej serii",
    )


@task("18.7", "WindowModule i fit_with_lightning: to samo w Lightning")
def check_lightning(_target: object) -> None:
    torch = _torch()
    from freshcast.neural import gru, lightning

    dataset, _, _ = _dataset(starts=list(range(0, 10)))
    valid, _, _ = _dataset(starts=[11, 12])
    torch.manual_seed(0)
    net = gru.GRUForecastNet(3, 1, horizon=3, n_stores=2, n_products=1, hidden=8)
    module = lightning.WindowModule(net, (torch.tensor([0, 1]), torch.tensor([0, 0])))
    batch = dataset.__getitems__([0, 1, 2])
    loss = module.training_step(batch, 0)
    expect(
        isinstance(loss, torch.Tensor) and loss.ndim == 0 and loss.requires_grad,
        "training_step ma zwrócić skalarny tensor straty z gradientem.",
    )
    with tempfile.TemporaryDirectory() as scratch:
        trained, score = lightning.fit_with_lightning(
            module,
            dataset,
            valid,
            checkpoint_dir=Path(scratch),
            max_epochs=2,
            batch_size=8,
        )
        saved = list(Path(scratch).glob("*.ckpt"))
    expect(
        isinstance(score, float) and np.isfinite(score) and len(saved) == 1,
        "fit_with_lightning ma zwrócić najlepszy błąd walidacyjny jako float i "
        "zostawić jeden checkpoint najlepszej epoki.",
    )
    expect(
        trained is module,
        "fit_with_lightning ma zwrócić ten sam moduł z wagami najlepszej epoki.",
    )
