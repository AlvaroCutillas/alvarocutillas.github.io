"""Tests for numerical identities and chronological portfolio construction."""

import numpy as np
import pandas as pd
import pytest

from src.data import simple_returns
from src.portfolio import (
    TRADING_DAYS, annual_estimates, bootstrap_weights, concentration, fixed_weight_holdout,
    optimize, portfolio_return, portfolio_variance, risk_contributions,
    turnover, walk_forward,
)


def test_simple_returns_no_fill_and_price_validation():
    prices = pd.DataFrame({"A": [100., 110., 99.], "B": [50., 50., 55.]})
    result = simple_returns(prices)
    np.testing.assert_allclose(result.to_numpy(), [[.1, 0], [-.1, .1]])
    with pytest.raises(ValueError):
        simple_returns(prices.assign(B=[50., np.nan, 55.]))
    with pytest.raises(ValueError):
        simple_returns(prices.assign(B=[50., 0., 55.]))


def test_annualized_mean_covariance_and_dimensions():
    returns = pd.DataFrame({"A": [.01, -.02, .03, .02], "B": [.02, .01, -.01, .00]})
    mu, sample, shrunk, lam = annual_estimates(returns)
    np.testing.assert_allclose(mu, returns.mean().to_numpy() * TRADING_DAYS)
    np.testing.assert_allclose(sample, returns.cov().to_numpy() * TRADING_DAYS)
    assert sample.shape == shrunk.shape == (2, 2)
    assert 0 <= lam <= 1


def test_portfolio_formulas_and_risk_identity():
    weights = np.array([.4, .6])
    mu = np.array([.08, .04])
    cov = np.array([[.04, .01], [.01, .09]])
    assert portfolio_return(weights, mu) == pytest.approx(.056)
    expected_var = .4**2 * .04 + 2 * .4 * .6 * .01 + .6**2 * .09
    assert portfolio_variance(weights, cov) == pytest.approx(expected_var)
    rc = risk_contributions(weights, cov)
    assert rc.sum() == pytest.approx(np.sqrt(expected_var))
    hhi, neff = concentration(weights)
    assert hhi == pytest.approx(.52)
    assert neff == pytest.approx(1 / .52)
    assert turnover(np.array([1., 0.]), np.array([0., 1.])) == pytest.approx(2.)


def test_optimizer_matches_two_asset_analytic_gmv_and_respects_cap():
    mu = np.array([.10, .04])
    cov = np.diag([.04, .09])
    gmv = optimize(mu, cov, "min_var")
    np.testing.assert_allclose(gmv, [.09 / .13, .04 / .13], atol=1e-5)
    capped = optimize(mu, cov, "min_var", cap=.6)
    assert capped.sum() == pytest.approx(1)
    assert capped.max() <= .6 + 1e-6
    frontier_point = optimize(mu, cov, "min_var", target=.07)
    assert portfolio_return(frontier_point, mu) == pytest.approx(.07)
    assert frontier_point.min() >= -1e-8
    with pytest.raises(ValueError):
        optimize(mu, cov, "min_var", cap=.4)


def test_seeded_bootstrap_is_reproducible():
    rng = np.random.default_rng(31)
    sample = pd.DataFrame(rng.normal([.0003, .0001, .0002], [.007, .003, .005], size=(120, 3)), columns=["A", "B", "C"])
    first = bootstrap_weights(sample, rf=.01, repetitions=12, seed=42)
    second = bootstrap_weights(sample, rf=.01, repetitions=12, seed=42)
    pd.testing.assert_frame_equal(first, second)
    assert (first[["A", "B", "C"]].sum(axis=1) - 1).abs().max() < 1e-6


def test_walk_forward_uses_only_prior_returns_and_applies_cost():
    rng = np.random.default_rng(7)
    dates = pd.bdate_range("2020-01-01", periods=45)
    assets = pd.DataFrame(rng.normal([.0004, .0001], [.01, .004], size=(45, 2)), index=dates, columns=["A", "B"])
    cash = pd.Series(np.zeros(45), index=dates)
    original = walk_forward(assets, cash, window=12, names=("GMV · sample", "Equal weight"))
    assert (original.audit.train_end < original.audit.index).all()
    first_date = original.net.index[0]
    altered = assets.copy()
    altered.loc[first_date, "A"] = .5
    changed = walk_forward(altered, cash, window=12, names=("GMV · sample", "Equal weight"))
    first_weight = original.weights.loc[(first_date, "GMV · sample"), ["A", "B"]].to_numpy(dtype=float)
    changed_weight = changed.weights.loc[(first_date, "GMV · sample"), ["A", "B"]].to_numpy(dtype=float)
    np.testing.assert_allclose(first_weight, changed_weight)
    assert original.trades.loc[(first_date, "Equal weight"), "turnover"] == pytest.approx(1)
    gross = original.gross.loc[first_date, "Equal weight"]
    net = original.net.loc[first_date, "Equal weight"]
    assert net == pytest.approx((1 - .0005) * (1 + gross) - 1)
    assert original.weights[["A", "B"]].sum(axis=1).sub(1).abs().max() < 1e-6


def test_fixed_holdout_restores_targets_after_weight_drift():
    dates = pd.to_datetime(["2020-01-30", "2020-01-31", "2020-02-03"])
    returns = pd.DataFrame({"A": [0., .10, 0.], "B": [0., 0., 0.]}, index=dates)
    gross, net, traded = fixed_weight_holdout(returns, np.array([.5, .5]), cost_bps=5)
    assert gross.iloc[1] == pytest.approx(.05)
    assert net.iloc[0] == pytest.approx(-.0005)
    assert traded > 1  # Initial deployment plus the next month's drift correction.
    assert net.iloc[2] < gross.iloc[2]
