"""Task checks: a registry, a runner and a progress log.

A check is a function registered under a task id. It imports the learner's
code (or receives an object from a notebook) and raises ``CheckFailed`` with
a message that says what is wrong without giving the solution away.
"""

import importlib
import json
import pkgutil
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from coursekit import paths

Status = Literal["ok", "todo", "fail", "error"]
CheckFunction = Callable[[Any], None]


class CheckFailed(AssertionError):  # noqa: N818 - reads better at the call sites
    """The learner's code ran but gave a wrong result."""


@dataclass(frozen=True)
class Task:
    """A registered check.

    ``graded`` is False for checks of the learner's machine (module 00).
    Course verification skips those: they have no reference solution.

    ``starts_as`` is the status the check must report in the learner view
    before any work: ``todo`` for code to write, ``fail`` for a ticket in
    existing code that runs but misbehaves.
    """

    id: str
    title: str
    func: CheckFunction
    graded: bool = True
    starts_as: Status = "todo"


@dataclass(frozen=True)
class Result:
    """Outcome of running one check."""

    task: Task
    status: Status
    message: str = ""


_REGISTRY: dict[str, Task] = {}
_SYMBOL: dict[Status, str] = {"ok": "✓", "todo": "·", "fail": "✗", "error": "✗"}


def task(
    task_id: str, title: str, *, graded: bool = True, starts_as: Status = "todo"
) -> Callable[[CheckFunction], CheckFunction]:
    """Register the decorated function as the check for ``task_id``."""

    def register(func: CheckFunction) -> CheckFunction:
        if task_id in _REGISTRY:
            raise ValueError(f"Duplicate check for task {task_id}.")
        _REGISTRY[task_id] = Task(task_id, title, func, graded, starts_as)
        return func

    return register


def expect(condition: bool, message: str) -> None:
    """Raise ``CheckFailed`` with ``message`` unless ``condition`` holds."""
    if not condition:
        raise CheckFailed(message)


def load_checks() -> dict[str, Task]:
    """Import every ``coursekit.checks.mXX`` module and return the registry."""
    package = importlib.import_module("coursekit.checks")
    for info in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"coursekit.checks.{info.name}")
    return dict(sorted(_REGISTRY.items()))


def select(selector: str | None) -> list[Task]:
    """Return the tasks matching a module (``07``), a task (``07.2``) or all.

    Raises:
        ValueError: Nothing matches the selector.
    """
    tasks = load_checks()
    if selector is None:
        return list(tasks.values())
    if selector in tasks:
        return [tasks[selector]]
    chosen = [t for key, t in tasks.items() if key.split(".")[0] == selector.zfill(2)]
    if not chosen:
        raise ValueError(
            f"Nie ma sprawdzeń dla {selector!r}. Podaj numer modułu (07) "
            "albo zadania (07.2)."
        )
    return chosen


def run(tasks: list[Task], target: Any = None) -> list[Result]:
    """Run the checks and return one result per task."""
    return [_run_one(t, target) for t in tasks]


def _run_one(item: Task, target: Any) -> Result:
    try:
        item.func(target)
    except NotImplementedError:
        return Result(item, "todo", "jeszcze nie zrobione")
    except CheckFailed as failure:
        return Result(item, "fail", str(failure))
    except Exception as error:  # noqa: BLE001 - any crash in learner code is a result
        return Result(item, "error", _describe_crash(error))
    return Result(item, "ok")


def _describe_crash(error: Exception) -> str:
    """Name the exception and the last line of learner code it passed through."""
    frames = traceback.extract_tb(error.__traceback__)
    own = [f for f in frames if "coursekit" not in f.filename]
    where = (
        f" ({own[-1].filename.split('/')[-1]}, linia {own[-1].lineno})" if own else ""
    )
    return f"Twój kod zgłosił {type(error).__name__}: {error}{where}"


def report(results: list[Result]) -> str:
    """Format results for the terminal or a notebook cell."""
    lines = []
    for result in results:
        lines.append(f"{_SYMBOL[result.status]} {result.task.id}  {result.task.title}")
        if result.message:
            lines.append(f"      {result.message}")
    passed = sum(r.status == "ok" for r in results)
    lines.append(f"\nZaliczone: {passed} z {len(results)}")
    return "\n".join(lines)


def record(results: list[Result]) -> None:
    """Append the outcomes to the learner's local progress log."""
    paths.STATE_DIR.mkdir(exist_ok=True)
    log: dict[str, dict[str, Any]] = {}
    if paths.PROGRESS_FILE.is_file():
        log = json.loads(paths.PROGRESS_FILE.read_text(encoding="utf-8"))
    now = datetime.now().isoformat(timespec="seconds")
    for result in results:
        entry = log.setdefault(result.task.id, {"attempts": 0, "first_passed": None})
        entry["attempts"] += 1
        entry["status"] = result.status
        entry["last_run"] = now
        if result.status == "ok" and entry["first_passed"] is None:
            entry["first_passed"] = now
    paths.PROGRESS_FILE.write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
