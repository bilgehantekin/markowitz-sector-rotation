"""
Fine-tuned Sensitivity Analysis for Tilt Strength
================================================
Test TS values from 0.0 to 0.5 in 0.05 increments
Focus on finding optimal balance between strategy and stability
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd
import numpy as np
from asset_fetch import load_prices
from macro_fetch import get_macro_panel
from signal_generation import compute_composite_scores
from backtest import run_backtest, performance_metrics
from config import DEFAULT_LOOKBACK, DEFAULT_RISK_AVERSION, DEFAULT_MAX_WEIGHT, DATA_DIR

print("\n" + "="*80)
print("FINE-TUNED TILT STRENGTH SENSITIVITY ANALYSIS")
print("="*80)

# Load data
print("\nLoading data ...")
prices = load_prices()
macro = get_macro_panel(prices.index)
scores = compute_composite_scores(prices, macro)

# Test different TS values with finer granularity
ts_values = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]

print(f"\nTesting {len(ts_values)} different Tilt Strength values:")
print(f"Risk Aversion: {DEFAULT_RISK_AVERSION}")
print(f"Max Weight: {DEFAULT_MAX_WEIGHT}")
print(f"Lookback: {DEFAULT_LOOKBACK}")
print()

results = []
for i, ts in enumerate(ts_values):
    try:
        res = run_backtest(
            prices, scores,
            risk_aversion=DEFAULT_RISK_AVERSION,
            tilt_strength=ts,
            max_weight=DEFAULT_MAX_WEIGHT,
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
        
        results.append({
            "tilt_strength": ts,
            "sharpe": sharpe,
            "bench_sharpe": bench_sharpe,
            "excess_sharpe": excess_sharpe,
            "ann_return": ann_return,
            "ann_vol": ann_vol,
            "total_return": total_return,
        })
        
        status = "✅" if excess_sharpe > 0 else "❌"
        print(f"  [{i+1:2d}/{len(ts_values)}] TS={ts:.2f}: "
              f"Sharpe={sharpe:.4f} | Excess={excess_sharpe:+.4f} | "
              f"AnnRet={ann_return:.2%} | AnnVol={ann_vol:.2%} {status}")
    
    except Exception as e:
        print(f"  [{i+1:2d}/{len(ts_values)}] TS={ts:.2f}: ERROR - {str(e)[:50]}")

# Create summary dataframe
df_results = pd.DataFrame(results)

# Save to CSV
output_path = DATA_DIR / "tilt_strength_finetuned.csv"
df_results.to_csv(output_path, index=False)
print(f"\n✓ Results saved to {output_path}")

# Print summary table
print("\n" + "─"*80)
print("SUMMARY TABLE")
print("─"*80)
print("\n" + df_results[["tilt_strength", "sharpe", "excess_sharpe", "ann_return", "ann_vol"]].to_string(index=False))

# Find best
best_idx = df_results["sharpe"].idxmax()
best = df_results.loc[best_idx]

print("\n" + "─"*80)
print("FINDINGS")
print("─"*80)
print(f"\n✅ BEST TILT STRENGTH: {best['tilt_strength']:.2f}")
print(f"   Sharpe Ratio: {best['sharpe']:.4f}")
print(f"   Excess Sharpe: {best['excess_sharpe']:+.4f}")
print(f"   Annual Return: {best['ann_return']:.2%}")
print(f"   Annual Volatility: {best['ann_vol']:.2%}")

# Show improvement vs current (TS=0.5)
current_ts = df_results[df_results["tilt_strength"] == 0.5].iloc[0]
improvement = (best["sharpe"] - current_ts["sharpe"]) / current_ts["sharpe"] * 100

print(f"\nComparison to Current (TS={current_ts['tilt_strength']:.2f}):")
print(f"   Current Sharpe: {current_ts['sharpe']:.4f}")
print(f"   Best Sharpe: {best['sharpe']:.4f}")
print(f"   Improvement: {improvement:+.2f}%")

# Show the sweet spot (balance between strategy and stability)
print(f"\n💡 STRATEGIC INSIGHT:")
print(f"   TS=0.0 (no strategy): Sharpe={df_results[df_results['tilt_strength']==0.0].iloc[0]['sharpe']:.4f}")
print(f"   TS=0.5 (current):     Sharpe={current_ts['sharpe']:.4f}")
print(f"   Best found:           Sharpe={best['sharpe']:.4f} at TS={best['tilt_strength']:.2f}")
print()

# Group into ranges
print("General Trend:")
for ts_range in [(0.0, 0.1), (0.15, 0.25), (0.3, 0.4), (0.45, 0.5)]:
    subset = df_results[(df_results["tilt_strength"] >= ts_range[0]) & 
                        (df_results["tilt_strength"] <= ts_range[1])]
    avg_sharpe = subset["sharpe"].mean()
    print(f"   TS {ts_range[0]:.2f}-{ts_range[1]:.2f}: Avg Sharpe = {avg_sharpe:.4f}")

print("\n" + "="*80 + "\n")
