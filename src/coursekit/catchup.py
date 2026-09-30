"""Catch up: fill in reference code for the modules before a given one.

The reference lives on the ``solutions`` branch. Catching up to module N
rewrites every package file that has tasks from earlier modules: those tasks
get the reference code, tasks from module N onward stay as stubs. Files the
learner writes whole (a Dockerfile, a workflow) are copied from
``reference/<module>/``.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from coursekit import markers, paths

_CANDIDATE_REFS = ("solutions", "origin/solutions", "upstream/solutions")
_TRACKED_DIRS = ("src/freshcast", "tests", "shelfwise", "labs")
# Lab notebooks are authored as jupytext files; the learner has the .ipynb.
_LAB_SUFFIX = ".lab.py"


def _git(*args: str) -> str | None:
    done = subprocess.run(  # noqa: S603
        ["git", "-C", str(paths.ROOT), *args],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return done.stdout if done.returncode == 0 else None


def find_solutions_ref() -> str:
    """Return the first git ref that holds the reference code.

    Raises:
        RuntimeError: The ``solutions`` branch has not been fetched.
    """
    for ref in _CANDIDATE_REFS:
        if _git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}") is not None:
            return ref
    raise RuntimeError(
        "Nie znaleziono gałęzi solutions. Pobierz ją poleceniem:\n"
        "  git fetch upstream solutions"
    )


def catch_up(module: int) -> list[Path]:
    """Write reference code for all tasks of modules before ``module``.

    Files are backed up to ``.course/backup/<timestamp>/`` before they are
    overwritten.

    Returns:
        The rewritten files, relative to the repository root.
    """
    ref = find_solutions_ref()
    listing = _git("ls-tree", "-r", "--name-only", ref, "--", *_TRACKED_DIRS) or ""
    backup_dir = paths.STATE_DIR / "backup" / datetime.now().strftime("%Y%m%d-%H%M%S")
    rewritten = []

    for name in listing.splitlines():
        if not name.endswith(".py") or name.endswith(_LAB_SUFFIX):
            continue
        source = _git("show", f"{ref}:{name}")
        if source is None:
            continue
        earlier = [t for t in markers.task_ids(source) if markers.module_of(t) < module]
        if not earlier:
            continue
        target = paths.ROOT / name
        if target.is_file():
            backup = backup_dir / name
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(target.read_bytes())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            markers.render(source, lambda t: markers.module_of(t) < module),
            encoding="utf-8",
        )
        rewritten.append(Path(name))
    _format([paths.ROOT / name for name in rewritten])
    rewritten.extend(_copy_whole_files(ref, module, backup_dir))
    return rewritten


def _format(files: list[Path]) -> None:
    """Format rewritten files: removing block markers leaves extra blank lines."""
    if not files:
        return
    subprocess.run(  # noqa: S603 - ruff on files this module just wrote
        [sys.executable, "-m", "ruff", "format", "--quiet", *map(str, files)],
        check=False,
    )


def _copy_whole_files(ref: str, module: int, backup_dir: Path) -> list[Path]:
    """Copy reference files that have no stub, such as a Dockerfile.

    They live under ``reference/<module>/<path>`` on the solutions branch
    and belong at ``<path>`` in the repository.
    """
    listing = _git("ls-tree", "-r", "--name-only", ref, "--", "reference") or ""
    copied = []
    for name in listing.splitlines():
        _, owner, *rest = Path(name).parts
        if not owner.isdigit() or int(owner) >= module:
            continue
        content = _git("show", f"{ref}:{name}")
        if content is None:
            continue
        relative = Path(*rest)
        target = paths.ROOT / relative
        if target.is_file():
            backup = backup_dir / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(target.read_bytes())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        copied.append(relative)
    return copied
