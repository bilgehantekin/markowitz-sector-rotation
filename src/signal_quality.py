"""
Signal Quality Filtering Module
===============================
Compute signal confidence scores and apply filtering for better strategy
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from signal_generation import (
    ma_trend_signal,
    momentum_signal,
    volatility_regime_signal,
    compute_macro_scores,
    TECHNICAL_WINDOWS,
)
from config import DATA_DIR, ALL_TICKERS


def compute_signal_confidence(
    prices: pd.DataFrame,
    macro: pd.DataFrame,
    tickers: list = None,
) -> pd.DataFrame:
    """
    Compute confidence/quality score for signals.
    
    Confidence based on technical component agreement:
    - If trend, momentum, volatility all agree → high confidence
    - If they conflict → low confidence
    
    Returns confidence scores in [0, 1]
    """
    tickers = tickers or ALL_TICKERS
    
    # Compute individual technical signals
    trend = ma_trend_signal(prices)
    mom = momentum_signal(prices)
    vol = volatility_regime_signal(prices)
    
    # Technical consensus: how much the three signals agree
    # Confidence = |average| of the three signals
    # High agreement = values close together = high average absolute value
    consensus = pd.DataFrame(index=prices.index, columns=tickers, dtype=float)
    
    for ticker in tickers:
        # Average of absolute values (agreement measure)
        # If all three are +1 or all are -1 → consensus is 1.0
        # If they conflict → consensus is lower
        avg_absolute = (trend[ticker].abs() + mom[ticker].abs() + vol[ticker].abs()) / 3
        consensus[ticker] = avg_absolute
    
    # Normalize to [0, 1]
    confidence = consensus.clip(0, 1)
    
    return confidence


def apply_confidence_filter(
    scores: pd.DataFrame,
    confidence: pd.DataFrame,
    threshold: float = 0.5,
    method: str = "weight",
) -> pd.DataFrame:
    """
    Apply confidence filtering to signals.
    
    Parameters
    ----------
    scores : DataFrame of raw signals [-1, 1]
    confidence : DataFrame of confidence scores [0, 1]
    threshold : confidence level (0-1)
    method : 'weight' (multiply by confidence) or 'threshold' (only high-conf)
    
    Returns
    -------
    Filtered signals
    """
    if method == "weight":
        # Multiply signals by confidence (weak signals get dampened)
        filtered = scores * confidence
        return filtered.clip(-1, 1)
    
    elif method == "threshold":
        # Only use signals above threshold, else neutral
        filtered = scores.copy()
        filtered[confidence < threshold] = 0.0
        return filtered
    
    else:
        raise ValueError(f"Unknown method: {method}")


def compute_quality_report(confidence: pd.DataFrame) -> dict:
    """Generate report on signal quality."""
    return {
        "mean_confidence": confidence.values.mean(),
        "median_confidence": np.median(confidence.values),
        "high_conf_pct": (confidence.values > 0.6).mean() * 100,
        "low_conf_pct": (confidence.values < 0.4).mean() * 100,
        "very_high_conf_pct": (confidence.values > 0.8).mean() * 100,
    }


if __name__ == "__main__":
    from asset_fetch import load_prices
    from macro_fetch import get_macro_panel
    from signal_generation import compute_composite_scores
    
    print("\n" + "="*80)
    print("SIGNAL QUALITY ANALYSIS")
    print("="*80)
    
    print("\nLoading data ...")
    prices = load_prices()
    macro = get_macro_panel(prices.index)
    original_scores = compute_composite_scores(prices, macro)
    
    print("Computing signal confidence ...")
    confidence = compute_signal_confidence(prices, macro)
    
    # Save confidence scores
    confidence.to_csv(DATA_DIR / "signal_confidence.csv")
    print(f"✓ Confidence scores saved")
    
    # Statistics
    report = compute_quality_report(confidence)
    print(f"\n📊 SIGNAL QUALITY STATISTICS:")
    print(f"   Mean Confidence: {report['mean_confidence']:.1%}")
    print(f"   Median Confidence: {report['median_confidence']:.1%}")
    print(f"   High Confidence (>60%): {report['high_conf_pct']:.1f}%")
    print(f"   Very High Confidence (>80%): {report['very_high_conf_pct']:.1f}%")
    print(f"   Low Confidence (<40%): {report['low_conf_pct']:.1f}%")
    
    # Show impact of filtering
    filtered_weight = apply_confidence_filter(original_scores, confidence, method="weight")
    filtered_threshold = apply_confidence_filter(original_scores, confidence, threshold=0.6, method="threshold")
    
    print(f"\n📌 FILTERING IMPACT:")
    print(f"   Original signal range: {original_scores.values.min():.3f} to {original_scores.values.max():.3f}")
    print(f"   Weighted (multiply by conf): {filtered_weight.values.min():.3f} to {filtered_weight.values.max():.3f}")
    print(f"   Threshold (conf > 0.6): {filtered_threshold.values.min():.3f} to {filtered_threshold.values.max():.3f}")
    print(f"   Threshold signals at zero: {(filtered_threshold == 0).sum().sum() / filtered_threshold.size * 100:.1f}%")
    
    print("\n" + "="*80 + "\n")
