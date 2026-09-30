"""Checks for module 16: the Dockerfile, the CI workflow, pre-commit.

These files are written whole by the learner, so there are no solution
blocks. The reference copies live under ``reference/16/`` on the
``solutions`` branch; ``course catchup`` puts them in place.
"""

import re
from pathlib import Path
from typing import Any

import yaml

from coursekit import paths
from coursekit.checking import expect, task

MODULE = "16"


def _file(relative: str) -> Path:
    """Return the author's reference file if present, else the learner's file."""
    reference = paths.ROOT / "reference" / MODULE / relative
    return reference if reference.is_file() else paths.ROOT / relative


def _read(relative: str) -> str:
    path = _file(relative)
    if not path.is_file():
        raise NotImplementedError
    return path.read_text(encoding="utf-8")


def _instructions(dockerfile: str) -> list[tuple[str, str]]:
    """Split a Dockerfile into (INSTRUCTION, arguments), joining continued lines."""
    joined = re.sub(r"\\\n", " ", dockerfile)
    pairs = []
    for line in joined.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        word, _, rest = stripped.partition(" ")
        pairs.append((word.upper(), rest.strip()))
    return pairs


@task("16.1", "Dockerfile: obraz z zablokowanymi zależnościami, bez roota")
def check_dockerfile(_target: object) -> None:
    steps = _instructions(_read("Dockerfile"))
    bases = [args.split()[0] for word, args in steps if word == "FROM"]
    expect(
        bool(bases) and all(base.startswith("python:3.12") for base in bases),
        "Każdy etap ma zaczynać od obrazu python:3.12 (na przykład "
        f"python:3.12-slim), a nie od :latest. Znalazłem: {bases}.",
    )
    runs = " ".join(args for word, args in steps if word == "RUN")
    expect(
        "uv sync" in runs and ("--locked" in runs or "--frozen" in runs),
        "Zależności mają być instalowane z pliku uv.lock: `uv sync --locked` "
        "albo `--frozen`. Bez tego obraz zbudowany jutro może mieć inne wersje.",
    )
    expect(
        "libgomp1" in runs,
        "Obraz slim nie ma biblioteki libgomp, której wymaga LightGBM. Bez niej "
        "`freshcast train` wywróci się przy imporcie.",
    )
    users = [args for word, args in steps if word == "USER"]
    expect(
        bool(users) and users[-1] not in ("root", "0"),
        "Kontener ma działać jako zwykły użytkownik. Ostatnia instrukcja USER "
        f"to: {users[-1] if users else 'brak'}.",
    )
    entry = [args for word, args in steps if word in ("ENTRYPOINT", "CMD")]
    expect(
        any("freshcast" in args for args in entry),
        "Obraz ma uruchamiać polecenie freshcast (ENTRYPOINT albo CMD).",
    )
    copied = " ".join(args for word, args in steps if word == "COPY")
    expect(
        "data" not in copied.split() and "artifacts" not in copied.split(),
        "Dane i artefakty nie trafiają do obrazu. Montuje się je przy uruchomieniu.",
    )

    ignored = _read(".dockerignore").split()
    for name in (".git", ".venv", "data"):
        expect(
            name in ignored or f"{name}/" in ignored,
            f".dockerignore ma wykluczać {name}.",
        )


def _workflow_commands(workflow: dict[str, Any]) -> list[str]:
    commands = []
    for job in workflow.get("jobs", {}).values():
        for step in job.get("steps", []):
            commands.append(str(step.get("run", "")) + " " + str(step.get("uses", "")))
    return commands


@task("16.2", "workflow CI: ruff, mypy i pytest na każdym pull requeście")
def check_workflow(_target: object) -> None:
    workflow = yaml.safe_load(_read(".github/workflows/ci.yml"))
    # YAML reads the bare key `on` as the boolean True.
    triggers = workflow.get("on", workflow.get(True, {}))
    names = triggers if isinstance(triggers, list | dict) else [triggers]
    expect(
        "pull_request" in names,
        f"Workflow ma się uruchamiać dla pull requestów. Wyzwalacze: {list(names)}.",
    )
    commands = " | ".join(_workflow_commands(workflow))
    expect(
        "actions/checkout" in commands and "setup-uv" in commands,
        "Workflow ma pobrać repozytorium (actions/checkout) i zainstalować uv "
        "(astral-sh/setup-uv).",
    )
    expect(
        "uv sync" in commands and ("--locked" in commands or "--frozen" in commands),
        "CI ma instalować dokładnie wersje z uv.lock: `uv sync --locked`.",
    )
    for tool, needle in [
        ("ruff check", "ruff check"),
        ("ruff format --check", "ruff format --check"),
        ("mypy", "mypy"),
        ("pytest", "pytest"),
    ]:
        expect(needle in commands, f"W workflow brakuje kroku `{tool}`.")


@task("16.3", "pre-commit: te same sprawdzenia przed każdym commitem")
def check_precommit(_target: object) -> None:
    config = yaml.safe_load(_read(".pre-commit-config.yaml"))
    hooks = [
        str(hook.get("id", "")) + " " + str(hook.get("entry", ""))
        for repo in config.get("repos", [])
        for hook in repo.get("hooks", [])
    ]
    text = " | ".join(hooks)
    expect(
        "ruff" in text and "format" in text,
        "pre-commit ma uruchamiać ruff w obu rolach: linter i formatter. "
        f"Znalezione hooki: {[hook.split()[0] for hook in hooks]}.",
    )
    expect("mypy" in text, "pre-commit ma uruchamiać mypy.")
