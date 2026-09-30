"""Solution blocks: the single source for exercise stubs and reference code.

Reference files on the ``solutions`` branch wrap every piece of code the
learner is asked to write in a block::

    result = ...  # optional placeholder shown to the learner

Rendering a file keeps the reference code of solved blocks and replaces the
others with their stub. Marker lines never survive rendering.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field

_START = re.compile(r"^(?P<indent>[ \t]*)# >>> SOLUTION (?P<task>\d{2}\.\d+[a-z]?)\s*$")
_STUB = re.compile(r"^[ \t]*# --- STUB\s*$")
_END = re.compile(r"^[ \t]*# <<< SOLUTION\s*$")
_STUB_LINE = re.compile(r"^(?P<indent>[ \t]*)#\| ?(?P<text>.*)$")


@dataclass
class Block:
    """One solution block: the reference lines and the stub that replaces them."""

    task: str
    indent: str
    solution: list[str] = field(default_factory=list)
    stub: list[str] = field(default_factory=list)
    in_stub: bool = False

    def add(self, line: str, number: int) -> None:
        """Add a line to the solution or, after the stub marker, to the stub."""
        if _STUB.match(line):
            self.in_stub = True
        elif not self.in_stub:
            self.solution.append(line)
        elif stub_line := _STUB_LINE.match(line):
            self.stub.append((stub_line["indent"] + stub_line["text"]).rstrip())
        else:
            raise ValueError(f"Line {number}: stub lines must start with '#|'.")

    def lines(self, solved: bool) -> list[str]:
        """Return the reference lines, or the stub when the block is unsolved."""
        if solved:
            return self.solution
        default = f'{self.indent}raise NotImplementedError("Zadanie {self.task}")'
        return self.stub or [default]


def module_of(task_id: str) -> int:
    """Return the module number of a task id such as ``07.2``."""
    return int(task_id.split(".")[0])


def parse(text: str) -> list[str | Block]:
    """Split ``text`` into plain lines and solution blocks.

    Raises:
        ValueError: A block is left open, nested or closed twice.
    """
    parts: list[str | Block] = []
    block: Block | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        start = _START.match(line)
        if start and block is not None:
            raise ValueError(f"Line {number}: block {block.task} is still open.")
        if start:
            block = Block(start["task"], start["indent"])
        elif _END.match(line):
            if block is None:
                raise ValueError(f"Line {number}: end marker without a start.")
            parts.append(block)
            block = None
        elif block is not None:
            block.add(line, number)
        else:
            parts.append(line)
    if block is not None:
        raise ValueError(f"Block {block.task} is never closed.")
    return parts


def task_ids(text: str) -> list[str]:
    """Return the task ids of all solution blocks in ``text``, in order."""
    return [part.task for part in parse(text) if isinstance(part, Block)]


def render(text: str, is_solved: Callable[[str], bool]) -> str:
    """Return ``text`` with every solution block resolved.

    Args:
        text: File content with solution blocks.
        is_solved: Called with a task id; True keeps the reference code,
            False puts the stub in its place.
    """
    out: list[str] = []
    for part in parse(text):
        if isinstance(part, Block):
            out.extend(part.lines(is_solved(part.task)))
        else:
            out.append(part)
    ending = "\n" if text.endswith("\n") else ""
    return "\n".join(out) + ending
