"""Mutants for ``freshcast.metrics`` (module 05)."""

from typing import Any

import numpy as np

from coursekit.mutation import Mutant

_METRICS = ("mae", "rmse", "wape", "bias")


def _module() -> Any:
    from freshcast import metrics

    return metrics


def _mae_is_rmse() -> None:
    module = _module()
    module.mae = module.rmse


def _rmse_without_root() -> None:
    module = _module()
    original = module.rmse

    def rmse(actual: Any, predicted: Any, mask: Any = None) -> float:
        return float(original(actual, predicted, mask) ** 2)

    module.rmse = rmse


def _wape_is_mean_of_ratios() -> None:
    module = _module()
    prepare = module.prepare

    def wape(actual: Any, predicted: Any, mask: Any = None) -> float:
        a, p = prepare(actual, predicted, mask)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratios = np.abs(a - p) / np.abs(a)
        return float(np.mean(ratios[np.isfinite(ratios)]))

    module.wape = wape


def _bias_sign_flipped() -> None:
    module = _module()
    original = module.bias

    def bias(actual: Any, predicted: Any, mask: Any = None) -> float:
        return float(-original(actual, predicted, mask))

    module.bias = bias


def _mask_ignored() -> None:
    module = _module()
    for name in _METRICS:
        original = getattr(module, name)

        def metric(
            actual: Any, predicted: Any, mask: Any = None, _original: Any = original
        ) -> float:
            return float(_original(actual, predicted, None))

        setattr(module, name, metric)


def _nan_treated_as_zero() -> None:
    module = _module()
    for name in _METRICS:
        original = getattr(module, name)

        def metric(
            actual: Any, predicted: Any, mask: Any = None, _original: Any = original
        ) -> float:
            clean_actual = np.nan_to_num(np.asarray(actual, dtype=float))
            clean_predicted = np.nan_to_num(np.asarray(predicted, dtype=float))
            return float(_original(clean_actual, clean_predicted, mask))

        setattr(module, name, metric)


def _shape_mismatch_truncated() -> None:
    module = _module()
    for name in _METRICS:
        original = getattr(module, name)

        def metric(
            actual: Any, predicted: Any, mask: Any = None, _original: Any = original
        ) -> float:
            a = np.asarray(actual, dtype=float).ravel()
            p = np.asarray(predicted, dtype=float).ravel()
            size = min(a.size, p.size)
            if a.size == p.size:
                return float(_original(actual, predicted, mask))
            return float(_original(a[:size], p[:size], None))

        setattr(module, name, metric)


MUTANTS = [
    Mutant("mae_is_rmse", "mae zwraca to samo co rmse", _mae_is_rmse),
    Mutant("rmse_without_root", "rmse nie wyciąga pierwiastka", _rmse_without_root),
    Mutant(
        "wape_is_mean_of_ratios",
        "wape liczy średnią z błędów procentowych poszczególnych wierszy",
        _wape_is_mean_of_ratios,
    ),
    Mutant("bias_sign_flipped", "bias ma odwrócony znak", _bias_sign_flipped),
    Mutant("mask_ignored", "metryki ignorują argument mask", _mask_ignored),
    Mutant(
        "nan_treated_as_zero",
        "NaN w danych jest po cichu liczony jako zero",
        _nan_treated_as_zero,
    ),
    Mutant(
        "shape_mismatch_truncated",
        "przy różnej długości wejść metryki obcinają dłuższe zamiast zgłosić błąd",
        _shape_mismatch_truncated,
    ),
]
