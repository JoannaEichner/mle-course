"""Download the course datasets and verify them against pinned checksums."""

import hashlib
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from coursekit import paths

_FRN_URL = (
    "https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K/resolve/main/data"
)
_CHUNK = 1 << 20


@dataclass(frozen=True)
class Dataset:
    """A file the course downloads."""

    name: str
    url: str
    path: Path
    sha256: str
    size_mb: int
    licence: str


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


def download(dataset: Dataset) -> None:
    """Download one dataset unless a verified copy is already in place.

    Raises:
        ValueError: The downloaded file does not match the pinned checksum.
    """
    if is_ready(dataset):
        print(f"✓ {dataset.name}: już pobrane")
        return
    dataset.path.parent.mkdir(parents=True, exist_ok=True)
    partial = dataset.path.with_suffix(dataset.path.suffix + ".part")
    print(f"↓ {dataset.name} (~{dataset.size_mb} MB, {dataset.licence})")
    with urllib.request.urlopen(dataset.url) as response, partial.open("wb") as out:  # noqa: S310
        total = int(response.headers.get("Content-Length", 0))
        done = 0
        while chunk := response.read(_CHUNK):
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done / total:5.1%}", end="", flush=True)
    print()
    actual = sha256_of(partial)
    if actual != dataset.sha256:
        partial.unlink()
        raise ValueError(
            f"Suma kontrolna pliku {dataset.path.name} się nie zgadza.\n"
            f"  oczekiwana: {dataset.sha256}\n  otrzymana:  {actual}\n"
            "Plik u źródła mógł się zmienić. Zgłoś to w repozytorium kursu."
        )
    partial.replace(dataset.path)
    print(f"✓ {dataset.name}: zapisane w {dataset.path.relative_to(paths.ROOT)}")


def download_all() -> None:
    """Download every dataset the course uses."""
    for dataset in DATASETS:
        download(dataset)
