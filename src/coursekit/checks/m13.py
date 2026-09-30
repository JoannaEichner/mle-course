"""Checks for module 13: series segments with k-means and PCA, a first MLP."""

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from coursekit.checking import CheckFailed, expect, task

KEY = ["store_id", "product_id"]
PROFILE_COLUMNS = [
    "log_mean_sales",
    "cv",
    "weekend_uplift",
    "discounted_share",
    "stockout_rate",
    "zero_share",
]


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


def _week(store: int, sales: list[float], **columns: list[float]) -> pd.DataFrame:
    """One series over Monday 2024-04-01 to Sunday 2024-04-07."""
    days = len(sales)
    return pd.DataFrame(
        {
            "store_id": store,
            "product_id": 7,
            "dt": pd.date_range("2024-04-01", periods=days),
            "sale_amount": sales,
            "discount": columns.get("discount", [1.0] * days),
            "oos_hours": columns.get("oos_hours", [0] * days),
        }
    )


def _panel() -> pd.DataFrame:
    """Two series, rows shuffled. Their profiles are worked out in the check."""
    first = _week(
        1,
        [0.0, 1.0, 1.0, 1.0, 1.0, 4.0, 6.0],
        discount=[1.0, 1.0, 0.8, 0.8, np.nan, 1.0, 0.5],
        oos_hours=[0, 0, 8, 0, 0, 0, 8],
    )
    second = _week(2, [3.0] * 7)
    return pd.concat([first, second], ignore_index=True).sample(
        frac=1.0, random_state=13
    )


@task("13.1", "series_profile: sześć liczb opisujących zachowanie serii")
def check_profile(_target: object) -> None:
    from freshcast import segments

    panel = _panel()
    before = panel.copy()
    profile = segments.series_profile(panel)
    expect(
        panel.equals(before),
        "series_profile zmieniła ramkę wejściową. Funkcja ma zwracać nową ramkę.",
    )
    expect(
        list(profile.columns) == PROFILE_COLUMNS and len(profile) == 2,
        f"series_profile ma zwrócić po jednym wierszu na serię i kolumny "
        f"{PROFILE_COLUMNS}. Dostałem {len(profile)} wierszy i kolumny "
        f"{list(profile.columns)}.",
    )
    expect(
        list(profile.index.names) == KEY and profile.index.tolist() == [(1, 7), (2, 7)],
        "Indeks wyniku to klucz serii (store_id, product_id), posortowany "
        f"rosnąco. Dostałem {profile.index.tolist()} z nazwami "
        f"{list(profile.index.names)}.",
    )

    # Series 1 sells 0, 1, 1, 1, 1 from Monday to Friday, then 4 and 6.
    wanted = {
        "log_mean_sales": (np.log(2.0), "średnia sprzedaż to 2, więc ln 2"),
        "cv": (
            1.0,
            "odchylenie populacyjne (ddof=0) wynosi 2, średnia też 2",
        ),
        "weekend_uplift": (
            1.5,
            "średnia z soboty i niedzieli to 5, średnia wszystkich dni 2",
        ),
        "discounted_share": (
            3 / 7,
            "rabat poniżej 1 ma 3 dni z 7, a dzień bez rabatu w danych (NaN) "
            "nie liczy się jako rabat",
        ),
        "stockout_rate": (
            1 / 7,
            "średnio 16/7 godziny braku na dobę, z 16 godzin okna",
        ),
        "zero_share": (1 / 7, "jeden dzień z 7 bez sprzedaży"),
    }
    for name, (value, reason) in wanted.items():
        got = float(profile[name].iloc[0])
        expect(
            bool(np.isclose(got, value, atol=1e-6)),
            f"{name} serii (1, 7) powinno wynosić {value:.4f} ({reason}). "
            f"Dostałem {got:.4f}.",
        )
    flat = profile.iloc[1]
    expect(
        bool(np.isclose(flat["log_mean_sales"], np.log(3.0)))
        and bool(np.allclose(flat[PROFILE_COLUMNS[1:]].to_numpy(dtype=float), 0.0)),
        "Seria (2, 7) sprzedaje codziennie 3, bez rabatu i braków towaru. "
        "Jej profil to ln 3 i same zera. Dostałem "
        f"{flat.round(4).to_dict()}. Liczby jednej serii nie mogą zależeć "
        "od drugiej.",
    )

    silent = pd.concat([panel, _week(3, [0.0] * 7)], ignore_index=True)
    _raises(
        lambda: segments.series_profile(silent),
        ValueError,
        "seria nie ma ani jednej sprzedaży",
    )
    weekdays = pd.concat([panel, _week(4, [1.0] * 5)], ignore_index=True)
    _raises(
        lambda: segments.series_profile(weekdays),
        ValueError,
        "seria ma tylko dni robocze",
    )


