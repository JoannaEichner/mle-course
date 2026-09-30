"""Download the course datasets and verify them against pinned checksums."""

import hashlib
import io
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from coursekit import paths

_FRN_URL = (
    "https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K/resolve/main/data"
)
_CHUNK = 1 << 20


@dataclass(frozen=True)
class Dataset:
    """A file the course downloads.

    ``sha256`` is the checksum of the file at ``path``. When ``member`` is
    set, the URL points to a zip archive and ``path`` is that member,
    extracted.
    """

    name: str
    url: str
    path: Path
    sha256: str
    size_mb: float
    licence: str
    member: str | None = None


DATASETS = [
    Dataset(
        name="FreshRetailNet-50K, 90 dni historii",
        url=f"{_FRN_URL}/train.parquet",
        path=paths.FRN_TRAIN,
        sha256="6706832db892bbae4969c19d87e07975d2543d2ba7d7d4756360654785de5a3d",
        size_mb=102,
        licence="CC BY 4.0, Dingdong-Inc",
    ),
    Dataset(
        name="FreshRetailNet-50K, tydzień testowy",
        url=f"{_FRN_URL}/eval.parquet",
        path=paths.FRN_EVAL,
        sha256="1b118840664280c6b88bffc84c80ee1f54c05d911e354b7599e5da10995e960e",
        size_mb=8,
        licence="CC BY 4.0, Dingdong-Inc",
    ),
    Dataset(
        name="Monash Car Parts",
        url=(
            "https://zenodo.org/records/4656022/files/"
            "car_parts_dataset_with_missing_values.zip"
        ),
        path=paths.CAR_PARTS,
        sha256="818470cd0a65679b38b48a20e4d916d11fbd2ccbf7f5f9d8d97093dd6c784600",
        size_mb=0.04,
        licence="CC BY 4.0, Monash Time Series Forecasting Repository",
        member="car_parts_dataset_with_missing_values.tsf",
    ),
    Dataset(
        name="UCI Online Retail II",
        url="https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip",
        path=paths.ONLINE_RETAIL,
        sha256="bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980",
        size_mb=44,
        licence="CC BY 4.0, UCI Machine Learning Repository",
        member="online_retail_II.xlsx",
    ),
]


def sha256_of(path: Path) -> str:
    """Return the SHA-256 of a file, read in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def is_ready(dataset: Dataset) -> bool:
    """Tell whether the file exists and matches its checksum."""
    return dataset.path.is_file() and sha256_of(dataset.path) == dataset.sha256


def _fetch(url: str, size_mb: float) -> bytes:
    """Download a URL into memory, printing progress for larger files."""
    buffer = io.BytesIO()
    with urllib.request.urlopen(url) as response:  # noqa: S310
        total = int(response.headers.get("Content-Length", 0))
        while chunk := response.read(_CHUNK):
            buffer.write(chunk)
            if total and size_mb >= 1:
                print(f"\r  {buffer.tell() / total:5.1%}", end="", flush=True)
    if total and size_mb >= 1:
        print()
    return buffer.getvalue()


def download(dataset: Dataset) -> None:
    """Download one dataset unless a verified copy is already in place.

    Raises:
        ValueError: The downloaded file does not match the pinned checksum.
    """
    if is_ready(dataset):
        print(f"✓ {dataset.name}: już pobrane")
        return
    print(f"↓ {dataset.name} (~{dataset.size_mb:g} MB, {dataset.licence})")
    content = _fetch(dataset.url, dataset.size_mb)
    if dataset.member is not None:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            content = archive.read(dataset.member)

    actual = hashlib.sha256(content).hexdigest()
    if actual != dataset.sha256:
        raise ValueError(
            f"Suma kontrolna pliku {dataset.path.name} się nie zgadza.\n"
            f"  oczekiwana: {dataset.sha256}\n  otrzymana:  {actual}\n"
            "Plik u źródła mógł się zmienić. Zgłoś to w repozytorium kursu."
        )
    dataset.path.parent.mkdir(parents=True, exist_ok=True)
    dataset.path.write_bytes(content)
    print(f"✓ {dataset.name}: zapisane w {dataset.path.relative_to(paths.ROOT)}")


def download_all() -> None:
    """Download every dataset the course uses."""
    for dataset in DATASETS:
        download(dataset)
