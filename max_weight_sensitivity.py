"""
Max Weight Sensitivity Analysis
================================
Test different max weight constraints and find the optimal value
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
from config import DEFAULT_LOOKBACK, DEFAULT_RISK_AVERSION, DEFAULT_TILT_STRENGTH, DATA_DIR

print("\n" + "="*80)
print("MAX WEIGHT SENSITIVITY ANALYSIS")
print("="*80)

# Load data
print("\nLoading data ...")
prices = load_prices()
macro = get_macro_panel(prices.index)
original_scores = compute_composite_scores(prices, macro)
confidence = compute_signal_confidence(prices, macro)
filtered_scores = apply_confidence_filter(original_scores, confidence, method="weight")

common_idx = prices.index.intersection(filtered_scores.index)
prices = prices.loc[common_idx]
scores = filtered_scores.loc[common_idx]

# Test different max weight values
max_weights = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.75, 1.0]

print(f"\nTesting {len(max_weights)} different Max Weight values:")
print(f"Tilt Strength: {DEFAULT_TILT_STRENGTH}")
print(f"Risk Aversion: {DEFAULT_RISK_AVERSION}")
print(f"Lookback: {DEFAULT_LOOKBACK}")
print()

results = []
for i, mw in enumerate(max_weights):
    try:
        res = run_backtest(
            prices, scores,
            risk_aversion=DEFAULT_RISK_AVERSION,
            tilt_strength=0.15,  # Use best tilt strength
            max_weight=mw,
            lookback=DEFAULT_LOOKBACK,
            start_date="2017-06-01"
        )
        
        strategy_metrics = performance_metrics(res["strategy_returns"], "s")
        benchmark_metrics = performance_metrics(res["benchmark_returns"], "b")
        
        sharpe = strategy_metrics["Sharpe Ratio"]
        bench_sharpe = benchmark_metrics["Sharpe Ratio"]
        excess_sharpe = sharpe - bench_sharpe
        
        # Additional metrics
        total_return = (1 + res["strategy_returns"]).prod() - 1
        ann_vol = res["strategy_returns"].std() * np.sqrt(252)
        ann_return = res["strategy_returns"].mean() * 252
        max_dd = strategy_metrics["Max Drawdown (%)"]
        
        results.append({
            "max_weight": mw,
            "sharpe": sharpe,
            "bench_sharpe": bench_sharpe,
            "excess_sharpe": excess_sharpe,
            "ann_return": ann_return,
            "ann_vol": ann_vol,
            "total_return": total_return,
            "max_drawdown": max_dd,
        })
        
        status = "✅" if sharpe > bench_sharpe else "❌"
        print(f"  [{i+1:2d}/{len(max_weights)}] MW={mw:.2f}: "
              f"Sharpe={sharpe:.4f} | Excess={excess_sharpe:+.4f} | "
              f"AnnRet={ann_return:.2%} | AnnVol={ann_vol:.2%} {status}")
    
    except Exception as e:
        print(f"  [{i+1:2d}/{len(max_weights)}] MW={mw:.2f}: ERROR - {str(e)[:50]}")

# Create summary dataframe
df_results = pd.DataFrame(results)

# Save to CSV
output_path = DATA_DIR / "max_weight_sensitivity.csv"
df_results.to_csv(output_path, index=False)
print(f"\n✓ Results saved to {output_path}")

# Print summary table
print("\n" + "─"*80)
print("SUMMARY TABLE (Sorted by Sharpe Ratio)")
print("─"*80)
df_sorted = df_results.sort_values("sharpe", ascending=False)
print("\n" + df_sorted[["max_weight", "sharpe", "excess_sharpe", "ann_return", "ann_vol", "max_drawdown"]].to_string(index=False))

# Find best
best_idx = df_results["sharpe"].idxmax()
best = df_results.loc[best_idx]

print("\n" + "─"*80)
print("OPTIMAL CONFIGURATION")
print("─"*80)
print(f"\n✅ BEST MAX WEIGHT: {best['max_weight']:.2f} (= {best['max_weight']*100:.0f}% per stock)")
print(f"   Sharpe Ratio: {best['sharpe']:.4f}")
print(f"   Excess Sharpe: {best['excess_sharpe']:+.4f}")
print(f"   Annual Return: {best['ann_return']:.2%}")
print(f"   Annual Volatility: {best['ann_vol']:.2%}")
print(f"   Max Drawdown: {best['max_drawdown']:.2f}%")

# Compare with current (0.25)
current_mw = df_results[df_results["max_weight"] == 0.25].iloc[0]
improvement = ((best["sharpe"] - current_mw["sharpe"]) / current_mw["sharpe"]) * 100

print(f"\nComparison to Current Max Weight (0.25 = 25%):")
print(f"   Current Sharpe: {current_mw['sharpe']:.4f}")
print(f"   Best Sharpe: {best['sharpe']:.4f}")
print(f"   Improvement: {improvement:+.2f}%")
print(f"   Annual Return Improvement: {(best['ann_return'] - current_mw['ann_return'])*100:+.2f}%")

# Show diversity trade-off
print(f"\n💡 DIVERSITY TRADE-OFF:")
print(f"   Max Weight 1.0/10 (equal-weight):  Sharpe={df_results[df_results['max_weight']==1.0].iloc[0]['sharpe']:.4f}")
print(f"   Max Weight 0.50 (2 stocks max):    Sharpe={df_results[df_results['max_weight']==0.50].iloc[0]['sharpe']:.4f}")
print(f"   Max Weight 0.25 (4 stocks max):    Sharpe={current_mw['sharpe']:.4f}")
print(f"   Max Weight 0.20 (5 stocks max):    Sharpe={df_results[df_results['max_weight']==0.20].iloc[0]['sharpe']:.4f}")
print(f"   Max Weight 0.10 (10 stocks max):   Sharpe={df_results[df_results['max_weight']==0.10].iloc[0]['sharpe']:.4f}")

print("\n" + "="*80 + "\n")