def _is_constant(labels: pd.Series) -> bool:
    return bool((labels == labels.iloc[0]).all())


def _blobs(per_blob: int = 20, seed: int = 13) -> pd.DataFrame:
    """Three tight groups far apart, in a frame with a non-default index."""
    rng = np.random.default_rng(seed)
    centres = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 10.0]])
    points = np.vstack([c + rng.normal(0, 0.3, (per_blob, 2)) for c in centres])
    return pd.DataFrame(
        points, columns=["a", "b"], index=range(100, 100 + 3 * per_blob)
    )


@task("13.2", "standardise i fit_segments: skalowanie i k-means z ziarnem")
def check_segments(_target: object) -> None:
    from freshcast import segments

    frame = pd.DataFrame({"a": [1.0, 3.0, 5.0], "const": [10.0, 10.0, 10.0]})
    before = frame.copy()
    scaled, scaler = segments.standardise(frame)
    expect(frame.equals(before), "standardise zmieniła ramkę wejściową.")
    root = np.sqrt(1.5)
    expect(
        isinstance(scaled, np.ndarray)
        and scaled.shape == (3, 2)
        and bool(np.allclose(scaled, [[-root, 0.0], [0.0, 0.0], [root, 0.0]])),
        "Kolumna [1, 3, 5] ma średnią 3 i odchylenie populacyjne sqrt(8/3), "
        f"więc po skalowaniu to [-1.2247, 0, 1.2247]. Kolumna stała ma dać "
        f"same zera, nie NaN. Dostałem {np.round(scaled, 4).tolist()}.",
    )
    again = scaler.transform(np.array([[5.0, 10.0]]))
    expect(
        bool(np.allclose(again, [[root, 0.0]])),
        "Zwrócony scaler ma być dopasowany do tych wierszy: wiersz [5, 10] "
        f"powinien dać [1.2247, 0]. Dostałem {np.round(again, 4).tolist()}.",
    )
    _raises(
        lambda: segments.standardise(frame.assign(a=[1.0, np.nan, 5.0])),
        ValueError,
        "w danych jest NaN",
    )
    _raises(
        lambda: segments.standardise(frame.assign(a=[1.0, np.inf, 5.0])),
        ValueError,
        "w danych jest nieskończoność",
    )
    _raises(
        lambda: segments.standardise(frame.iloc[:0]),
        ValueError,
        "nie ma ani jednego wiersza",
    )

    blobs = _blobs()
    blobs_before = blobs.copy()
    result = segments.fit_segments(blobs, 3, seed=1)
    expect(blobs.equals(blobs_before), "fit_segments zmieniła ramkę wejściową.")
    labels = result.labels
    expect(
        isinstance(labels, pd.Series)
        and labels.index.equals(blobs.index)
        and labels.name == "segment",
        "labels ma być Series o nazwie 'segment' z indeksem profilu "
        f"(tu 100..159). Dostałem nazwę {getattr(labels, 'name', None)!r}.",
    )
    groups = [labels.iloc[i * 20 : (i + 1) * 20] for i in range(3)]
    expect(
        all(_is_constant(g) for g in groups)
        and len({int(g.iloc[0]) for g in groups}) == 3,
        "Trzy odległe grupy po 20 punktów mają dać trzy segmenty, po jednym na "
        f"grupę. Dostałem etykiety {[sorted(set(g)) for g in groups]}.",
    )
    expect(
        result.kmeans.cluster_centers_.shape == (3, 2),
        "kmeans ma być dopasowanym obiektem KMeans z 3 centrami.",
    )
    repeat = segments.fit_segments(blobs, 3, seed=1)
    expect(
        repeat.labels.equals(labels),
        "To samo wejście, k i seed mają dawać te same etykiety. Dwa wywołania "
        "dały różne.",
    )

    rng = np.random.default_rng(5)
    mixed = pd.DataFrame(
        {
            "signal": np.repeat([0.0, 10.0], 40) + rng.normal(0, 0.3, 80),
            "noise_in_thousands": rng.normal(0, 1000.0, 80),
        }
    )
    halves = segments.fit_segments(mixed, 2, seed=0).labels
    expect(
        _is_constant(halves.iloc[:40])
        and _is_constant(halves.iloc[40:])
        and halves.iloc[0] != halves.iloc[40],
        "Kolumna signal rozdziela dwie grupy po 40 wierszy, a druga kolumna to "
        "szum w tysiącach. Po skalowaniu k-means ma znaleźć te grupy. "
        "Bez skalowania o wyniku decyduje szum.",
    )

    _raises(
        lambda: segments.fit_segments(blobs, 1),
        ValueError,
        "k wynosi 1",
    )
    _raises(
        lambda: segments.fit_segments(blobs.head(5), 6),
        ValueError,
        "k jest większe niż liczba wierszy",
    )
    _raises(
        lambda: segments.fit_segments(blobs.assign(a=np.nan), 3),
        ValueError,
        "profil ma NaN",
    )


