---
name: hint
description: One hint for the task the learner is stuck on, never the solution.
argument-hint: "[task id, e.g. 07.3]"
disable-model-invocation: true
---

# Hint

Task: `$ARGUMENTS`. If empty, take the task of the file they are working on or the last failing entry in `.course/progress.json`, and confirm it with them.

## The hint ladder

| Rung | Gives | Example for "lag within a series" |
|---|---|---|
| 1. Direction | which concept or lecture section applies | "Which operations keep one row per input row?" |
| 2. Approach | the steps in words, the function names, the pitfall | "Group by the series key, then shift inside each group. What happens on the first days?" |
| 3. Near-code | the shape of the code with the key line left open, or a pointed question about the exact wrong line | "`df.groupby(...)[column].___(lag)`: what goes in the gap?" |

One rung per request, the lowest one that can unblock them. The same task again gets the next rung.

## Steps

1. **Look before you speak.** Read the task's docstring, the learner's current code for it and the task's entry in `tutor/notes/NN.md`. Run `uv run course check <task>`. Done when you can say in one sentence where they are stuck: not started, wrong idea, right idea with a wrong detail, or working code that fails one requirement.
2. **Ask** what they tried and what they expected, unless they already said.
3. **Give one rung.** Record the rung and the sticking point in `.course/progress.md`.
4. **After rung 3**, build a worked example of the same technique on a different toy table with different column names, run it and show the output. Then tell them the reference is on the `solutions` branch and `uv run course catchup` exists. Whether to look is their call.
5. **End** with a question or a concrete next action for them.

## Branches

- They ask for the solution outright: say in one sentence that you will not write it and what they gain from that, then offer the next rung.
- Their code already passes: say so, and offer one remark on it against `docs/standard.md`.
- They are stuck on a concept, not on the task: switch to `.claude/skills/explain/SKILL.md`.
