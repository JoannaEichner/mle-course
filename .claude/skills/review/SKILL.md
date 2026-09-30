---
name: review
description: Checkpoint review of the learner's branch against the engineering standard.
disable-model-invocation: true
---

# Review

Review the learner's branch the way a colleague reviews a pull request. The output is findings and questions. The learner writes every fix.

| Checkpoint | After module | Covers |
|---|---|---|
| 1 | 04 | modules 01-04 |
| 2 | 11 | modules 05-11 |
| 3 | 16 | modules 12-16 |
| 4 | 19 | modules 17-19 and the capstone report |

## Steps

1. **Gather.** `git status`, `git log --oneline main..HEAD`, `git diff main...HEAD`. Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run pytest` and `uv run course check` for the checkpoint's modules. Done when you hold every output.
2. **Read the whole diff against `docs/standard.md`.** Every rule that is in force for the checkpoint's modules, applied to every changed file. Done when each rule is either satisfied or has a finding.
3. **Report in Polish**, in this order:
   - the verdict: "do scalenia" or "do poprawy",
   - blocking findings: a failing check, test or linter; a violated rule marked **blokuje**; a correctness or leakage bug. For each: `file:line`, the rule id, a concrete input that goes wrong, and a question or direction for the fix,
   - up to five non-blocking findings, most valuable first,
   - one specific thing done well.
4. **Record** the verdict and recurring issues in `.course/progress.md`. A second review of the same branch starts from the earlier findings.
