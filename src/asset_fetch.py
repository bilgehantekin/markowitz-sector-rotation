"""
BIST Asset Price Fetcher
========================
Fetches daily adjusted close prices for selected BIST equities from Yahoo Finance.

Sectors & Tickers:
  - Mining/Industrial : EREGL.IS, SISE.IS
  - Export-Oriented   : TOASO.IS, FROTO.IS, THYAO.IS
  - Interest-Sensitive: GARAN.IS, AKBNK.IS, EKGYO.IS
  - Defensive/Retail  : BIMAS.IS, MGROS.IS
"""

import yfinance as yf
import pandas as pd
from pathlib import Path

# ── Asset Universe ──────────────────────────────────────────────────────────
SECTORS = {
    "Mining/Industrial":  ["EREGL.IS", "SISE.IS"],
    "Export-Oriented":    ["TOASO.IS", "FROTO.IS", "THYAO.IS"],
    "Interest-Sensitive": ["GARAN.IS", "AKBNK.IS", "EKGYO.IS"],
    "Defensive/Retail":   ["BIMAS.IS", "MGROS.IS"],
}

ALL_TICKERS = [t for tickers in SECTORS.values() for t in tickers]

# ── Paths ───────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def fetch_prices(
    tickers: list[str] = ALL_TICKERS,
    start: str = "2016-01-01",
    end: str = "2026-02-24",
) -> pd.DataFrame:
    """Download daily adjusted close prices from Yahoo Finance."""
    print(f"Fetching {len(tickers)} tickers from {start} to {end} ...")
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)

    # yf.download returns multi-level columns when multiple tickers
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]]
        prices.columns = tickers

    prices.index = pd.to_datetime(prices.index)
    prices = prices.sort_index()

    # Report missing data
    missing = prices.isna().sum()
    if missing.any():
        print("Missing data per ticker:")
        print(missing[missing > 0])

    # Forward-fill then back-fill small gaps (holidays / halts)
    prices = prices.ffill().bfill()

    return prices


def save_prices(prices: pd.DataFrame, filename: str = "bist_prices.csv") -> Path:
    """Save price DataFrame to CSV."""
    path = DATA_DIR / filename
    prices.to_csv(path)
    print(f"Saved {prices.shape[0]} rows x {prices.shape[1]} cols -> {path}")
    return path


def load_prices(filename: str = "bist_prices.csv") -> pd.DataFrame:
    """Load previously saved price data."""
    path = DATA_DIR / filename
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df


def summary(prices: pd.DataFrame) -> pd.DataFrame:
    """Quick summary statistics for the price data."""
    returns = prices.pct_change(fill_method=None).dropna()
    stats = pd.DataFrame({
        "Start": prices.apply(lambda s: s.first_valid_index()),
        "End": prices.apply(lambda s: s.last_valid_index()),
        "Days": prices.count(),
        "Last Price": prices.iloc[-1],
        "Ann. Return (%)": (returns.mean() * 252 * 100).round(2),
        "Ann. Vol (%)": (returns.std() * (252 ** 0.5) * 100).round(2),
    })
    return stats


# ── CLI entry point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    prices = fetch_prices()
    save_prices(prices)

    print("\n── Summary ──")
    print(summary(prices).to_string())
