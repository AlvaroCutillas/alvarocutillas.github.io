"""Portfolio estimators, constrained optimization, diagnostics and backtesting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf

TRADING_DAYS = 252


def annual_estimates(returns: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    values = returns.to_numpy(dtype=float)
    if values.ndim != 2 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("Returns require at least two complete finite observations")
    mu = values.mean(axis=0) * TRADING_DAYS
    sample = np.cov(values, rowvar=False, ddof=1) * TRADING_DAYS
    if not np.allclose(sample, sample.T, atol=1e-12):
        raise ValueError("Sample covariance is not symmetric")
    if np.linalg.eigvalsh(sample).min() < -1e-10:
        raise ValueError("Sample covariance is not positive semidefinite")
    estimator = LedoitWolf().fit(values)
    shrunk = estimator.covariance_ * TRADING_DAYS
    return mu, sample, shrunk, float(estimator.shrinkage_)


def portfolio_return(weights: np.ndarray, mu: np.ndarray) -> float:
    return float(np.dot(weights, mu))


def portfolio_variance(weights: np.ndarray, cov: np.ndarray) -> float:
    return float(weights @ cov @ weights)


def portfolio_volatility(weights: np.ndarray, cov: np.ndarray) -> float:
    return float(np.sqrt(max(portfolio_variance(weights, cov), 0)))


def concentration(weights: np.ndarray) -> tuple[float, float]:
    hhi = float(np.sum(np.square(weights)))
    return hhi, 1.0 / hhi


def risk_contributions(weights: np.ndarray, cov: np.ndarray) -> np.ndarray:
    volatility = portfolio_volatility(weights, cov)
    if volatility <= 0:
        raise ValueError("Positive portfolio volatility required")
    result = weights * (cov @ weights) / volatility
    if not np.isclose(result.sum(), volatility, atol=1e-9, rtol=1e-8):
        raise ArithmeticError("Risk contributions do not reconcile")
    return result


def turnover(target: np.ndarray, pretrade: np.ndarray) -> float:
    """Two-sided absolute traded notional; no 0.5 multiplier."""
    return float(np.abs(target - pretrade).sum())


def _validate_weights(weights: np.ndarray, cap: float, target: float | None = None, mu: np.ndarray | None = None) -> None:
    if not np.isfinite(weights).all() or abs(weights.sum() - 1) > 2e-6:
        raise ArithmeticError("Invalid optimizer budget")
    if weights.min() < -2e-6 or weights.max() > cap + 2e-6:
        raise ArithmeticError("Optimizer violated bounds")
    if target is not None and abs(portfolio_return(weights, mu) - target) > 2e-5:
        raise ArithmeticError("Optimizer violated target return")


def optimize(
    mu: np.ndarray, cov: np.ndarray, mode: str, rf: float = 0.0,
    cap: float = 1.0, target: float | None = None,
) -> np.ndarray:
    n = len(mu)
    if cap * n < 1 - 1e-10:
        raise ValueError("Infeasible position cap")
    if cov.shape != (n, n) or not np.isfinite(mu).all() or not np.isfinite(cov).all():
        raise ValueError("Invalid moments")
    if mode not in {"min_var", "max_sharpe"}:
        raise ValueError(f"Unknown optimization mode: {mode}")
    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1, "jac": lambda w: np.ones(n)}]
    if target is not None:
        constraints.append({"type": "eq", "fun": lambda w: float(w @ mu - target), "jac": lambda w: mu})
    if mode == "min_var":
        fun = lambda w: float(w @ cov @ w)
        jac = lambda w: 2 * cov @ w
    else:
        def fun(w: np.ndarray) -> float:
            var = max(float(w @ cov @ w), 1e-15)
            return -float((w @ mu - rf) / np.sqrt(var))

        def jac(w: np.ndarray) -> np.ndarray:
            var = max(float(w @ cov @ w), 1e-15)
            excess = float(w @ mu - rf)
            return -(mu / np.sqrt(var) - excess * (cov @ w) / (var ** 1.5))
    result = minimize(
        fun, np.repeat(1 / n, n), jac=jac, method="SLSQP",
        bounds=[(0, cap)] * n, constraints=constraints,
        options={"maxiter": 500, "ftol": 1e-9},
    )
    if not result.success:
        raise RuntimeError(f"{mode} optimization failed: {result.message}")
    weights = np.asarray(result.x)
    _validate_weights(weights, cap, target, mu)
    return weights


def efficient_frontier(mu: np.ndarray, cov: np.ndarray, points: int = 301) -> pd.DataFrame:
    """Trace the upper branch using actual constrained solves, not a spline."""
    gmv = optimize(mu, cov, "min_var")
    floor = portfolio_return(gmv, mu)
    ceiling = float(np.max(mu) - 1e-5)
    rows = []
    for target in np.linspace(floor, ceiling, points):
        w = optimize(mu, cov, "min_var", target=float(target))
        rows.append({"target_return": target, "volatility": portfolio_volatility(w, cov), "return": portfolio_return(w, mu)})
    return pd.DataFrame(rows)


def max_drawdown(daily: pd.Series) -> float:
    wealth = (1 + daily).cumprod()
    peak = np.maximum.accumulate(np.r_[1.0, wealth.to_numpy()])[1:]
    return float((wealth.to_numpy() / peak - 1).min())


def performance(daily: pd.Series, cash: pd.Series) -> dict[str, float]:
    daily = daily.astype(float)
    cash = cash.loc[daily.index].astype(float)
    excess = daily - cash
    years = len(daily) / TRADING_DAYS
    return {
        "annual_return": float((1 + daily).prod() ** (1 / years) - 1),
        "annual_volatility": float(daily.std(ddof=1) * np.sqrt(TRADING_DAYS)),
        "sharpe_excess_bil": float(excess.mean() / excess.std(ddof=1) * np.sqrt(TRADING_DAYS)),
        "max_drawdown": max_drawdown(daily),
        "terminal_wealth": float((1 + daily).prod()),
    }


STRATEGIES = (
    "Equal weight",
    "GMV · sample",
    "Max Sharpe · sample",
    "GMV · Ledoit–Wolf",
    "Max Sharpe · sample capped",
    "Max Sharpe · LW capped",
)


def strategy_weights(mu: np.ndarray, sample: np.ndarray, shrunk: np.ndarray, rf: float, names=STRATEGIES) -> dict[str, np.ndarray]:
    n = len(mu)
    recipes = {
        "Equal weight": lambda: np.repeat(1 / n, n),
        "GMV · sample": lambda: optimize(mu, sample, "min_var"),
        "Max Sharpe · sample": lambda: optimize(mu, sample, "max_sharpe", rf),
        "GMV · Ledoit–Wolf": lambda: optimize(mu, shrunk, "min_var"),
        "Max Sharpe · sample capped": lambda: optimize(mu, sample, "max_sharpe", rf, cap=.25),
        "Max Sharpe · LW capped": lambda: optimize(mu, shrunk, "max_sharpe", rf, cap=.25),
    }
    return {name: recipes[name]() for name in names}


@dataclass
class Backtest:
    gross: pd.DataFrame
    net: pd.DataFrame
    weights: pd.DataFrame
    trades: pd.DataFrame
    audit: pd.DataFrame


def walk_forward(
    returns: pd.DataFrame, cash: pd.Series, window: int = 756,
    rebalance: str = "monthly", cost_bps: float = 5.0,
    names: tuple[str, ...] = STRATEGIES,
) -> Backtest:
    """Estimate on observations [t-window,t), trade before return t."""
    if window < 2 or len(returns) <= window or not returns.index.equals(cash.index):
        raise ValueError("Invalid aligned backtest input")
    if rebalance not in {"monthly", "quarterly"}:
        raise ValueError("Rebalance must be monthly or quarterly")
    if cost_bps < 0:
        raise ValueError("Negative cost")
    dates = returns.index
    n = returns.shape[1]
    current = {name: np.zeros(n) for name in names}
    gross_records = []
    net_records = []
    weight_records = []
    trade_records = []
    audit_records = []
    previous_period = None
    for i in range(window, len(returns)):
        date = dates[i]
        period = date.to_period("M" if rebalance == "monthly" else "Q")
        is_rebalance = period != previous_period
        previous_period = period
        day_costs = {name: 0.0 for name in names}
        if is_rebalance:
            train = returns.iloc[i - window:i]
            train_cash = cash.iloc[i - window:i]
            if train.index.max() >= date:
                raise AssertionError("Look-ahead in training window")
            mu, sample, shrunk, _ = annual_estimates(train)
            rf = float(train_cash.mean() * TRADING_DAYS)
            try:
                targets = strategy_weights(mu, sample, shrunk, rf, names)
            except RuntimeError as exc:
                raise RuntimeError(f"Optimizer failed at {date.date()}: {exc}") from exc
            audit_records.append({"rebalance_date": date, "train_start": train.index.min(), "train_end": train.index.max(), "train_rows": len(train)})
            for name, target in targets.items():
                traded = turnover(target, current[name])
                day_costs[name] = cost_bps / 10000 * traded
                trade_records.append({"date": date, "strategy": name, "turnover": traded, "cost_fraction": day_costs[name]})
                forecast_cov = shrunk if ("Ledoit" in name or "LW capped" in name) else sample
                weight_records.append({
                    "date": date, "strategy": name, **dict(zip(returns.columns, target)),
                    "effective_positions": concentration(target)[1],
                    "predicted_volatility": portfolio_volatility(target, forecast_cov),
                })
                current[name] = target.copy()
        day = returns.iloc[i].to_numpy(dtype=float)
        gross_row = {"date": date}
        net_row = {"date": date}
        for name in names:
            weight = current[name]
            gross = float(weight @ day)
            if gross <= -1:
                raise ArithmeticError("Portfolio wealth cannot be nonpositive")
            gross_row[name] = gross
            net_row[name] = (1 - day_costs[name]) * (1 + gross) - 1
            current[name] = weight * (1 + day) / (1 + gross)
            if not np.isclose(current[name].sum(), 1, atol=1e-9):
                raise ArithmeticError("Drifted weights do not sum to one")
        gross_records.append(gross_row)
        net_records.append(net_row)
    gross = pd.DataFrame(gross_records).set_index("date")
    net = pd.DataFrame(net_records).set_index("date")
    weights = pd.DataFrame(weight_records).set_index(["date", "strategy"])
    trades = pd.DataFrame(trade_records).set_index(["date", "strategy"])
    audit = pd.DataFrame(audit_records).set_index("rebalance_date")
    return Backtest(gross, net, weights, trades, audit)


def fixed_weight_holdout(returns: pd.DataFrame, target: np.ndarray, cost_bps: float = 5.0) -> tuple[pd.Series, pd.Series, float]:
    """Apply one pre-test allocation to later data, restoring it monthly."""
    target = np.asarray(target, dtype=float)
    if len(target) != returns.shape[1] or not np.isclose(target.sum(), 1):
        raise ValueError("Invalid fixed holdout weights")
    current = np.zeros_like(target)
    previous_month = None
    gross_rows = []
    net_rows = []
    total_turnover = 0.0
    for date, row in returns.iterrows():
        month = date.to_period("M")
        cost = 0.0
        if month != previous_month:
            traded = turnover(target, current)
            total_turnover += traded
            cost = cost_bps / 10000 * traded
            current = target.copy()
            previous_month = month
        daily = row.to_numpy(dtype=float)
        gross = float(current @ daily)
        gross_rows.append((date, gross))
        net_rows.append((date, (1 - cost) * (1 + gross) - 1))
        current = current * (1 + daily) / (1 + gross)
    gross_series = pd.Series(dict(gross_rows), name="gross")
    net_series = pd.Series(dict(net_rows), name="net")
    return gross_series, net_series, total_turnover


def bootstrap_weights(train: pd.DataFrame, rf: float, repetitions: int = 300, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = train.to_numpy()
    rows = []
    for rep in range(repetitions):
        sample = pd.DataFrame(data[rng.integers(0, len(data), len(data))], columns=train.columns)
        mu, cov, _, _ = annual_estimates(sample)
        for label, mode in (("GMV · sample", "min_var"), ("Max Sharpe · sample", "max_sharpe")):
            weights = optimize(mu, cov, mode, rf)
            rows.append({"replicate": rep, "strategy": label, **dict(zip(train.columns, weights)), "effective_positions": concentration(weights)[1]})
    return pd.DataFrame(rows)


def perturb_mean_weights(train: pd.DataFrame, rf: float, repetitions: int = 300, seed: int = 1729) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    mu, cov, _, _ = annual_estimates(train)
    # Half one standard error of the annualized historical mean, asset by asset.
    se = train.std(ddof=1).to_numpy() / np.sqrt(len(train)) * TRADING_DAYS
    rows = []
    for rep in range(repetitions):
        altered = mu + rng.normal(0, .5 * se)
        weights = optimize(altered, cov, "max_sharpe", rf)
        rows.append({"replicate": rep, **dict(zip(train.columns, weights)), "effective_positions": concentration(weights)[1]})
    return pd.DataFrame(rows)