@task("13.3", "inertia_by_k i silhouette_by_k: dowody przy wyborze k")
def check_choose_k(_target: object) -> None:
    from freshcast import segments

    line = np.array([[0.0], [1.0], [10.0], [11.0]])
    inertia = segments.inertia_by_k(line, [1, 2, 4])
    expect(
        isinstance(inertia, pd.Series)
        and inertia.index.tolist() == [1, 2, 4]
        and inertia.name == "inertia",
        "inertia_by_k ma zwrócić Series o nazwie 'inertia' z indeksem k, "
        "w kolejności podanej w ks.",
    )
    expect(
        bool(np.allclose(inertia.to_numpy(), [101.0, 1.0, 0.0])),
        "Punkty 0, 1, 10, 11: dla k=1 inercja to 101 (kwadraty odległości od "
        "średniej 5.5), dla k=2 to 1 (grupy {0, 1} i {10, 11}), dla k=4 to 0. "
        f"Dostałem {inertia.round(4).tolist()}.",
    )
    backwards = segments.inertia_by_k(line, [4, 1])
    expect(
        backwards.index.tolist() == [4, 1]
        and bool(np.allclose(backwards.to_numpy(), [0.0, 101.0])),
        "Wynik ma iść w kolejności ks. Dla [4, 1] oczekiwano inercji [0, 101]. "
        f"Dostałem {backwards.round(4).tolist()}.",
    )
    _raises(lambda: segments.inertia_by_k(line, [0]), ValueError, "k wynosi 0")
    _raises(
        lambda: segments.inertia_by_k(line, [5]),
        ValueError,
        "k jest większe niż liczba punktów",
    )

    silhouette = segments.silhouette_by_k(line, [2])
    expect(
        isinstance(silhouette, pd.Series)
        and silhouette.index.tolist() == [2]
        and silhouette.name == "silhouette",
        "silhouette_by_k ma zwrócić Series o nazwie 'silhouette' z indeksem k.",
    )
    expect(
        bool(np.isclose(silhouette.iloc[0], 0.899749, atol=1e-5)),
        "Punkty 0, 1, 10, 11 w dwóch grupach: punkt 0 ma a=1 i b=10.5, punkt 1 "
        "ma a=1 i b=9.5, reszta symetrycznie. Średnia sylwetka to 0.89975. "
        f"Dostałem {silhouette.iloc[0]:.5f}.",
    )
    _raises(
        lambda: segments.silhouette_by_k(line, [1]),
        ValueError,
        "k wynosi 1 (sylwetka nie ma wtedy z czym porównywać)",
    )
    _raises(
        lambda: segments.silhouette_by_k(line, [4]),
        ValueError,
        "k równa się liczbie punktów",
    )

    blobs = _blobs().to_numpy()
    ks = [2, 3, 4, 5]
    scores = segments.silhouette_by_k(blobs, ks)
    expect(
        ks[int(np.argmax(scores.to_numpy()))] == 3 and float(scores.max()) > 0.8,
        "Trzy wyraźnie odległe grupy: sylwetka ma być największa dla k=3 i "
        f"powyżej 0.8. Dostałem {scores.round(3).to_dict()}.",
    )
    curve = segments.inertia_by_k(blobs, ks)
    drops = -curve.diff().dropna()
    expect(
        bool((drops >= 0).all()) and float(drops.iloc[0]) > 50 * float(drops.iloc[1]),
        "Inercja trzech grup ma spadać ostro do k=3 i potem prawie płasko. "
        f"Dostałem {curve.round(1).to_dict()}.",
    )


