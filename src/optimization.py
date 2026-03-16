"""
Portfolio Optimization Module
=============================
Markowitz mean-variance optimizer with signal-tilted inputs.
"""

from pathlib import Path

import cvxpy as cp
import numpy as np
import pandas as pd

from config import (
    DEFAULT_LOOKBACK,
    DEFAULT_MAX_WEIGHT,
    DEFAULT_MIN_WEIGHT,
    DEFAULT_RISK_AVERSION,
    DEFAULT_SHRINK_FACTOR,
    DEFAULT_TILT_STRENGTH,
)


# ═══════════════════════════════════════════════════════════════════════════
#  Expected returns & covariance estimation
# ═══════════════════════════════════════════════════════════════════════════

def estimate_mu(
    returns: pd.DataFrame,
    scores: pd.Series,
    lookback: int = DEFAULT_LOOKBACK,
    tilt_strength: float = DEFAULT_TILT_STRENGTH,
) -> np.ndarray:
    """Estimate expected returns with a signal tilt on the rolling mean."""
    recent = returns.iloc[-lookback:]
    mu_base = recent.mean().values * 252

    s = scores.values if hasattr(scores, "values") else np.array(scores)
    return mu_base * (1.0 + tilt_strength * s)


def estimate_sigma(
    returns: pd.DataFrame,
    scores: pd.Series,
    lookback: int = DEFAULT_LOOKBACK,
    shrink_factor: float = DEFAULT_SHRINK_FACTOR,
) -> np.ndarray:
    """Estimate covariance with diagonal shrinkage plus signal-based scaling."""
    recent = returns.iloc[-lookback:]
    S = recent.cov().values * 252

    diag = np.diag(np.diag(S))
    S_shrunk = (1 - shrink_factor) * S + shrink_factor * diag

    s = scores.values if hasattr(scores, "values") else np.array(scores)
    scale = 1.0 - 0.3 * s
    scale = np.clip(scale, 0.5, 1.5)

    D = np.diag(scale)
    S_adj = D @ S_shrunk @ D
    S_adj += np.eye(S_adj.shape[0]) * 1e-8
    return S_adj


# ═══════════════════════════════════════════════════════════════════════════
#  Markowitz solver
# ═══════════════════════════════════════════════════════════════════════════

def markowitz_optimize(
    mu: np.ndarray,
    sigma: np.ndarray,
    risk_aversion: float = DEFAULT_RISK_AVERSION,
    min_weight: float = DEFAULT_MIN_WEIGHT,
    max_weight: float = DEFAULT_MAX_WEIGHT,
) -> np.ndarray:
    """Solve a long-only, fully invested Markowitz allocation."""
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
        return np.ones(n) / n

    weights = np.array(w.value).flatten()
    weights = np.maximum(weights, 0)
    weights /= weights.sum()
    return weights


def equal_weight(n: int) -> np.ndarray:
    """1/N equal-weight benchmark."""
    return np.ones(n) / n


def validate_weight_vector(
    weights: pd.Series | np.ndarray,
    max_weight: float = DEFAULT_MAX_WEIGHT,
    atol: float = 1e-6,
) -> dict[str, bool | float]:
    """Check budget, long-only, and cap constraints for a weight vector."""
    array = weights.to_numpy() if isinstance(weights, pd.Series) else np.asarray(weights)
    return {
        "sum_to_one": bool(np.isclose(array.sum(), 1.0, atol=atol)),
        "non_negative": bool((array >= -atol).all()),
        "within_cap": bool((array <= max_weight + atol).all()),
        "weight_sum": float(array.sum()),
        "min_weight": float(array.min()),
        "max_weight": float(array.max()),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Convenience: compute weights for a given date
# ═══════════════════════════════════════════════════════════════════════════

def compute_weights(
    prices: pd.DataFrame,
    scores: pd.DataFrame,
    date: pd.Timestamp,
    lookback: int = DEFAULT_LOOKBACK,
    risk_aversion: float = DEFAULT_RISK_AVERSION,
    tilt_strength: float = DEFAULT_TILT_STRENGTH,
    max_weight: float = DEFAULT_MAX_WEIGHT,
) -> pd.Series:
    """Compute optimal weights for a rebalance date."""
    prices_up_to = prices.loc[:date]
    returns = prices_up_to.pct_change(fill_method=None).dropna()

    if returns.empty:
        raise ValueError(f"No return history available on or before {date}.")

    if len(returns) < lookback:
        lookback = len(returns)

    score_history = scores.loc[:date]
    if score_history.empty:
        raise ValueError(f"No composite score available on or before {date}.")
    score_row = score_history.iloc[-1].reindex(prices.columns)

    mu = estimate_mu(returns, score_row, lookback=lookback, tilt_strength=tilt_strength)
    sigma = estimate_sigma(returns, score_row, lookback=lookback)

    w = markowitz_optimize(mu, sigma, risk_aversion=risk_aversion, max_weight=max_weight)

    return pd.Series(w, index=prices.columns, name=date)


# ── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parent))

    from asset_fetch import load_prices
    from macro_fetch import get_macro_panel
    from signal_generation import compute_composite_scores

    prices = load_prices()
    macro = get_macro_panel(prices.index)
    scores = compute_composite_scores(prices, macro)

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
