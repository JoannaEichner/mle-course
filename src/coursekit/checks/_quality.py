"""Shared helpers for checks of lab modules written by the learner."""

import subprocess
import sys
import types
from pathlib import Path

from coursekit import paths
from coursekit.checking import CheckFailed, expect


def run_tool(*args: str) -> tuple[bool, str]:
    """Run a Python tool such as ruff or mypy and return (passed, first lines)."""
    done = subprocess.run(  # noqa: S603 - fixed tool names, the path is the learner's file
        [sys.executable, "-m", *args],
        capture_output=True,
        text=True,
        cwd=paths.ROOT,
        check=False,
    )
    lines = (done.stdout + done.stderr).strip().splitlines()
    return done.returncode == 0, "\n   ".join(lines[:6])


def expect_clean(module: types.ModuleType) -> None:
    """Fail unless the module's file passes ruff check, ruff format and mypy --strict."""
    path = str(Path(module.__file__ or ""))
    name = Path(path).name
    passed, output = run_tool("ruff", "check", "--no-cache", path)
    expect(passed, f"ruff check zgłasza problemy:\n   {output}")
    passed, _ = run_tool("ruff", "format", "--check", "--no-cache", path)
    expect(passed, f"Plik nie jest sformatowany. Uruchom: uv run ruff format {name}")
    passed, output = run_tool("mypy", "--strict", "--no-error-summary", path)
    expect(passed, f"mypy --strict zgłasza błędy:\n   {output}")


def need(module: types.ModuleType, *names: str) -> None:
    """Report todo when none of ``names`` exists yet, a failure when only some do."""
    absent = [name for name in names if not hasattr(module, name)]
    if len(absent) == len(names):
        raise NotImplementedError
    if absent:
        raise CheckFailed(
            f"W {Path(module.__file__ or '').name} brakuje: {', '.join(absent)}."
        )
