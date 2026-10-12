"""Execute the full empirical study and regenerate the standalone website page."""

from __future__ import annotations

import argparse
from importlib.metadata import version
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd

from src.data import ASSETS, CASH_PROXY, download_prices
from src.portfolio import (
    STRATEGIES, TRADING_DAYS, annual_estimates, bootstrap_weights,
    concentration, efficient_frontier, fixed_weight_holdout, max_drawdown, performance,
    perturb_mean_weights, portfolio_return, portfolio_volatility,
    risk_contributions, strategy_weights, walk_forward,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TRAIN_END = "2018-12-31"
ROBUST_NAMES = ("Equal weight", "GMV · Ledoit–Wolf", "Max Sharpe · sample capped")


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def summarize_backtest(backtest, cash: pd.Series) -> pd.DataFrame:
    years = len(backtest.net) / TRADING_DAYS
    rows = []
    for name in backtest.net.columns:
        net = performance(backtest.net[name], cash)
        gross = performance(backtest.gross[name], cash)
        weights = backtest.weights.xs(name, level="strategy")
        trades = backtest.trades.xs(name, level="strategy")
        rows.append({
            "strategy": name, **net,
            "gross_annual_return": gross["annual_return"],
            "gross_sharpe_excess_bil": gross["sharpe_excess_bil"],
            "return_cost_drag_pp": 100 * (gross["annual_return"] - net["annual_return"]),
            "annual_turnover": float(trades.turnover.sum() / years),
            "mean_effective_positions": float(weights.effective_positions.mean()),
            "mean_predicted_volatility": float(weights.predicted_volatility.mean()),
            "volatility_forecast_ratio": float(net["annual_volatility"] / weights.predicted_volatility.mean()),
        })
    return pd.DataFrame(rows).set_index("strategy")


def describe_assets(train: pd.DataFrame, cash: pd.Series) -> pd.DataFrame:
    rows = []
    for ticker, role in ASSETS.items():
        daily = train[ticker]
        excess = daily - cash
        rows.append({
            "ticker": ticker, "role": role,
            "annual_arithmetic_mean": float(daily.mean() * TRADING_DAYS),
            "annual_compounded_return": float((1 + daily).prod() ** (TRADING_DAYS / len(daily)) - 1),
            "annual_volatility": float(daily.std(ddof=1) * np.sqrt(TRADING_DAYS)),
            "sharpe_excess_bil": float(excess.mean() / excess.std(ddof=1) * np.sqrt(TRADING_DAYS)),
            "max_drawdown": max_drawdown(daily),
            "skew": float(daily.skew()), "excess_kurtosis": float(daily.kurt()),
            "observations": int(len(daily)),
        })
    return pd.DataFrame(rows).set_index("ticker")


def run(refresh: bool = False) -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    returns, volumes = download_prices(ROOT, refresh=refresh)
    audit = json.loads((ROOT / "data" / "processed" / "data_audit.json").read_text(encoding="utf-8"))
    assets = returns[list(ASSETS)]
    cash = returns[CASH_PROXY]
    train = assets.loc[:TRAIN_END]
    train_cash = cash.loc[train.index]
    if len(train) < 1500 or len(assets.loc["2019-01-01":]) < 1500:
        raise ValueError("Chronological diagnostic split is too short")
    for ticker in ASSETS:
        daily = returns[ticker]
        max_abs = float(daily.abs().max())
        if max_abs > .35:
            raise ValueError(f"Potential adjusted-price outlier for {ticker}: {max_abs:.1%}")

    description = describe_assets(train, train_cash)
    description.to_csv(RESULTS / "descriptive_stats.csv", float_format="%.10g")
    corr = train.corr()
    corr.to_csv(RESULTS / "training_correlations.csv", float_format="%.10g")
    mu, sample, shrunk, shrinkage = annual_estimates(train)
    rf = float(train_cash.mean() * TRADING_DAYS)
    baseline_weights = strategy_weights(mu, sample, shrunk, rf)
    baseline_rows = []
    risk_rows = []
    for name, weights in baseline_weights.items():
        model_cov = shrunk if ("Ledoit" in name or "LW capped" in name) else sample
        vol = portfolio_volatility(weights, model_cov)
        hhi, neff = concentration(weights)
        baseline_rows.append({
            "strategy": name, "expected_return": portfolio_return(weights, mu),
            "predicted_volatility": vol, "estimated_sharpe_excess_bil": (portfolio_return(weights, mu) - rf) / vol,
            "hhi": hhi, "effective_positions": neff, "largest_weight": float(weights.max()),
            **dict(zip(ASSETS, weights)),
        })
        risk = risk_contributions(weights, model_cov)
        for ticker, weight, contribution in zip(ASSETS, weights, risk):
            risk_rows.append({"strategy": name, "ticker": ticker, "capital_weight": weight,
                              "volatility_contribution": contribution, "risk_share": contribution / vol})
    baseline = pd.DataFrame(baseline_rows).set_index("strategy")
    baseline.to_csv(RESULTS / "baseline_portfolios.csv", float_format="%.10g")
    pd.DataFrame(risk_rows).to_csv(RESULTS / "risk_contributions.csv", index=False, float_format="%.10g")
    frontier = efficient_frontier(mu, sample)
    frontier.to_csv(RESULTS / "efficient_frontier.csv", index=False, float_format="%.10g")

    fixed_test = assets.loc["2019-01-01":]
    fixed_cash = cash.loc[fixed_test.index]
    fixed_rows = []
    fixed_daily = {}
    for name, weights in baseline_weights.items():
        _, net_daily, traded = fixed_weight_holdout(fixed_test, weights, cost_bps=5)
        fixed_daily[name] = net_daily
        fixed_rows.append({"strategy": name, **performance(net_daily, fixed_cash),
                           "annual_turnover": float(traded / (len(fixed_test) / TRADING_DAYS))})
    fixed_metrics = pd.DataFrame(fixed_rows).set_index("strategy")
    fixed_metrics.to_csv(RESULTS / "fixed_holdout_metrics.csv", float_format="%.10g")
    pd.DataFrame(fixed_daily).to_csv(RESULTS / "fixed_holdout_daily_net.csv", float_format="%.10g")

    bootstrap = bootstrap_weights(train, rf, repetitions=300, seed=42)
    bootstrap.to_csv(RESULTS / "bootstrap_weights.csv", index=False, float_format="%.10g")
    perturb = perturb_mean_weights(train, rf, repetitions=300, seed=1729)
    perturb.to_csv(RESULTS / "mean_perturbation_weights.csv", index=False, float_format="%.10g")

    backtest = walk_forward(assets, cash, window=756, rebalance="monthly", cost_bps=5)
    if not (backtest.audit.train_end < backtest.audit.index).all():
        raise AssertionError("Look-ahead audit failed")
    backtest.gross.to_csv(RESULTS / "walk_forward_daily_gross.csv", float_format="%.10g")
    backtest.net.to_csv(RESULTS / "walk_forward_daily_net.csv", float_format="%.10g")
    backtest.weights.to_csv(RESULTS / "walk_forward_weights.csv", float_format="%.10g")
    backtest.trades.to_csv(RESULTS / "turnover.csv", float_format="%.10g")
    backtest.audit.to_csv(RESULTS / "walk_forward_audit.csv")
    oos = summarize_backtest(backtest, cash)
    oos.to_csv(RESULTS / "walk_forward_metrics.csv", float_format="%.10g")
    matched_rows = []
    for name in STRATEGIES:
        matched_rows.append({"strategy": name, **performance(backtest.net.loc[fixed_test.index.min():, name], cash)})
    matched = pd.DataFrame(matched_rows).set_index("strategy")
    matched.to_csv(RESULTS / "matched_period_walk_forward_metrics.csv", float_format="%.10g")

    # Compare a few ex-ante design choices over exactly the same later period.
    robustness_runs = {
        "2y / monthly": walk_forward(assets, cash, window=504, names=ROBUST_NAMES),
        "3y / monthly": backtest,
        "5y / monthly": walk_forward(assets, cash, window=1260, names=ROBUST_NAMES),
        "3y / quarterly": walk_forward(assets, cash, window=756, rebalance="quarterly", names=ROBUST_NAMES),
    }
    raw_common_start = max(run.net.index.min() for run in robustness_runs.values())
    # Start on the next quarter's first session so every design has an active
    # rebalance opportunity on the comparison boundary.
    common_start = assets.index[(assets.index > raw_common_start) &
                                (assets.index.to_period("Q") > raw_common_start.to_period("Q"))][0]
    robust_rows = []
    for design, run_data in robustness_runs.items():
        for name in ROBUST_NAMES:
            metrics = performance(run_data.net.loc[common_start:, name], cash)
            trades = run_data.trades.xs(name, level="strategy").loc[common_start:]
            years = len(run_data.net.loc[common_start:]) / TRADING_DAYS
            robust_rows.append({"design": design, "strategy": name, **metrics,
                                "annual_turnover": float(trades.turnover.sum() / years)})
    robustness = pd.DataFrame(robust_rows)
    robustness.to_csv(RESULTS / "robustness.csv", index=False, float_format="%.10g")

    bootstrap_ms = bootstrap.loc[bootstrap.strategy == "Max Sharpe · sample", list(ASSETS)]
    bootstrap_gmv = bootstrap.loc[bootstrap.strategy == "GMV · sample", list(ASSETS)]
    perturb_weights = perturb[list(ASSETS)]
    summary = {
        "environment": {"python": platform.python_version(), **{package: version(package) for package in
                        ("numpy", "pandas", "scipy", "scikit-learn", "matplotlib", "yfinance")}},
        "data": audit,
        "train_start": str(train.index.min().date()),
        "train_end": str(train.index.max().date()),
        "train_rows": len(train),
        "oos_start": str(backtest.net.index.min().date()),
        "oos_end": str(backtest.net.index.max().date()),
        "oos_rows": len(backtest.net),
        "cash_proxy": "BIL adjusted-price daily returns; trailing arithmetic mean for optimization and realized daily return for Sharpe",
        "training_cash_rate": rf,
        "frontier_points": len(frontier),
        "shrinkage_intensity": shrinkage,
        "sample_cov_condition_number": float(np.linalg.cond(sample)),
        "sample_cov_min_eigenvalue": float(np.linalg.eigvalsh(sample).min()),
        "bootstrap_repetitions": 300,
        "perturb_repetitions": 300,
        "perturbation_scale": "Independent normal shocks, 0.5 × each asset's training-sample annual-mean standard error; covariance fixed",
        "bootstrap_mean_neff_max_sharpe": float(bootstrap.loc[bootstrap.strategy == "Max Sharpe · sample", "effective_positions"].mean()),
        "bootstrap_mean_neff_gmv": float(bootstrap.loc[bootstrap.strategy == "GMV · sample", "effective_positions"].mean()),
        "bootstrap_ms_weight_p05": bootstrap_ms.quantile(.05).to_dict(),
        "bootstrap_ms_weight_p50": bootstrap_ms.quantile(.50).to_dict(),
        "bootstrap_ms_weight_p95": bootstrap_ms.quantile(.95).to_dict(),
        "bootstrap_gmv_weight_p05": bootstrap_gmv.quantile(.05).to_dict(),
        "bootstrap_gmv_weight_p50": bootstrap_gmv.quantile(.50).to_dict(),
        "bootstrap_gmv_weight_p95": bootstrap_gmv.quantile(.95).to_dict(),
        "perturb_ms_weight_p05": perturb_weights.quantile(.05).to_dict(),
        "perturb_ms_weight_p95": perturb_weights.quantile(.95).to_dict(),
        "baseline": baseline.to_dict(orient="index"),
        "fixed_holdout_start": str(fixed_test.index.min().date()),
        "fixed_holdout_end": str(fixed_test.index.max().date()),
        "fixed_holdout": fixed_metrics.to_dict(orient="index"),
        "out_of_sample": oos.to_dict(orient="index"),
        "matched_period_walk_forward": matched.to_dict(orient="index"),
        "robustness_common_start": str(common_start.date()),
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    from analysis.visualization import generate_figures
    from analysis.page import build_page
    generate_figures(ROOT, train, cash.loc[train.index], description, corr, frontier, baseline,
                     pd.DataFrame(risk_rows), bootstrap, perturb, backtest, oos)
    build_page(ROOT, summary, description, baseline, oos, robustness, corr)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Redownload provider data instead of using local raw cache")
    args = parser.parse_args()
    result = run(refresh=args.refresh)
    print(f"Generated portfolio project: {result['data']['common_start']} to {result['data']['common_end']}; "
          f"{result['oos_rows']} out-of-sample sessions")