def _hours(**hours: float) -> list[float]:
    """A day of 24 hourly sales, zero except the hours given as ``h08=2.0``."""
    day = [0.0] * 24
    for name, value in hours.items():
        day[int(name[1:])] = value
    return day


@task("13.4", "hour_profiles i project_2d: PCA na profilach godzinowych")
def check_projection(_target: object) -> None:
    from freshcast import segments

    hourly = pd.DataFrame(
        {
            "store_id": [2, 1, 2, 1],
            "product_id": [7, 7, 7, 7],
            "dt": pd.to_datetime(
                ["2024-04-01", "2024-04-01", "2024-04-02", "2024-04-02"]
            ),
            "hours_sale": [
                _hours(h18=3.0),
                _hours(h08=1.0, h09=3.0),
                _hours(h19=1.0),
                _hours(h08=2.0),
            ],
        }
    )
    before = hourly.copy()
    profiles = segments.hour_profiles(hourly)
    expect(
        hourly["store_id"].tolist() == [2, 1, 2, 1]
        and list(hourly.columns) == list(before.columns),
        "hour_profiles zmieniła ramkę wejściową (kolejność wierszy albo kolumny).",
    )
    expect(
        profiles.shape == (2, 24)
        and list(profiles.columns)[:3] == ["h00", "h01", "h02"]
        and profiles.columns[-1] == "h23"
        and profiles.index.tolist() == [(1, 7), (2, 7)]
        and list(profiles.index.names) == KEY,
        "hour_profiles ma zwrócić po wierszu na serię (posortowane po kluczu, "
        "indeks store_id i product_id) i 24 kolumny h00..h23. Dostałem "
        f"kształt {profiles.shape} i indeks {profiles.index.tolist()}.",
    )
    expect(
        bool(np.allclose(profiles.sum(axis=1), 1.0)),
        "Każdy wiersz profilu godzinowego ma sumować się do 1.",
    )
    got = profiles[["h08", "h09"]].iloc[0].tolist()
    expect(
        bool(np.allclose(got, [0.5, 0.5])),
        "Seria (1, 7): w pierwszym dniu 1 o ósmej i 3 o dziewiątej, w drugim "
        "2 o ósmej. Sprzedaż sumuje się po dniach (3 i 3), dopiero potem "
        f"liczymy udziały: 0.5 i 0.5. Dostałem {got}.",
    )
    got = profiles[["h18", "h19"]].iloc[1].tolist()
    expect(
        bool(np.allclose(got, [0.75, 0.25])),
        f"Seria (2, 7) ma mieć udziały 0.75 o 18 i 0.25 o 19. Dostałem {got}.",
    )
    sales = hourly["hours_sale"].tolist()
    quiet = [_hours(), sales[1], _hours(), sales[3]]
    silent = hourly.assign(hours_sale=pd.Series(quiet, index=hourly.index))
    _raises(
        lambda: segments.hour_profiles(silent),
        ValueError,
        "seria (2, 7) nie ma sprzedaży w żadnej godzinie",
    )

    cross = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 2.0], [0.0, -2.0]])
    coordinates, explained = segments.project_2d(cross)
    expect(
        coordinates.shape == (4, 2) and explained.shape == (2,),
        "project_2d ma zwrócić współrzędne (n, 2) i dwa udziały wariancji. "
        f"Dostałem kształty {coordinates.shape} i {explained.shape}.",
    )
    expect(
        bool(np.allclose(explained, [0.8, 0.2])),
        "Wariancja w kolumnie y to 8/3, w kolumnie x 2/3. Pierwsza składowa "
        f"niesie więc 0.8, druga 0.2. Dostałem {np.round(explained, 4).tolist()}.",
    )
    expect(
        bool(np.allclose(np.abs(coordinates), [[0, 1], [0, 1], [2, 0], [2, 0]])),
        "Pierwsza składowa biegnie wzdłuż osi y, druga wzdłuż x. Bezwzględne "
        "współrzędne powinny wynosić [[0, 1], [0, 1], [2, 0], [2, 0]] "
        "(znak składowej jest dowolny). "
        f"Dostałem {np.round(coordinates, 3).tolist()}.",
    )
    _, shifted = segments.project_2d(cross + 100.0)
    expect(
        bool(np.allclose(shifted, explained)),
        "Przesunięcie wszystkich punktów o stałą nie zmienia rozrzutu, więc "
        "udziały wariancji mają zostać [0.8, 0.2]. "
        f"Dostałem {np.round(shifted, 4).tolist()}.",
    )
    line3 = np.array([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [3.0, 6.0, 9.0]])
    coordinates, explained = segments.project_2d(line3)
    expect(
        coordinates.shape == (3, 2) and bool(np.allclose(explained, [1.0, 0.0])),
        "Punkty na jednej prostej (3 kolumny) mają dać (n, 2) współrzędne, a "
        f"udziały [1, 0]. Dostałem {coordinates.shape} i "
        f"{np.round(explained, 4).tolist()}.",
    )
    _raises(
        lambda: segments.project_2d(np.array([[1.0], [2.0], [3.0]])),
        ValueError,
        "jest tylko jedna kolumna",
    )
    _raises(
        lambda: segments.project_2d(np.array([[1.0, 2.0]])),
        ValueError,
        "jest tylko jeden wiersz",
    )
    _raises(
        lambda: segments.project_2d(np.array([[1.0, np.nan], [2.0, 3.0], [4.0, 5.0]])),
        ValueError,
        "w macierzy jest NaN",
    )


