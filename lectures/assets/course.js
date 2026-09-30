/* ML Engineering from Scratch: shared lecture behaviour.
   No build step, no dependencies besides the vendored highlight.js and,
   for runnable Python, Pyodide from its CDN. */

(function () {
  "use strict";

  const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";
  const MODULE = document.body.dataset.module || "index";
  const LETTERS = "ABCDEFGH";

  /* ---------- storage ---------- */

  const store = {
    get(key, fallback) {
      try {
        const raw = localStorage.getItem("mle:" + key);
        return raw === null ? fallback : JSON.parse(raw);
      } catch (error) {
        return fallback;
      }
    },
    set(key, value) {
      try {
        localStorage.setItem("mle:" + key, JSON.stringify(value));
      } catch (error) {
        /* private mode or file:// without storage: progress is just not kept */
      }
    },
  };

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([name, value]) => {
      if (name === "class") node.className = value;
      else if (name === "text") node.textContent = value;
      else if (name === "html") node.innerHTML = value;
      else if (name.startsWith("on")) node.addEventListener(name.slice(2), value);
      else if (value !== false && value !== null) node.setAttribute(name, value);
    });
    [].concat(children || []).forEach((child) => {
      if (child) node.append(child);
    });
    return node;
  }

  /* ---------- theme ---------- */

  function initTheme() {
    const saved = store.get("theme", null);
    if (saved) document.documentElement.dataset.theme = saved;
    const button = document.getElementById("theme-toggle");
    if (!button) return;
    button.addEventListener("click", () => {
      const dark =
        document.documentElement.dataset.theme === "dark" ||
        (!document.documentElement.dataset.theme &&
          matchMedia("(prefers-color-scheme: dark)").matches);
      const next = dark ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      store.set("theme", next);
    });
  }

  /* ---------- table of contents and reading progress ---------- */

  function initToc() {
    const list = document.querySelector(".toc ol");
    const sections = [...document.querySelectorAll(".lecture section[id]")];
    if (!list || !sections.length) return;
    const links = new Map();
    sections.forEach((section) => {
      const heading = section.querySelector("h2");
      if (!heading) return;
      const link = el("a", { href: "#" + section.id, text: heading.textContent });
      links.set(section, link);
      list.append(el("li", {}, link));
    });
    const spy = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          links.forEach((link) => link.classList.remove("current"));
          const link = links.get(entry.target);
          if (link) link.classList.add("current");
        });
      },
      { rootMargin: "-20% 0px -70% 0px" }
    );
    sections.forEach((section) => spy.observe(section));
  }

  function initProgressLine() {
    const line = document.querySelector(".progress-line");
    if (!line) return;
    const update = () => {
      const max = document.documentElement.scrollHeight - innerHeight;
      line.style.width = (max > 0 ? (scrollY / max) * 100 : 0) + "%";
    };
    addEventListener("scroll", update, { passive: true });
    update();
  }

  /* ---------- code blocks ---------- */

  function initCode() {
    document.querySelectorAll("pre > code").forEach((code) => {
      if (window.hljs && /language-/.test(code.className)) {
        window.hljs.highlightElement(code);
      }
      const pre = code.parentElement;
      if (pre.closest(".no-copy")) return;
      const button = el("button", { class: "copy-button", type: "button", text: "Kopiuj" });
      button.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(code.textContent);
          button.textContent = "Skopiowano";
        } catch (error) {
          button.textContent = "Zaznacz ręcznie";
        }
        setTimeout(() => (button.textContent = "Kopiuj"), 1500);
      });
      pre.append(button);
    });
  }

  /* ---------- quizzes ---------- */

  const quizzes = [];

  function quizKey(id) {
    return "quiz:" + MODULE + ":" + id;
  }

  function updateScore() {
    const done = quizzes.filter((quiz) => quiz.done).length;
    const score = document.querySelector(".topbar .score");
    if (score && quizzes.length) score.textContent = `Quizy ${done}/${quizzes.length}`;
    if (quizzes.length) store.set("progress:" + MODULE, { done, total: quizzes.length });
  }

  function initQuiz(root) {
    const id = root.id;
    const multi = root.dataset.type === "multi";
    const list = root.querySelector(".quiz-options");
    if (!id || !list) return null;

    const state = el("span", { class: "state" });
    const kind = root.classList.contains("predict") ? "Przewidź wynik" : "Quiz";
    root.prepend(el("div", { class: "quiz-tag" }, [el("span", { text: kind }), state]));

    const options = [...list.children].map((item, index) => {
      const why = item.querySelector(".why");
      if (why) why.remove();
      const button = el("button", {
        class: "quiz-option",
        type: "button",
        "aria-pressed": "false",
      });
      const text = el("span", { class: "text" });
      text.innerHTML = item.innerHTML;
      button.append(el("span", { class: "mark", text: LETTERS[index] }), text);
      if (why) button.append(why);
      item.replaceChildren(button);
      return { button, correct: item.hasAttribute("data-correct") };
    });

    const feedback = el("span", { class: "quiz-feedback", role: "status" });
    const actions = el("div", { class: "quiz-actions" });
    root.append(actions);

    const quiz = { id, done: false, attempts: 0, actions, onAnswer: null };

    function finish(restored) {
      quiz.done = true;
      options.forEach(({ button, correct }) => {
        button.disabled = true;
        button.classList.toggle("right", correct);
        if (!correct && !button.classList.contains("wrong")) {
          button.classList.add("reveal");
        }
      });
      state.textContent = "zaliczone";
      state.classList.add("done");
      if (!restored) {
        store.set(quizKey(id), { done: true, attempts: quiz.attempts });
        feedback.textContent =
          quiz.attempts === 1 ? "Dobrze, za pierwszym razem." : "Dobrze.";
      }
      reset.hidden = false;
      if (check) check.hidden = true;
      updateScore();
    }

    function clear() {
      quiz.done = false;
      quiz.attempts = 0;
      options.forEach(({ button }) => {
        button.disabled = false;
        button.classList.remove("right", "wrong", "reveal");
        button.setAttribute("aria-pressed", "false");
      });
      state.textContent = "";
      state.classList.remove("done");
      feedback.textContent = "";
      reset.hidden = true;
      if (check) check.hidden = false;
      store.set(quizKey(id), { done: false, attempts: 0 });
      updateScore();
    }

    const reset = el("button", {
      class: "button quiet",
      type: "button",
      text: "Jeszcze raz",
      hidden: "",
      onclick: clear,
    });

    let check = null;
    if (multi) {
      check = el("button", { class: "button", type: "button", text: "Sprawdź" });
      check.addEventListener("click", () => {
        quiz.attempts += 1;
        let allRight = true;
        options.forEach(({ button, correct }) => {
          const chosen = button.getAttribute("aria-pressed") === "true";
          button.classList.remove("right", "wrong");
          if (chosen) button.classList.add(correct ? "right" : "wrong");
          if (chosen !== correct) allRight = false;
        });
        if (quiz.onAnswer) quiz.onAnswer();
        if (allRight) finish(false);
        else feedback.textContent = "Jeszcze nie. Popraw zaznaczenie i sprawdź ponownie.";
      });
      options.forEach(({ button }) => {
        button.addEventListener("click", () => {
          const pressed = button.getAttribute("aria-pressed") === "true";
          button.setAttribute("aria-pressed", String(!pressed));
          button.classList.remove("right", "wrong");
        });
      });
      actions.append(check);
    } else {
      options.forEach(({ button, correct }) => {
        button.addEventListener("click", () => {
          quiz.attempts += 1;
          if (quiz.onAnswer) quiz.onAnswer();
          if (correct) {
            finish(false);
          } else {
            button.classList.add("wrong");
            button.disabled = true;
            feedback.textContent = "To nie to. Przeczytaj wyjaśnienie i wybierz ponownie.";
          }
        });
      });
    }
    actions.append(reset, feedback);

    const saved = store.get(quizKey(id), null);
    if (saved && saved.done) {
      quiz.attempts = saved.attempts || 1;
      finish(true);
    }
    quizzes.push(quiz);
    return quiz;
  }

  /* ---------- Python in the browser ---------- */

  let pyodideReady = null;

  function loadPyodideOnce() {
    if (!pyodideReady) {
      pyodideReady = new Promise((resolve, reject) => {
        const script = el("script", { src: PYODIDE_URL + "pyodide.js" });
        script.onload = () =>
          window.loadPyodide({ indexURL: PYODIDE_URL }).then(resolve, reject);
        script.onerror = () =>
          reject(new Error("Nie udało się pobrać Pyodide. Sprawdź połączenie z siecią."));
        document.head.append(script);
      }).catch((error) => {
        pyodideReady = null;
        throw error;
      });
    }
    return pyodideReady;
  }

  function trimTraceback(message) {
    const lines = String(message).trimEnd().split("\n");
    const start = lines.findIndex((line) => line.includes('File "<exec>"'));
    const kept = start >= 0 ? lines.slice(start) : lines.slice(-3);
    return "Traceback (most recent call last):\n" + kept.join("\n");
  }

  /* Runs each code string in order in one fresh namespace.
     Returns { output, error } where error is null on success. */
  async function runPython(codes) {
    const py = await loadPyodideOnce();
    let output = "";
    py.setStdout({ batched: (text) => (output += text + "\n") });
    py.setStderr({ batched: (text) => (output += text + "\n") });
    const namespace = py.globals.get("dict")();
    try {
      for (const code of codes) {
        await py.runPythonAsync(code, { globals: namespace });
      }
      return { output, error: null };
    } catch (error) {
      return { output, error: trimTraceback(error.message) };
    } finally {
      namespace.destroy();
    }
  }

  function runButton(label, handler) {
    const button = el("button", { class: "button quiet", type: "button", text: label });
    button.addEventListener("click", async () => {
      const original = button.textContent;
      button.disabled = true;
      button.textContent = pyodideReady ? "Uruchamiam…" : "Ładuję Pythona…";
      try {
        await handler();
      } finally {
        button.disabled = false;
        button.textContent = original;
      }
    });
    return button;
  }

  function show(outputNode, result, okText) {
    outputNode.classList.remove("ok", "fail");
    let text = (result.output + (result.error ? result.error : "")).trimEnd();
    if (!result.error && okText) text = (text ? text + "\n\n" : "") + okText;
    outputNode.textContent = text || "(brak wyjścia)";
    if (result.error) outputNode.classList.add("fail");
  }

  function initPredict(root) {
    const quiz = initQuiz(root);
    const code = root.querySelector("pre > code");
    if (!code) return;
    const source = code.textContent;
    const output = el("pre", { class: "py-output no-copy", "aria-live": "polite" });
    const run = runButton("Uruchom kod", async () => {
      try {
        show(output, await runPython([source]));
      } catch (error) {
        show(output, { output: "", error: error.message });
      }
    });
    if (quiz) {
      run.hidden = !quiz.done && quiz.attempts === 0;
      quiz.onAnswer = () => (run.hidden = false);
      quiz.actions.prepend(run);
      quiz.actions.after(output);
    } else {
      root.append(el("div", { class: "quiz-actions" }, run), output);
    }
  }

  function initPyrun(root) {
    const id = root.id;
    const starter = root.querySelector('script[data-role="starter"]');
    const test = root.querySelector('script[data-role="test"]');
    if (!id || !starter) return;
    const key = "code:" + MODULE + ":" + id;
    const initial = starter.textContent.replace(/^\n/, "").trimEnd() + "\n";

    const state = el("span", { class: "state" });
    root.prepend(el("div", { class: "quiz-tag" }, [el("span", { text: "Ćwiczenie" }), state]));

    const area = el("textarea", {
      spellcheck: "false",
      autocapitalize: "off",
      autocomplete: "off",
      "aria-label": "Kod Pythona",
    });
    area.value = store.get(key, initial);
    area.rows = Math.max(6, area.value.split("\n").length + 1);
    area.addEventListener("input", () => store.set(key, area.value));
    area.addEventListener("keydown", (event) => {
      if (event.key !== "Tab") return;
      event.preventDefault();
      const at = area.selectionStart;
      area.setRangeText("    ", at, area.selectionEnd, "end");
      store.set(key, area.value);
    });

    const output = el("pre", { class: "py-output no-copy", "aria-live": "polite" });
    const quiz = { id, done: false, attempts: 0 };
    const actions = el("div", { class: "quiz-actions" });

    function markDone(restored) {
      quiz.done = true;
      state.textContent = "zaliczone";
      state.classList.add("done");
      if (!restored) store.set(quizKey(id), { done: true, attempts: quiz.attempts });
      updateScore();
    }

    actions.append(
      runButton("Uruchom", async () => {
        try {
          show(output, await runPython([area.value]));
        } catch (error) {
          show(output, { output: "", error: error.message });
        }
      })
    );
    if (test) {
      const check = runButton("Sprawdź", async () => {
        quiz.attempts += 1;
        let result;
        try {
          result = await runPython([area.value, test.textContent]);
        } catch (error) {
          result = { output: "", error: error.message };
        }
        show(output, result, "Wszystkie testy przeszły.");
        if (!result.error) {
          output.classList.add("ok");
          markDone(false);
        }
      });
      check.classList.remove("quiet");
      actions.append(check);
    }
    actions.append(
      el("button", {
        class: "button quiet",
        type: "button",
        text: "Przywróć kod startowy",
        onclick: () => {
          area.value = initial;
          store.set(key, initial);
          output.textContent = "";
          output.classList.remove("ok", "fail");
        },
      })
    );
    root.append(area, actions, output);

    if (test) {
      const saved = store.get(quizKey(id), null);
      if (saved && saved.done) markDone(true);
      quizzes.push(quiz);
    }
  }

  /* ---------- checklists and tabs ---------- */

  function initSteps() {
    document.querySelectorAll(".step").forEach((step) => {
      const box = step.querySelector(".tick input");
      if (!box || !step.id) return;
      const key = "step:" + MODULE + ":" + step.id;
      const apply = () => step.classList.toggle("done", box.checked);
      box.checked = store.get(key, false);
      apply();
      box.addEventListener("change", () => {
        store.set(key, box.checked);
        apply();
        updateSteps();
      });
    });
    updateSteps();
  }

  function updateSteps() {
    const steps = [...document.querySelectorAll(".step .tick input")];
    if (!steps.length) return;
    const done = steps.filter((box) => box.checked).length;
    const score = document.querySelector(".topbar .score");
    if (score) score.textContent = `Kroki ${done}/${steps.length}`;
    store.set("progress:" + MODULE, { done, total: steps.length });
  }

  function initTabs() {
    document.querySelectorAll(".tabs").forEach((tabs) => {
      const group = tabs.dataset.group;
      const buttons = [...tabs.querySelectorAll(".segmented button")];
      const select = (name) => {
        buttons.forEach((button) =>
          button.setAttribute("aria-pressed", String(button.dataset.tab === name))
        );
        document
          .querySelectorAll(`.tab-panel[data-group="${group}"]`)
          .forEach((panel) => (panel.hidden = panel.dataset.tab !== name));
        store.set("tab:" + group, name);
      };
      buttons.forEach((button) =>
        button.addEventListener("click", () => select(button.dataset.tab))
      );
      select(store.get("tab:" + group, buttons[0].dataset.tab));
    });
  }

  /* ---------- course map ---------- */

  function initMap() {
    document.querySelectorAll(".module[data-module]").forEach((card) => {
      const progress = store.get("progress:" + card.dataset.module, null);
      const side = card.querySelector(".side");
      if (!progress || !side || !progress.total) return;
      const complete = progress.done === progress.total;
      side.append(
        el("span", {
          class: "pill" + (complete ? " done" : ""),
          text: `${progress.done}/${progress.total}`,
        })
      );
    });
  }

  /* ---------- boot ---------- */

  window.Course = { el, store, runPython };

  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initToc();
    initProgressLine();
    initCode();
    document.querySelectorAll(".quiz").forEach(initQuiz);
    document.querySelectorAll(".predict").forEach(initPredict);
    document.querySelectorAll(".pyrun").forEach(initPyrun);
    initSteps();
    initTabs();
    initMap();
    updateScore();
  });
})();
