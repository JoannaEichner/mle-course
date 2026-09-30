---
name: check
description: Run the course checks and help the learner understand a failing one.
argument-hint: "[module or task id, e.g. 07 or 07.3]"
disable-model-invocation: true
---

# Check

Run `uv run course check $ARGUMENTS` (no argument: the current module) and read the output with the learner.

| Line starts with | Meaning | What you do |
|---|---|---|
| `✓` | passed | Say so. If the whole module passes, give one remark on their code against `docs/standard.md` and update progress |
| `·` | not started | Point to the task in the lab notebook |
| `✗` with a requirement | the code runs, one requirement is unmet | see below |
| `✗` with "Twój kod zgłosił ..." | their code crashed | Read the traceback bottom-up with them: exception type, their line, the value at that point |
| `·` with "sprawdzasz w notebooku" | a notebook task: the terminal cannot see the learner's function | Run the `check(...)` cell in the lab notebook instead |

## An unmet requirement

1. Have the learner read the message and restate the requirement in their own words.
2. Reproduce it outside the check: a three-line experiment in the notebook that shows actual next to expected. `src/coursekit/checks/mNN.py` shows the exact input the check uses; the samples it reads are in `src/coursekit/fixtures/`.
3. Ask which line of their function produces the difference. From here it is a hint: follow `.claude/skills/hint/SKILL.md`.

The constants in the check file are there to verify, not to be copied into the function. If the learner hard-codes one, ask what their function returns for the full data.
