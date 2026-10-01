"""Environment diagnosis behind ``course doctor``."""

import ctypes
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from coursekit import datasets, paths

Level = Literal["ok", "warn", "fail", "later"]
_SYMBOL: dict[Level, str] = {"ok": "✓", "warn": "!", "fail": "✗", "later": "·"}
_GB = 1024**3
_MIN_FREE_DISK_GB = 10
_SMALL_PROFILE_BELOW_GB = 6
_FULL_PROFILE_FROM_GB = 12


@dataclass(frozen=True)
class Finding:
    """One line of the diagnosis."""

    name: str
    level: Level
    detail: str
    fix: str = ""


def _run(*command: str) -> str | None:
    """Return the command's output, or None if it is missing or fails."""
    try:
        done = subprocess.run(  # noqa: S603
            command, capture_output=True, text=True, timeout=20, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def is_wsl() -> bool:
    """Tell whether Python runs inside Windows Subsystem for Linux."""
    return "microsoft" in platform.release().lower()


def total_memory_gb() -> float | None:
    """Return the RAM visible to Linux, or None when it cannot be read."""
    meminfo = Path("/proc/meminfo")
    if not meminfo.is_file():
        return None
    for line in meminfo.read_text(encoding="utf-8").splitlines():
        if line.startswith("MemTotal:"):
            return int(line.split()[1]) * 1024 / _GB
    return None


def recommended_profile(memory_gb: float | None) -> str:
    """Pick the data profile that fits the machine's memory."""
    if memory_gb is not None and memory_gb < _SMALL_PROFILE_BELOW_GB:
        return "small"
    return "standard"


def check_system() -> Finding:
    system = platform.system()
    if system == "Linux":
        where = "Linux w WSL2" if is_wsl() else "Linux"
        return Finding("System", "ok", where)
    if system == "Windows":
        return Finding(
            "System",
            "fail",
            "Python działa w Windows, poza WSL",
            "Otwórz terminal Ubuntu (WSL) i tam sklonuj repo. Patrz lekcja 0.",
        )
    return Finding(
        "System", "warn", f"{system}: nietestowany, moduł 18 (GPU) nie zadziała"
    )


def check_repo_location() -> Finding:
    if is_wsl() and str(paths.ROOT).startswith("/mnt/"):
        return Finding(
            "Położenie repo",
            "fail",
            f"{paths.ROOT} leży na dysku Windows, praca będzie bardzo wolna",
            "Sklonuj repo do katalogu domowego Linuksa, np. ~/mle-course.",
        )
    return Finding("Położenie repo", "ok", str(paths.ROOT))


def check_memory() -> Finding:
    memory = total_memory_gb()
    if memory is None:
        return Finding("Pamięć", "warn", "nie udało się odczytać ilości RAM")
    detail = f"{memory:.1f} GB widoczne dla Linuksa"
    if memory < _SMALL_PROFILE_BELOW_GB:
        fix = "Laby zadziałają na profilu small."
        if is_wsl():
            fix += (
                " WSL domyślnie dostaje połowę RAM komputera. Limit podniesiesz"
                " w pliku %UserProfile%\\.wslconfig (sekcja [wsl2], memory=...)."
            )
        return Finding("Pamięć", "warn", detail, fix)
    if memory < _FULL_PROFILE_FROM_GB:
        return Finding("Pamięć", "ok", f"{detail}, profil full niezalecany")
    return Finding("Pamięć", "ok", detail)


def check_disk() -> Finding:
    free = shutil.disk_usage(paths.ROOT).free / _GB
    if free < _MIN_FREE_DISK_GB:
        return Finding(
            "Dysk",
            "warn",
            f"{free:.0f} GB wolnego, zalecane {_MIN_FREE_DISK_GB} GB",
            "Zwolnij miejsce. Środowisko z PyTorch zajmie kilka GB.",
        )
    return Finding("Dysk", "ok", f"{free:.0f} GB wolnego")


def check_python() -> Finding:
    version = ".".join(map(str, sys.version_info[:3]))
    if sys.version_info[:2] != (3, 12):
        return Finding(
            "Python",
            "fail",
            f"{version}, kurs wymaga 3.12",
            "Uruchamiaj polecenia przez `uv run`, a nie systemowym Pythonem.",
        )
    return Finding("Python", "ok", version)


def check_system_libraries() -> Finding:
    """LightGBM needs the OpenMP runtime, which minimal Ubuntu images lack."""
    try:
        ctypes.CDLL("libgomp.so.1")
    except OSError:
        return Finding(
            "Biblioteki systemowe",
            "fail",
            "brak libgomp (wymaga jej LightGBM)",
            "sudo apt install -y libgomp1",
        )
    return Finding("Biblioteki systemowe", "ok", "libgomp dostępna")


def check_uv() -> Finding:
    version = _run("uv", "--version")
    if version is None:
        return Finding(
            "uv",
            "fail",
            "nie znaleziono",
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
        )
    return Finding("uv", "ok", version)


def check_git() -> list[Finding]:
    if _run("git", "--version") is None:
        return [Finding("git", "fail", "nie znaleziono", "sudo apt install git")]
    findings = []
    name = _run("git", "config", "user.name")
    email = _run("git", "config", "user.email")
    if name and email:
        findings.append(Finding("git", "ok", f"{name} <{email}>"))
    else:
        findings.append(
            Finding(
                "git",
                "fail",
                "brak user.name lub user.email",
                'git config --global user.name "Imię Nazwisko" oraz '
                'git config --global user.email "ty@example.com"',
            )
        )
    remotes = (_run("git", "-C", str(paths.ROOT), "remote") or "").split()
    if "upstream" in remotes:
        findings.append(Finding("Remote upstream", "ok", "ustawiony"))
    else:
        findings.append(
            Finding(
                "Remote upstream",
                "warn",
                "brak, nie pobierzesz aktualizacji kursu ani rozwiązań",
                "git remote add upstream https://github.com/RedHot099/mle-course.git",
            )
        )
    return findings


def check_data() -> Finding:
    missing = [d.path.name for d in datasets.DATASETS if not datasets.is_ready(d)]
    if missing:
        return Finding(
            "Dane",
            "fail",
            f"brak lub uszkodzone: {', '.join(missing)}",
            "uv run course data",
        )
    return Finding("Dane", "ok", "wszystkie zbiory pobrane, sumy kontrolne zgodne")


def check_editor() -> Finding:
    if _run("code", "--version") is None:
        fix = (
            "Zainstaluj VS Code w Windows z rozszerzeniem WSL. Patrz lekcja 00."
            if is_wsl()
            else "Zainstaluj VS Code i włącz polecenie `code` w terminalu."
        )
        return Finding("VS Code", "warn", "polecenie `code` niedostępne", fix)
    return Finding("VS Code", "ok", "polecenie `code` działa")


def check_docker() -> Finding:
    if _run("docker", "info", "--format", "{{.ServerVersion}}") is None:
        return Finding("Docker", "later", "niedostępny, potrzebny od modułu 15")
    return Finding("Docker", "ok", "działa")


def check_gpu() -> Finding:
    gpu = _run("nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader")
    if gpu is None:
        return Finding("GPU", "later", "nvidia-smi nie działa, potrzebne od modułu 18")
    return Finding("GPU", "ok", gpu.splitlines()[0])


def diagnose() -> list[Finding]:
    """Run every check and return the findings in display order."""
    return [
        check_system(),
        check_repo_location(),
        check_memory(),
        check_disk(),
        check_python(),
        check_system_libraries(),
        check_uv(),
        *check_git(),
        check_data(),
        check_editor(),
        check_docker(),
        check_gpu(),
    ]


def report(findings: list[Finding]) -> str:
    """Format the findings as a table followed by the fixes."""
    width = max(len(f.name) for f in findings)
    lines = ["Środowisko kursu", ""]
    for finding in findings:
        lines.append(
            f"{_SYMBOL[finding.level]} {finding.name.ljust(width)}  {finding.detail}"
        )
        if finding.fix:
            lines.append(f"  {' ' * width}  → {finding.fix}")
    failed = sum(f.level == "fail" for f in findings)
    warned = sum(f.level == "warn" for f in findings)
    lines.append("")
    if failed:
        lines.append(f"Do naprawy: {failed}. Ostrzeżenia: {warned}.")
    elif warned:
        lines.append(f"Możesz zaczynać. Ostrzeżenia: {warned}.")
    else:
        lines.append("Wszystko gotowe.")
    lines.append("Legenda: ✓ działa, ! ostrzeżenie, ✗ do naprawy, · potrzebne później")
    return "\n".join(lines)


def has_failures(findings: list[Finding]) -> bool:
    """Tell whether any finding blocks the course."""
    return any(f.level == "fail" for f in findings)
