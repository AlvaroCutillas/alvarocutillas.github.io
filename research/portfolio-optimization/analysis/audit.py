"""Independent checks on the generated dataset, results and standalone page."""

from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

from src.data import ASSETS, simple_returns
from src.portfolio import performance
from analysis.interactive import read_data

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT.parents[1]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.figures = 0
        self.svgs = 0
        self.sections = 0
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "figure": self.figures += 1
        if tag == "svg": self.svgs += 1
        if tag == "section": self.sections += 1
        if tag == "script": self.scripts += 1


def audit() -> None:
    processed = ROOT / "data" / "processed"
    results = ROOT / "results"
    prices = pd.read_csv(processed / "adjusted_prices.csv", index_col=0, parse_dates=True)
    returns = pd.read_csv(processed / "daily_simple_returns.csv", index_col=0, parse_dates=True)
    report = json.loads((processed / "data_audit.json").read_text(encoding="utf-8"))
    summary = json.loads((results / "summary.json").read_text(encoding="utf-8"))
    assert prices.index.is_monotonic_increasing and prices.index.is_unique
    assert returns.index.is_monotonic_increasing and returns.index.is_unique
    assert not prices.isna().any().any() and (prices > 0).all().all()
    assert not returns.isna().any().any()
    assert list(prices.columns) == [*ASSETS, "BIL"]
    np.testing.assert_allclose(simple_returns(prices), returns, rtol=1e-8, atol=1e-10)
    assert len(prices) == report["price_rows"] and len(returns) == report["return_rows"]

    baseline = pd.read_csv(results / "baseline_portfolios.csv", index_col=0)
    weights = baseline[list(ASSETS)].to_numpy()
    np.testing.assert_allclose(weights.sum(axis=1), 1, atol=2e-6)
    assert weights.min() >= -2e-6 and weights.max() <= 1 + 2e-6
    for name in baseline.index:
        if "capped" in name:
            assert baseline.loc[name, list(ASSETS)].max() <= .25 + 2e-6
    risk = pd.read_csv(results / "risk_contributions.csv")
    for name in baseline.index:
        calculated = risk.loc[risk.strategy == name, "volatility_contribution"].sum()
        assert np.isclose(calculated, baseline.loc[name, "predicted_volatility"], rtol=1e-7)
    frontier = pd.read_csv(results / "efficient_frontier.csv")
    assert len(frontier) >= 20
    assert (frontier["target_return"] - frontier["return"]).abs().max() < 2e-5

    bootstrap = pd.read_csv(results / "bootstrap_weights.csv")
    assert set(bootstrap.groupby("strategy").size()) == {300}
    np.testing.assert_allclose(bootstrap[list(ASSETS)].sum(axis=1), 1, atol=2e-6)
    perturb = pd.read_csv(results / "mean_perturbation_weights.csv")
    assert len(perturb) == 300
    np.testing.assert_allclose(perturb[list(ASSETS)].sum(axis=1), 1, atol=2e-6)

    gross = pd.read_csv(results / "walk_forward_daily_gross.csv", index_col=0, parse_dates=True)
    net = pd.read_csv(results / "walk_forward_daily_net.csv", index_col=0, parse_dates=True)
    trades = pd.read_csv(results / "turnover.csv", parse_dates=["date"])
    audit_dates = pd.read_csv(results / "walk_forward_audit.csv", parse_dates=["rebalance_date", "train_end"])
    assert (audit_dates.train_end < audit_dates.rebalance_date).all()
    assert (audit_dates.train_rows == 756).all()
    assert net.index.equals(gross.index) and len(net) == summary["oos_rows"]
    cost = trades.pivot(index="date", columns="strategy", values="cost_fraction").reindex(net.index).fillna(0)
    cost = cost[net.columns]
    np.testing.assert_allclose((1 - cost) * (1 + gross) - 1, net, atol=2e-9)
    fixed = pd.read_csv(results / "fixed_holdout_daily_net.csv", index_col=0, parse_dates=True)
    fixed_metrics = pd.read_csv(results / "fixed_holdout_metrics.csv", index_col=0)
    assert str(fixed.index.min().date()) == summary["fixed_holdout_start"]
    assert str(fixed.index.max().date()) == summary["fixed_holdout_end"]
    for name in fixed.columns:
        calculated = performance(fixed[name], returns["BIL"])
        assert np.isclose(calculated["sharpe_excess_bil"], fixed_metrics.loc[name, "sharpe_excess_bil"], rtol=1e-8)
    matched = pd.read_csv(results / "matched_period_walk_forward_metrics.csv", index_col=0)
    for name in net.columns:
        calculated = performance(net.loc[fixed.index.min():, name], returns["BIL"])
        assert np.isclose(calculated["annual_return"], matched.loc[name, "annual_return"], rtol=1e-8)
    path = SITE / "projects" / "portfolio-optimization.html"
    page = path.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(page)
    assert parser.figures == parser.svgs == 13 and parser.sections == 16
    assert parser.scripts == 1 and '<script id="chart-interactions">' in page
    client_script = (ROOT / "analysis" / "chart_interactions.js").read_text(encoding="utf-8")
    assert f'<script id="chart-interactions">{client_script}</script>' in page, "Stale embedded interaction code"
    assert "<script src=" not in page, "The chart interactions must remain self-contained"
    assert page.count('data-chart="true"') == 12
    assert page.count("interactive-chart' data-chart-slug=") == 12
    correlation_figure = re.search(r"<figure\b[^>]*data-chart-slug='correlation'.*?</figure>", page, re.S).group(0)
    assert "interactive-chart" not in correlation_figure and "tabindex=" not in correlation_figure
    assert "chart-hint" not in correlation_figure and 'data-chart="true"' not in correlation_figure
    assert 'aria-label="Highlight a portfolio"' not in page
    interactive = [data for svg in re.findall(r"<svg\b.*?</svg>", page, re.S) if (data := read_data(svg)) is not None]
    assert len(interactive) == 12
    for chart in interactive:
        assert chart["box"][2] > chart["box"][0] and chart["box"][3] > chart["box"][1]
        assert chart["xlim"][0] != chart["xlim"][1] and chart["ylim"][0] != chart["ylim"][1]
        if chart["mode"] == "time":
            assert chart["dates"] == net.index.strftime("%Y-%m-%d").tolist()
            assert len(chart["x"]) == len(net)
            for series in chart["series"]:
                wealth = (1 + net[series["name"]]).cumprod()
                expected = wealth if chart["format"] == "wealth" else 100 * (wealth / wealth.cummax().clip(lower=1) - 1)
                np.testing.assert_allclose(series["values"], expected, atol=2e-6)
        elif chart["mode"] == "heatmap":
            assert np.asarray(chart["values"]).shape == (len(chart["rows"]), len(chart["columns"]))
            assert np.isfinite(chart["values"]).all()
            if chart["kind"] == "correlation":
                correlation = pd.read_csv(results / "training_correlations.csv", index_col=0)
                np.testing.assert_allclose(chart["values"], correlation, atol=1e-8)
        else:
            assert len(chart["points"]) > 0
            assert np.isfinite([[point["x"], point["y"]] for point in chart["points"]]).all()
    assert len(parser.ids) == len(set(parser.ids)), "Duplicate IDs across inline SVGs"
    svg_refs = re.findall(r'url\(#([^)]+)\)|(?:xlink:)?href="#([^"]+)"', page)
    assert all((left or right) in parser.ids for left, right in svg_refs), "Broken inline SVG reference"
    assert all(link[1:] in parser.ids for link in parser.links if link.startswith("#"))
    assert not any(link.startswith("file:") for link in parser.links)
    assert "Work in progress" not in page and "hello@example.com" not in page
    assert 'href="https://alvarocutillas.github.io/"' in page
    landing = (SITE / "index.html").read_text(encoding="utf-8")
    card = landing.split('href="projects/portfolio-optimization.html"', 1)[1].split("</a>", 1)[0]
    assert "Work in progress" not in card
    assert re.search(r"net OOS Sharpe", card)
    print(f"Audit passed: {len(returns):,} return rows, {len(net):,} test days, "
          f"{parser.figures} inline figures, {parser.sections} sections, 0 broken in-page anchors")


if __name__ == "__main__":
    audit()
