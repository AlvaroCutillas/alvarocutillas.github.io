"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const client = require("../analysis/chart_interactions.js");
const page = fs.readFileSync(path.resolve(root, "../../projects/portfolio-optimization.html"), "utf8");
const embeddedScript = page.match(/<script id="chart-interactions">([\s\S]*?)<\/script>/)[1];
const sources = Object.fromEntries(fs.readdirSync(path.join(root, "figures")).filter(file => file.endsWith(".svg"))
  .map(file => [file.slice(0, -4), fs.readFileSync(path.join(root, "figures", file), "utf8")]));
const models = Object.fromEntries(Object.entries(sources).filter(([, source]) => source.includes('<metadata data-chart="true">')).map(([slug, source]) => {
  const encoded = source.match(/<metadata data-chart="true">([\s\S]*?)<\/metadata>/)[1];
  return [slug, JSON.parse(encoded.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&"))];
}));

test("pointer coordinates align with actual exported SVG markers", () => {
  const data = models.oos_risk_return;
  data.points.forEach(item => {
    const section = sources.oos_risk_return.slice(sources.oos_risk_return.indexOf(`id="${item.gid}"`));
    const use = section.match(/<use\b[^>]*\bx="([^"]+)"\s+y="([^"]+)"/);
    let center;
    if (use) center = [Number(use[1]), Number(use[2])];
    else {
      const values = section.match(/<path d="([^"]+)"/)[1].match(/[-+]?\d*\.?\d+/g).map(Number);
      const x = values.filter((_, i) => i % 2 === 0), y = values.filter((_, i) => i % 2 === 1);
      center = [(Math.min(...x) + Math.max(...x)) / 2, (Math.min(...y) + Math.max(...y)) / 2];
    }
    const point = client.project(data, item.x, item.y);
    assert.ok(Math.abs(point.x - center[0]) < .0001);
    assert.ok(Math.abs(point.y - center[1]) < .0001);
    const recovered = client.unproject(data, point);
    assert.ok(Math.abs(recovered.x - item.x) < 1e-10 && Math.abs(recovered.y - item.y) < 1e-10);
  });
});

test("coincident capped strategies remain selectable at multiple display sizes", () => {
  const data = models.oos_risk_return;
  for (const scale of [.5, 1, 1.8]) {
    const point = client.project(data, data.points[4].x, data.points[4].y);
    assert.deepEqual(client.pickPoints(data, point, scale).sort(), [4, 5]);
    const equalWeight = client.project(data, data.points[0].x, data.points[0].y);
    assert.deepEqual(client.pickPoints(data, equalWeight, scale), [0]);
  }
});

test("dense frontier reports one solved portfolio and heatmaps retain row orientation", () => {
  const frontier = models.frontier, item = frontier.points[150];
  const indices = client.pickPoints(frontier, client.project(frontier, item.x, item.y), 1);
  assert.deepEqual(indices, [150]);
  const weights = models.rolling_weights;
  assert.deepEqual(client.heatCell(weights, client.project(weights, 5, 0)), { row: 0, column: 5 });
  assert.deepEqual(client.heatCell(weights, client.project(weights, 9, 9)), { row: 9, column: 9 });
  assert.equal(client.nearestIndex([1, 4, 5, 8], 3.7), 1);
  assert.equal(client.nearestIndex([1, 4, 5, 8], 4.5), 1);
});

// A DOM contract harness exercises events without opening a browser or URL.
function harness() {
  const ids = new Map(), figures = [], frames = new Map();
  let nextFrame = 0;
  class Element {
    constructor(tag) { this.tag = tag; this.children = []; this.attributes = {}; this.events = {}; this.style = {}; this.dataset = {}; this._text = ""; }
    setAttribute(key, value) { this.attributes[key] = String(value); if (key === "id") { this.id = String(value); ids.set(this.id, this); } }
    getAttribute(key) { return this.attributes[key] ?? null; }
    append(...elements) { this.children.push(...elements); }
    replaceChildren(...elements) { this.children = elements; this._text = ""; }
    set textContent(value) { this._text = String(value); this.children = []; }
    get textContent() { return this._text + this.children.map(child => child.textContent).join(" "); }
    addEventListener(name, callback) { (this.events[name] ||= []).push(callback); }
    fire(name, event = {}) { (this.events[name] || []).forEach(callback => callback({ target: this, ...event })); }
    getBoundingClientRect() { return { left: 40, top: 450, width: 310, height: 240 }; }
    querySelector(selector) { if (selector === ".plot svg") return this.svg; if (selector === "metadata[data-chart]") return this.metadata; return null; }
    querySelectorAll() { return this.buttons || []; }
    closest() { return this; }
  }
  const document = {
    body: new Element("body"), activeElement: null, events: {},
    createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag),
    getElementById: id => ids.get(id) || null,
    querySelectorAll: () => figures,
    addEventListener(name, callback) { (this.events[name] ||= []).push(callback); }
  };
  const matrix = { a: 1.25, b: 0, c: 0, d: 1.25, e: 40, f: 100,
    inverse() { return { a: .8, b: 0, c: 0, d: .8, e: -32, f: -80 }; } };
  Object.entries(models).forEach(([slug, data]) => {
    const figure = new Element("figure"), svg = new Element("svg"), metadata = new Element("metadata");
    figure.dataset.chartSlug = slug; figure.svg = svg; svg.metadata = metadata;
    metadata.textContent = JSON.stringify(data);
    svg.setAttribute("aria-describedby", `${slug}-hint`);
    svg.getScreenCTM = () => matrix;
    svg.createSVGPoint = () => ({ x: 0, y: 0, matrixTransform(m) { return { x: m.a * this.x + m.c * this.y + m.e, y: m.b * this.x + m.d * this.y + m.f }; } });
    (data.points || []).filter(item => item.gid).forEach(item => { const group = new Element("g"); group.setAttribute("id", `${slug}-${item.gid}`); });
    figure.buttons = (data.legend || []).map(item => { const button = new Element("button"); button.dataset.chartPoint = String(item.index); return button; });
    figures.push(figure);
  });
  const window = {
    innerWidth: 978, innerHeight: 764, events: {},
    requestAnimationFrame(callback) { frames.set(++nextFrame, callback); return nextFrame; },
    cancelAnimationFrame(id) { frames.delete(id); },
    addEventListener(name, callback) { (this.events[name] ||= []).push(callback); },
    flush() { const queued = [...frames.values()]; frames.clear(); queued.forEach(callback => callback()); }
  };
  vm.runInNewContext(embeddedScript, { document, window });
  return { document, window, ids, figures, tooltip: document.body.children[0],
    find: slug => figures.find(figure => figure.dataset.chartSlug === slug),
    eventPoint: (data, x, y) => { const point = client.project(data, x, y); return { clientX: 40 + 1.25 * point.x, clientY: 100 + 1.25 * point.y }; } };
}

