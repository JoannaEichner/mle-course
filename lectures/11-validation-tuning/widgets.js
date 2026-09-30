/* Widget of lecture 11: rolling-origin folds against a random K-fold split. */

(function () {
  "use strict";

  const { el } = window.Course;
  const SVG = "http://www.w3.org/2000/svg";
  const DAYS = 90;
  const HORIZON = 7;
  const TEST = 7;

  function svg(tag, attrs, text) {
    const node = document.createElementNS(SVG, tag);
    Object.entries(attrs || {}).forEach(([name, value]) => node.setAttribute(name, value));
    if (text !== undefined) node.textContent = text;
    return node;
  }

  /* Deterministic shuffle, so the random split looks the same on every visit. */
  function shuffled(count, seed) {
    const order = Array.from({ length: count }, (_, i) => i);
    let state = seed;
    for (let i = count - 1; i > 0; i--) {
      state = (state * 1103515245 + 12345) % 2147483648;
      const j = state % (i + 1);
      [order[i], order[j]] = [order[j], order[i]];
    }
    return order;
  }

  function rows(mode, folds) {
    const usable = DAYS - TEST;
    if (mode === "time") {
      return Array.from({ length: folds }, (_, index) => {
        const end = usable - (folds - 1 - index) * HORIZON;
        const start = end - HORIZON;
        return Array.from({ length: DAYS }, (_, day) =>
          day >= usable ? "test" : day < start ? "train" : day < end ? "valid" : "unused"
        );
      });
    }
    const order = shuffled(usable, 17);
    return Array.from({ length: folds }, (_, index) => {
      const valid = new Set(order.filter((_, position) => position % folds === index));
      return Array.from({ length: DAYS }, (_, day) =>
        day >= usable ? "test" : valid.has(day) ? "valid" : "train"
      );
    });
  }

  const COLORS = {
    train: "var(--series-1)",
    valid: "var(--series-2)",
    test: "var(--muted)",
    unused: "var(--hairline)",
  };

  function foldWidget() {
    const root = document.getElementById("fold-widget");
    if (!root) return;
    const part = (name) => root.querySelector(`[data-role="${name}"]`);
    const buttons = [...root.querySelectorAll(".segmented button")];
    let mode = "time";

    function render() {
      const folds = Number(part("folds").value);
      part("folds-value").textContent = String(folds);
      const grid = rows(mode, folds);
      const cell = 6.6;
      const rowHeight = 22;
      const left = 60;
      const width = left + DAYS * cell + 10;
      const height = grid.length * rowHeight + 30;
      const chart = svg("svg", { class: "chart", viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "Podział dni na trening, walidację i test w kolejnych foldach" });
      grid.forEach((row, index) => {
        const y = 6 + index * rowHeight;
        chart.append(svg("text", { x: 0, y: y + 12 }, `fold ${index + 1}`));
        row.forEach((kind, day) => {
          chart.append(svg("rect", { x: left + day * cell, y, width: cell - 1, height: rowHeight - 6, fill: COLORS[kind], rx: 1 }));
        });
      });
      chart.append(svg("text", { x: left, y: height - 4 }, "dzień 1"));
      chart.append(svg("text", { x: left + DAYS * cell, y: height - 4, "text-anchor": "end" }, "dzień 90"));
      part("chart").replaceChildren(chart);

      const leaks = grid.reduce((count, row) => {
        const firstValid = row.indexOf("valid");
        return count + row.filter((kind, day) => kind === "train" && day > firstValid).length;
      }, 0);
      const verdict = part("verdict");
      if (mode === "time") {
        verdict.className = "verdict good";
        verdict.textContent = "Każdy fold uczy się tylko na dniach sprzed swojego okna, tak jak prognoza w produkcji.";
      } else {
        verdict.className = "verdict bad";
        verdict.textContent = `Łącznie ${leaks} dni treningu leży po pierwszym dniu walidacji swojego foldu: model uczy się na przyszłości.`;
      }
    }

    buttons.forEach((button) =>
      button.addEventListener("click", () => {
        mode = button.dataset.tab;
        buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
        render();
      })
    );
    part("folds").addEventListener("input", render);
    render();
  }

  document.addEventListener("DOMContentLoaded", foldWidget);
})();
