"""Helpers for lab notebooks."""

import os
from typing import Any

from coursekit import checking


def check(task_id: str, target: Any = None) -> None:
    """Run the check for one task and print the outcome under the cell.

    Args:
        task_id: Task id such as ``07.2``.
        target: The object to check, for tasks solved inside the notebook.
            Leave empty for tasks solved in the ``freshcast`` package.
    """
    results = checking.run(checking.select(task_id), target)
    checking.record(results)
    for result in results:
        symbol = {"ok": "✅", "todo": "⬜", "fail": "❌", "error": "❌"}[result.status]
        print(f"{symbol} {result.task.id}  {result.task.title}")
        if result.message:
            print(f"   {result.message}")
    # Course verification runs solved notebooks with COURSE_STRICT=1, so a
    # graded check that fails there stops the notebook instead of printing a
    # cross. Ungraded tasks, such as the capstone report, may stay open.
    if os.environ.get("COURSE_STRICT") == "1":
        failed = [r for r in results if r.status != "ok" and r.task.graded]
        if failed:
            raise AssertionError(f"{failed[0].task.id}: {failed[0].message}")
