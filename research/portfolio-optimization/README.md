# Portfolio Optimization Under Estimation Error

An empirical research note on whether estimated mean–variance portfolios remain defensible after input uncertainty, concentration, out-of-sample evaluation, turnover and simple trading costs. The primary publication is [`../../projects/portfolio-optimization.html`](../../projects/portfolio-optimization.html). It is regenerated from executed data and contains inline SVG figures, CSS and interpretation.

## Universe and source

The constant risky-asset universe is SPY (US large cap), IWM (US small cap), EFA (developed international), EEM (emerging markets), AGG (US aggregate bonds), TLT (long Treasuries), LQD (investment-grade credit), VNQ (US real estate), GLD (gold) and DBC (broad commodities). BIL is a separate cash-rate proxy and is not an optimized holding. This set covers materially different asset classes while retaining a common history and substantial median daily share volume. ETF selection is itself subject to survivorship and product-choice bias.

Issuer-reported launch dates all precede the 2010 sample start: SPY 1993-01-22; IWM 2000-05-22; EFA 2001-08-14; EEM 2003-04-07; AGG 2003-09-22; TLT and LQD 2002-07-22; VNQ 2004-09-23; GLD 2004-11-18; DBC 2006-02-03; BIL 2007-05-25. Sources: [State Street SPY](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy), [iShares ETF list](https://www.ishares.com/us/products/etf-investments), [Vanguard VNQ fact sheet](https://workplace.vanguard.com/assets/corp/fund_communications/pdf_publish/us-products/fact-sheet/F0986.pdf), [State Street GLD](https://www.ssga.com/us/en/individual/etfs/spdr-gold-shares-gld), [Invesco DBC](https://www.invesco.com/us/en/financial-products/etfs/invesco-db-commodity-index-tracking-fund.html), and [State Street BIL](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil). The DBC issuer reports a 2025 underlying-index methodology change, a limitation for constant-exposure interpretation.

Data are Yahoo Finance **Adj Close** and volume downloaded with `yfinance` (`auto_adjust=False` explicitly). Yahoo describes Adj Close as adjusted for applicable splits and distributions: <https://help.yahoo.com/kb/SLN28256.html>. The downloader interface is documented at <https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html>. Prices in this run cover 2010-01-04 through 2026-09-25; simple returns cover 2010-01-05 through 2026-09-25 (4,207 aligned sessions). The fixed diagnostic training sample ends 2018-12-31; the monthly walk-forward evaluation begins 2013-01-07 after 756 prior sessions. These dates are recorded again in `results/summary.json` and `data/processed/data_audit.json`.

Raw provider responses are cached under `data/raw/`; aligned adjusted prices and cleaned returns are written under `data/processed/`. Those folders are ignored by Git to avoid unnecessarily redistributing provider data. The results CSV/JSON and SVG figures contain derived research outputs. Check the data provider's terms before any public redistribution. Rerunning with `--refresh` may change results if Yahoo revises history.

The downloader requires positive adjusted prices, at least 3,500 observations per symbol, chronological unique dates, and a complete common panel. It never forward-fills returns or sets missing returns to zero. The executed sample has no missing adjusted closes and excludes no provider calendar rows. Median volume, missing counts and first/last dates are recorded per symbol. A daily adjusted simple return above 35% in absolute value triggers review rather than being silently accepted.
Median daily share volume must be at least 500,000 in the selected sample; no symbol fails this screen. No candidate was excluded for inception date, missing adjusted prices or this volume criterion. The universe was fixed before optimization, so the analysis does not select assets based on realized portfolio performance.

## Method

- Daily **simple arithmetic** returns: `P_t / P_(t-1) - 1`. Optimization uses `252 × daily mean` and `252 × daily sample covariance`. Reported annual return is compounded wealth growth, which is distinct from the arithmetic mean. Volatility uses `sqrt(252) × daily standard deviation`.
- The estimated excess-return objective uses the **trailing** annualized arithmetic BIL adjusted-price return. Out-of-sample Sharpe uses contemporaneous daily BIL returns. BIL is a fee-bearing ETF proxy, not a frictionless risk-free rate.
- Equal weighting, long-only sample GMV, long-only sample estimated maximum Sharpe, Ledoit–Wolf GMV, 25%-capped sample maximum Sharpe, and 25%-capped Ledoit–Wolf maximum Sharpe are evaluated. Ledoit–Wolf's implementation shrinks daily sample covariance toward a scaled-identity target; the fitted intensity is recorded.
- The efficient frontier solves constrained variance minimization at 301 target returns, from the global minimum-variance portfolio to just below the highest asset mean. The line connects solved points without fitted smoothing. All optimization success flags, budget residuals, bounds and target-return residuals are checked. Sample covariance symmetry and positive semidefiniteness are checked. A two-asset analytical GMV case is tested.
- A fixed 2010–2018 training sample produces one set of weights that is separately evaluated over 2019–2026 with monthly target restoration and the same cost model. This is a chronological diagnostic; it does not adapt to later information.
- Rolling-strategy metrics are also recalculated on the fixed holdout's 2019–2026 calendar window to distinguish the effect of updating estimates from differences in evaluation period.
- A fixed-seed, 300-repetition iid bootstrap re-estimates means/covariance and both GMV and maximum-Sharpe weights. A separate 300-repetition experiment perturbs annual expected returns at half their estimated standard errors, holding covariance fixed. The iid assumption is a limitation, not a claim about market dynamics.
- On the first available session of each month, the walk-forward test estimates only the previous 756 daily observations, trades before the current return, holds through the month, and repeats. Turnover is `sum(abs(new - drifted pretrade weights))`, **without** a 0.5 factor. Initial deployment from cash is charged. A hypothetical 5 bp rate per unit turnover is applied multiplicatively to gross daily wealth on trade dates.
- Focused robustness runs compare two-, three- and five-year training windows plus quarterly rebalancing for three representative strategies over a common later period.

## Reproduce

From this directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest tests -q
python -m analysis.run_analysis
python -m analysis.audit
node --test tests/test_chart_interactions.cjs
```

Use `python -m analysis.run_analysis --refresh` to redownload data. The default run reuses the local raw cache, enabling exact regeneration of the current page from the existing provider observations. `pytest.ini` uses plain assertions because assertion rewriting stalls during collection in the current Windows Anaconda environment; the tests still execute all assertions.

## Files

- `src/data.py`: download, price/return validation and audit.
- `src/portfolio.py`: estimators, optimizer, risk identities, resampling and walk-forward engine.
- `analysis/run_analysis.py`: full execution and result provenance.
- `analysis/visualization.py`: thirteen research SVG figures.
- `analysis/interactive.py`: executed data and SVG coordinate metadata for twelve interactive charts; the correlation matrix remains static.
- `analysis/chart_interactions.js` and `.css`: local hover, tap and keyboard interaction, embedded directly in the generated HTML. No external library or network request is needed. Time-series tooltips show dates and net portfolio value per $1 initially invested; aggregate charts show the applicable sample period. The risk–return scatter uses circular markers, labels and an expanded vertical axis; coincident points expose both results together.
- `analysis/page.py`: standalone page generation and landing-card metrics from the same results.
- `results/`: JSON/CSV tables, daily paths, allocations, trades and no-look-ahead audit.
- `tests/`: numerical identities, optimizer feasibility, deterministic bootstrap and chronology.

## Limits

Historical expected returns are noisy; covariance and correlations change; daily ETF returns are not iid Gaussian. A ten-product survivor universe is not a representative investment opportunity set. The study has one historical path, one data provider, an ETF cash proxy and a simplified fixed transaction-cost rate. The backtest is evidence about this sample, not a forecast or an investment recommendation. Statistical significance of small Sharpe differences is not established. Independent data, better execution estimates and alternative estimation models are sensible next checks.