@task("13.5", "TabularMLP: warstwy liniowe z ReLU, jedna prognoza na wiersz")
def check_network(_target: object) -> None:
    import torch

    from freshcast.models import mlp

    net = mlp.TabularMLP(3, (4, 2))
    expect(
        isinstance(net, torch.nn.Module),
        "TabularMLP ma dziedziczyć po torch.nn.Module.",
    )
    count = sum(p.numel() for p in net.parameters())
    expect(
        count == 29,
        "Sieć 3 -> 4 -> 2 -> 1 ma 29 parametrów: (3*4 + 4) + (4*2 + 2) + "
        f"(2*1 + 1). Dostałem {count}.",
    )
    linear = mlp.TabularMLP(3, ())
    count = sum(p.numel() for p in linear.parameters())
    expect(
        count == 4,
        "Bez warstw ukrytych sieć to jedna warstwa liniowa 3 -> 1, czyli 4 "
        f"parametry. Dostałem {count}.",
    )
    shape = tuple(net(torch.zeros(5, 3)).shape)
    expect(
        shape == (5,),
        "forward ma zwrócić tensor o kształcie (n,): jedna liczba na wiersz, "
        f"nie (n, 1). Dla 5 wierszy dostałem {shape}.",
    )

    # Weights set by hand: the hidden layer computes [x, -x], the output adds
    # the two and 0.5. With a ReLU in between that is |x| + 0.5.
    tiny = mlp.TabularMLP(1, (2,))
    with torch.no_grad():
        weights = list(tiny.parameters())
        weights[0].copy_(torch.tensor([[1.0], [-1.0]]))
        weights[1].zero_()
        weights[2].copy_(torch.tensor([[1.0, 1.0]]))
        weights[3].fill_(0.5)
        got = tiny(torch.tensor([[-2.0], [3.0], [0.0]])).tolist()
    expect(
        bool(np.allclose(got, [2.5, 3.5, 0.5])),
        "Sieć 1 -> 2 -> 1 z ręcznie ustawionymi wagami (parametry w kolejności "
        "warstw, każda: waga, potem wyraz wolny) ma policzyć |x| + 0.5. Dla "
        "[-2, 3, 0] to [2.5, 3.5, 0.5]. Bez ReLU po warstwie ukrytej wyszłoby "
        f"zawsze 0.5. Dostałem {np.round(got, 3).tolist()}.",
    )
    _raises(lambda: mlp.TabularMLP(0), ValueError, "n_inputs wynosi 0")
    _raises(
        lambda: mlp.TabularMLP(3, (4, 0)),
        ValueError,
        "szerokość warstwy ukrytej wynosi 0",
    )


