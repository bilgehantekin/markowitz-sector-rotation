"""
Portfolio Optimization Module
=============================
Markowitz Mean-Variance optimizer with signal-tilted inputs.

The composite scores from signal_generation are used to:
  1) Tilt the expected return vector (μ)
  2) Shrink/expand covariance entries for high/low conviction assets

Constraints: fully invested (Σw=1), long-only (w≥0).
"""

import numpy as np
import pandas as pd
import cvxpy as cp
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════
#  Expected returns & covariance estimation
# ═══════════════════════════════════════════════════════════════════════════

def estimate_mu(
    returns: pd.DataFrame,
    scores: pd.Series,
    lookback: int = 252,
    tilt_strength: float = 0.5,
) -> np.ndarray:
    """Estimate expected returns with signal tilt.

    Base μ = rolling mean of daily returns (annualised).
    Tilt: μ_adj = μ_base + tilt_strength * score * |μ_base|

    Parameters
    ----------
    returns   : recent daily returns (last `lookback` days)
    scores    : composite signal scores for each asset (single row)
    lookback  : rolling window for base estimate
    tilt_strength : how much the signal tilts μ (0 = ignore, 1 = double)
    """
    recent = returns.iloc[-lookback:]
    mu_base = recent.mean().values * 252  # annualise

    s = scores.values if hasattr(scores, "values") else np.array(scores)
    mu_adj = mu_base * (1.0 + tilt_strength * s)

    return mu_adj


def estimate_sigma(
    returns: pd.DataFrame,
    scores: pd.Series,
    lookback: int = 252,
    shrink_factor: float = 0.3,
) -> np.ndarray:
    """Estimate covariance matrix with Ledoit-Wolf shrinkage + signal adjustment.

    Steps:
      1) Sample covariance from recent returns
      2) Ledoit-Wolf shrinkage toward diagonal
      3) Scale rows/cols: assets with negative scores get inflated vol
    """
    recent = returns.iloc[-lookback:]
    S = recent.cov().values * 252  # annualise

    # Ledoit-Wolf shrinkage toward diagonal
    diag = np.diag(np.diag(S))
    S_shrunk = (1 - shrink_factor) * S + shrink_factor * diag

    # Signal-based vol scaling: penalise negative-score assets
    s = scores.values if hasattr(scores, "values") else np.array(scores)
    # scale = 1 - 0.3*score → high score = lower vol, low score = higher vol
    scale = 1.0 - 0.3 * s
    scale = np.clip(scale, 0.5, 1.5)

    # Apply to covariance: Σ_adj = D @ Σ @ D where D = diag(scale)
    D = np.diag(scale)
    S_adj = D @ S_shrunk @ D

    return S_adj


# ═══════════════════════════════════════════════════════════════════════════
#  Markowitz solver
# ═══════════════════════════════════════════════════════════════════════════

def markowitz_optimize(
    mu: np.ndarray,
    sigma: np.ndarray,
    risk_aversion: float = 2.0,
    min_weight: float = 0.0,
    max_weight: float = 0.40,
) -> np.ndarray:
    """Solve the Markowitz mean-variance problem.

    max  μ'w - (γ/2) w'Σw
    s.t. Σw = 1, w ≥ min_weight, w ≤ max_weight

    Parameters
    ----------
    mu    : expected return vector (n,)
    sigma : covariance matrix (n, n)
    risk_aversion : γ parameter (higher = more conservative)
    min_weight : minimum weight per asset
    max_weight : maximum weight per asset (diversification cap)

    Returns
    -------
    Optimal weight vector (n,).
    """
    n = len(mu)
    w = cp.Variable(n)

    ret = mu @ w
    risk = cp.quad_form(w, cp.psd_wrap(sigma))
    objective = cp.Maximize(ret - (risk_aversion / 2) * risk)

    constraints = [
        cp.sum(w) == 1,
        w >= min_weight,
        w <= max_weight,
    ]

    prob = cp.Problem(objective, constraints)
    prob.solve(solver=cp.CLARABEL)

    if prob.status not in ("optimal", "optimal_inaccurate"):
        # Fallback to equal weight
        return np.ones(n) / n

    weights = np.array(w.value).flatten()
    # Clean tiny negatives from numerical noise
    weights = np.maximum(weights, 0)
    weights /= weights.sum()
    return weights


def equal_weight(n: int) -> np.ndarray:
    """1/N equal-weight benchmark."""
    return np.ones(n) / n


# ═══════════════════════════════════════════════════════════════════════════
#  Convenience: compute weights for a given date
# ═══════════════════════════════════════════════════════════════════════════

def compute_weights(
    prices: pd.DataFrame,
    scores: pd.DataFrame,
    date: pd.Timestamp,
    lookback: int = 252,
    risk_aversion: float = 2.0,
    tilt_strength: float = 0.5,
    max_weight: float = 0.40,
) -> pd.Series:
    """Compute optimal weights for a rebalance date.

    Parameters
    ----------
    prices : full daily price history
    scores : full composite score history
    date   : the rebalance date
    """
    # Use data up to (and including) this date
    prices_up_to = prices.loc[:date]
    returns = prices_up_to.pct_change(fill_method=None).dropna()

    if len(returns) < lookback:
        lookback = len(returns)

    score_row = scores.loc[date] if date in scores.index else pd.Series(0.0, index=prices.columns)

    mu = estimate_mu(returns, score_row, lookback=lookback, tilt_strength=tilt_strength)
    sigma = estimate_sigma(returns, score_row, lookback=lookback)

    w = markowitz_optimize(mu, sigma, risk_aversion=risk_aversion, max_weight=max_weight)

    return pd.Series(w, index=prices.columns, name=date)


# ── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from asset_fetch import load_prices
    from macro_fetch import load_macro
    from signal_generation import compute_composite_scores

    prices = load_prices()
    macro = load_macro()
    scores = compute_composite_scores(prices, macro)

    # Test: compute weights for the last available date
    test_date = scores.index[-1]
    w_opt = compute_weights(prices, scores, test_date)
    w_eq = equal_weight(len(prices.columns))

    print(f"Weights as of {test_date.date()}:\n")
    comparison = pd.DataFrame({
        "Optimized": w_opt.round(4),
        "Equal (1/N)": w_eq.round(4),
        "Score": scores.loc[test_date].round(3),
    })
    print(comparison.to_string())
    print(f"\nSum of optimized weights: {w_opt.sum():.4f}")
