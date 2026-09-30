"""Where MLflow keeps its records on this machine.

This file is given. MLflow can log to a server; for the course everything
stays in two local places: a SQLite file for parameters and metrics, and a
directory for artifacts such as tables and models.
"""

from pathlib import Path

import mlflow

DATABASE = "mlflow.db"
ARTIFACTS = "mlartifacts"


def use_local_tracking(directory: Path, experiment: str) -> str:
    """Point MLflow at ``directory`` and select the experiment, creating it if new.

    Args:
        directory: Where ``mlflow.db`` and ``mlartifacts/`` live. Created if
            missing.
        experiment: Name of the experiment that runs will be logged to.

    Returns:
        The tracking URI. Pass it to ``mlflow ui --backend-store-uri`` to
        browse the runs.
    """
    directory.mkdir(parents=True, exist_ok=True)
    uri = f"sqlite:///{(directory / DATABASE).resolve()}"
    mlflow.set_tracking_uri(uri)
    if mlflow.get_experiment_by_name(experiment) is None:
        artifacts = (directory / ARTIFACTS).resolve().as_uri()
        mlflow.create_experiment(experiment, artifact_location=artifacts)
    mlflow.set_experiment(experiment)
    return uri