test("hover compares both capped portfolios and keyboard can isolate one", () => {
  const env = harness(), data = models.oos_risk_return, figure = env.find("oos_risk_return");
  figure.svg.fire("pointermove", env.eventPoint(data, data.points[4].x, data.points[4].y)); env.window.flush();
  assert.equal(env.tooltip.hidden, false);
  assert.match(env.tooltip.textContent, /Overlapping portfolios/);
  assert.match(env.tooltip.textContent, /Max Sharpe · sample capped/);
  assert.match(env.tooltip.textContent, /Max Sharpe · LW capped/);
  figure.svg.fire("keydown", { key: "End", preventDefault() {} });
  assert.doesNotMatch(env.tooltip.textContent, /Max Sharpe · sample capped/);
  assert.equal(env.ids.get("oos_risk_return-strategy-4").style.opacity, ".12");
  assert.equal(env.ids.get("oos_risk_return-strategy-5").style.opacity, "");
  figure.svg.fire("blur");
  assert.equal(env.tooltip.hidden, true);
  assert.equal(figure.svg.getAttribute("aria-describedby"), "oos_risk_return-hint");
});

test("tap exposes a dated allocation and keyboard exposes final portfolio values", () => {
  const env = harness(), heat = env.find("rolling_weights"), data = models.rolling_weights;
  heat.svg.fire("pointerup", env.eventPoint(data, 5, 0));
  assert.ok(env.tooltip.textContent.includes(`SPY · ${data.columns[5]}`));
  assert.ok(env.tooltip.textContent.includes(`${(100 * data.values[0][5]).toFixed(2)}%`));
  const wealth = env.find("wealth"), series = models.wealth;
  let prevented = false;
  wealth.svg.fire("keydown", { key: "End", preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.ok(env.tooltip.textContent.includes(series.dates.at(-1)));
  assert.ok(env.tooltip.textContent.includes(`$${series.series[0].values.at(-1).toFixed(4)}`));
  assert.match(env.tooltip.textContent, /\$1 initial investment/);
  wealth.svg.fire("keydown", { key: "Escape" });
  assert.equal(env.tooltip.hidden, true);
});

test("correlation remains static and twelve interactive charts support a narrow viewport", () => {
  const env = harness();
  assert.equal(env.figures.length, 12);
  assert.equal(env.find("correlation"), undefined);
  const correlation = page.match(/<figure\b[^>]*data-chart-slug='correlation'[\s\S]*?<\/figure>/)[0];
  assert.doesNotMatch(correlation, /interactive-chart|tabindex=|chart-hint|data-chart="true"/);
  assert.doesNotMatch(page, /aria-label="Highlight a portfolio"/);
  env.window.innerWidth = 375; env.window.innerHeight = 600;
  env.figures.forEach(figure => {
    figure.svg.fire("keydown", { key: "Home", preventDefault() {} });
    assert.equal(env.tooltip.hidden, false, figure.dataset.chartSlug);
    assert.ok(parseFloat(env.tooltip.style.left) >= 12);
    assert.ok(parseFloat(env.tooltip.style.left) + 310 <= 363);
    assert.ok(parseFloat(env.tooltip.style.top) >= 12);
    assert.ok(parseFloat(env.tooltip.style.top) + 240 <= 588);
  });
});
