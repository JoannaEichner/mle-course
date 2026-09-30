"""Choosing where tensors live, and making runs repeatable."""

import logging

import torch

logger = logging.getLogger(__name__)


def pick_device(prefer_gpu: bool = True) -> torch.device:
    """Return the CUDA device when one is usable and wanted, else the CPU.

    The choice is logged, so a run that silently fell back to the CPU is
    visible in the output instead of just being slow.
    """
    raise NotImplementedError("Zadanie 18.1")


def seed_everything(seed: int) -> None:
    """Seed Python, NumPy and PyTorch (CPU and every GPU).

    Seeds make runs repeatable on the same machine. Some GPU kernels are
    not deterministic, so two GPU runs can still differ in the last digits.
    """
    raise NotImplementedError("Zadanie 18.1")
