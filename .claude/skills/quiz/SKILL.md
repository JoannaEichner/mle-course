---
name: quiz
description: Five oral-exam style questions on a module.
argument-hint: "[module, e.g. 07]"
disable-model-invocation: true
---

# Quiz

Module: `$ARGUMENTS` (default: the current one).

Sources: the lecture's sections and rules, the quiz bank in `tutor/notes/NN.md`, the weak spots in `.course/progress.md`.

1. Ask five questions, one at a time, and wait for each answer. Mix the kinds: predict the output of tiny code, find the bug, explain why a rule exists, say what you would check first. Write new questions; the lecture's own quizzes are already done.
2. After each answer: right or wrong, and why in one sentence. After a wrong one, ask a follow-up that isolates the misconception.
3. Close with the score, the one topic to revisit with its lecture section, and a note in `.course/progress.md`.
