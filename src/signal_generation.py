"""
Signal Generation Module
========================
Hybrid regime signal combining technical and macro information.
"""

import numpy as np
import pandas as pd
from typing import List

from config import (
    DATA_DIR,
    DEFAULT_MACRO_WEIGHT,
    DEFAULT_TECH_WEIGHT,
    SCORES_FILENAME,
    SECTORS,
    TECHNICAL_WINDOWS,
)


TICKER_SECTOR = {
    ticker: sector
    for sector, tickers in SECTORS.items()
    for ticker in tickers
}


# ═══════════════════════════════════════════════════════════════════════════
#  1. TECHNICAL SIGNALS  (per asset, daily)
# ═══════════════════════════════════════════════════════════════════════════

def ma_trend_signal(
    prices: pd.DataFrame,
    short: int = TECHNICAL_WINDOWS["ma_short"],
    long: int = TECHNICAL_WINDOWS["ma_long"],
) -> pd.DataFrame:
    """Trend signal: +1 when the short moving average exceeds the long one."""
    ma_short = prices.rolling(short, min_periods=short).mean()
    ma_long = prices.rolling(long, min_periods=long).mean()

    signal = pd.DataFrame(index=prices.index, columns=prices.columns, dtype=float)
    signal[ma_short > ma_long] = 1.0
    signal[ma_short <= ma_long] = -1.0
    return signal


def momentum_signal(
    prices: pd.DataFrame,
    lookback: int = TECHNICAL_WINDOWS["momentum"],
) -> pd.DataFrame:
    """Momentum signal: normalized 3-month return mapped to [-1, +1].

    Uses a cross-sectional z-score so that at each date the scores
    reflect relative strength across assets.
    """
    ret = prices.pct_change(periods=lookback)
    mu = ret.mean(axis=1)
    sigma = ret.std(axis=1)
    z = ret.sub(mu, axis=0).div(sigma.replace(0, np.nan), axis=0)
    return z.clip(-3, 3) / 3.0


def volatility_regime_signal(
    prices: pd.DataFrame,
    window: int = TECHNICAL_WINDOWS["volatility"],
    baseline_window: int = TECHNICAL_WINDOWS["volatility_baseline"],
) -> pd.DataFrame:
    """Volatility regime: penalise assets in high-vol regime.

    Compares each asset's recent volatility to its own 1-year rolling
    median.  High vol → negative signal, low vol → positive signal.
    """
    daily_ret = prices.pct_change(fill_method=None)
    vol = daily_ret.rolling(window, min_periods=window).std() * np.sqrt(252)
    vol_median = vol.rolling(baseline_window, min_periods=baseline_window).median()

    signal = pd.DataFrame(index=prices.index, columns=prices.columns, dtype=float)
    signal[vol < vol_median] = 0.5
    signal[vol >= vol_median] = -0.5
    return signal


def compute_technical_scores(prices: pd.DataFrame) -> pd.DataFrame:
    """Combine technical signals into a single score in [-1, +1]."""
    trend = ma_trend_signal(prices)
    mom = momentum_signal(prices)
    vol = volatility_regime_signal(prices)

    composite = 0.40 * trend + 0.35 * mom + 0.25 * vol
    return composite.clip(-1, 1)


# ═══════════════════════════════════════════════════════════════════════════
#  2. MACRO REGIME SIGNALS  (per sector, daily)
# ═══════════════════════════════════════════════════════════════════════════

def _rate_regime(wacf: pd.Series) -> pd.Series:
    """Classify interest-rate regime.

    Returns +1 (rate cutting / low), 0 (neutral), -1 (rate hiking / high).
    Based on 6-month change in WACF rate.
    """
    chg_6m = wacf - wacf.shift(126)  # ~6 months of trading days
    regime = pd.Series(0.0, index=wacf.index)
    regime[chg_6m < -2] = 1.0    # cutting → positive
    regime[chg_6m > 2] = -1.0    # hiking  → negative
    return regime


def _inflation_regime(cpi_yoy: pd.Series) -> pd.Series:
    """Classify inflation regime.

    Returns +1 (disinflation), 0 (stable), -1 (accelerating).
    Based on 3-month change in YoY CPI.
    """
    chg_3m = cpi_yoy - cpi_yoy.shift(63)
    regime = pd.Series(0.0, index=cpi_yoy.index)
    regime[chg_3m < -2] = 1.0    # disinflation → positive
    regime[chg_3m > 2] = -1.0    # accelerating  → negative
    return regime


