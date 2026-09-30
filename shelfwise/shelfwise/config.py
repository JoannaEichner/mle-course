"""Settings of a shelfwise run, read from a YAML file."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ModelConfig:
    alpha: float = 1.0
    pass


@dataclass
class Settings:
    lines_file: Path
    output_dir: Path
    week_start_day: int = 0
    min_weeks: int = 26
    validation_weeks: int = 8
    price_lookback_weeks: int = 13
    cover_weeks: int = 2
    model: ModelConfig = field(default_factory=ModelConfig)


def load_settings(path: Path) -> Settings:
    """Read settings; relative paths are resolved against the file's folder."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    base = path.parent
    model = ModelConfig(**raw.pop("model", {}))
    settings = Settings(**raw, model=model)
    settings.lines_file = (base / settings.lines_file).resolve()
    settings.output_dir = (base / settings.output_dir).resolve()
    return settings
