"""Checks for module 00: the learner's machine and first pull request.

These are not graded tasks with a reference solution. They look at the
environment the course runs in.
"""

import subprocess

from coursekit import doctor, paths
from coursekit.checking import expect, task

JOURNAL = paths.ROOT / "notes" / "journal.md"
_MIN_JOURNAL_LINES = 3


def _git(*args: str) -> str:
    done = subprocess.run(  # noqa: S603
        ["git", "-C", str(paths.ROOT), *args],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return done.stdout.strip()


@task("00.1", "środowisko: course doctor bez błędów", graded=False)
def check_environment(_target: object) -> None:
    failed = [f.name for f in doctor.diagnose() if f.level == "fail"]
    expect(
        not failed,
        f"course doctor zgłasza błędy: {', '.join(failed)}. Uruchom "
        "`uv run course doctor` i napraw punkty oznaczone ✗.",
    )


@task("00.2", "dziennik nauki w notes/journal.md", graded=False)
def check_journal(_target: object) -> None:
    if not JOURNAL.is_file():
        raise NotImplementedError
    lines = [line for line in JOURNAL.read_text("utf-8").splitlines() if line.strip()]
    expect(
        len(lines) >= _MIN_JOURNAL_LINES,
        f"Dziennik ma {len(lines)} niepustych linii. Napisz co najmniej "
        f"{_MIN_JOURNAL_LINES}: po co robisz kurs i co chcesz umieć.",
    )


@task("00.3", "pierwszy commit i remote upstream", graded=False)
def check_first_commit(_target: object) -> None:
    if not JOURNAL.is_file():
        raise NotImplementedError
    expect(
        bool(_git("log", "--oneline", "--", "notes/journal.md")),
        "Plik notes/journal.md istnieje, ale nie ma go w żadnym commicie. "
        "Dodaj go (`git add`) i zatwierdź (`git commit`).",
    )
    expect(
        "upstream" in _git("remote").split(),
        "Brakuje remote `upstream`, z którego pobierzesz aktualizacje kursu. "
        "Dodaj go poleceniem `git remote add upstream <adres repozytorium kursu>`.",
    )
