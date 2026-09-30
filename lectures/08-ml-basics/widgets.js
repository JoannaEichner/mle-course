/* Widgets of lecture 08: gradient descent on a tiny, fixed data set. */

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

  /* Standardised feature (mean 0, variance 1) and a target near 0.8 x + 1.5.
     With such x the loss curvature is 2 in both directions, so steps below
     1.0 converge and steps above it diverge. */
  const X = [-1.6, -1.2, -0.9, -0.5, -0.3, 0.0, 0.2, 0.5, 0.7, 1.0, 1.3, 0.8];
  const meanX = X.reduce((a, b) => a + b, 0) / X.length;
  const sdX = Math.sqrt(X.reduce((a, b) => a + (b - meanX) ** 2, 0) / X.length);
  const XS = X.map((x) => (x - meanX) / sdX);
  const NOISE = [0.3, -0.2, 0.1, -0.35, 0.25, -0.1, 0.2, -0.25, 0.05, 0.3, -0.15, -0.1];
  const Y = XS.map((x, i) => 0.8 * x + 1.5 + NOISE[i]);
  const RATES = [0.01, 0.05, 0.1, 0.3, 0.6, 0.9, 1.05];

  function mean(values) {
    return values.reduce((a, b) => a + b, 0) / values.length;
  }

  /* With a standardised feature the least-squares solution is closed-form. */
  const W_STAR = mean(XS.map((x, i) => x * Y[i]));
  const B_STAR = mean(Y);

  function loss(w, b) {
    return XS.reduce((sum, x, i) => sum + (w * x + b - Y[i]) ** 2, 0) / XS.length;
  }

  const MIN_LOSS = loss(W_STAR, B_STAR);

  function gradient(w, b) {
    let gw = 0;
    let gb = 0;
    XS.forEach((x, i) => {
      const r = w * x + b - Y[i];
      gw += (2 * r * x) / XS.length;
      gb += (2 * r) / XS.length;
    });
    return [gw, gb];
  }

  function gdWidget() {
    const root = document.getElementById("gd-widget");
    if (!root) return;
    const part = (name) => root.querySelector(`[data-role="${name}"]`);
    const slider = part("rate");
    const output = part("rate-value");
    let state;

    function reset() {
      state = { w: 0, b: 0, losses: [loss(0, 0)] };
      render();
    }

    function step(times) {
      const rate = RATES[Number(slider.value)];
      for (let i = 0; i < times; i++) {
        const [gw, gb] = gradient(state.w, state.b);
        state.w -= rate * gw;
        state.b -= rate * gb;
        const value = loss(state.w, state.b);
        state.losses.push(value);
        if (!Number.isFinite(value) || value > 1e6) break;
      }
      render();
    }

    function scatter() {
      const width = 300;
      const height = 220;
      const sx = (x) => 20 + ((x + 2.2) / 4.4) * (width - 30);
      const sy = (y) => height - 20 - ((y + 0.5) / 4.5) * (height - 30);
      const chart = svg("svg", { class: "chart", viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "Punkty danych i dopasowana prosta" });
      chart.append(svg("line", { x1: 20, y1: height - 20, x2: width - 5, y2: height - 20, stroke: "var(--axis)" }));
      chart.append(svg("line", { x1: 20, y1: 5, x2: 20, y2: height - 20, stroke: "var(--axis)" }));
      XS.forEach((x, i) => chart.append(svg("circle", { cx: sx(x), cy: sy(Y[i]), r: 4, fill: "var(--series-1)" })));
      const clampY = (y) => Math.max(-0.5, Math.min(4, y));
      const left = -2.2;
      const right = 2.2;
      if (Number.isFinite(state.w) && Number.isFinite(state.b)) {
        chart.append(svg("line", {
          x1: sx(left), y1: sy(clampY(state.w * left + state.b)),
          x2: sx(right), y2: sy(clampY(state.w * right + state.b)),
          stroke: "var(--series-2)", "stroke-width": 2.5,
        }));
      }
      chart.append(svg("text", { x: width - 8, y: height - 6, "text-anchor": "end" }, "cecha (standaryzowana)"));
      chart.append(svg("text", { x: 24, y: 14 }, "sprzedaż"));
      return chart;
    }

    function lossChart() {
      const width = 300;
      const height = 220;
      const values = state.losses.map((v) => Math.log10(Math.max(v, 1e-3)));
      const top = Math.max(2, ...values.filter(Number.isFinite));
      const bottom = -1.5;
      const steps = Math.max(10, state.losses.length - 1);
      const sx = (i) => 30 + (i / steps) * (width - 40);
      const sy = (v) => height - 20 - ((Math.min(v, top) - bottom) / (top - bottom)) * (height - 30);
      const chart = svg("svg", { class: "chart", viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "Strata po kolejnych krokach" });
      chart.append(svg("line", { x1: 30, y1: height - 20, x2: width - 5, y2: height - 20, stroke: "var(--axis)" }));
      chart.append(svg("line", { x1: 30, y1: 5, x2: 30, y2: height - 20, stroke: "var(--axis)" }));
      const points = values.map((v, i) => `${sx(i)},${sy(Number.isFinite(v) ? v : top)}`).join(" ");
      chart.append(svg("polyline", { points, fill: "none", stroke: "var(--series-3)", "stroke-width": 2.5 }));
      chart.append(svg("text", { x: width - 8, y: height - 6, "text-anchor": "end" }, "krok"));
      chart.append(svg("text", { x: 34, y: 14 }, "MSE (skala log)"));
      return chart;
    }

    function render() {
      output.textContent = String(RATES[Number(slider.value)]);
      part("scatter").replaceChildren(scatter());
      part("loss").replaceChildren(lossChart());
      const last = state.losses[state.losses.length - 1];
      const shown = Number.isFinite(last) && last < 1e6 ? last.toFixed(4) : "rozbiega się";
      part("stats").replaceChildren(
        stat("krok", String(state.losses.length - 1)),
        stat("w", Number.isFinite(state.w) ? state.w.toFixed(3) : "∞"),
        stat("b", Number.isFinite(state.b) ? state.b.toFixed(3) : "∞"),
        stat("MSE", shown)
      );
      const verdict = part("verdict");
      const growing = state.losses.length > 2 && last > state.losses[state.losses.length - 2];
      if (!Number.isFinite(last) || last > 1e3 || growing) {
        verdict.className = "verdict bad";
        verdict.textContent = "Strata rośnie: krok jest za duży i każdy ruch przeskakuje minimum coraz dalej.";
      } else if (state.losses.length > 1 && last - MIN_LOSS < 0.001) {
        verdict.className = "verdict good";
        verdict.textContent = "Prosta prawie się nie rusza: model doszedł do minimum straty.";
      } else {
        verdict.className = "verdict";
        verdict.textContent = "Każdy krok przesuwa w i b przeciwnie do gradientu.";
      }
    }

    slider.addEventListener("input", reset);
    part("step").addEventListener("click", () => step(1));
    part("ten").addEventListener("click", () => step(10));
    part("reset").addEventListener("click", reset);
    reset();
  }

  document.addEventListener("DOMContentLoaded", gdWidget);
})();
