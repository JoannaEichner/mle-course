"""Mutants for ``freshcast.storage.s3`` (module 15)."""

from pathlib import Path
from typing import Any

from coursekit.mutation import Mutant


def _cls() -> Any:
    from freshcast.storage.s3 import S3Storage

    return S3Storage


def _exists_by_prefix() -> None:
    cls = _cls()

    def exists(self: Any, key: str) -> bool:
        return bool(self.list_keys(key))

    cls.exists = exists


def _list_unsorted() -> None:
    cls = _cls()
    original = cls.list_keys

    def list_keys(self: Any, prefix: str = "") -> list[str]:
        return sorted(original(self, prefix), reverse=True)

    cls.list_keys = list_keys


def _missing_download_is_silent() -> None:
    cls = _cls()
    original = cls.download_file

    def download_file(self: Any, key: str, path: Path) -> None:
        try:
            original(self, key, path)
        except FileNotFoundError:
            return

    cls.download_file = download_file


def _delete_does_nothing() -> None:
    _cls().delete = lambda self, key: None


def _cache_never_refreshed() -> None:
    cls = _cls()
    original = cls.fetch
    seen: dict[str, Path] = {}

    def fetch(self: Any, key: str) -> Path:
        if key not in seen:
            seen[key] = original(self, key)
        return seen[key]

    cls.fetch = fetch


def _no_retry() -> None:
    cls = _cls()
    original = cls.__init__

    def __init__(self: Any, *args: Any, **kwargs: Any) -> None:  # noqa: N807
        kwargs["attempts"] = 1
        original(self, *args, **kwargs)

    cls.__init__ = __init__


def _retry_everything() -> None:
    from freshcast.storage import s3
    from freshcast.storage.retry import retry

    s3.is_transient = lambda error: True
    cls = _cls()
    original = cls.__init__

    def __init__(self: Any, *args: Any, **kwargs: Any) -> None:  # noqa: N807
        original(self, *args, **kwargs)
        self._retrying = retry(
            attempts=kwargs.get("attempts", 3),
            retry_if=lambda error: True,
            sleep=kwargs.get("sleep", lambda _: None),
        )

    cls.__init__ = __init__


MUTANTS = [
    Mutant(
        "exists_by_prefix",
        "exists zwraca True dla samego początku klucza (np. 'models')",
        _exists_by_prefix,
    ),
    Mutant(
        "list_unsorted",
        "list_keys zwraca klucze w odwrotnej kolejności",
        _list_unsorted,
    ),
    Mutant(
        "missing_download_is_silent",
        "pobranie nieistniejącego klucza kończy się bez błędu",
        _missing_download_is_silent,
    ),
    Mutant("delete_does_nothing", "delete niczego nie usuwa", _delete_does_nothing),
    Mutant(
        "cache_never_refreshed",
        "fetch zwraca starą kopię, gdy obiekt pod tym kluczem został podmieniony",
        _cache_never_refreshed,
    ),
    Mutant("no_retry", "przejściowe błędy połączenia nie są ponawiane", _no_retry),
    Mutant(
        "retry_everything",
        "błędy trwałe (np. brak dostępu) też są ponawiane",
        _retry_everything,
    ),
]
