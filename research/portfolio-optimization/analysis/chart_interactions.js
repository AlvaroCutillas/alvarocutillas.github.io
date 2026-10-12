/* Local SVG interaction layer. All values come from the executed research. */
(() => {
  "use strict";
  const namespace = "http://www.w3.org/2000/svg";
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));

  function project(data, x, y) {
    const [left, top, right, bottom] = data.box;
    return {
      x: left + (x - data.xlim[0]) / (data.xlim[1] - data.xlim[0]) * (right - left),
      y: bottom - (y - data.ylim[0]) / (data.ylim[1] - data.ylim[0]) * (bottom - top)
    };
  }

  function unproject(data, point) {
    const [left, top, right, bottom] = data.box;
    return {
      x: data.xlim[0] + (point.x - left) / (right - left) * (data.xlim[1] - data.xlim[0]),
      y: data.ylim[0] + (bottom - point.y) / (bottom - top) * (data.ylim[1] - data.ylim[0])
    };
  }

  function nearestIndex(values, value) {
    let low = 0, high = values.length - 1;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (values[middle] < value) low = middle + 1;
      else high = middle;
    }
    return low > 0 && Math.abs(values[low - 1] - value) <= Math.abs(values[low] - value) ? low - 1 : low;
  }

  function pickPoints(data, pointer, scale) {
    const candidates = data.points.map((item, index) => {
      const point = project(data, item.x, item.y);
      let dx = pointer.x - point.x, dy = pointer.y - point.y;
      if (item.bounds) {
        const a = project(data, item.bounds[0], item.bounds[1]);
        const b = project(data, item.bounds[2], item.bounds[3]);
        dx = pointer.x - clamp(pointer.x, Math.min(a.x, b.x), Math.max(a.x, b.x));
        dy = pointer.y - clamp(pointer.y, Math.min(a.y, b.y), Math.max(a.y, b.y));
      } else if (item.range) {
        const a = project(data, item.range[0], item.y), b = project(data, item.range[1], item.y);
        dx = pointer.x - clamp(pointer.x, Math.min(a.x, b.x), Math.max(a.x, b.x));
      }
      return { item, index, distance: Math.hypot(dx, dy) * scale };
    }).sort((a, b) => a.distance - b.distance);
    const marker = candidates.find(candidate => candidate.item.kind !== "line" && candidate.distance <= 12);
    const nearest = marker || candidates[0];
    if (!nearest || nearest.distance > 18) return [];
    if (nearest.item.bounds || nearest.item.range || nearest.item.kind === "line") return [nearest.index];
    return candidates.filter(candidate => candidate.item.kind !== "line" &&
      !candidate.item.bounds && !candidate.item.range && candidate.distance <= 18 &&
      candidate.distance <= nearest.distance + 8).map(candidate => candidate.index);
  }

  function heatCell(data, pointer) {
    const value = unproject(data, pointer);
    const column = Math.floor(value.x + .5), row = Math.floor(value.y + .5);
    if (row < 0 || row >= data.rows.length || column < 0 || column >= data.columns.length) return null;
    return { row, column };
  }

  // Export the geometry for direct, browser-independent regression checks.
  if (typeof module !== "undefined" && module.exports) {
    module.exports = { project, unproject, nearestIndex, pickPoints, heatCell };
  }
  if (typeof document === "undefined") return;

  const tooltip = document.createElement("div");
  tooltip.className = "chart-tooltip";
  tooltip.id = "portfolio-chart-tooltip";
  tooltip.setAttribute("role", "tooltip");
  tooltip.hidden = true;
  document.body.append(tooltip);
  let active = null, contentKey = "";

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function svgNode(tag, attributes) {
    const element = document.createElementNS(namespace, tag);
    Object.entries(attributes).forEach(([name, value]) => element.setAttribute(name, String(value)));
    return element;
  }

  function contents(key, heading, context, blocks) {
    if (key === contentKey) return;
    contentKey = key;
    tooltip.replaceChildren(node("div", "chart-tooltip-heading", heading), node("div", "chart-tooltip-context", context));
    blocks.forEach(block => {
      const element = node("div", "chart-tooltip-block");
      if (block.title) element.append(node("div", "chart-tooltip-title", block.title));
      block.rows.forEach(([label, value]) => {
        const row = node("div", "chart-tooltip-row");
        row.append(node("span", "chart-tooltip-label", label), node("span", "chart-tooltip-value", value));
        element.append(row);
      });
      tooltip.append(element);
    });
  }

  function place(client) {
    tooltip.hidden = false;
    const bounds = tooltip.getBoundingClientRect();
    let left = client.x + 18, top = client.y + 18;
    if (left + bounds.width > window.innerWidth - 12) left = client.x - bounds.width - 18;
    if (top + bounds.height > window.innerHeight - 12) top = client.y - bounds.height - 18;
    tooltip.style.left = `${clamp(left, 12, Math.max(12, window.innerWidth - bounds.width - 12))}px`;
    tooltip.style.top = `${clamp(top, 12, Math.max(12, window.innerHeight - bounds.height - 12))}px`;
  }

  function clear() {
    tooltip.hidden = true;
    contentKey = "";
    if (active) {
      active.overlay.replaceChildren();
      active.groups.forEach(group => { group.style.opacity = ""; });
      active.svg.setAttribute("aria-describedby", active.hint);
    }
    active = null;
  }

  document.querySelectorAll(".interactive-chart").forEach(figure => {
    const svg = figure.querySelector(".plot svg");
    const data = JSON.parse(svg.querySelector("metadata[data-chart]").textContent);
    const slug = figure.dataset.chartSlug;
    const overlay = svgNode("g", { "pointer-events": "none", "aria-hidden": "true" });
    svg.append(overlay);
    const groups = (data.points || []).filter(item => item.gid)
      .map(item => document.getElementById(`${slug}-${item.gid}`)).filter(Boolean);
    const state = { svg, overlay, groups, hint: svg.getAttribute("aria-describedby") || "" };
    let cursor = -1, frame = null, lastClient = null;

    function activate() {
      if (active !== state) clear();
      active = state;
      svg.setAttribute("aria-describedby", `${state.hint} ${tooltip.id}`.trim());
      overlay.replaceChildren();
    }

    function scale() {
      const matrix = svg.getScreenCTM();
      return matrix ? Math.hypot(matrix.a, matrix.b) : 1;
    }

    function clientToSvg(client) {
      const matrix = svg.getScreenCTM();
      if (!matrix) return null;
      const point = svg.createSVGPoint();
      point.x = client.x; point.y = client.y;
      return point.matrixTransform(matrix.inverse());
    }

    function toClient(point) {
      const value = svg.createSVGPoint();
      value.x = point.x; value.y = point.y;
      return value.matrixTransform(svg.getScreenCTM());
    }

    function ring(point, color = "#edf6f0") {
      overlay.append(svgNode("circle", { cx: point.x, cy: point.y, r: 6 / scale(), fill: "none",
        stroke: color, "stroke-width": 1.8, "vector-effect": "non-scaling-stroke" }));
    }

    function showPoints(indices, client, select = false) {
      activate();
      const items = indices.map(index => data.points[index]);
      groups.forEach(group => { group.style.opacity = select && group.id !== `${slug}-${items[0].gid}` ? ".12" : ""; });
      items.forEach(item => ring(project(data, item.x, item.y)));
      const heading = items.length === 1 ? items[0].title : "Overlapping portfolios";
      const blocks = items.map(item => ({ title: items.length > 1 ? item.title : "", rows: item.rows }));
      contents(`${slug}:points:${indices.join(",")}`, heading, data.context, blocks);
      place(client);
    }

    function showTime(index, client) {
      activate();
      const x = project(data, data.x[index], data.ylim[0]).x;
      overlay.append(svgNode("line", { x1: x, x2: x, y1: data.box[1], y2: data.box[3],
        stroke: "#9ab4a5", "stroke-width": 1, "stroke-dasharray": "4 4", "vector-effect": "non-scaling-stroke" }));
      const rows = data.series.map(series => {
        const value = series.values[index];
        ring(project(data, data.x[index], value), series.color);
        return [series.name, data.format === "wealth" ? `$${value.toFixed(4)}` : `${value.toFixed(2)}%`];
      });
      contents(`${slug}:time:${index}`, data.dates[index], data.context, [{ rows }]);
      place(client);
    }

    function showHeat(cell, client) {
      activate();
      const { row, column } = cell;
      const a = project(data, column - .5, row - .5), b = project(data, column + .5, row + .5);
      overlay.append(svgNode("rect", { x: Math.min(a.x, b.x), y: Math.min(a.y, b.y),
        width: Math.abs(a.x - b.x), height: Math.abs(a.y - b.y), fill: "none", stroke: "#eef5f0",
        "stroke-width": 1.8, "vector-effect": "non-scaling-stroke" }));
      const value = data.values[row][column];
      const correlation = data.kind === "correlation";
      const heading = `${data.rows[row]} · ${data.columns[column]}`;
      const rows = correlation ? [["Daily return correlation", value.toFixed(4)]] :
        [["ETF", data.rows[row]], ["Rebalance date", data.columns[column]], ["Target capital weight", `${(100 * value).toFixed(2)}%`]];
      contents(`${slug}:cell:${row}:${column}`, heading, data.context, [{ rows }]);
      place(client);
    }

    function inspect(client) {
      const point = clientToSvg(client);
      if (!point || point.x < data.box[0] || point.x > data.box[2] || point.y < data.box[1] || point.y > data.box[3]) {
        if (active === state) clear();
        return;
      }
      if (data.mode === "time") {
        cursor = nearestIndex(data.x, unproject(data, point).x);
        showTime(cursor, client);
      } else if (data.mode === "heatmap") {
        const cell = heatCell(data, point);
        if (cell) { cursor = cell.row * data.columns.length + cell.column; showHeat(cell, client); }
      } else {
        const indices = pickPoints(data, point, scale());
        if (indices.length) { cursor = indices[0]; showPoints(indices, client); }
        else if (active === state) clear();
      }
    }

    svg.addEventListener("pointermove", event => {
      lastClient = { x: event.clientX, y: event.clientY };
      if (frame === null) frame = window.requestAnimationFrame(() => { frame = null; inspect(lastClient); });
    });
    svg.addEventListener("pointerleave", () => {
      if (frame !== null) { window.cancelAnimationFrame(frame); frame = null; }
      if (active === state) clear();
    });
    svg.addEventListener("pointerup", event => inspect({ x: event.clientX, y: event.clientY }));
    svg.addEventListener("blur", () => { if (active === state) clear(); });
    svg.addEventListener("keydown", event => {
      if (event.key === "Escape") { clear(); return; }
      if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const total = data.mode === "time" ? data.x.length : data.mode === "heatmap" ? data.rows.length * data.columns.length : data.points.length;
      let step = event.key === "ArrowLeft" || event.key === "ArrowUp" ? -1 : 1;
      if (data.mode === "heatmap" && ["ArrowUp", "ArrowDown"].includes(event.key)) step *= data.columns.length;
      cursor = event.key === "Home" ? 0 : event.key === "End" ? total - 1 : clamp(cursor < 0 ? 0 : cursor + step, 0, total - 1);
      let anchor;
      if (data.mode === "time") {
        anchor = project(data, data.x[cursor], data.series[0].values[cursor]);
        showTime(cursor, toClient(anchor));
      } else if (data.mode === "heatmap") {
        const cell = { row: Math.floor(cursor / data.columns.length), column: cursor % data.columns.length };
        anchor = project(data, cell.column, cell.row);
        showHeat(cell, toClient(anchor));
      } else {
        const item = data.points[cursor];
        anchor = project(data, item.x, item.y);
        showPoints([cursor], toClient(anchor), true);
      }
    });

    figure.querySelectorAll("[data-chart-point]").forEach(button => {
      const index = Number(button.dataset.chartPoint);
      const show = () => {
        const bounds = button.getBoundingClientRect();
        cursor = index;
        showPoints([index], { x: bounds.left + bounds.width / 2, y: bounds.top }, true);
      };
      button.addEventListener("pointerenter", show);
      button.addEventListener("focus", show);
      button.addEventListener("click", show);
      button.addEventListener("pointerleave", () => { if (document.activeElement !== button && active === state) clear(); });
      button.addEventListener("blur", () => { if (active === state) clear(); });
    });
  });

  window.addEventListener("scroll", clear, { passive: true });
  window.addEventListener("resize", clear);
  document.addEventListener("keydown", event => { if (event.key === "Escape") clear(); });
  document.addEventListener("pointerdown", event => { if (!event.target.closest(".interactive-chart")) clear(); });
})();
