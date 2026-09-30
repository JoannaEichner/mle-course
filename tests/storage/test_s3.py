"""Tests of the S3 service class, against a fake S3 from moto.

The first test is given as a pattern. The rest is yours: `uv run course
check 15.6` runs your tests against deliberately broken versions of the
service and tells you which bugs they would let through.
"""

from collections.abc import Iterator
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

from freshcast.storage.s3 import S3Storage

BUCKET = "test-bucket"


@pytest.fixture(name="storage")
def fixture_storage(tmp_path: Path) -> Iterator[S3Storage]:
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=BUCKET)
        yield S3Storage(
            client, BUCKET, cache_dir=tmp_path / "cache", sleep=lambda _: None
        )


def test_uploaded_file_comes_back_unchanged(storage: S3Storage, tmp_path: Path) -> None:
    source = tmp_path / "in.txt"
    source.write_text("hello", encoding="utf-8")

    storage.upload_file(source, "folder/in.txt")
    storage.download_file("folder/in.txt", tmp_path / "out.txt")

    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "hello"


# Your tests go here.
