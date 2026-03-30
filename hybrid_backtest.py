"""
Hybrid Strategy Backtest
========================
Confidence-weighted signals + optimal TS combination
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd
import numpy as np
from asset_fetch import load_prices
from macro_fetch import get_macro_panel
from signal_generation import compute_composite_scores
from signal_quality import compute_signal_confidence, apply_confidence_filter
from backtest import run_backtest, performance_metrics
from config import (
    DEFAULT_LOOKBACK, 
    DEFAULT_RISK_AVERSION, 
    DEFAULT_MAX_WEIGHT, 
    DATA_DIR
)

print("\n" + "="*80)
print("HYBRID STRATEGY: CONFIDENCE-WEIGHTED SIGNALS")
print("="*80)

# Load data
print("\nLoading data ...")
prices = load_prices()
macro = get_macro_panel(prices.index)
original_scores = compute_composite_scores(prices, macro)

print("Computing signal confidence ...")
confidence = compute_signal_confidence(prices, macro)

# Align indices
common_idx = prices.index.intersection(original_scores.index).intersection(confidence.index)
prices = prices.loc[common_idx]
original_scores = original_scores.loc[common_idx]
confidence = confidence.loc[common_idx]

print(f"Common period: {prices.index[0].date()} to {prices.index[-1].date()}")

# ═══════════════════════════════════════════════════════════════════════════
# TEST DIFFERENT HYBRID CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("TESTING HYBRID CONFIGURATIONS")
print("─"*80)

configs = [
    ("baseline", original_scores, 0.50, "Original (TS=0.5)"),
    ("baseline_low_ts", original_scores, 0.15, "Original with TS=0.15"),
    ("weighted_conf", apply_confidence_filter(original_scores, confidence, method="weight"), 0.20, "Confidence-weighted (TS=0.2)"),
    ("weighted_conf_low", apply_confidence_filter(original_scores, confidence, method="weight"), 0.15, "Confidence-weighted (TS=0.15)"),
    ("threshold_05", apply_confidence_filter(original_scores, confidence, threshold=0.5, method="threshold"), 0.25, "High-confidence only (thresh=0.5, TS=0.25)"),
    ("threshold_06", apply_confidence_filter(original_scores, confidence, threshold=0.6, method="threshold"), 0.25, "Very high-conf only (thresh=0.6, TS=0.25)"),
]

results = []
print(f"\nTesting {len(configs)} configurations:\n")

for name, scores, ts_value, label in configs:
    try:
        res = run_backtest(
            prices, scores,
            risk_aversion=DEFAULT_RISK_AVERSION,
            tilt_strength=ts_value,
            max_weight=DEFAULT_MAX_WEIGHT,
            lookback=DEFAULT_LOOKBACK,
            start_date="2017-06-01"
        )
        
        strategy_metrics = performance_metrics(res["strategy_returns"], "s")
        benchmark_metrics = performance_metrics(res["benchmark_returns"], "b")
        
        sharpe = strategy_metrics["Sharpe Ratio"]
        bench_sharpe = benchmark_metrics["Sharpe Ratio"]
        excess_sharpe = sharpe - bench_sharpe
        
        ann_return = res["strategy_returns"].mean() * 252
        ann_vol = res["strategy_returns"].std() * np.sqrt(252)
        
        results.append({
            "config": name,
            "label": label,
            "ts": ts_value,
            "sharpe": sharpe,
            "excess_sharpe": excess_sharpe,
            "ann_return": ann_return,
            "ann_vol": ann_vol,
        })
        
        status = "✅" if excess_sharpe > 0 else "❌"
        print(f"  {label:45s} → Sharpe={sharpe:.4f} | Excess={excess_sharpe:+.4f} {status}")
    
    except Exception as e:
        print(f"  {label:45s} → ERROR: {str(e)[:40]}")

df_results = pd.DataFrame(results)
df_results.to_csv(DATA_DIR / "hybrid_strategy_results.csv", index=False)

# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("SUMMARY & RECOMMENDATION")
print("─"*80)

best_idx = df_results["sharpe"].idxmax()
best = df_results.loc[best_idx]

current_baseline = df_results[df_results['config'] == 'baseline'].iloc[0]
baseline_low_ts = df_results[df_results['config'] == 'baseline_low_ts'].iloc[0]

print(f"\n📊 COMPARISON:")
print(f"\n  Current Strategy (TS=0.50):")
print(f"    Sharpe: {current_baseline['sharpe']:.4f}")
print(f"    Excess: {current_baseline['excess_sharpe']:+.4f}")
print(f"    Ann.Vol: {current_baseline['ann_vol']:.2%}")

print(f"\n  Baseline with TS=0.15 (Minimal tilt):")
print(f"    Sharpe: {baseline_low_ts['sharpe']:.4f} ({(baseline_low_ts['sharpe']/current_baseline['sharpe']-1)*100:+.2f}%)")
print(f"    Excess: {baseline_low_ts['excess_sharpe']:+.4f}")
print(f"    Ann.Vol: {baseline_low_ts['ann_vol']:.2%}")

print(f"\n  BEST FOUND - {best['label']}:")
print(f"    Sharpe: {best['sharpe']:.4f} ({(best['sharpe']/current_baseline['sharpe']-1)*100:+.2f}%)")
print(f"    Excess: {best['excess_sharpe']:+.4f}")
print(f"    Ann.Vol: {best['ann_vol']:.2%}")
print(f"    TS Value: {best['ts']:.2f}")

print(f"\n✅ RECOMMENDATION:")
print(f"   Use: {best['label']}")
print(f"   Configuration: TS={best['ts']:.2f}")
if 'weighted' in best['config']:
    print(f"   Filter: Apply confidence weighting to signals")
elif 'threshold' in best['config']:
    print(f"   Filter: Use only high-confidence signals")
else:
    print(f"   Filter: No filtering")

improvement = (best['sharpe'] - current_baseline['sharpe']) / current_baseline['sharpe'] * 100
print(f"   Improvement: {improvement:+.2f}% Sharpe ratio")

print("\n" + "="*80 + "\n")

# Show all ranked
print("📋 ALL CONFIGURATIONS RANKED BY SHARPE:\n")
df_sorted = df_results.sort_values("sharpe", ascending=False)
for idx, row in df_sorted.iterrows():
    print(f"  {idx+1}. {row['label']:45s} → {row['sharpe']:.4f} ({row['excess_sharpe']:+.4f})")

print("\n")
