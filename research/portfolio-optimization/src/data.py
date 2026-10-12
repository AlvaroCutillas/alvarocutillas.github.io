"""Download and audit distribution-adjusted ETF prices."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ASSETS = {
    "SPY": "US large-cap equities",
    "IWM": "US small-cap equities",
    "EFA": "Developed-market equities",
    "EEM": "Emerging-market equities",
    "AGG": "US aggregate bonds",
    "TLT": "Long-duration US Treasuries",
    "LQD": "Investment-grade corporate bonds",
    "VNQ": "US real estate",
    "GLD": "Gold",
    "DBC": "Broad commodities",
}
CASH_PROXY = "BIL"
ISSUER_INCEPTIONS = {
    "SPY": "1993-01-22", "IWM": "2000-05-22", "EFA": "2001-08-14",
    "EEM": "2003-04-07", "AGG": "2003-09-22", "TLT": "2002-07-22",
    "LQD": "2002-07-22", "VNQ": "2004-09-23", "GLD": "2004-11-18",
    "DBC": "2006-02-03", "BIL": "2007-05-25",
}
START = "2010-01-01"
END_EXCLUSIVE = "2026-09-28"


def simple_returns(prices: pd.DataFrame) -> pd.DataFrame:
    if prices.empty or prices.isna().any().any() or (prices <= 0).any().any():
        raise ValueError("Prices must be complete and positive")
    result = prices.pct_change(fill_method=None).iloc[1:]
    if result.isna().any().any() or not np.isfinite(result.to_numpy()).all():
        raise ValueError("Invalid simple returns")
    return result


def download_prices(root: Path, refresh: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return a constant-universe adjusted-price panel and volume panel.

    Raw provider responses are cached locally and excluded from Git by .gitignore.
    No missing value is filled; only dates present for every symbol survive.
    """
    raw = root / "data" / "raw"
    processed = root / "data" / "processed"
    cache = root / ".cache"
    for path in (raw, processed, cache):
        path.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(cache))

    prices: dict[str, pd.Series] = {}
    volumes: dict[str, pd.Series] = {}
    audit = []
    for ticker in [*ASSETS, CASH_PROXY]:
        target = raw / f"{ticker}.csv"
        if target.exists() and not refresh:
            frame = pd.read_csv(target, index_col=0, parse_dates=True)
        else:
            frame = yf.download(
                ticker, start=START, end=END_EXCLUSIVE,
                auto_adjust=False, actions=False, progress=False,
                threads=False, multi_level_index=False, timeout=30,
            )
            if frame.empty:
                raise RuntimeError(f"No Yahoo Finance history for {ticker}; no synthetic substitute is allowed")
            frame.to_csv(target, float_format="%.12g")
        if not {"Adj Close", "Volume"}.issubset(frame.columns):
            raise ValueError(f"Adjusted close or volume missing for {ticker}")
        frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
        if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
            raise ValueError(f"Duplicate or unsorted dates for {ticker}")
        adj = pd.to_numeric(frame["Adj Close"], errors="coerce")
        vol = pd.to_numeric(frame["Volume"], errors="coerce")
        if (adj.dropna() <= 0).any():
            raise ValueError(f"Non-positive adjusted price for {ticker}")
        if adj.notna().sum() < 3500:
            raise ValueError(f"Insufficient common-era history for {ticker}")
        if pd.Timestamp(ISSUER_INCEPTIONS[ticker]) >= adj.first_valid_index():
            raise ValueError(f"Provider history begins before or at issuer inception for {ticker}")
        if vol.median() < 500_000:
            raise ValueError(f"Median daily share volume below liquidity screen for {ticker}")
        prices[ticker] = adj.rename(ticker)
        volumes[ticker] = vol.rename(ticker)
        audit.append({
            "ticker": ticker,
            "role": ASSETS.get(ticker, "Cash-rate proxy; outside optimized universe"),
            "first_available": str(adj.first_valid_index().date()),
            "issuer_inception": ISSUER_INCEPTIONS[ticker],
            "last_available": str(adj.last_valid_index().date()),
            "rows": int(len(frame)),
            "missing_adjusted_close": int(adj.isna().sum()),
            "median_daily_volume": int(vol.median()),
        })

    all_prices = pd.concat(prices.values(), axis=1).sort_index()
    all_volumes = pd.concat(volumes.values(), axis=1).sort_index()
    panel = all_prices.dropna(how="any")
    if len(panel) < 3500:
        raise ValueError("Insufficient aligned history")
    if not np.isfinite(panel.to_numpy()).all():
        raise ValueError("Non-finite adjusted prices")
    panel.to_csv(processed / "adjusted_prices.csv", float_format="%.12g")
    returns = simple_returns(panel)
    if (returns <= -1).any().any():
        raise ValueError("Invalid simple return <= -100%")
    returns.to_csv(processed / "daily_simple_returns.csv", float_format="%.12g")
    audit_report = {
        "provider": "Yahoo Finance via yfinance; Adj Close (split/distribution adjusted)",
        "download_end_exclusive": END_EXCLUSIVE,
        "common_start": str(panel.index.min().date()),
        "common_end": str(panel.index.max().date()),
        "price_rows": int(len(panel)),
        "return_rows": int(len(returns)),
        "excluded_calendar_rows": int(len(all_prices) - len(panel)),
        "symbols": audit,
    }
    (processed / "data_audit.json").write_text(json.dumps(audit_report, indent=2), encoding="utf-8")
    return returns, all_volumes.loc[panel.index]