def _toy_problem(rows: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Learnable, and not linear: a V-shape in the first column."""
    rng = np.random.default_rng(seed)
    features = rng.normal(size=(rows, 3))
    target = np.abs(features[:, 0]) + 0.5 * features[:, 1]
    return features, target + rng.normal(0, 0.05, rows)


@task("13.6", "train_mlp: mini-batche, strata walidacyjna, early stopping")
def check_training(_target: object) -> None:
    import torch

    from freshcast.models import mlp

    x_train, y_train = _toy_problem(256, seed=1)
    x_valid, y_valid = _toy_problem(64, seed=2)
    copies = [a.copy() for a in (x_train, y_train, x_valid, y_valid)]
    settings: dict[str, Any] = {
        "hidden": (16,),
        "batch_size": 32,
        "learning_rate": 0.01,
    }

    model, history = mlp.train_mlp(
        x_train, y_train, x_valid, y_valid, epochs=30, patience=30, seed=0, **settings
    )
    expect(
        isinstance(model, mlp.TabularMLP)
        and list(history.columns) == ["train_loss", "valid_loss"],
        "train_mlp ma zwrócić (model, historia). Historia to ramka z kolumnami "
        f"train_loss i valid_loss, a jest {list(getattr(history, 'columns', []))}.",
    )
    expect(
        len(history) == 30,
        "Przy patience równym liczbie epok i danych, na których strata maleje, "
        f"trening ma przejść wszystkie 30 epok. Przeszedł {len(history)}.",
    )
    expect(
        all(
            np.array_equal(a, b)
            for a, b in zip((x_train, y_train, x_valid, y_valid), copies, strict=True)
        ),
        "train_mlp zmieniła tablice wejściowe.",
    )
    first, last = history.iloc[0], history.iloc[-1]
    expect(
        bool(last["train_loss"] < 0.1 * first["train_loss"])
        and bool(last["valid_loss"] < 0.1 * first["valid_loss"]),
        "Na prostym zadaniu (V w pierwszej kolumnie plus składnik liniowy) obie "
        "straty mają spaść w 30 epokach co najmniej dziesięciokrotnie. "
        f"Pierwsza epoka: {first.round(3).to_dict()}, ostatnia: "
        f"{last.round(3).to_dict()}.",
    )
    with torch.no_grad():
        predicted = model(torch.tensor(x_valid, dtype=torch.float32)).numpy()
    error = float(np.mean((predicted - y_valid) ** 2))
    expect(
        bool(np.isclose(error, history["valid_loss"].min(), rtol=1e-3, atol=1e-6)),
        "Zwrócony model ma mieć wagi z epoki o najniższej stracie walidacyjnej "
        f"({history['valid_loss'].min():.5f}). Jego błąd średniokwadratowy na "
        f"zbiorze walidacyjnym to {error:.5f}.",
    )

    _, again = mlp.train_mlp(
        x_train, y_train, x_valid, y_valid, epochs=30, patience=30, seed=0, **settings
    )
    _, other = mlp.train_mlp(
        x_train, y_train, x_valid, y_valid, epochs=30, patience=30, seed=1, **settings
    )
    expect(
        again.equals(history),
        "Te same dane i ten sam seed mają dać tę samą historię strat.",
    )
    expect(
        not other.equals(history),
        "Inny seed ma dać inne wagi początkowe i inną kolejność batchy, a więc "
        "inną historię strat.",
    )

    _, small = mlp.train_mlp(
        x_train, y_train, x_valid, y_valid, epochs=3, patience=3, seed=0,
        hidden=(16,), batch_size=16, learning_rate=0.01,
    )  # fmt: skip
    _, whole = mlp.train_mlp(
        x_train, y_train, x_valid, y_valid, epochs=3, patience=3, seed=0,
        hidden=(16,), batch_size=256, learning_rate=0.01,
    )  # fmt: skip
    expect(
        float(small["train_loss"].iloc[-1]) < 0.5 * float(whole["train_loss"].iloc[-1]),
        "Batch 16 daje 16 kroków na epokę, batch 256 (cały zbiór) jeden. Po "
        "trzech epokach strata treningowa z mniejszym batchem ma być co "
        f"najmniej dwa razy niższa. Jest {small['train_loss'].iloc[-1]:.3f} "
        f"kontra {whole['train_loss'].iloc[-1]:.3f}.",
    )

    # Targets with no link to the inputs: the validation loss can only get
    # worse as the network memorises the 40 training rows.
    rng = np.random.default_rng(7)
    noise = [rng.normal(size=size) for size in [(40, 3), (40,), (40, 3), (40,)]]
    model, history = mlp.train_mlp(
        *noise, hidden=(32,), epochs=300, batch_size=40, learning_rate=0.02,
        patience=5, seed=0,
    )  # fmt: skip
    best = int(np.argmin(history["valid_loss"].to_numpy()))
    expect(
        len(history) < 300,
        "Na szumie strata walidacyjna nie ma szans maleć długo. Trening miał "
        f"się zatrzymać, a przeszedł wszystkie {len(history)} epok.",
    )
    expect(
        len(history) == best + 1 + 5,
        "Trening ma stanąć, gdy strata walidacyjna nie poprawiła się przez "
        "patience=5 epok z rzędu. Najlepsza była epoka "
        f"{best} (licząc od 0), więc historia ma mieć {best + 6} wierszy. "
        f"Ma {len(history)}.",
    )
    with torch.no_grad():
        predicted = model(torch.tensor(noise[2], dtype=torch.float32)).numpy()
    error = float(np.mean((predicted - noise[3]) ** 2))
    expect(
        bool(np.isclose(error, history["valid_loss"].min(), rtol=1e-3, atol=1e-6)),
        "Po zatrzymaniu model ma wrócić do wag najlepszej epoki. Jego błąd "
        f"walidacyjny to {error:.4f}, najlepsza epoka miała "
        f"{history['valid_loss'].min():.4f}, ostatnia "
        f"{history['valid_loss'].iloc[-1]:.4f}.",
    )

    bad_x = x_train.copy()
    bad_x[3, 1] = np.nan
    _raises(
        lambda: mlp.train_mlp(bad_x, y_train, x_valid, y_valid, epochs=2),
        ValueError,
        "w danych treningowych jest NaN",
    )
    _raises(
        lambda: mlp.train_mlp(x_train, y_train[:-1], x_valid, y_valid, epochs=2),
        ValueError,
        "X i y mają różną liczbę wierszy",
    )
    _raises(
        lambda: mlp.train_mlp(x_train, y_train, x_valid[:0], y_valid[:0], epochs=2),
        ValueError,
        "zbiór walidacyjny jest pusty",
    )
    _raises(
        lambda: mlp.train_mlp(x_train, y_train, x_valid, y_valid, epochs=0),
        ValueError,
        "epochs wynosi 0",
    )
    _raises(
        lambda: mlp.train_mlp(x_train, y_train, x_valid, y_valid, batch_size=0),
        ValueError,
        "batch_size wynosi 0",
    )


def _sales_panel(days: int = 40) -> tuple[pd.DataFrame, pd.Series]:
    """Four series. Feature ``a`` is in the thousands, ``b`` around zero."""
    rng = np.random.default_rng(13)
    rows = 4 * days
    frame = pd.DataFrame(
        {
            "store_id": np.repeat(np.arange(4), days),
            "product_id": 7,
            "dt": np.tile(pd.date_range("2024-04-01", periods=days), 4),
            "a": rng.uniform(0, 1000, rows),
            "b": rng.normal(size=rows),
        }
    )
    return frame, 10 + 0.01 * frame["a"] + 2 * frame["b"]


@task("13.7", "MLPForecaster: skalowanie, braki, wydzielona walidacja")
def check_forecaster(_target: object) -> None:
    from freshcast.models import mlp

    frame, target = _sales_panel()
    settings: dict[str, Any] = {
        "hidden": (16,),
        "epochs": 100,
        "batch_size": 64,
        "learning_rate": 0.02,
        "patience": 25,
        "valid_days": 7,
        "seed": 0,
    }
    before = frame.copy()
    model = mlp.MLPForecaster(["a", "b"], **settings)
    _raises(lambda: model.predict(frame), RuntimeError, "predict jest wołany przed fit")
    expect(model.fit(frame, target) is model, "fit ma zwracać self.")
    forecast = model.predict(frame)
    expect(frame.equals(before), "fit albo predict zmieniło ramkę X.")
    expect(
        isinstance(forecast, np.ndarray)
        and forecast.shape == (len(frame),)
        and forecast.dtype == np.float64,
        "predict ma zwrócić tablicę NumPy float64 z jedną prognozą na wiersz X.",
    )
    error = float(np.mean(np.abs(forecast - target.to_numpy())))
    expect(
        error < 0.5,
        "Cel to 10 + 0.01 a + 2 b bez szumu, a cecha a jest rzędu tysięcy. "
        "Po skalowaniu cech sieć powinna to odtworzyć ze średnim błędem poniżej "
        f"0.5 (cel ma rozstęp około 18). Jest {error:.2f}.",
    )
    head = model.predict(frame.head(5))
    expect(
        bool(np.allclose(head, forecast[:5])),
        "Prognoza wiersza ma nie zależeć od tego, jakie inne wiersze są w X. "
        "Statystyki skalowania pochodzą z fit, nie z danych do predict.",
    )
    repeat = mlp.MLPForecaster(["a", "b"], **settings).fit(frame, target)
    expect(
        bool(np.allclose(repeat.predict(frame), forecast)),
        "Ten sam seed i te same dane mają dać te same prognozy.",
    )

    # The last 7 days get a target 1000 higher. They are held out to decide
    # when to stop, so they must not be trained on, and their loss stays huge.
    last_week = frame["dt"].max() - pd.Timedelta(days=6)
    shifted = target.where(frame["dt"] < last_week, target + 1000.0)
    held = mlp.MLPForecaster(["a", "b"], **settings).fit(frame, shifted)
    log = getattr(held, "history_", None)
    expect(
        log is not None
        and float(log["valid_loss"].min()) > 1e5
        and float(log["train_loss"].iloc[-1]) < 100.0,
        "fit ma odłożyć ostatnie valid_days dni zbioru na walidację i nie "
        "trenować na nich. W teście te dni mają cel wyższy o 1000: strata "
        "walidacyjna powinna zostać rzędu 1e6, a treningowa spaść poniżej 100. "
        f"Jest {None if log is None else log.iloc[-1].round(1).to_dict()}.",
    )

    negative = mlp.MLPForecaster(["a"], **settings).fit(frame, target - 100.0)
    expect(
        float(negative.predict(frame).min()) == 0.0,
        "Prognozy ujemne mają być podniesione do zera.",
    )

    # Rows with a missing ``a`` also have a target 40 higher, so the network
    # can only get them right if it is told which values were missing.
    rng = np.random.default_rng(3)
    early = np.flatnonzero((frame["dt"] < last_week).to_numpy())
    gaps = rng.choice(early, 25, replace=False)
    holes = frame.copy()
    holes.loc[holes.index[gaps], "a"] = np.nan
    lifted = target.copy()
    lifted.iloc[gaps] += 40.0 - 0.01 * frame["a"].iloc[gaps]
    tolerant = mlp.MLPForecaster(["a", "b"], **settings).fit(holes, lifted)
    got = tolerant.predict(holes)
    expect(
        bool(np.isfinite(got).all()),
        "Brak w cesze nie może dawać NaN w prognozie: ma być zastąpiony średnią "
        "z treningu i oznaczony dodatkowym wejściem 0/1.",
    )
    expect(
        float(np.mean(got[gaps])) > 35.0,
        "Wiersze z brakiem w cesze a mają cel około 50, reszta około 15. Sieć "
        "dostaje dodatkowe wejście 0/1 dla każdej cechy, która miała braki "
        "w treningu, więc ma to rozpoznać. Średnia prognoza na wierszach "
        f"z brakiem to {float(np.mean(got[gaps])):.1f}.",
    )
    unseen = frame.assign(b=frame["b"].where(frame.index != 0))
    _raises(
        lambda: tolerant.predict(unseen),
        ValueError,
        "w predict brakuje wartości w kolumnie, która w treningu jej nie miała",
    )
    _raises(
        lambda: tolerant.predict(frame.assign(b=np.inf)),
        ValueError,
        "w predict jest nieskończoność",
    )
    _raises(
        lambda: mlp.MLPForecaster(["a", "b"], **settings).fit(
            frame.assign(a=np.nan), target
        ),
        ValueError,
        "cała cecha jest pusta w wierszach treningowych",
    )
    _raises(
        lambda: mlp.MLPForecaster(["a", "b"], **{**settings, "valid_days": 40}).fit(
            frame, target
        ),
        ValueError,
        "valid_days obejmuje cały zakres dat",
    )
