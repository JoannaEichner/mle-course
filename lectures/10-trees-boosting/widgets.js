/* Widget of lecture 10: gradient boosting with stumps on one feature. */

(function () {
  "use strict";

  const { el } = window.Course;
  const SVG = "http://www.w3.org/2000/svg";

  function svg(tag, attrs, text) {
    const node = document.createElementNS(SVG, tag);
    Object.entries(attrs || {}).forEach(([name, value]) => node.setAttribute(name, value));
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function stat(label, value) {
    return el("div", { class: "stat" }, [
      el("span", { class: "stat-label", text: label }),
      el("span", { class: "stat-value", text: value }),
    ]);
  }

  /* A fixed pseudo-random sequence, so every reader sees the same data. */
  function noise(seed) {
    let state = seed;
    return () => {
      state = (state * 1103515245 + 12345) % 2147483648;
      return state / 2147483648 - 0.5;
    };
  }

  function truth(x) {
    return 2 + 1.5 * Math.sin(x / 1.6) + (x > 6 ? 1.2 : 0);
  }

  function sample(count, seed) {
    const draw = noise(seed);
    return Array.from({ length: count }, (_, i) => {
      const x = (10 * (i + 0.5)) / count + draw() * 0.3;
      return { x, y: truth(x) + draw() * 1.6 };
    });
  }

  const TRAIN = sample(40, 7);
  const HOLDOUT = sample(40, 99);
  const RATES = [0.1, 0.3, 1.0];

  /* The best single split of the residuals: threshold and two leaf means. */
  function stump(points, residuals) {
    const order = points.map((p, i) => i).sort((a, b) => points[a].x - points[b].x);
    const total = residuals.reduce((a, b) => a + b, 0);
    let best = { error: Infinity, threshold: 0, left: 0, right: 0 };
    let leftSum = 0;
    for (let k = 1; k < order.length; k++) {
      leftSum += residuals[order[k - 1]];
      const leftMean = leftSum / k;
      const rightMean = (total - leftSum) / (order.length - k);
      let error = 0;
      order.forEach((index, position) => {
        const mean = position < k ? leftMean : rightMean;
        error += (residuals[index] - mean) ** 2;
      });
      if (error < best.error) {
        const threshold = (points[order[k - 1]].x + points[order[k]].x) / 2;
        best = { error, threshold, left: leftMean, right: rightMean };
      }
    }
    return best;
  }

  function boost(rounds, rate) {
    const base = TRAIN.reduce((a, p) => a + p.y, 0) / TRAIN.length;
    const stumps = [];
    let fitted = TRAIN.map(() => base);
    for (let r = 0; r < rounds; r++) {
      const residuals = TRAIN.map((p, i) => p.y - fitted[i]);
      const s = stump(TRAIN, residuals);
      stumps.push(s);
      fitted = TRAIN.map((p, i) => fitted[i] + rate * (p.x <= s.threshold ? s.left : s.right));
    }
    return (x) => stumps.reduce((sum, s) => sum + rate * (x <= s.threshold ? s.left : s.right), base);
  }

  function mse(points, model) {
    return points.reduce((a, p) => a + (p.y - model(p.x)) ** 2, 0) / points.length;
  }

  function boostingWidget() {
    const root = document.getElementById("boosting-widget");
    if (!root) return;
    const part = (name) => root.querySelector(`[data-role="${name}"]`);
    const roundsInput = part("rounds");
    const rateInput = part("rate");

    function render() {
      const rounds = Number(roundsInput.value);
      const rate = RATES[Number(rateInput.value)];
      part("rounds-value").textContent = String(rounds);
      part("rate-value").textContent = String(rate);
      const model = boost(rounds, rate);

      const width = 640;
      const height = 260;
      const sx = (x) => 30 + (x / 10) * (width - 40);
      const sy = (y) => height - 25 - ((y + 0.5) / 6) * (height - 35);
      const chart = svg("svg", { class: "chart", viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "Punkty i prognoza boostingu" });
      chart.append(svg("line", { x1: 30, y1: height - 25, x2: width - 5, y2: height - 25, stroke: "var(--axis)" }));
      TRAIN.forEach((p) => chart.append(svg("circle", { cx: sx(p.x), cy: sy(p.y), r: 3.5, fill: "var(--series-1)" })));
      HOLDOUT.forEach((p) => chart.append(svg("circle", { cx: sx(p.x), cy: sy(p.y), r: 3.5, fill: "none", stroke: "var(--muted)" })));
      const path = [];
      for (let i = 0; i <= 400; i++) {
        const x = (10 * i) / 400;
        path.push(`${i ? "L" : "M"}${sx(x).toFixed(1)},${sy(Math.max(-0.5, Math.min(5.5, model(x)))).toFixed(1)}`);
      }
      chart.append(svg("path", { d: path.join(" "), fill: "none", stroke: "var(--series-2)", "stroke-width": 2.5 }));
      chart.append(svg("text", { x: width - 8, y: height - 8, "text-anchor": "end" }, "cecha"));
      part("chart").replaceChildren(chart);

      const trainError = mse(TRAIN, model);
      const holdoutError = mse(HOLDOUT, model);
      part("stats").replaceChildren(
        stat("drzewa", String(rounds)),
        stat("MSE trening", trainError.toFixed(3)),
        stat("MSE odłożone", holdoutError.toFixed(3))
      );
      const verdict = part("verdict");
      const best = Math.min(...[0, 5, 10, 20, 40, 60, 80, 100, 150, 200].map((r) => mse(HOLDOUT, boost(r, rate))));
      if (rounds === 0) {
        verdict.className = "verdict";
        verdict.textContent = "Zero drzew: prognoza to średnia celu.";
      } else if (holdoutError > best * 1.1 && trainError < holdoutError * 0.5) {
        verdict.className = "verdict bad";
        verdict.textContent = "Błąd na treningu dalej spada, a na punktach odłożonych rośnie: model uczy się szumu.";
      } else {
        verdict.className = "verdict";
        verdict.textContent = "Każde drzewo poprawia błędy wszystkich poprzednich, o ułamek równy krokowi uczenia.";
      }
    }

    roundsInput.addEventListener("input", render);
    rateInput.addEventListener("input", render);
    render();
  }

  document.addEventListener("DOMContentLoaded", boostingWidget);
})();
