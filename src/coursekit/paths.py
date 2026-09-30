"""Locations of course files and the learner's local settings."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
STATE_DIR = ROOT / ".course"
CONFIG_FILE = STATE_DIR / "config.toml"
PROGRESS_FILE = STATE_DIR / "progress.json"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

FRN_TRAIN = RAW_DIR / "freshretailnet" / "train.parquet"
FRN_EVAL = RAW_DIR / "freshretailnet" / "eval.parquet"
CAR_PARTS = RAW_DIR / "car_parts" / "car_parts_dataset_with_missing_values.tsf"
ONLINE_RETAIL = RAW_DIR / "online_retail" / "online_retail_II.xlsx"
# Typed parquet copy of the workbook, written once in lab 06 (task 06.1).
ONLINE_RETAIL_CACHE = ONLINE_RETAIL.with_suffix(".parquet")
ONLINE_RETAIL_DAILY = PROCESSED_DIR / "online_retail_daily.parquet"


@dataclass(frozen=True)
class Profile:
    """How much of FreshRetailNet the labs load."""

    name: str
    cities: tuple[int, ...] | None
    series: int
    description: str


PROFILES = {
    "small": Profile(
        "small", (14,), 493, "jedno małe miasto, dla maszyn poniżej 6 GB RAM"
    ),
    "standard": Profile("standard", (3,), 2648, "jedno średnie miasto, domyślny"),
    "full": Profile("full", None, 50000, "wszystkie miasta, moduł 14 i capstone"),
}
DEFAULT_PROFILE = "standard"


def read_profile_name() -> str:
    """Return the profile saved by ``course doctor``, or the default one."""
    if not CONFIG_FILE.is_file():
        return DEFAULT_PROFILE
    with CONFIG_FILE.open("rb") as handle:
        name = tomllib.load(handle).get("profile", DEFAULT_PROFILE)
    if name not in PROFILES:
        allowed = ", ".join(PROFILES)
        raise ValueError(
            f"Nieznany profil {name!r} w {CONFIG_FILE}. Dozwolone: {allowed}."
        )
    return str(name)


def write_profile_name(name: str) -> None:
    """Save the chosen profile to the learner's local config."""
    if name not in PROFILES:
        raise ValueError(f"Nieznany profil {name!r}. Dozwolone: {', '.join(PROFILES)}.")
    STATE_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(f'profile = "{name}"\n', encoding="utf-8")


def active_profile() -> Profile:
    """Return the profile the labs should use on this machine."""
    return PROFILES[read_profile_name()]
