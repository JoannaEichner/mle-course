"""Linear regression trained by gradient descent, written out in NumPy.

Nothing here is used in production: scikit-learn does the same job better.
It exists so that "the model learns" stops being a figure of speech.
"""

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def predict_linear(X: FloatArray, weights: FloatArray, intercept: float) -> FloatArray:
    """Return ``X @ weights + intercept``: one prediction per row of ``X``."""
    raise NotImplementedError("Zadanie 08.3")


def mse(actual: FloatArray, predicted: FloatArray) -> float:
    """Mean squared error: the loss that gradient descent minimises here."""
    raise NotImplementedError("Zadanie 08.3")


def mse_gradient(
    X: FloatArray, y: FloatArray, weights: FloatArray, intercept: float
) -> tuple[FloatArray, float]:
    """Return the gradient of the MSE with respect to weights and intercept.

    With ``error = prediction - y`` and ``n`` rows:

    - for the weights: ``2 / n * X.T @ error``,
    - for the intercept: ``2 / n * error.sum()``.

    Returns:
        ``(gradient_of_weights, gradient_of_intercept)``.
    """
    raise NotImplementedError("Zadanie 08.3")


def fit_linear_gd(
    X: FloatArray, y: FloatArray, *, learning_rate: float, steps: int
) -> tuple[FloatArray, float, list[float]]:
    """Fit a linear model by gradient descent, starting from all zeros.

    Every step moves the parameters against the gradient, by
    ``learning_rate`` times the gradient.

    Args:
        X: Features, shape ``(n, k)``. Scale them first: columns on very
            different scales make one learning rate fit none of them.
        y: Target, shape ``(n,)``.
        learning_rate: Size of each step, above 0.
        steps: Number of steps, at least 1.

    Returns:
        ``(weights, intercept, losses)`` where ``losses[i]`` is the MSE
        before step ``i``, so ``losses[0]`` is the loss of the all-zero model.

    Raises:
        ValueError: ``learning_rate`` is not positive, ``steps`` is below 1,
            or the loss stopped being finite, which means the learning rate
            is too large.
    """
    raise NotImplementedError("Zadanie 08.3")
