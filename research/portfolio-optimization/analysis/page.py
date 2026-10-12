"""Render a self-contained research page from executed results and SVG figures."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re

import pandas as pd

from src.data import ASSETS
from analysis.interactive import legend_markup, read_data


def percent(value: float, digits: int = 1) -> str:
    return f"{100 * value:.{digits}f}%"


def number(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th scope='col'>{escape(str(cell))}</th>" for cell in headers)
    body = "".join("<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<div class='table-wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def figure(root: Path, slug: str, title: str, caption: str) -> str:
    source = (root / "figures" / f"{slug}.svg").read_text(encoding="utf-8")
    data = read_data(source)
    svg = source[source.index("<svg"):]
    # Matplotlib reuses IDs such as figure_1 across files. Scope them before
    # putting multiple SVG documents into one standalone HTML document.
    ids = re.findall(r'\bid="([^"]+)"', svg)
    for old in sorted(set(ids), key=len, reverse=True):
        new = f"{slug}-{old}"
        svg = svg.replace(f'id="{old}"', f'id="{new}"')
        svg = svg.replace(f'url(#{old})', f'url(#{new})')
        svg = svg.replace(f'href="#{old}"', f'href="#{new}"')
    hint_id = f"{slug}-hint"
    interactive_attributes = f"tabindex='0' aria-describedby='{hint_id}' " if data is not None else ""
    svg = svg.replace("<svg ", f"<svg role='img' {interactive_attributes}aria-label='{escape(title, quote=True)}' ", 1)
    hint = f'<p class="chart-hint" id="{hint_id}"><span>Explore the data</span> · Hover or tap · Focus the chart and use arrow keys</p>' if data is not None else ""
    interactive_class = " interactive-chart" if data is not None else ""
    legend = legend_markup(data, slug) if data is not None else ""
    return f"<figure class='figure-card figure-wide{interactive_class}' data-chart-slug='{slug}'><div class='plot'>{hint}{svg}{legend}</div><figcaption><strong>{escape(title)}</strong>{caption}</figcaption></figure>"


def build_page(root: Path, summary: dict, description: pd.DataFrame, baseline: pd.DataFrame,
               oos: pd.DataFrame, robustness: pd.DataFrame, corr: pd.DataFrame) -> Path:
    site = root.parents[1]
    destination = site / "projects" / "portfolio-optimization.html"
    black_scholes = (site / "projects" / "black-scholes.html").read_text(encoding="utf-8")
    css = black_scholes.split("<style>", 1)[1].split("</style>", 1)[0]
    css += (root / "analysis" / "chart_interactions.css").read_text(encoding="utf-8")
    chart_client = (root / "analysis" / "chart_interactions.js").read_text(encoding="utf-8")
    css += """
    .key-point{border-left:2px solid var(--accent);padding:5px 0 5px 18px;margin:25px 0;color:#e0e7e1}
    .key-point.warm{border-color:var(--warm)}
    .article a.text-link{color:var(--accent);border-bottom:1px solid var(--accent-deep)}
    .article a.text-link:hover{color:var(--text)}
    .table-wrap table{min-width:680px}
    .figure-card .plot svg{display:block;width:100%;height:auto;max-width:100%}
    .result-pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:24px 0}
    .result-pair .panel{min-width:0}
    .result-pair .panel h3{margin-top:0}
    @media(max-width:760px){.result-pair{grid-template-columns:1fr}}
    """
    d = summary["data"]
    ew = oos.loc["Equal weight"]
    gmv = oos.loc["GMV · sample"]
    gmv_lw = oos.loc["GMV · Ledoit–Wolf"]
    ms = oos.loc["Max Sharpe · sample"]
    cap = oos.loc["Max Sharpe · sample capped"]
    cap_lw = oos.loc["Max Sharpe · LW capped"]
    b_gmv = baseline.loc["GMV · sample"]
    b_ms = baseline.loc["Max Sharpe · sample"]
    b_cap = baseline.loc["Max Sharpe · sample capped"]
    b_lw = baseline.loc["GMV · Ledoit–Wolf"]
    fixed_ew = summary["fixed_holdout"]["Equal weight"]
    fixed_cap = summary["fixed_holdout"]["Max Sharpe · sample capped"]
    matched_cap = summary["matched_period_walk_forward"]["Max Sharpe · sample capped"]

    universe_rows = []
    for item in d["symbols"]:
        if item["ticker"] not in ASSETS:
            continue
        universe_rows.append([item["ticker"], item["role"], item["issuer_inception"], item["first_available"], item["last_available"],
                              f"{item['median_daily_volume']:,}", item["missing_adjusted_close"]])
    asset_rows = []
    for ticker, row in description.iterrows():
        asset_rows.append([ticker, percent(row.annual_arithmetic_mean), percent(row.annual_volatility),
                           number(row.sharpe_excess_bil), percent(row.max_drawdown), int(row.observations)])
    baseline_rows = []
    for name, row in baseline.iterrows():
        baseline_rows.append([name, percent(row.expected_return), percent(row.predicted_volatility),
                              number(row.estimated_sharpe_excess_bil), percent(row.largest_weight), number(row.effective_positions)])
    oos_rows = []
    for name, row in oos.iterrows():
        oos_rows.append([name, percent(row.annual_return), percent(row.annual_volatility),
                         number(row.sharpe_excess_bil), percent(row.max_drawdown), number(row.annual_turnover),
                         number(row.mean_effective_positions)])
    fixed_rows = []
    for name, row in summary["fixed_holdout"].items():
        fixed_rows.append([name, percent(row["annual_return"]), percent(row["annual_volatility"]),
                           number(row["sharpe_excess_bil"]), percent(row["max_drawdown"]),
                           number(row["annual_turnover"])])
    bootstrap_rows = []
    for ticker in ASSETS:
        bootstrap_rows.append([ticker, percent(summary["bootstrap_ms_weight_p05"][ticker], 0),
                               percent(summary["bootstrap_ms_weight_p50"][ticker], 0),
                               percent(summary["bootstrap_ms_weight_p95"][ticker], 0)])
    robust_rows = []
    for _, row in robustness.iterrows():
        robust_rows.append([row.design, row.strategy, percent(row.annual_return),
                            number(row.sharpe_excess_bil), number(row.annual_turnover)])

    fig_risk_return = figure(root, "oos_risk_return", "Out-of-sample risk and return", f"Net monthly-rebalanced results, {summary['oos_start']}–{summary['oos_end']}. Each circular marker retains its measured coordinates; hover near the two capped strategies to compare their close results. The capped sample maximum-Sharpe portfolio has the highest observed excess-return Sharpe here, but its advantage over equal weighting is modest in annual return. Source: executed Yahoo Finance adjusted-price study.")
    fig_asset = figure(root, "asset_risk_return", "Training-sample asset risk and return", f"Arithmetic daily means and sample volatility multiplied by 252 and √252. These are historical estimates, not expected future returns. Source: adjusted ETF prices, {summary['train_start']}–{summary['train_end']}.")
    fig_corr = figure(root, "correlation", "Training-sample correlation", f"The scale runs from white (−1, opposite movement) to blue (+1, movement together), with signed values printed in each cell. SPY and TLT correlation is {number(corr.loc['SPY','TLT'])}; correlation helped diversification in this sample but can change in stress. Source: daily simple returns, {summary['train_start']}–{summary['train_end']}.")
    fig_weights = figure(root, "baseline_weights", "In-sample allocation choices", f"Uncapped sample GMV allocates {percent(b_gmv['AGG'])} to AGG; uncapped estimated maximum Sharpe allocates {percent(b_ms['AGG'])}. The cap spreads exposure but lowers estimated in-sample Sharpe from {number(b_ms.estimated_sharpe_excess_bil)} to {number(b_cap.estimated_sharpe_excess_bil)}. Source: 2010–2018 training data.")
    fig_frontier = figure(root, "frontier", "Long-only efficient frontier", f"The curve connects {summary['frontier_points']} constrained minimum-variance solutions at target arithmetic returns. Every point is solved with the same long-only bounds; no fitted smoothing is applied. Estimated returns and risk depend on the training sample. Source: 2010–2018 sample moments.")
    fig_sensitivity = figure(root, "mean_sensitivity", "Maximum-Sharpe sensitivity to means", f"Across 300 independent half-standard-error perturbations, AGG spans {percent(summary['perturb_ms_weight_p05']['AGG'],0)}–{percent(summary['perturb_ms_weight_p95']['AGG'],0)} and LQD spans {percent(summary['perturb_ms_weight_p05']['LQD'],0)}–{percent(summary['perturb_ms_weight_p95']['LQD'],0)}. Covariance is held fixed. Source: executed perturbation experiment.")
    fig_bootstrap = figure(root, "bootstrap_weights", "Bootstrap allocation uncertainty", f"The maximum-Sharpe AGG median weight is {percent(summary['bootstrap_ms_weight_p50']['AGG'],0)} with a {percent(summary['bootstrap_ms_weight_p05']['AGG'],0)}–{percent(summary['bootstrap_ms_weight_p95']['AGG'],0)} 5th–95th range. GMV is much steadier here because AGG's estimated low volatility dominates. Source: 300 seeded iid resamples of 2010–2018 daily returns.")
    fig_shrink = figure(root, "shrinkage_weights", "Sample versus Ledoit–Wolf GMV", f"Ledoit–Wolf estimates a {percent(summary['shrinkage_intensity'],2)} shrinkage intensity in the training sample. AGG remains {percent(b_lw['AGG'])} of the shrunk GMV portfolio versus {percent(b_gmv['AGG'])} with sample covariance. Source: executed estimators.")
    fig_risk = figure(root, "risk_contributions", "Capital versus risk shares", "For the capped sample maximum-Sharpe portfolio, each volatility contribution is wᵢ(Σw)ᵢ/σₚ and contributions sum to portfolio volatility. A 25% capital cap does not impose a 25% risk cap. Source: training covariance and optimized weights.")
    fig_rolling = figure(root, "rolling_weights", "Walk-forward allocation path", "Each column uses only the preceding 756 daily observations. Color shows the position chosen before that rebalance period's returns; shifts reflect changing estimated inputs, not advance knowledge of later prices. Source: executed monthly backtest.")
    fig_wealth = figure(root, "wealth", "Growth of one dollar", f"Net wealth includes a hypothetical 5 bp cost per unit of two-sided absolute turnover. The capped sample strategy compounds at {percent(cap.annual_return)} annually versus {percent(ew.annual_return)} for equal weight. These are backtest outcomes, not forecasts.")
    fig_drawdown = figure(root, "drawdowns", "Realized drawdowns", f"The capped sample strategy's largest out-of-sample drawdown is {percent(cap.max_drawdown)} versus {percent(ew.max_drawdown)} for equal weight. Historical drawdowns depend on start date and market regime. Source: net daily wealth paths.")
    fig_turnover = figure(root, "turnover", "Trading required by each strategy", f"Uncapped maximum Sharpe trades {number(ms.annual_turnover)} of capital per year under the absolute-weight-change convention, versus {number(ew.annual_turnover)} for equal weight. Costs are illustrative and omit spread, impact and taxes. Source: pretrade drifted weights and monthly targets.")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="Empirical portfolio optimization under estimation error: adjusted ETF data, bootstrap uncertainty, covariance shrinkage and walk-forward results." />
  <meta name="theme-color" content="#050505" />
  <title>Portfolio Optimization Under Estimation Error — Álvaro Cutillas</title>
  <style>{css}</style>
</head>
<body>
<a class="skip" href="#content">Skip to research</a>
<nav aria-label="Primary navigation"><div class="wrap nav-inner">
  <a class="brand" href="https://alvarocutillas.github.io/">Álvaro Cutillas</a>
  <div class="nav-links"><a href="#question">Question</a><a href="#estimation">Estimation</a><a href="#walk-forward">Walk-forward</a><a href="#reliability">Reliability</a></div>
</div></nav>
<main id="content">
  <header class="hero"><div class="wrap">
    <div class="eyebrow">Project 03 / Quantitative research / Portfolio construction</div>
    <h1>Portfolio Optimization<br><span>Under Estimation Error.</span></h1>
    <p class="lede">Efficient frontiers, robust covariance estimation and out-of-sample portfolio construction.</p>
    <p class="context">What looks optimal when estimated from history? How much of that answer survives uncertain inputs, concentration, trading and a strictly chronological test?</p>
    <div class="tag-row"><span class="tag">Python</span><span class="tag">NumPy</span><span class="tag">SciPy</span><span class="tag">Ledoit–Wolf</span><span class="tag">Walk-forward</span><span class="tag">10 ETFs</span></div>
    <div class="hero-stats" aria-label="Executed out-of-sample results">
      <div class="stat"><strong>{number(cap.sharpe_excess_bil)}</strong><small>Capped max-Sharpe · net OOS Sharpe</small></div>
      <div class="stat"><strong>{number(ew.sharpe_excess_bil)}</strong><small>Equal weight · net OOS Sharpe</small></div>
      <div class="stat"><strong class="accent">{number(cap.mean_effective_positions)}</strong><small>Capped max-Sharpe · mean effective positions</small></div>
      <div class="stat"><strong>{number(cap.annual_turnover)}</strong><small>Capped max-Sharpe · annual traded notional</small></div>
    </div>
  </div></header>
  <div class="wrap document">
    <aside class="toc" aria-label="On this page"><div class="toc-title">Research sections</div>
      <a href="#question">01 / Question & findings</a><a href="#data">02 / Universe & data</a>
      <a href="#framework">03 / Model & conventions</a><a href="#baseline">04 / In-sample portfolios</a>
      <a href="#frontier">05 / Efficient frontier</a><a href="#estimation">06 / Estimation error</a>
      <a href="#bootstrap">07 / Bootstrap uncertainty</a><a href="#shrinkage">08 / Shrinkage & constraints</a>
      <a href="#risk">09 / Risk decomposition</a><a href="#walk-forward">10 / Walk-forward design</a>
      <a href="#oos">11 / Out-of-sample results</a><a href="#drawdowns">12 / Drawdowns & forecast risk</a>
      <a href="#costs">13 / Turnover & costs</a><a href="#robustness">14 / Robustness</a>
      <a href="#reliability">15 / Reliability & limits</a><a href="#reproduce">16 / Reproduce & conclude</a>
    </aside>
    <div class="article">
      <section id="question"><span class="section-label">01 / Research question</span><h2>How much should we trust an optimized portfolio?</h2>
        <p class="lead">Mean–variance optimization can produce precise weights from imprecise historical estimates. This study asks whether allocations based on estimated returns and covariance stay useful after resampling uncertainty and live-like re-estimation.</p>
        <div class="result-pair"><div class="panel"><span class="micro">Observed trade-off</span><h3>Constraints helped more than covariance shrinkage</h3><p>On the {summary['oos_start']}–{summary['oos_end']} walk-forward sample, the uncapped sample maximum-Sharpe portfolio has net Sharpe {number(ms.sharpe_excess_bil)} and mean effective positions {number(ms.mean_effective_positions)}. A 25% position cap raises those to {number(cap.sharpe_excess_bil)} and {number(cap.mean_effective_positions)} while cutting annual turnover from {number(ms.annual_turnover)} to {number(cap.annual_turnover)}.</p></div>
        <div class="panel"><span class="micro">Practical benchmark</span><h3>The evidence is mixed</h3><p>On the rolling {summary['oos_start']}–{summary['oos_end']} test, equal weighting earns {percent(ew.annual_return)} compounded annually with Sharpe {number(ew.sharpe_excess_bil)}; the capped optimizer earns {percent(cap.annual_return)} and Sharpe {number(cap.sharpe_excess_bil)}. Yet the one-time {summary['fixed_holdout_start']}–{summary['fixed_holdout_end']} holdout reverses this: fixed equal weight earns {percent(fixed_ew['annual_return'])} against {percent(fixed_cap['annual_return'])} for the fixed capped optimizer. Both comparisons matter.</p></div></div>
        {fig_risk_return}
        <p class="key-point">The in-sample question is “which weights maximize an estimated objective?” The investable question is “which decisions remain defensible when estimates and markets change?”</p>
      </section>

      <section id="data"><span class="section-label">02 / Asset universe & data</span><h2>Ten diversified ETFs, one fixed universe.</h2>
        <p>U.S.-listed asset-class ETFs provide a common adjusted-price history from {d['common_start']} to {d['common_end']}. BIL is downloaded separately as a short-Treasury ETF cash proxy and is never optimized as a risky asset. Issuer inception dates predate the selected 2010 start. Each symbol has {d['price_rows']:,} aligned prices and no missing adjusted close in this chosen period; the common panel loses {d['excluded_calendar_rows']} provider calendar rows. Median daily share volume exceeds the 500,000-share screen for every symbol, but this does not prove that every trade could be executed at the reported close.</p>
        {table(['ETF','Exposure','Issuer inception','First data','Last data','Median daily shares','Missing adj. closes'], universe_rows)}
        <p class="table-note">Source: Yahoo Finance adjusted close via yfinance; provider download through {d['download_end_exclusive']} exclusive. Adjusted close reflects reported splits and distributions. <a class="text-link" href="https://help.yahoo.com/kb/SLN28256.html">Yahoo's adjustment definition</a> and <a class="text-link" href="https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html">yfinance download reference</a>. Inception dates: <a class="text-link" href="https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy">State Street SPY</a>, <a class="text-link" href="https://www.ishares.com/us/products/etf-investments">iShares funds</a>, <a class="text-link" href="https://workplace.vanguard.com/assets/corp/fund_communications/pdf_publish/us-products/fact-sheet/F0986.pdf">Vanguard VNQ</a>, <a class="text-link" href="https://www.ssga.com/us/en/individual/etfs/spdr-gold-shares-gld">State Street GLD</a>, <a class="text-link" href="https://www.invesco.com/us/en/financial-products/etfs/invesco-db-commodity-index-tracking-fund.html">Invesco DBC</a>, <a class="text-link" href="https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil">State Street BIL</a>. Original provider CSVs are cached locally; the cleaned panel and data audit are generated by the research code.</p>
        <p>Prices are aligned on the intersection of dates. No return is forward-filled or set to zero. Daily simple returns start on {summary['train_start']}; the diagnostic training sample ends on {summary['train_end']} ({summary['train_rows']:,} sessions). Descriptive statistics below use training observations only.</p>
        {table(['ETF','Mean return','Volatility','Excess Sharpe','Max drawdown','Days'], asset_rows)}
        {fig_asset}{fig_corr}
        <p>Equity risk dominates the higher-volatility side of the scatter. In this training period SPY–TLT correlation is {number(corr.loc['SPY','TLT'])}, whereas SPY–AGG is {number(corr.loc['SPY','AGG'])}. Those cross-asset relationships can make bonds useful diversifiers, but fixed historical correlation is not a crisis guarantee. The high dispersion of realized asset means relative to annual volatility foreshadows estimation risk.</p>
      </section>

      <section id="framework"><span class="section-label">03 / Portfolio framework</span><h2>Clear conventions before optimization.</h2>
        <p>All calculations use daily arithmetic simple returns, <code>Rₜ = Pₜ / Pₜ₋₁ − 1</code>, from positive distribution-adjusted prices. Portfolio return is the weighted sum of constituent simple returns. Daily log returns add through time for a single asset; they are not silently substituted into this portfolio's linear return and covariance formulas. Reported annual compounded returns are geometric wealth growth, distinct from annualized arithmetic sample means.</p>
        <div class="formula"><span class="formula-label">Portfolio model</span><div>E[Rₚ] = wᵀμ &nbsp; | &nbsp; σₚ² = wᵀΣw &nbsp; | &nbsp; σₚ = √(wᵀΣw)</div><div>Σᵢ wᵢ = 1 &nbsp; | &nbsp; wᵢ ≥ 0 &nbsp; | &nbsp; capped cases: wᵢ ≤ 0.25</div></div>
        <p><code>μ</code> is the vector of estimated annual arithmetic returns, <code>Σ</code> the annualized daily covariance matrix, and <code>w</code> invested capital weights. Covariance determines how assets move together, so portfolio volatility is not a weighted average of standalone volatilities. Daily means and covariances are multiplied by 252; volatility scales by √252. These are finite-sample estimates, not population parameters.</p>
        <div class="formula"><span class="formula-label">Objectives</span><div>Equal weight: wᵢ = 1/N</div><div>GMV: min wᵀΣ̂w</div><div>Estimated maximum Sharpe: max (wᵀμ̂ − r̂f) / √(wᵀΣ̂w)</div><div>Efficient frontier: min wᵀΣ̂w subject to wᵀμ̂ = μtarget</div></div>
        <p>The risk-free benchmark is the trailing arithmetic annualized return of BIL's adjusted prices, not an assumed constant. In the full training sample its estimate is {percent(summary['training_cash_rate'],2)}. BIL is an ETF with fees and price noise; its return is an imperfect proxy for a frictionless cash rate. Realized daily BIL returns are subtracted for reported out-of-sample Sharpe ratios.</p>
      </section>

      <section id="baseline"><span class="section-label">04 / In-sample portfolios</span><h2>Classical optimization prefers concentrated answers.</h2>
        <p>Using only the {summary['train_start']}–{summary['train_end']} window, the long-only GMV portfolio puts {percent(b_gmv['AGG'])} in AGG and has {number(b_gmv.effective_positions)} effective positions. Estimated maximum Sharpe puts {percent(b_ms['AGG'])} in AGG with {number(b_ms.effective_positions)} effective positions. The optimizer is responding to observed bond risk and return, not discovering a timeless economic law.</p>
        {table(['Training strategy','Estimated return','Predicted vol.','Estimated Sharpe','Largest weight','Effective N'], baseline_rows)}
        {fig_weights}
        <p>The table is deliberately labeled in-sample. Expected-return optimization looks attractive here, but its estimated Sharpe is conditional on noisy <code>μ̂</code>. A 25% ex-ante cap sacrifices some fitted Sharpe while materially reducing concentration. Equal weight is a real investable benchmark: it avoids parameter estimation, though it still rebalances and bears asset-class risk.</p>
        <h3>A separate chronological check</h3>
        <p>Weights fitted only through {summary['train_end']} are then held as fixed targets from {summary['fixed_holdout_start']} through {summary['fixed_holdout_end']}, restored monthly with the same 5 bp cost convention. No test return affects these target weights. This is a one-time holdout diagnostic; the later walk-forward analysis is the primary adaptive strategy test.</p>
        {table(['Fixed-weight holdout · net','CAGR','Volatility','Excess Sharpe','Max DD','Annual turnover'], fixed_rows)}
        <p>The fixed capped maximum-Sharpe portfolio does not travel well: its {percent(fixed_cap['annual_return'])} CAGR and {number(fixed_cap['sharpe_excess_bil'])} Sharpe trail equal weight's {percent(fixed_ew['annual_return'])} and {number(fixed_ew['sharpe_excess_bil'])}. Over those same calendar dates, the rolling capped strategy reaches {percent(matched_cap['annual_return'])} and {number(matched_cap['sharpe_excess_bil'])}. Updating estimates helped in this realized period, but the two implementations differ in rebalance history and the fixed holdout pays an initial deployment cost.</p>
      </section>

      <section id="frontier"><span class="section-label">05 / Efficient frontier</span><h2>The frontier is an estimate, not a promise.</h2>
        {fig_frontier}
        <p>The curve is solved at feasible target arithmetic returns under full investment and long-only bounds. The curvature varies along the frontier: a broad middle section is nearly straight in these data, while the ends bend more visibly. Long-only bounds also change which assets have positive optimal weights as the target return rises, so this need not resemble a single unconstrained arc. Points below it have higher estimated volatility for a given estimated return. The sample maximum-Sharpe point uses the trailing BIL estimate as its reference rate. An asset manager should treat frontier geometry as a diagnostic of input assumptions: modest changes to mean estimates can move its tangent portfolio substantially. <a class="text-link" href="https://www.cvxgrp.org/cvx_short_course/docs/applications/notebooks/portfolio_optimization.html">CVX Group's constrained portfolio formulation</a>.</p>
      </section>

      <section id="estimation"><span class="section-label">06 / Expected-return estimation error</span><h2>Small input changes, large allocation changes.</h2>
        <p>The optimizer sees <code>μ̂</code> and <code>Σ̂</code>, not population <code>μ</code> and <code>Σ</code>. The standard error of a historical mean shrinks slowly, particularly for volatile assets and correlated observations. To isolate mean dependence, 300 seeded experiments add independent normal shocks with standard deviation equal to half each asset's annualized training-mean standard error; the covariance estimate is held fixed.</p>
        {fig_sensitivity}
        <p>The weight ranges make the sensitivity concrete. AGG's 5th–95th interval is {percent(summary['perturb_ms_weight_p05']['AGG'],0)}–{percent(summary['perturb_ms_weight_p95']['AGG'],0)}; SPY's is {percent(summary['perturb_ms_weight_p05']['SPY'],0)}–{percent(summary['perturb_ms_weight_p95']['SPY'],0)}. Boundary switches indicate that the fitted best asset mix is much less precise than its point estimate. These are local stress tests, not confidence intervals for true optimal weights; the independent-shock assumption ignores cross-asset estimation dependence.</p>
      </section>

      <section id="bootstrap"><span class="section-label">07 / Resampling uncertainty</span><h2>There is a distribution of “optimal” portfolios.</h2>
        <p>For each of 300 iid bootstrap draws, the pipeline resamples training dates, re-estimates both means and covariance, and re-solves long-only GMV and estimated maximum Sharpe. The random seed is fixed at 42. The resulting intervals describe estimator sensitivity conditional on the historical sample and resampling scheme.</p>
        {fig_bootstrap}
        {table(['ETF','MS 5th','MS median','MS 95th'], bootstrap_rows)}
        <p>AGG's GMV 5th–95th range is {percent(summary['bootstrap_gmv_weight_p05']['AGG'],0)}–{percent(summary['bootstrap_gmv_weight_p95']['AGG'],0)}, far narrower than the maximum-Sharpe range. The latter changes as return rankings move under resampling. Even the steadier GMV result is economically concentrated in one bond fund; stability of a concentrated estimate does not remove model or regime risk. Iid resampling understates dependence and volatility clustering in financial returns.</p>
      </section>

      <section id="shrinkage"><span class="section-label">08 / Shrinkage & constraints</span><h2>Regularization has distinct jobs.</h2>
        <p>Ledoit–Wolf estimates daily covariance by shrinking the sample covariance toward a scaled-identity target, then annualizes it. Its fitted training shrinkage intensity is {percent(summary['shrinkage_intensity'],2)}. This is covariance regularization; it does not repair noisy historical expected returns. The 25% cap is a separate ex-ante decision limit. It prevents single-name dominance even when the fitted objective prefers it.</p>
        {fig_shrink}
        <p>In this universe, shrinkage barely changes the training GMV weights. Out of sample, its GMV annual volatility is {percent(gmv_lw.annual_volatility)} versus {percent(gmv.annual_volatility)} with sample covariance, while Sharpe is {number(gmv_lw.sharpe_excess_bil)} versus {number(gmv.sharpe_excess_bil)}. This is not strong evidence that shrinkage improves risk here; it modestly changes realized returns. Adding shrinkage to the capped maximum-Sharpe portfolio changes net Sharpe from {number(cap.sharpe_excess_bil)} to {number(cap_lw.sharpe_excess_bil)}, a negligible difference.</p>
      </section>

      <section id="risk"><span class="section-label">09 / Risk decomposition</span><h2>Capital weights conceal risk concentration.</h2>
        <div class="formula"><span class="formula-label">Euler volatility allocation</span><div>MRCᵢ = (Σw)ᵢ / σₚ &nbsp; | &nbsp; RCᵢ = wᵢMRCᵢ &nbsp; | &nbsp; ΣᵢRCᵢ = σₚ</div><div>HHI = Σᵢwᵢ² &nbsp; | &nbsp; N_eff = 1 / HHI</div></div>
        {fig_risk}
        <p>Equal weight has an effective count of 10 by construction. The training GMV count is {number(b_gmv.effective_positions)}, while the capped maximum-Sharpe count is {number(b_cap.effective_positions)}. The code verifies that risk contributions add back to modeled portfolio volatility. A position cap controls capital concentration, yet correlated equity sleeves can still dominate risk. A risk manager needs both views.</p>
      </section>

      <section id="walk-forward"><span class="section-label">10 / Walk-forward design</span><h2>Every decision precedes its test return.</h2>
        <p>The primary test begins {summary['oos_start']} and ends {summary['oos_end']} ({summary['oos_rows']:,} daily returns). On the first available session of each month, each strategy estimates 756 trailing daily observations ending before the rebalance date, chooses weights, and holds them until the next month. Six strategies isolate equal weighting, sample versus shrunk GMV, and sample versus shrunk maximum-Sharpe with and without a 25% position cap. No future return enters a training window.</p>
        <p>The 2010–2018 chronological split above is an in-sample diagnostic; the rolling backtest is the main out-of-sample evaluation. Its early years overlap the fixed training period in calendar time, but every walk-forward prediction is still formed only from prior daily data. Portfolio weights drift with constituent returns between trades.</p>
        {fig_rolling}
      </section>

      <section id="oos"><span class="section-label">11 / Realized results</span><h2>Optimization's out-of-sample gain is conditional.</h2>
        {table(['Strategy · net','CAGR','Volatility','Excess Sharpe','Max DD','Annual turnover','Mean effective N'], oos_rows)}
        <p>In this sample, capped sample maximum Sharpe leads equal weight by {number(100*(cap.annual_return-ew.annual_return),2)} percentage points of annual compounded return and {number(cap.sharpe_excess_bil-ew.sharpe_excess_bil,2)} in excess-return Sharpe, with lower realized volatility. Uncapped maximum Sharpe gives little additional return while increasing turnover and concentration. GMV lowers volatility sharply to {percent(gmv.annual_volatility)}, but its {percent(gmv.annual_return)} CAGR and {number(gmv.sharpe_excess_bil)} Sharpe trail equal weight. An investor targeting lower absolute risk might still prefer it; the objective is different.</p>
        {fig_wealth}
        <p>Equal weighting is a serious comparison rather than a straw man. The capped optimizer's observed advantage depends on the selected ETF universe, 2013–2026 regimes, BIL proxy, and 5 bp cost model. It is not evidence of alpha or a reliable future Sharpe.</p>
      </section>

      <section id="drawdowns"><span class="section-label">12 / Drawdown & risk forecasts</span><h2>Predicted risk is not realized risk.</h2>
        {fig_drawdown}
        <p>The walk-forward sample GMV strategy's mean predicted annual volatility is {percent(gmv.mean_predicted_volatility)} and its realized volatility is {percent(gmv.annual_volatility)}. For uncapped maximum Sharpe the same comparison is {percent(ms.mean_predicted_volatility)} predicted versus {percent(ms.annual_volatility)} realized. Averaging monthly risk forecasts is not itself a calibrated forecast test, but these gaps warn against treating fitted volatility as a guarantee. Drawdowns also show losses that a single variance estimate hides.</p>
      </section>

      <section id="costs"><span class="section-label">13 / Turnover & transaction costs</span><h2>A fitted edge must pay for trading.</h2>
        <div class="formula"><span class="formula-label">Cost convention</span><div>Turnoverₜ = Σᵢ |wᵢ,new − wᵢ,pretrade|</div><div>Costₜ = 0.0005 × Turnoverₜ</div><div>1 + Rnet,ₜ = (1 − Costₜ)(1 + Rgross,ₜ)</div></div>
        <p>This is absolute traded notional, with no factor of one-half; a 100% switch from one asset to another counts 200% turnover. Pretrade weights include prior-day drift. The first deployment from cash is charged. At an illustrative 5 basis points per unit turnover, annual CAGR drag is {number(ms.return_cost_drag_pp,3)} percentage points for uncapped maximum Sharpe, {number(cap.return_cost_drag_pp,3)} for capped maximum Sharpe, and {number(ew.return_cost_drag_pp,3)} for equal weight.</p>
        {fig_turnover}
        <p>The measured cost drag is small relative to return uncertainty at this low assumed rate, but the turnover gap is material. Real execution depends on spreads, volume, market impact, taxes and rebalancing mechanics. These are neither broker quotes nor a claim of implementable net performance.</p>
      </section>

      <section id="robustness"><span class="section-label">14 / Focused robustness checks</span><h2>Some rankings depend on the window.</h2>
        <p>To test estimation-horizon dependence, the analysis reruns equal weight, shrunk GMV, and capped sample maximum Sharpe with two, three, and five years of trailing data. A quarterly three-year variant probes trading frequency. All rows below are evaluated over a common later period starting {summary['robustness_common_start']}; the same 5 bp cost convention applies. This limited grid was chosen for interpretability, not tuned to maximize backtest Sharpe.</p>
        {table(['Design','Strategy','CAGR','Excess Sharpe','Annual turnover'], robust_rows)}
        <p>The capped maximum-Sharpe Sharpe ranges across monthly estimation windows from {number(robustness.loc[(robustness.strategy=='Max Sharpe · sample capped') & (robustness.design!='3y / quarterly'),'sharpe_excess_bil'].min())} to {number(robustness.loc[(robustness.strategy=='Max Sharpe · sample capped') & (robustness.design!='3y / quarterly'),'sharpe_excess_bil'].max())}. Its annual turnover ranges from {number(robustness.loc[(robustness.strategy=='Max Sharpe · sample capped') & (robustness.design!='3y / quarterly'),'annual_turnover'].min())} to {number(robustness.loc[(robustness.strategy=='Max Sharpe · sample capped') & (robustness.design!='3y / quarterly'),'annual_turnover'].max())}. This makes the gain sensitive to design; it is not a stable population effect inferred from a parameter sweep.</p>
      </section>

      <section id="reliability"><span class="section-label">15 / Reliability & limits</span><h2>Three different uncertainties.</h2>
        <div class="three-col"><div class="panel"><span class="micro">Estimation error</span><h3>Finite historical samples</h3><p>Means are noisy, covariance shifts, and bootstrap intervals depend on iid resampling. Sample Sharpe ratios have substantial uncertainty. The study does not claim statistical significance for small differences.</p></div><div class="panel"><span class="micro">Model error</span><h3>Changing regimes</h3><p>Mean–variance objectives compress downside asymmetry into two moments. ETF returns are not iid Gaussian; correlations can rise or reverse during stress. Product selection and surviving ETF histories also bias the historical universe. DBC's underlying index methodology changed in 2025, weakening a constant-exposure interpretation.</p></div><div class="panel"><span class="micro">Implementation error</span><h3>Data and trading</h3><p>Yahoo adjusted closes can be revised or contain errors; distributions are provider-adjusted. BIL is not a frictionless bill rate. Flat turnover costs omit spreads, impact, taxes and exchange-specific execution.</p></div></div>
        <p>The pipeline rejects duplicate dates, missing aligned returns, nonpositive adjusted prices, extreme one-day adjusted returns, asymmetric or non-PSD sample covariance, failed optimizations, infeasible bounds and any training window ending on or after its test date. These checks reduce coding risk but cannot validate future market relationships.</p>
      </section>

      <section id="reproduce"><span class="section-label">16 / Reproducibility & conclusion</span><h2>What survives the audit?</h2>
        <p>Classical optimization gives a sharply concentrated in-sample answer: the sample GMV and maximum-Sharpe portfolios lean heavily on AGG. Bootstrap and mean perturbations show that maximum-Sharpe weights are much less dependable than a single output vector suggests. A 25% cap reduces concentration and turnover, and improved the observed rolling out-of-sample Sharpe here. Covariance shrinkage made only modest changes in this ten-ETF study. Equal weight stayed competitive and decisively beat every fixed optimized portfolio in the {summary['fixed_holdout_start']}–{summary['fixed_holdout_end']} chronological holdout.</p>
        <p>The practical finding is conditional: monthly re-estimation plus a position cap helped on this realized path, whereas a single historical estimate did not travel well. The rolling advantage over equal weight is too small and design-sensitive to treat as a universal prescription. The next research step would test independent data sources and richer costs before exploring return-estimate shrinkage, Black–Litterman or robust optimization.</p>
        <h3>Reproduce locally</h3><pre>cd research/portfolio-optimization
python -m venv .venv
python -m pip install -r requirements.txt
python -m pytest tests -q
python -m analysis.run_analysis</pre>
        <p class="source-note">The analysis writes cached provider data, a cleaned return panel, auditable CSV/JSON results and SVG figures. The standalone HTML is generated from those executed results and can open without Python or a chart runtime. To redownload provider data, add <code>--refresh</code>; provider revisions can change the numerical results.</p>
      </section>
    </div>
  </div>
</main>
<footer class="wrap"><span>© 2026 Álvaro Cutillas</span><span>Quantitative Finance Portfolio</span></footer>
<script id="chart-interactions">{chart_client}</script>
</body>
</html>
"""
    destination.write_text(html, encoding="utf-8")
    landing_path = site / "index.html"
    landing = landing_path.read_text(encoding="utf-8")
    card_start = landing.index('<a class="project-card" href="projects/portfolio-optimization.html">')
    card_end = landing.index("</a>", card_start) + len("</a>")
    card = landing[card_start:card_end]
    metrics_markup = (
        '<!-- portfolio-optimization-results -->'
        f'<div class="metrics"><div class="metric"><b>{number(cap.sharpe_excess_bil)}</b><span>net OOS Sharpe</span></div>'
        f'<div class="metric"><b>{number(cap.mean_effective_positions)}</b><span>effective positions</span></div></div>'
        '<!-- /portfolio-optimization-results -->'
    )
    status_pattern = r'(<div class="project-status">Work in progress</div>|<!-- portfolio-optimization-results -->.*?<!-- /portfolio-optimization-results -->)'
    updated_card, count = re.subn(status_pattern, lambda _: metrics_markup, card, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Could not find portfolio card status to replace with executed results")
    landing_path.write_text(landing[:card_start] + updated_card + landing[card_end:], encoding="utf-8")
    # Portfolio EN/ES localization.
    import sys
    sys.path.insert(0, str(site / "research" / "localization"))
    from localize import localize_page
    localize_page(destination)
    localize_page(landing_path)
    return destination
