"""
BIST Asset Price Fetcher
========================
Fetches and cleans daily adjusted-close data for the project universe.
"""

from pathlib import Path

import pandas as pd
import yfinance as yf

from config import (
    ALL_TICKERS,
    DATA_DIR,
    DEFAULT_PRICE_END,
    DEFAULT_PRICE_START,
    PRICE_FILENAME,
    SECTORS,
)


def detect_synthetic_non_trading_days(prices: pd.DataFrame) -> pd.DatetimeIndex:
    """Detect rows where every asset price is unchanged from the prior row."""
    repeated = prices.eq(prices.shift(1)).all(axis=1)
    return prices.index[repeated.fillna(False)]


def clean_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Apply conservative cleaning without backfilling future prices."""
    cleaned = prices.copy()
    cleaned.index = pd.to_datetime(cleaned.index)
    cleaned = cleaned.sort_index()
    cleaned = cleaned.astype(float)

    missing = cleaned.isna().sum()
    if missing.any():
        print("Missing data per ticker before cleaning:")
        print(missing[missing > 0])

    cleaned = cleaned.ffill()
    cleaned = cleaned.dropna(how="any")

    synthetic_days = detect_synthetic_non_trading_days(cleaned)
    if len(synthetic_days) > 0:
        cleaned = cleaned.drop(index=synthetic_days)
        print(f"Removed {len(synthetic_days)} synthetic non-trading rows.")

    return cleaned


def fetch_prices(
    tickers: list[str] = ALL_TICKERS,
    start: str = DEFAULT_PRICE_START,
    end: str = DEFAULT_PRICE_END,
) -> pd.DataFrame:
    """Download daily adjusted-close prices from Yahoo Finance."""
    print(f"Fetching {len(tickers)} tickers from {start} to {end} ...")
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    if raw.empty:
        raise ValueError("Yahoo Finance returned an empty price panel.")

    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]]
        prices.columns = tickers

    return clean_prices(prices)


def save_prices(prices: pd.DataFrame, filename: str = PRICE_FILENAME) -> Path:
    """Save a cleaned price DataFrame to CSV."""
    path = DATA_DIR / filename
    prices.to_csv(path)
    print(f"Saved {prices.shape[0]} rows x {prices.shape[1]} cols -> {path}")
    return path


def load_prices(filename: str = PRICE_FILENAME, clean: bool = True) -> pd.DataFrame:
    """Load price data from CSV and optionally re-apply cleaning rules."""
    path = DATA_DIR / filename
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return clean_prices(df) if clean else df


def summary(prices: pd.DataFrame) -> pd.DataFrame:
    """Quick summary statistics for the price data."""
    returns = prices.pct_change(fill_method=None).dropna()
    stats = pd.DataFrame(
        {
            "Start": prices.apply(lambda s: s.first_valid_index()),
            "End": prices.apply(lambda s: s.last_valid_index()),
            "Days": prices.count(),
            "Last Price": prices.iloc[-1],
            "Ann. Return (%)": (returns.mean() * 252 * 100).round(2),
            "Ann. Vol (%)": (returns.std() * (252**0.5) * 100).round(2),
        }
    )
    return stats


if __name__ == "__main__":
    try:
        prices = fetch_prices()
        save_prices(prices)
    except Exception as exc:
        cache_path = DATA_DIR / PRICE_FILENAME
        if not cache_path.exists():
            raise
        print(f"Price refresh failed ({exc}). Falling back to cached data at {cache_path}.")
        prices = load_prices()

    print("\n── Universe ──")
    for sector, tickers in SECTORS.items():
        print(f"{sector}: {', '.join(tickers)}")

    print("\n── Summary ──")
    print(summary(prices).to_string())
