/* Widgets of lecture 07. Everything is computed in the browser on tiny
   hand-made tables, except the memory chart, which shows measured numbers. */

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

  /* cells: array of rows; a cell is a value or { text, class }. */
  function table(headers, rows, options) {
    const opts = options || {};
    const head = el("tr", {}, headers.map((name) => el("th", { text: name })));
    const body = rows.map((row, index) => {
      const cells = row.map((cell) => {
        const value = cell !== null && typeof cell === "object" ? cell : { text: cell };
        return el("td", { class: value.class || "", text: String(value.text) });
      });
      const tr = el("tr", { class: (opts.rowClass && opts.rowClass(index)) || "" }, cells);
      if (opts.onPick) {
        tr.classList.add("row-pick");
        tr.tabIndex = 0;
        tr.addEventListener("click", () => opts.onPick(index));
        tr.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            opts.onPick(index);
          }
        });
      }
      return tr;
    });
    return el("table", { class: "data" }, [el("thead", {}, head), el("tbody", {}, body)]);
  }

  function fill(host, node) {
    host.replaceChildren(node);
  }

  function stat(label, value) {
    return el("div", { class: "stat" }, [
      el("span", { class: "stat-label", text: label }),
      el("span", { class: "stat-value", text: value }),
    ]);
  }

  function number(value) {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }

  /* ---------- memory per row ---------- */

  function memoryChart() {
    const root = document.getElementById("memory-chart");
    if (!root) return;
    const host = root.querySelector(".chart-host");
    const series = [
      { key: "scalar", name: "kolumny skalarne", color: "var(--series-1)" },
      { key: "nested", name: "dwie kolumny godzinowe", color: "var(--series-2)" },
    ];
    const rows = [
      { label: "Wszystkie kolumny, typy domyślne", scalar: 134, nested: 624 },
      { label: "Bez kolumn godzinowych", scalar: 134, nested: 0 },
      { label: "Bez kolumn godzinowych, małe typy", scalar: 64, nested: 0 },
    ];

    const legend = el(
      "ul",
      { class: "legend" },
      series.map((item) =>
        el("li", {}, [
          el("span", { class: "swatch", style: `background:${item.color}` }),
          el("span", { text: item.name }),
        ])
      )
    );

    const width = 640;
    const rowHeight = 52;
    const barHeight = 20;
    const plotWidth = 540;
    const max = 800;
    const gap = 2;
    const chart = svg("svg", {
      class: "chart",
      viewBox: `0 0 ${width} ${rows.length * rowHeight + 6}`,
      role: "img",
      "aria-label": "Pamięć na wiersz w trzech wariantach wczytania",
    });
    const tip = el("div", { class: "chart-tip", hidden: "" });

    function showTip(event, row, item) {
      tip.replaceChildren(
        el("strong", { text: `${row[item.key]} B ` }),
        document.createTextNode(item.name)
      );
      tip.hidden = false;
      const box = host.getBoundingClientRect();
      const mark = event.currentTarget.getBoundingClientRect();
      tip.style.left = mark.left - box.left + mark.width / 2 - tip.offsetWidth / 2 + "px";
      tip.style.top = mark.top - box.top - tip.offsetHeight - 6 + "px";
    }

    rows.forEach((row, index) => {
      const top = index * rowHeight;
      chart.append(svg("text", { x: 0, y: top + 14 }, row.label));
      let x = 0;
      series.forEach((item, position) => {
        const value = row[item.key];
        if (!value) return;
        const last = position === series.length - 1 || !row[series[position + 1].key];
        const w = (value / max) * plotWidth - (last ? 0 : gap);
        const mark = svg("rect", {
          x,
          y: top + 22,
          width: Math.max(w, 1),
          height: barHeight,
          rx: last ? 4 : 0,
          fill: item.color,
          tabindex: 0,
          role: "img",
          "aria-label": `${row.label}: ${item.name}, ${value} bajtów`,
        });
        if (last) {
          // Only the data end is rounded: cover the left corners of the last segment.
          chart.append(
            svg("rect", { x, y: top + 22, width: 6, height: barHeight, fill: item.color })
          );
        }
        ["pointerenter", "focus"].forEach((type) =>
          mark.addEventListener(type, (event) => showTip(event, row, item))
        );
        ["pointerleave", "blur"].forEach((type) =>
          mark.addEventListener(type, () => (tip.hidden = true))
        );
        chart.append(mark);
        x += (value / max) * plotWidth;
      });
      const total = row.scalar + row.nested;
      chart.append(
        svg("text", { x: x + 8, y: top + 22 + barHeight / 2 + 4, class: "value" }, `${total} B`)
      );
    });
    chart.append(
      svg("line", {
        class: "axis",
        x1: 0,
        x2: 0,
        y1: 18,
        y2: rows.length * rowHeight,
      })
    );

    const details = el("details", {}, [
      el("summary", { text: "Pokaż liczby w tabeli" }),
      table(
        ["wariant", "skalarne (B)", "godzinowe (B)", "razem (B)"],
        rows.map((row) => [row.label, row.scalar, row.nested, row.scalar + row.nested])
      ),
    ]);
    host.replaceChildren(legend, chart, tip, details);
  }

  /* ---------- merge explorer ---------- */

  function mergeWidget() {
    const root = document.getElementById("merge-widget");
    if (!root) return;
    const part = (role) => root.querySelector(`[data-role="${role}"]`);
    const fact = [
      { dt: "pon", product_id: 4, sale: 3 },
      { dt: "pon", product_id: 37, sale: 5 },
      { dt: "wt", product_id: 4, sale: 2 },
      { dt: "wt", product_id: 37, sale: 6 },
      { dt: "wt", product_id: 92, sale: 1 },
    ];
    const total = fact.reduce((sum, row) => sum + row.sale, 0);

    function render() {
      const duplicate = part("duplicate").checked;
      const missing = part("missing").checked;
      const how = part("how").value;
      const validate = part("validate").value;
      const indicator = part("indicator").checked;

      let dim = [
        { product_id: 4, category: "warzywa" },
        { product_id: 37, category: "owoce" },
        { product_id: 92, category: "nabiał" },
      ];
      if (missing) dim = dim.filter((row) => row.product_id !== 92);
      if (duplicate) dim.push({ product_id: 4, category: "warzywa (stary wpis)" });

      fill(
        part("fact"),
        table(["dt", "product_id", "sale"], fact.map((r) => [r.dt, r.product_id, r.sale]))
      );
      fill(
        part("dim"),
        table(
          ["product_id", "category"],
          dim.map((r) => [r.product_id, r.category]),
          { rowClass: (i) => (duplicate && i === dim.length - 1 ? "row-new" : "") }
        )
      );

      const verdict = part("verdict");
      verdict.className = "verdict";
      const call =
        `sales.merge(products, on="product_id", how="${how}"` +
        (validate ? `, validate="${validate}"` : "") +
        (indicator ? ", indicator=True" : "") +
        ")";

      if (validate && duplicate) {
        fill(part("result"), el("p", { class: "cell-dim", text: "brak wyniku" }));
        fill(part("stats"), stat("Wiersze", `${fact.length} → błąd`));
        verdict.classList.add("good");
        verdict.replaceChildren(
          el("code", { text: call }),
          el("br"),
          document.createTextNode(
            "MergeError: Merge keys are not unique in right dataset; not a many-to-one merge. " +
              "Złączenie się nie wykonało. Tego właśnie chcesz."
          )
        );
        return;
      }

      const result = [];
      fact.forEach((row) => {
        const matches = dim.filter((d) => d.product_id === row.product_id);
        if (!matches.length && how === "left") {
          result.push({ ...row, category: "NaN", merge: "left_only", nan: true });
        }
        matches.forEach((match, index) =>
          result.push({ ...row, category: match.category, merge: "both", extra: index > 0 })
        );
      });

      const headers = ["dt", "product_id", "sale", "category"].concat(indicator ? ["_merge"] : []);
      fill(
        part("result"),
        table(
          headers,
          result.map((r) =>
            [r.dt, r.product_id, r.sale, { text: r.category, class: r.nan ? "cell-bad" : "" }].concat(
              indicator ? [{ text: r.merge, class: r.nan ? "cell-bad" : "" }] : []
            )
          ),
          { rowClass: (i) => (result[i].extra ? "row-new" : "") }
        )
      );

      const sum = result.reduce((acc, row) => acc + row.sale, 0);
      fill(
        part("stats"),
        el("div", { class: "stat-row" }, [
          stat("Wiersze", `${fact.length} → ${result.length}`),
          stat("Suma sprzedaży", `${total} → ${sum}`),
        ])
      );

      const added = result.filter((r) => r.extra).length;
      const lost = missing && how === "inner";
      const holes = result.filter((r) => r.nan).length;
      const notes = [];
      if (added) {
        notes.push(
          `Przybyły ${added} wiersze i suma sprzedaży wzrosła z ${total} do ${sum}. Błędu nie było.`
        );
      }
      if (lost) {
        notes.push(
          "Zniknął wiersz produktu 92, który nie ma pary w wymiarze. W złączeniu inner " +
            "indicator nie ma czego pokazać, dlatego sprawdzenie robi się na how=\"left\"."
        );
      }
      if (holes && indicator) {
        notes.push(
          "Kolumna _merge pokazuje wiersz left_only. Masz co policzyć i z czym rzucić ValueError."
        );
      } else if (holes) {
        notes.push(
          "Wiersz produktu 92 ma NaN w kolumnie category i nic tego nie sygnalizuje. " +
            "validate tego nie łapie."
        );
      }
      const bad = added || lost || (holes && !indicator);
      if (!notes.length) notes.push("Każdy wiersz faktów znalazł dokładnie jedną parę.");
      verdict.classList.add(bad ? "bad" : "good");
      verdict.replaceChildren(
        el("code", { text: call }),
        el("br"),
        document.createTextNode(notes.join(" "))
      );
    }

    root.querySelectorAll("input, select").forEach((control) =>
      control.addEventListener("change", render)
    );
    render();
  }

  /* ---------- agg, transform, shift ---------- */

  function groupbyWidget() {
    const root = document.getElementById("groupby-widget");
    if (!root) return;
    const part = (role) => root.querySelector(`[data-role="${role}"]`);
    const rows = [
      ["A", 1, 2],
      ["A", 2, 4],
      ["A", 3, 6],
      ["B", 1, 10],
      ["B", 2, 20],
      ["B", 3, 30],
    ];
    const operations = {
      agg: {
        code: 'df.groupby("series")["sale"].agg("mean")',
        headers: ["series", "mean"],
        rows: [
          ["A", 4],
          ["B", 20],
        ],
        note: "2 wiersze, jeden na grupę. Indeksem wyniku jest klucz grupy.",
      },
      transform: {
        code: 'df.groupby("series")["sale"].transform("mean")',
        headers: ["series", "day", "wynik"],
        rows: rows.map(([series, day]) => [series, day, series === "A" ? 4 : 20]),
        note: "6 wierszy, tyle co na wejściu, z tym samym indeksem. Można od razu przypisać jako kolumnę.",
      },
      shift: {
        code: 'df.groupby("series")["sale"].shift(1)',
        headers: ["series", "day", "wynik"],
        rows: rows.map(([series, day, sale], index) => [
          series,
          day,
          day === 1 ? { text: "NaN", class: "cell-dim" } : rows[index - 1][2],
        ]),
        note: "6 wierszy. Pierwszy dzień każdej serii nie ma poprzednika, więc dostaje NaN.",
      },
    };

    fill(part("input"), table(["series", "day", "sale"], rows));

    function render(name) {
      const operation = operations[name];
      root.querySelectorAll("[data-op]").forEach((button) =>
        button.setAttribute("aria-pressed", String(button.dataset.op === name))
      );
      fill(part("output"), table(operation.headers, operation.rows));
      part("code").textContent = operation.code;
      part("verdict").textContent = operation.note;
    }

    root.querySelectorAll("[data-op]").forEach((button) =>
      button.addEventListener("click", () => render(button.dataset.op))
    );
    render("agg");
  }

  /* ---------- window explorer ---------- */

  function windowWidget() {
    const root = document.getElementById("window-widget");
    if (!root) return;
    const part = (role) => root.querySelector(`[data-role="${role}"]`);
    const sales = { A: [3, 5, 4, 6, 8, 7], B: [20, 22, 19, 25, 24, 30] };
    const rows = [];
    Object.entries(sales).forEach(([series, values]) =>
      values.forEach((sale, index) => rows.push({ series, day: index + 1, sale }))
    );
    let target = 7;

    function render() {
      const size = Number(part("window").value);
      const lag = Number(part("lag").value);
      const grouped = part("grouped").checked;
      part("window-out").textContent = size;
      part("lag-out").textContent = lag;

      const end = target - lag;
      const start = end - size + 1;
      const seriesStart = rows.findIndex((row) => row.series === rows[target].series);
      const floor = grouped ? seriesStart : 0;
      const complete = start >= floor;
      const used = [];
      for (let i = Math.max(start, floor); i <= end; i += 1) used.push(i);

      const foreign = used.filter((i) => rows[i].series !== rows[target].series);
      const includesToday = used.includes(target);
      const value = complete
        ? used.reduce((sum, i) => sum + rows[i].sale, 0) / used.length
        : null;

      fill(
        part("table"),
        table(
          ["series", "day", "sale", "cecha"],
          rows.map((row, index) => {
            let saleClass = "";
            if (used.includes(index)) {
              const wrong =
                row.series !== rows[target].series || (index === target && lag === 0);
              saleClass = wrong ? "cell-bad" : "cell-hot";
            }
            const feature =
              index === target ? (value === null ? "NaN" : number(value)) : "·";
            return [
              row.series,
              row.day,
              { text: row.sale, class: saleClass },
              { text: feature, class: index === target ? "cell-target" : "cell-dim" },
            ];
          }),
          {
            onPick: (index) => {
              target = index;
              render();
            },
          }
        )
      );

      const base = grouped ? 'df.groupby("series")["sale"]' : 'df["sale"]';
      const again = grouped ? '.groupby(df["series"])' : "";
      part("code").textContent =
        lag === 0
          ? `${base}.rolling(${size}).mean()`
          : `past = ${base}.shift(${lag})\npast${again}.rolling(${size}).mean()`;

      const verdict = part("verdict");
      verdict.className = "verdict";
      const here = `Seria ${rows[target].series}, dzień ${rows[target].day}.`;
      if (foreign.length) {
        verdict.classList.add("bad");
        verdict.textContent =
          `${here} Do średniej weszły wartości innej serii (czerwone komórki). ` +
          "pandas nie zgłosił błędu.";
      } else if (includesToday) {
        verdict.classList.add("bad");
        verdict.textContent =
          `${here} Okno zawiera dzień bieżący. Cecha niesie część wartości, którą ma ` +
          "pomóc przewidzieć. To przeciek.";
      } else if (!complete) {
        verdict.textContent =
          `${here} NaN: seria nie ma jeszcze ${size + lag - 1} dni historii przed tym dniem. ` +
          "To poprawna odpowiedź. Wyłącz groupby i zobacz, czym pandas ją zastąpi.";
      } else {
        verdict.classList.add("good");
        verdict.textContent =
          `${here} Średnia z ${size} dni tej samej serii, kończących się ` +
          `${lag === 1 ? "wczoraj" : lag + " dni wcześniej"}: ${number(value)}.`;
      }
    }

    root.querySelectorAll("input").forEach((control) =>
      control.addEventListener("input", render)
    );
    render();
  }

  document.addEventListener("DOMContentLoaded", () => {
    memoryChart();
    mergeWidget();
    groupbyWidget();
    windowWidget();
  });
})();
