"""A registry of features and the order in which to compute them.

Every feature is a pure function from the frame to one Series, and it
declares which columns it reads. Those declarations form a graph. Building a
set of features means walking that graph so that each input exists before
the function that needs it runs.
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass

import pandas as pd

Compute = Callable[[pd.DataFrame], pd.Series]


@dataclass(frozen=True)
class Feature:
    """One feature: its name, the columns it reads and how to compute it."""

    name: str
    requires: tuple[str, ...]
    compute: Compute


class Registry:
    """Features by name."""

    def __init__(self) -> None:
        self.features: dict[str, Feature] = {}

    def register(
        self, name: str, requires: Iterable[str] = ()
    ) -> Callable[[Compute], Compute]:
        """Return a decorator that adds the decorated function as a feature.

        Raises:
            ValueError: The name is already taken.
        """

        def decorate(compute: Compute) -> Compute:
            if name in self.features:
                raise ValueError(f"Feature {name!r} is registered twice.")
            self.features[name] = Feature(name, tuple(requires), compute)
            return compute

        return decorate


def resolve_order(
    names: Iterable[str], features: Mapping[str, Feature], available: Iterable[str]
) -> list[str]:
    """Return the features to compute, each after everything it requires.

    Args:
        names: The features that were asked for.
        features: All known features by name.
        available: Columns the frame already has.

    Returns:
        Names of the requested features and of every registered feature they
        depend on, directly or through other features. No name appears
        twice. Columns that are already available are not in the list.

    Raises:
        ValueError: A requested or required name is neither a registered
            feature nor an available column, or the requirements form a cycle.
    """
    raise NotImplementedError("Zadanie 09.5")


def build_features(
    df: pd.DataFrame, names: Iterable[str], features: Mapping[str, Feature]
) -> pd.DataFrame:
    """Return ``df`` with the requested features and their dependencies added.

    Args:
        df: The panel. It is not modified.
        names: Features to add.
        features: All known features by name.

    Raises:
        ValueError: A feature returned a Series whose index differs from the
            frame's, which would silently misalign its values.
    """
    raise NotImplementedError("Zadanie 09.5")
