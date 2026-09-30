"""The ``course`` command."""

import argparse
import sys

from coursekit import catchup, checking, datasets, doctor, paths


def _doctor(_: argparse.Namespace) -> int:
    findings = doctor.diagnose()
    print(doctor.report(findings))
    if not paths.CONFIG_FILE.is_file():
        paths.write_profile_name(doctor.recommended_profile(doctor.total_memory_gb()))
    profile = paths.active_profile()
    print(f"\nProfil danych: {profile.name} ({profile.description})")
    print("Zmienisz go poleceniem: uv run course profile <small|standard|full>")
    return 1 if doctor.has_failures(findings) else 0


def _data(_: argparse.Namespace) -> int:
    datasets.download_all()
    return 0


def _check(args: argparse.Namespace) -> int:
    results = checking.run(checking.select(args.selector))
    checking.record(results)
    print(checking.report(results))
    return 0 if all(r.status == "ok" for r in results) else 1


def _profile(args: argparse.Namespace) -> int:
    if args.name:
        paths.write_profile_name(args.name)
    for profile in paths.PROFILES.values():
        mark = "→" if profile.name == paths.read_profile_name() else " "
        print(
            f"{mark} {profile.name:<9} {profile.series:>6} serii  {profile.description}"
        )
    return 0


def _catchup(args: argparse.Namespace) -> int:
    rewritten = catchup.catch_up(args.module)
    if not rewritten:
        print(f"Przed modułem {args.module:02d} nie ma zadań w pakiecie.")
        return 0
    print(f"Wpisano kod referencyjny modułów przed {args.module:02d}:")
    for path in rewritten:
        print(f"  {path}")
    print("Poprzednie wersje plików są w .course/backup/.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="course", description="Narzędzia kursu ML Engineering from Scratch."
    )
    commands = parser.add_subparsers(required=True, metavar="polecenie")

    sub = commands.add_parser("doctor", help="sprawdź środowisko")
    sub.set_defaults(handler=_doctor)

    sub = commands.add_parser("data", help="pobierz dane kursu")
    sub.set_defaults(handler=_data)

    sub = commands.add_parser(
        "check", help="sprawdź zadania, np. `check 07` lub `check 07.2`"
    )
    sub.add_argument(
        "selector", nargs="?", help="numer modułu albo zadania; puste = wszystko"
    )
    sub.set_defaults(handler=_check)

    sub = commands.add_parser("profile", help="pokaż albo ustaw profil danych")
    sub.add_argument("name", nargs="?", choices=list(paths.PROFILES))
    sub.set_defaults(handler=_profile)

    sub = commands.add_parser(
        "catchup", help="wpisz kod referencyjny modułów przed podanym, np. `catchup 08`"
    )
    sub.add_argument("module", type=int)
    sub.set_defaults(handler=_catchup)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command and return the process exit code."""
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (ValueError, RuntimeError) as error:
        print(f"Błąd: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
