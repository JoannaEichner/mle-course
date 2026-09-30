/* Widget of lecture 12: choosing a threshold on real scores.
   The counts are the LightGBM probabilities of the lab's test week (city 3,
   18,536 rows, 1,505 full stockouts), in 50 bins of width 0.02. */

(function () {
  "use strict";

  const { el } = window.Course;
  const SVG = "http://www.w3.org/2000/svg";
  const POS = [95, 44, 20, 22, 19, 19, 17, 7, 16, 16, 18, 19, 19, 26, 33, 24, 31, 41, 36, 58, 54, 55, 61, 66, 53, 40, 31, 46, 36, 29, 35, 44, 41, 37, 36, 32, 64, 47, 60, 50, 6, 2, 0, 0, 0, 0, 0, 0, 0, 0];
  const NEG = [13472, 1165, 420, 227, 147, 110, 74, 76, 53, 55, 65, 48, 67, 58, 60, 56, 59, 53, 62, 44, 51, 57, 58, 69, 44, 40, 27, 24, 16, 23, 35, 36, 30, 37, 33, 19, 17, 16, 15, 10, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0];
  const BINS = POS.length;
  const TOTAL_POS = POS.reduce((a, b) => a + b, 0);
  const TOTAL_NEG = NEG.reduce((a, b) => a + b, 0);
  const COSTS = [[1, 1], [1, 5], [1, 10]];

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

  function counts(k) {
    const tp = POS.slice(k).reduce((a, b) => a + b, 0);
    const fp = NEG.slice(k).reduce((a, b) => a + b, 0);
    return { tp, fp, fn: TOTAL_POS - tp, tn: TOTAL_NEG - fp };
  }

  function thresholdWidget() {
    const root = document.getElementById("threshold-widget");
    if (!root) return;
    const part = (name) => root.querySelector(`[data-role="${name}"]`);

    function render() {
      const k = Number(part("threshold").value);
      const [costFalse, costMissed] = COSTS[Number(part("costs").value)];
      part("threshold-value").textContent = (k / BINS).toFixed(2);
      const c = counts(k);
      const precision = c.tp + c.fp ? c.tp / (c.tp + c.fp) : 0;
      const recall = c.tp / TOTAL_POS;
      const f1 = precision + recall ? (2 * precision * recall) / (precision + recall) : 0;
      const cost = c.fp * costFalse + c.fn * costMissed;
      const allCosts = Array.from({ length: BINS + 1 }, (_, i) => {
        const d = counts(i);
        return d.fp * costFalse + d.fn * costMissed;
      });
      const best = allCosts.indexOf(Math.min(...allCosts));

      const width = 640;
      const height = 190;
      const chart = svg("svg", { class: "chart", viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "Rozkład wyników dla braków i dla pozostałych dni, z progiem" });
      const barWidth = (width - 20) / BINS;
      const scale = (value) => (Math.log1p(value) / Math.log1p(13472)) * 70;
      POS.forEach((value, i) => chart.append(svg("rect", { x: 10 + i * barWidth, y: 80 - scale(value), width: barWidth - 1, height: scale(value), fill: "var(--series-2)" })));
      NEG.forEach((value, i) => chart.append(svg("rect", { x: 10 + i * barWidth, y: 100, width: barWidth - 1, height: scale(value), fill: "var(--series-1)" })));
      const x = 10 + k * barWidth;
      chart.append(svg("line", { x1: x, y1: 0, x2: x, y2: height - 12, stroke: "var(--ink)", "stroke-width": 2 }));
      chart.append(svg("text", { x: width - 10, y: 14, "text-anchor": "end" }, "pełny brak jutro (skala log)"));
      chart.append(svg("text", { x: width - 10, y: height - 2, "text-anchor": "end" }, "bez pełnego braku"));
      chart.append(svg("text", { x: 12, y: height - 2 }, "wynik 0"));
      chart.append(svg("text", { x: x + 4, y: 94 }, "alarm →"));
      part("chart").replaceChildren(chart);

      part("stats").replaceChildren(
        stat("trafione alarmy", String(c.tp)),
        stat("fałszywe alarmy", String(c.fp)),
        stat("przegapione", String(c.fn)),
        stat("precision", precision.toFixed(2)),
        stat("recall", recall.toFixed(2)),
        stat("F1", f1.toFixed(2)),
        stat("koszt", String(cost))
      );
      const verdict = part("verdict");
      if (k === best) {
        verdict.className = "verdict good";
        verdict.textContent = `To najtańszy próg przy tych kosztach (${costFalse} za fałszywy alarm, ${costMissed} za przegapiony brak).`;
      } else {
        verdict.className = "verdict";
        verdict.textContent = `Najtańszy próg przy tych kosztach to ${(best / BINS).toFixed(2)}, z kosztem ${allCosts[best]}.`;
      }
    }

    part("threshold").addEventListener("input", render);
    part("costs").addEventListener("change", render);
    render();
  }

  document.addEventListener("DOMContentLoaded", thresholdWidget);
})();
