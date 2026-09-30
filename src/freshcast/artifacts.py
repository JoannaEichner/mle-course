"""Saving a trained model together with everything needed to trust it later."""

from datetime import datetime
from pathlib import Path
from typing import Any

from freshcast.models.panel import PanelForecaster

MODEL_FILE = "model.joblib"
METADATA_FILE = "metadata.json"


def model_signature(name: str, moment: datetime) -> str:
    """Return the directory name of a saved model: ``<name>_<YYYYmmdd-HHMMSS>``."""
    raise NotImplementedError("Zadanie 14.2")


def save_model(
    model: PanelForecaster,
    directory: Path,
    name: str,
    metadata: dict[str, Any],
    *,
    moment: datetime | None = None,
) -> Path:
    """Write the model and its metadata to a new, uniquely named directory.

    Args:
        model: A fitted forecaster.
        directory: Parent directory of all saved models.
        name: What the model is, for example ``lightgbm``.
        metadata: Facts about the run: features, parameters, training
            period, scores. Must be JSON-serialisable.
        moment: Time stamp of the run. Defaults to now.

    Returns:
        The directory that was created: ``directory/<signature>``.

    Raises:
        FileExistsError: A model with the same signature already exists.
            Saved models are never overwritten.
    """
    raise NotImplementedError("Zadanie 14.2")


def load_model(model_dir: Path) -> tuple[PanelForecaster, dict[str, Any]]:
    """Read a saved model and its metadata.

    Only load models you saved yourself: ``joblib`` files can run arbitrary
    code when opened.

    Raises:
        FileNotFoundError: The directory lacks the model or the metadata.
    """
    raise NotImplementedError("Zadanie 14.2")
