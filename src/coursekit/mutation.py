"""Mutation checks: does a test suite notice a broken implementation?

A mutant is a small, deliberate bug patched into the learner's own code at
test time. Good tests fail on every mutant. Mutants wrap the learner's
functions from the outside, so this file holds no reference solution.
"""

import importlib
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ENV_VAR = "COURSE_MUTANT"


@dataclass(frozen=True)
class Mutant:
    """A deliberate bug.

    ``description`` completes the sentence "Twoje testy przechodzą, mimo że".
    """

    name: str
    description: str
    apply: Callable[[], None]


def load_group(group: str) -> dict[str, Mutant]:
    """Return the mutants defined in ``coursekit.mutants.<group>``."""
    module = importlib.import_module(f"coursekit.mutants.{group}")
    return {mutant.name: mutant for mutant in module.MUTANTS}


def _pytest(test_path: Path, *extra: str, mutant: str | None = None) -> str | None:
    """Run pytest on ``test_path``. Return its output, or None if it failed."""
    env = dict(os.environ)
    if mutant is not None:
        env[ENV_VAR] = mutant
    else:
        env.pop(ENV_VAR, None)
    # Project-level addopts are cleared so the output format is predictable.
    command = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", "-x"]
    plugins = ["-p", "coursekit.mutation", "-p", "no:cacheprovider"]
    done = subprocess.run(  # noqa: S603
        [*command, *plugins, *extra, str(test_path)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    return done.stdout if done.returncode == 0 else None


def count_tests(test_path: Path) -> int:
    """Return how many tests pytest collects from ``test_path``."""
    output = _pytest(test_path, "--collect-only")
    if output is None:
        return 0
    return sum("::" in line for line in output.splitlines())


def suite_passes(test_path: Path) -> bool:
    """Tell whether the tests pass on the unmodified code."""
    return _pytest(test_path) is not None


def survivors(test_path: Path, group: str) -> list[Mutant]:
    """Return the mutants that the tests fail to notice."""
    return [
        mutant
        for name, mutant in load_group(group).items()
        if _pytest(test_path, mutant=f"{group}:{name}") is not None
    ]


def pytest_configure() -> None:
    """Pytest hook: patch in the mutant named by the environment, if any."""
    selected = os.environ.get(ENV_VAR)
    if not selected:
        return
    group, name = selected.split(":", maxsplit=1)
    load_group(group)[name].apply()
