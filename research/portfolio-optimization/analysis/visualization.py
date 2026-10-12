"""Regenerate portfolio research SVG figures from executed results."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd

from src.data import ASSETS
from analysis.interactive import allocation_rows, attach_data, percent, record

BG = "#050505"
PANEL = "#0d0d0d"
TEXT = "#f5f5f2"
MUTED = "#9a9a94"
GRID = "#303030"
SAGE = "#a7bdb3"
DEEP = "#6e9080"
WARM = "#d3ad84"
COLORS = [SAGE, WARM, "#79978b", "#b6afa2", "#667b73", "#987e6d", "#c4d2c9", "#8b9590", "#ccbea8", "#566c62"]

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": PANEL, "savefig.facecolor": BG,
    "text.color": TEXT, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": GRID, "axes.titlecolor": TEXT, "grid.color": GRID,
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans", "sans-serif"],
    "font.size": 10, "axes.titlesize": 14,
    "axes.titleweight": "semibold", "svg.fonttype": "none", "svg.hashsalt": "portfolio-optimization",
})


def finish(fig, ax, path: Path, grid_axis: str = "both", hover: dict | None = None) -> None:
    if grid_axis:
        ax.grid(True, axis=grid_axis, linewidth=.65, alpha=.65)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.set_gid("chart-axes")
    fig.savefig(path, format="svg", bbox_inches="tight", pad_inches=.2, metadata={"Date": None})
    if hover is not None:
        attach_data(path, ax, hover)
    plt.close(fig)


def bar_record(bar, title: str, rows: list) -> dict:
    x, y, width, height = bar.get_x(), bar.get_y(), bar.get_width(), bar.get_height()
    return record(x + width / 2, y + height / 2, title, rows,
                  bounds=[float(x), float(y), float(x + width), float(y + height)])


def generate_figures(root: Path, train: pd.DataFrame, cash: pd.Series,
                     description: pd.DataFrame, corr: pd.DataFrame, frontier: pd.DataFrame,
                     baseline: pd.DataFrame, risk: pd.DataFrame, bootstrap: pd.DataFrame,
                     perturb: pd.DataFrame, backtest, oos: pd.DataFrame) -> None:
    output = root / "figures"
    output.mkdir(exist_ok=True)
    tickers = list(ASSETS)
    training_period = f"Training sample · {train.index.min():%Y-%m-%d}–{train.index.max():%Y-%m-%d}"
    test_period = f"Net walk-forward · {backtest.net.index.min():%Y-%m-%d}–{backtest.net.index.max():%Y-%m-%d}"

    fig, ax = plt.subplots(figsize=(9, 5.3))
    points = []
    for i, ticker in enumerate(tickers):
        row = description.loc[ticker]
        ax.scatter(100 * row.annual_volatility, 100 * row.annual_arithmetic_mean,
                   s=70, color=COLORS[i], edgecolor=BG, linewidth=1, zorder=3)
        ax.annotate(ticker, (100 * row.annual_volatility, 100 * row.annual_arithmetic_mean),
                    xytext=(6, 5), textcoords="offset points", fontsize=9)
        points.append(record(100 * row.annual_volatility, 100 * row.annual_arithmetic_mean,
                             f"{ticker} · {ASSETS[ticker]}", [["Annual volatility", percent(row.annual_volatility)],
                             ["Arithmetic mean return", percent(row.annual_arithmetic_mean)],
                             ["Excess Sharpe", f"{row.sharpe_excess_bil:.3f}"]]))
    ax.set(title="Asset return and risk · training sample", xlabel="Annualized volatility (%)", ylabel="Annualized arithmetic mean return (%)")
    ax.margins(x=.08, y=.13)
    finish(fig, ax, output / "asset_risk_return.svg", hover={"mode": "points", "context": training_period, "points": points})

    fig, ax = plt.subplots(figsize=(8.8, 7))
    cmap = LinearSegmentedColormap.from_list("portfolio_corr", ["#f5f8fc", "#85afd0", "#244c7c"])
    im = ax.imshow(corr.to_numpy(), cmap=cmap, vmin=-1, vmax=1)
    ax.set_xticks(range(len(tickers)), tickers, rotation=45, ha="right")
    ax.set_yticks(range(len(tickers)), tickers)
    ax.set_title("Daily return correlation · training sample", pad=18)
    for i in range(len(tickers)):
        for j in range(len(tickers)):
            value = corr.iloc[i, j]
            rgb = np.asarray(cmap(im.norm(value))[:3])
            linear_rgb = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
            luminance = float(linear_rgb @ np.array([.2126, .7152, .0722]))
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8,
                    color=BG if luminance > .18 else TEXT)
    colorbar = fig.colorbar(im, ax=ax, shrink=.72, label="Correlation")
    colorbar.set_ticks([-1, -.5, 0, .5, 1], labels=["−1.0", "−0.5", "0.0", "+0.5", "+1.0"])
    finish(fig, ax, output / "correlation.svg", grid_axis="")

    fig, ax = plt.subplots(figsize=(9, 5.6))
    points = [record(100 * row.volatility, 100 * row["return"], "Solved efficient portfolio",
              [["Estimated annual volatility", percent(row.volatility)], ["Estimated arithmetic return", percent(row["return"])],
               ["Target return", percent(row.target_return)]], kind="line") for _, row in frontier.iterrows()]
    ax.plot(100 * frontier.volatility, 100 * frontier["return"], color=SAGE, linewidth=2.6, label="Solved long-only frontier")
    for ticker in tickers:
        row = description.loc[ticker]
        ax.scatter(100 * row.annual_volatility, 100 * row.annual_arithmetic_mean, color=MUTED, s=24)
        ax.annotate(ticker, (100 * row.annual_volatility, 100 * row.annual_arithmetic_mean), xytext=(4, 3), textcoords="offset points", fontsize=7)
        points.append(record(100 * row.annual_volatility, 100 * row.annual_arithmetic_mean, ticker,
                             [["Annual volatility", percent(row.annual_volatility)], ["Arithmetic mean return", percent(row.annual_arithmetic_mean)]]))
    for name, color, marker in [("Equal weight", WARM, "o"), ("GMV · sample", TEXT, "s"), ("Max Sharpe · sample", DEEP, "D")]:
        row = baseline.loc[name]
        ax.scatter(100 * row.predicted_volatility, 100 * row.expected_return, s=95, color=color, marker=marker, edgecolor=BG, label=name, zorder=5)
        points.append(record(100 * row.predicted_volatility, 100 * row.expected_return, name,
                             [["Estimated annual volatility", percent(row.predicted_volatility)], ["Estimated arithmetic return", percent(row.expected_return)],
                              ["Estimated excess Sharpe", f"{row.estimated_sharpe_excess_bil:.3f}"], *allocation_rows(row, tickers)]))
    ax.set(title="Estimated efficient frontier · training sample", xlabel="Estimated annual volatility (%)", ylabel="Estimated annual arithmetic return (%)")
    ax.margins(x=.08, y=.13)
    ax.legend(frameon=False, fontsize=8, loc="best", labelcolor=TEXT)
    finish(fig, ax, output / "frontier.svg", hover={"mode": "points", "context": training_period, "points": points})

    names = ["Equal weight", "GMV · sample", "Max Sharpe · sample", "Max Sharpe · sample capped"]
    fig, ax = plt.subplots(figsize=(10, 5.8))
    x = np.arange(len(tickers))
    width = .19
    points = []
    for i, name in enumerate(names):
        bars = ax.bar(x + (i - 1.5) * width, 100 * baseline.loc[name, tickers].to_numpy(dtype=float), width,
                      color=[WARM, SAGE, "#6e9080", "#c6d4cc"][i], label=name)
        points.extend(bar_record(bar, f"{ticker} · {name}", [["Capital weight", percent(baseline.loc[name, ticker])]])
                      for bar, ticker in zip(bars, tickers))
    ax.set_xticks(x, tickers)
    ax.set(title="What the optimizer wants to own", ylabel="Capital weight (%)")
    ax.legend(frameon=False, fontsize=8, ncol=2, labelcolor=TEXT)
    finish(fig, ax, output / "baseline_weights.svg", grid_axis="y", hover={"mode": "points", "context": training_period, "points": points})

    selected = risk.loc[risk.strategy == "Max Sharpe · sample capped"].set_index("ticker").loc[tickers]
    fig, ax = plt.subplots(figsize=(9.6, 5.1))
    x = np.arange(len(tickers))
    capital_bars = ax.bar(x - .18, 100 * selected.capital_weight, .35, color=SAGE, label="Capital weight")
    risk_bars = ax.bar(x + .18, 100 * selected.risk_share, .35, color=WARM, label="Share of portfolio volatility")
    points = [bar_record(bar, f"{ticker} · {label}", [["Capital weight", percent(selected.loc[ticker, "capital_weight"])],
              ["Share of portfolio volatility", percent(selected.loc[ticker, "risk_share"])]])
              for bars, label in [(capital_bars, "Capital weight"), (risk_bars, "Risk share")] for bar, ticker in zip(bars, tickers)]
    ax.set_xticks(x, tickers)
    ax.set(title="Capital allocation is not risk allocation", ylabel="Share (%)")
    ax.legend(frameon=False, fontsize=8, labelcolor=TEXT)
    finish(fig, ax, output / "risk_contributions.svg", grid_axis="y", hover={"mode": "points", "context": training_period, "points": points})

    fig, ax = plt.subplots(figsize=(10, 5.7))
    points = []
    for i, (name, color) in enumerate([("GMV · sample", SAGE), ("Max Sharpe · sample", WARM)]):
        subset = bootstrap.loc[bootstrap.strategy == name, tickers]
        low, mid, high = [subset.quantile(q).to_numpy() * 100 for q in (.05, .5, .95)]
        y = np.arange(len(tickers)) + (i - .5) * .19
        ax.hlines(y, low, high, color=color, linewidth=3, alpha=.9)
        ax.scatter(mid, y, color=color, s=22, label=name, zorder=3)
        points.extend(record(median, position, f"{ticker} · {name}", [["5th percentile", f"{lo:.2f}%"],
                      ["Median weight", f"{median:.2f}%"], ["95th percentile", f"{hi:.2f}%"], ["Resamples", "300"]],
                      range=[float(lo), float(hi)]) for ticker, lo, median, hi, position in zip(tickers, low, mid, high, y))
    ax.set_yticks(range(len(tickers)), tickers)
    ax.invert_yaxis()
    ax.set(title="Bootstrap allocation ranges · 300 resamples", xlabel="Weight (%) · 5th to 95th percentile")
    ax.legend(frameon=False, fontsize=8, labelcolor=TEXT)
    finish(fig, ax, output / "bootstrap_weights.svg", grid_axis="x", hover={"mode": "points", "context": training_period, "points": points})

    fig, ax = plt.subplots(figsize=(9.5, 5.7))
    low, mid, high = [perturb[tickers].quantile(q).to_numpy() * 100 for q in (.05, .5, .95)]
    y = np.arange(len(tickers))
    ax.hlines(y, low, high, color=SAGE, linewidth=3)
    ax.scatter(mid, y, color=SAGE, s=28, label="Perturbed median")
    ax.scatter(100 * baseline.loc["Max Sharpe · sample", tickers].to_numpy(dtype=float), y,
               color=WARM, marker="x", s=50, linewidth=1.5, label="Original estimate")
    points = [record(median, position, f"{ticker} · Maximum-Sharpe sensitivity", [["Original weight", percent(baseline.loc["Max Sharpe · sample", ticker])],
              ["5th percentile", f"{lo:.2f}%"], ["Perturbed median", f"{median:.2f}%"], ["95th percentile", f"{hi:.2f}%"],
              ["Perturbations", "300"]], range=[float(min(lo, 100 * baseline.loc["Max Sharpe · sample", ticker])), float(max(hi, 100 * baseline.loc["Max Sharpe · sample", ticker]))])
              for ticker, lo, median, hi, position in zip(tickers, low, mid, high, y)]
    ax.set_yticks(y, tickers)
    ax.invert_yaxis()
    ax.set(title="Expected-return estimation sensitivity", xlabel="Estimated maximum-Sharpe weight (%) · 5th to 95th percentile")
    ax.legend(frameon=False, fontsize=8, labelcolor=TEXT)
    finish(fig, ax, output / "mean_sensitivity.svg", grid_axis="x", hover={"mode": "points", "context": training_period, "points": points})

    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    x = np.arange(len(tickers))
    points = []
    for name, shift, color in [("GMV · sample", -.18, SAGE), ("GMV · Ledoit–Wolf", .18, WARM)]:
        bars = ax.bar(x + shift, 100 * baseline.loc[name, tickers].to_numpy(dtype=float), .35, color=color, label=name)
        points.extend(bar_record(bar, f"{ticker} · {name}", [["Capital weight", percent(baseline.loc[name, ticker])]])
                      for bar, ticker in zip(bars, tickers))
    ax.set_xticks(x, tickers)
    ax.set(title="Covariance shrinkage · minimum-variance weights", ylabel="Capital weight (%)")
    ax.legend(frameon=False, fontsize=8, labelcolor=TEXT)
    finish(fig, ax, output / "shrinkage_weights.svg", grid_axis="y", hover={"mode": "points", "context": training_period, "points": points})

    rolling = backtest.weights.xs("Max Sharpe · sample capped", level="strategy")[tickers]
    fig, ax = plt.subplots(figsize=(10.2, 5.6))
    image = ax.imshow(rolling.T.to_numpy(), aspect="auto", interpolation="nearest", cmap=LinearSegmentedColormap.from_list("weights", [PANEL, DEEP, SAGE]), vmin=0, vmax=.25)
    ax.set_yticks(range(len(tickers)), tickers)
    positions = np.linspace(0, len(rolling) - 1, 7, dtype=int)
    ax.set_xticks(positions, [str(rolling.index[i].year) for i in positions])
    ax.set(title="Walk-forward weights · capped maximum Sharpe", xlabel="Rebalance year")
    fig.colorbar(image, ax=ax, shrink=.73, label="Capital weight")
    finish(fig, ax, output / "rolling_weights.svg", grid_axis="", hover={"mode": "heatmap", "kind": "weights",
           "context": "Capped maximum Sharpe · monthly target weights", "rows": tickers,
           "columns": [f"{date:%Y-%m-%d}" for date in rolling.index], "values": rolling.T.to_numpy().round(8).tolist()})

    shown = ["Equal weight", "GMV · sample", "Max Sharpe · sample", "Max Sharpe · sample capped", "Max Sharpe · LW capped"]
    colors = [TEXT, SAGE, "#728d80", WARM, "#cdb497"]
    fig, ax = plt.subplots(figsize=(10.2, 5.8))
    series = []
    for name, color in zip(shown, colors):
        wealth = (1 + backtest.net[name]).cumprod()
        ax.plot(wealth.index, wealth, color=color, linewidth=1.7, label=name)
        series.append({"name": name, "color": color, "values": wealth.to_numpy().round(8).tolist()})
    ax.set(title="Out-of-sample wealth · net of illustrative costs", ylabel="Growth of $1", xlabel="Date")
    ax.legend(frameon=False, fontsize=8, ncol=2, labelcolor=TEXT)
    time_data = {"mode": "time", "context": "Net portfolio value · $1 initial investment", "format": "wealth",
                 "x": mdates.date2num(backtest.net.index).tolist(), "dates": [f"{date:%Y-%m-%d}" for date in backtest.net.index], "series": series}
    finish(fig, ax, output / "wealth.svg", hover=time_data)

    fig, ax = plt.subplots(figsize=(10.2, 5.3))
    series = []
    for name, color in zip(shown, colors):
        wealth = (1 + backtest.net[name]).cumprod()
        drawdown = wealth / wealth.cummax().clip(lower=1.0) - 1
        ax.plot(drawdown.index, 100 * drawdown, color=color, linewidth=1.4, label=name)
        series.append({"name": name, "color": color, "values": (100 * drawdown).to_numpy().round(6).tolist()})
    ax.set(title="Out-of-sample drawdowns", ylabel="Drawdown (%)", xlabel="Date")
    ax.legend(frameon=False, fontsize=8, ncol=2, labelcolor=TEXT)
    finish(fig, ax, output / "drawdowns.svg", hover=dict(time_data, context="Net portfolio drawdown from its prior peak", format="percent", series=series))

    fig, ax = plt.subplots(figsize=(9.5, 5.3))
    y = np.arange(len(oos))
    bars = ax.barh(y, oos.annual_turnover.to_numpy(), color=[WARM, SAGE, DEEP, "#8ea599", "#bea282", "#d3ad84"])
    points = [bar_record(bar, name, [["Annual traded notional", f"{row.annual_turnover:.3f} × portfolio value"],
              ["Annual CAGR cost drag", f"{row.return_cost_drag_pp:.3f} percentage points"]]) for bar, (name, row) in zip(bars, oos.iterrows())]
    ax.set_yticks(y, oos.index)
    ax.invert_yaxis()
    ax.set(title="Annual traded notional", xlabel="Annual turnover (sum of absolute weight changes)")
    finish(fig, ax, output / "turnover.svg", grid_axis="x", hover={"mode": "points", "context": test_period, "points": points})

    fig, ax = plt.subplots(figsize=(9.2, 6.8))
    colors = {
        "Equal weight": TEXT,
        "GMV · sample": SAGE,
        "Max Sharpe · sample": "#79978b",
        "GMV · Ledoit–Wolf": DEEP,
        "Max Sharpe · sample capped": WARM,
        "Max Sharpe · LW capped": "#c4d2c9",
    }
    label_offsets = {
        "Equal weight": (7, -12),
        "GMV · sample": (7, -5),
        "Max Sharpe · sample": (7, 7),
        "GMV · Ledoit–Wolf": (7, 7),
        "Max Sharpe · sample capped": (7, 30),
        "Max Sharpe · LW capped": (7, -20),
    }
    points = []
    for i, (name, row) in enumerate(oos.iterrows()):
        color = colors[name]
        xy = (100 * row.annual_volatility, 100 * row.annual_return)
        artist = ax.scatter(*xy, s=60, color=color, marker="o", edgecolor=BG, linewidth=.8, zorder=4)
        gid = f"strategy-{i}"
        artist.set_gid(gid)
        ax.annotate(name, xy, xytext=label_offsets[name], textcoords="offset points",
                    color=color, fontsize=9, ha="left", va="center")
        points.append(record(*xy, name, [["Realized annual volatility", percent(row.annual_volatility)],
                      ["Compounded annual return", percent(row.annual_return)], ["Excess Sharpe", f"{row.sharpe_excess_bil:.3f}"],
                      ["Maximum drawdown", percent(row.max_drawdown)], ["Mean effective positions", f"{row.mean_effective_positions:.2f}"]], gid=gid))
    ax.set(title="Out-of-sample risk and return · net", xlabel="Realized annual volatility (%)", ylabel="Compounded annual return (%)")
    # More vertical space and headroom for the labels while keeping true coordinates.
    x = 100 * oos.annual_volatility
    y = 100 * oos.annual_return
    ax.set_xlim(x.min() - .45, x.max() + 1.8)
    ax.set_ylim(y.min() - .55, max(8.8, float(y.max()) + 1.75))
    finish(fig, ax, output / "oos_risk_return.svg", hover={"mode": "points", "context": test_period,
           "points": points})