def _fx_regime(usdtry_chg_1m: pd.Series) -> pd.Series:
    """Classify FX regime.

    Returns +1 (TL strengthening), 0 (stable), -1 (TL weakening sharply).
    """
    regime = pd.Series(0.0, index=usdtry_chg_1m.index)
    regime[usdtry_chg_1m < -1] = 1.0    # TL gaining → positive
    regime[usdtry_chg_1m > 5] = -1.0    # TL losing sharply → negative
    return regime


# Sector sensitivity matrix: how each macro regime affects each sector.
# Values are multipliers for the regime signal.
SECTOR_MACRO_SENSITIVITY = {
    #                        rate_regime  infl_regime  fx_regime
    "Mining/Industrial":  (   0.2,          0.3,        0.5  ),
    "Export-Oriented":    (   0.1,          0.2,       -0.7  ),  # weak TL helps exporters
    "Interest-Sensitive": (   0.7,          0.2,        0.1  ),
    "Defensive/Retail":   (   0.1,          0.6,        0.3  ),
}


def compute_macro_scores(macro: pd.DataFrame, tickers: List[str]) -> pd.DataFrame:
    """Compute macro regime score for each ticker based on its sector.

    Parameters
    ----------
    macro : DataFrame with columns USDTRY, CPI_YOY, WACF_RATE, USDTRY_CHG_1M
    tickers : list of ticker names matching the price columns

    Returns
    -------
    DataFrame of macro scores in [-1, +1], same shape as prices.
    """
    rate_reg = _rate_regime(macro["WACF_RATE"])
    infl_reg = _inflation_regime(macro["CPI_YOY"])
    fx_reg = _fx_regime(macro["USDTRY_CHG_1M"])

    scores = pd.DataFrame(index=macro.index, columns=tickers, dtype=float)

    for ticker in tickers:
        sector = TICKER_SECTOR.get(ticker, None)
        if sector is None:
            scores[ticker] = 0.0
            continue

        w_rate, w_infl, w_fx = SECTOR_MACRO_SENSITIVITY[sector]
        raw = w_rate * rate_reg + w_infl * infl_reg + w_fx * fx_reg
        scores[ticker] = raw.clip(-1, 1)

    return scores


# ═══════════════════════════════════════════════════════════════════════════
#  3. COMPOSITE SCORE
# ═══════════════════════════════════════════════════════════════════════════

def compute_composite_scores(
    prices: pd.DataFrame,
    macro: pd.DataFrame,
    tech_weight: float = DEFAULT_TECH_WEIGHT,
    macro_weight: float = DEFAULT_MACRO_WEIGHT,
) -> pd.DataFrame:
    """Combine technical and macro scores into final composite signal.

    Parameters
    ----------
    prices : daily close prices (tickers as columns)
    macro  : daily macro panel (USDTRY, CPI_YOY, WACF_RATE, USDTRY_CHG_1M)
    tech_weight  : weight for technical score (default 0.4)
    macro_weight : weight for macro score    (default 0.6)

    Returns
    -------
    DataFrame of composite scores in [-1, +1].
    """
    common_idx = prices.index.intersection(macro.index)
    prices_a = prices.loc[common_idx]
    macro_a = macro.loc[common_idx]

    tech = compute_technical_scores(prices_a)
    mac = compute_macro_scores(macro_a, prices_a.columns.tolist())

    composite = tech_weight * tech + macro_weight * mac
    composite = composite.clip(-1, 1)

    valid_rows = tech.notna().all(axis=1) & mac.notna().all(axis=1)
    return composite.loc[valid_rows]


# ── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from asset_fetch import load_prices
    from macro_fetch import get_macro_panel

    prices = load_prices()
    macro = get_macro_panel(prices.index)

    scores = compute_composite_scores(prices, macro)

    path = DATA_DIR / SCORES_FILENAME
    scores.to_csv(path)
    print(f"Saved composite scores -> {path}")
    print(f"Shape: {scores.shape}")
    print(f"Date range: {scores.index[0].date()} -> {scores.index[-1].date()}")
    print()
    print("── Latest scores ──")
    print(scores.tail(1).T.to_string())
    print()
    print("── Score distribution ──")
    print(scores.describe().round(3).to_string())
