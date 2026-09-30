"""Calling again what failed for a reason that may pass by itself.

A network call can fail because the server is busy or the connection broke,
and the same call made a moment later works. A call can also fail for good:
the object does not exist, the password is wrong. Retrying the second kind
only delays the error, so every retry here is decided by a predicate the
caller supplies.
"""

import logging
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def retry(
    *,
    retry_if: Callable[[Exception], bool],
    attempts: int = 3,
    base_delay: float = 0.5,
    factor: float = 2.0,
    max_delay: float = 10.0,
    sleep: Callable[[float], None] = time.sleep,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Build a decorator that calls a function again after a transient failure.

    The decorated function is called at most ``attempts`` times in all. After
    the k-th failure that ``retry_if`` accepts, the decorator waits
    ``min(base_delay * factor ** (k - 1), max_delay)`` seconds, then tries
    again. With the defaults the waits are 0.5 s and 1 s. There is no wait
    after the last attempt. The delays carry no random jitter: add it when
    many clients may retry in the same second.

    A failure that ``retry_if`` rejects is raised at once, and the failure of
    the last attempt is raised as it is. Only ``Exception`` is considered:
    ``KeyboardInterrupt`` always stops the program.

    Args:
        retry_if: Called with the exception; True means retrying may help.
        attempts: Total number of calls, at least 1. 1 means never retry.
        base_delay: Wait after the first failure, in seconds, at least 0.
        factor: How much longer each wait is than the one before, at least 1.
        max_delay: Upper limit of a single wait, in seconds.
        sleep: Waits for the given number of seconds. Tests pass a recorder
            here so that they do not really wait.

    Returns:
        A decorator. The decorated function keeps its name and docstring,
        takes the same arguments and returns the same value.

    Raises:
        ValueError: ``attempts`` is below 1, ``base_delay`` or ``max_delay``
            is negative, or ``factor`` is below 1. Raised by this call, not
            by the first use of the decorated function.
    """
    raise NotImplementedError("Zadanie 15.2")
