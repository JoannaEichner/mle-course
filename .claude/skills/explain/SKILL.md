---
name: explain
description: Explain a concept from the course with a runnable example.
argument-hint: "[concept, e.g. rolling]"
disable-model-invocation: true
---

# Explain

Concept: `$ARGUMENTS`.

1. **Locate.** Find where the course teaches it (`grep` in `lectures/`, `docs/glossary.md`) and use the course's words and examples.
2. **Ask** what they think it means, in one question. Skip if they just told you.
3. **Explain** in at most six sentences, anchored in the course data. Follow with a demo of 3-8 lines on a toy table: run it and show the output. When the point is a surprise, have them predict the output first.
4. **Check** with one question that needs the concept applied, not recited. After a wrong answer, take a different angle (an analogy, a drawn table, a counter-example), not the same explanation again.
5. **Point** to the lecture section. Record in `.course/progress.md` when it took more than one angle.
