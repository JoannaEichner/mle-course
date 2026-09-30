"""A service class over the S3 API, and publishing saved models through it.

S3 stores objects, not files: a bucket is a flat list of keys such as
``models/lightgbm_20240625-143005/model.joblib``, and the slashes are only a
naming habit. Amazon invented the API, and many servers speak it, among them
the moto server, which the course runs locally. Code written for one runs against the
other: only the endpoint and the credentials change, and those come from
settings and the environment, never from constants in the code.
"""

import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Self

from botocore.exceptions import (
    ClientError,
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

from freshcast.config import DEFAULT_REGION, StorageSettings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT = 5  # seconds to establish a connection
READ_TIMEOUT = 30  # seconds to wait for the server's next bytes

# What S3 answers for a key that is not there: a HEAD request has no body, so
# it only carries the status as the code, while a GET names the error.
MISSING_CODES = frozenset({"404", "NoSuchKey", "NotFound"})

# Failures that may pass by themselves. Everything else would fail again.
TRANSIENT_CONNECTION_ERRORS = (
    EndpointConnectionError,
    ConnectionClosedError,
    ConnectTimeoutError,
    ReadTimeoutError,
)
TRANSIENT_STATUSES = frozenset({429, 500, 502, 503, 504})
TRANSIENT_CODES = frozenset({"RequestTimeout", "SlowDown", "Throttling"})


def is_missing(error: ClientError) -> bool:
    """Tell whether an S3 error means that the key or bucket is not there."""
    return error.response["Error"]["Code"] in MISSING_CODES


def is_transient(error: Exception) -> bool:
    """Tell whether repeating the call that raised ``error`` may succeed.

    Transient are the failures of the connection (it could not be made, it
    timed out, it was closed) and the answers that mean "busy or broken on
    our side": HTTP status 429, 500, 502, 503 or 504, and the error codes
    ``RequestTimeout``, ``SlowDown`` and ``Throttling``.

    Everything else would fail the same way again: a missing key or bucket,
    access denied, a rejected request, missing credentials, and any exception
    that does not come from ``botocore``.
    """
    raise NotImplementedError("Zadanie 15.2")


def make_client(
    endpoint_url: str | None = None,
    *,
    access_key: str | None = None,
    secret_key: str | None = None,
    region: str = DEFAULT_REGION,
) -> "S3Client":
    """Create a boto3 S3 client from explicit arguments.

    The client makes one attempt per request and waits at most
    ``CONNECT_TIMEOUT`` seconds to connect and ``READ_TIMEOUT`` for an
    answer. It does not retry on its own: retrying is done in one place,
    ``freshcast.storage.retry``, so that it shows in the logs and can be tested.

    Args:
        endpoint_url: Address of an S3-compatible server, for example
            ``http://localhost:9000``. None means Amazon S3.
        access_key: Access key id. With ``secret_key``, it is used as given.
        secret_key: Secret access key.
        region: Region name. Local servers accept any, but it has to be
            set.

    Returns:
        A client for the ``s3`` service. When no keys are given, boto3 looks
        for them itself: the environment variables ``AWS_ACCESS_KEY_ID`` and
        ``AWS_SECRET_ACCESS_KEY`` first, then the shared credentials file.

    Raises:
        ValueError: Only one of ``access_key`` and ``secret_key`` is given.
    """
    raise NotImplementedError("Zadanie 15.3")


class S3Storage:
    """One bucket, seen through the few operations the project needs.

    Every request to the server is retried when it fails for a transient
    reason (see ``is_transient``), so callers see either a result or an error
    that retrying could not fix.

    Args:
        client: A boto3 S3 client, see ``make_client``. Tests pass one made
            by ``moto``.
        bucket: Name of the bucket. It must exist, see ``ensure_bucket``.
        cache_dir: Where ``fetch`` keeps local copies. None means no cache.
        attempts: How many times a request is made before its error is
            raised.
        sleep: Waits between attempts. Tests pass a recorder so they do not
            really wait.
    """

    bucket: str
    cache_dir: Path | None
    _client: "S3Client"

    def __init__(
        self,
        client: "S3Client",
        bucket: str,
        *,
        cache_dir: Path | None = None,
        attempts: int = 3,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        raise NotImplementedError("Zadanie 15.3")

    @classmethod
    def from_settings(
        cls, settings: StorageSettings, *, cache_dir: Path | None = None
    ) -> Self:
        """Build a service on a new client made from the storage settings.

        The settings hold the bucket, the endpoint and the region. The keys
        are not among them: boto3 finds them in the environment.
        """
        raise NotImplementedError("Zadanie 15.3")

    def ensure_bucket(self) -> None:
        """Create the bucket unless it exists. Safe to call every time.

        Buckets in other regions than ``us-east-1`` need a location
        constraint on Amazon S3, which this helper does not send.
        """
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except ClientError as error:
            if not is_missing(error):
                raise
            self._client.create_bucket(Bucket=self.bucket)

    def upload_file(self, path: Path, key: str) -> None:
        """Copy a local file into the bucket under ``key``.

        An object that already has this key is replaced.

        Raises:
            FileNotFoundError: ``path`` is not an existing file.
            botocore.exceptions.ClientError: The server refused the request,
                for example because the bucket does not exist.
        """
        raise NotImplementedError("Zadanie 15.3")

    def download_file(self, key: str, path: Path) -> None:
        """Copy the object ``key`` to a local file, replacing it if it exists.

        Missing parent directories of ``path`` are created. The file appears
        only when the whole object has arrived, so an interrupted download
        never leaves half a file behind.

        Raises:
            FileNotFoundError: The bucket has no object with this key.
            botocore.exceptions.ClientError: Any other refusal by the server.
        """
        raise NotImplementedError("Zadanie 15.3")

    def exists(self, key: str) -> bool:
        """Tell whether an object with exactly this key is in the bucket.

        A key that is only the beginning of other keys (``models`` when
        ``models/a.txt`` exists) does not exist.

        Raises:
            botocore.exceptions.ClientError: Any failure other than "not
                found", for example access denied. "I could not find out"
                must not turn into "no".
        """
        raise NotImplementedError("Zadanie 15.3")

    def list_keys(self, prefix: str = "") -> list[str]:
        """List the keys that start with ``prefix``, in ascending order.

        The server returns at most 1000 keys per request. All of them are
        returned, however many there are. An empty bucket gives an empty list.
        """

        raise NotImplementedError("Zadanie 15.3")

    def delete(self, key: str) -> None:
        """Remove the object ``key``. A key that is not there is not an error."""
        raise NotImplementedError("Zadanie 15.3")

    def fetch(self, key: str) -> Path:
        """Return a local copy of an object, downloading it only when needed.

        Each call asks the server whether the object has changed since the
        copy was made (a request without a body) and transfers the bytes only
        when it has, or when there is no copy yet. A copy of an object that
        was replaced under the same key is never returned.

        Args:
            key: The object to fetch.

        Returns:
            A file inside ``cache_dir`` with the content of the object and
            the last part of the key as its name, so ``data/daily.parquet``
            comes back as ``.../daily.parquet``. Different keys never share
            a file.

        Raises:
            RuntimeError: The service was created without ``cache_dir``.
            ValueError: ``key`` is empty, begins with a slash or has a ``..``
                part, so the copy could land outside ``cache_dir``.
            FileNotFoundError: The bucket has no object with this key.
        """
        raise NotImplementedError("Zadanie 15.4")


def _join_key(*parts: str) -> str:
    """Join key parts with slashes, leaving out the empty ones."""
    return "/".join(part.strip("/") for part in parts if part.strip("/"))


def publish_model(storage: S3Storage, model_dir: Path, prefix: str = "") -> str:
    """Upload a saved model directory under its signature.

    The directory name is the signature (see ``artifacts.model_signature``).
    Every file lands at ``<prefix>/<signature>/<path in the directory>``.
    ``metadata.json`` is uploaded last, so a signature that has it in the
    bucket is complete. Published models are never overwritten, like saved
    ones.

    Args:
        storage: The bucket to publish to.
        model_dir: A directory written by ``save_model``, with whatever else
            the run added (history, backtest, forecast).
        prefix: Where the models live in the bucket. Slashes at its ends are
            ignored; empty means the root of the bucket.

    Returns:
        The key prefix of the published model: ``<prefix>/<signature>``.

    Raises:
        FileNotFoundError: ``model_dir`` lacks the model or the metadata file.
            Nothing is uploaded then.
        FileExistsError: Objects already exist under this signature.
        botocore.exceptions.ClientError: The bucket does not exist or refuses.
    """
    raise NotImplementedError("Zadanie 15.5")


def fetch_model(
    storage: S3Storage, signature: str, target_dir: Path, prefix: str = ""
) -> Path:
    """Download a published model into ``target_dir/<signature>``.

    Args:
        storage: The bucket the model was published to.
        signature: Name of the model, as returned in the key prefix by
            ``publish_model``.
        target_dir: Parent directory for the download. Created if missing.
        prefix: The same prefix that was used to publish.

    Returns:
        The model directory, laid out as ``save_model`` wrote it, ready for
        ``load_model``. It appears only when every file has arrived.

    Raises:
        FileNotFoundError: No complete model is published under this
            signature: there are no objects, or ``metadata.json`` is missing.
        FileExistsError: ``target_dir/<signature>`` already exists.
    """
    raise NotImplementedError("Zadanie 15.5")
