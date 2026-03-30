"""
Quick Optimization: Tech vs Macro Weight Analysis
================================================
Focused analysis on the most important parameter combination
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
from config import DEFAULT_LOOKBACK

print("\n" + "="*80)
print("QUICK OPTIMIZATION: TECH vs MACRO WEIGHT ANALYSIS")
print("="*80)

# Load data once
print("\nLoading data ...")
prices = load_prices()
macro = get_macro_panel(prices.index)

# Fixed optimal parameters from previous analysis
OPTIMAL_RA = 5.0
OPTIMAL_TS = 0.0
OPTIMAL_MW = 0.20

# Test different tech/macro weight combinations
tech_weights = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]

print(f"\nTesting {len(tech_weights)} Tech/Macro Weight combinations")
print(f"With optimal parameters: RA={OPTIMAL_RA}, TS={OPTIMAL_TS}, MW={OPTIMAL_MW}")
print()

results = []

for i, tw in enumerate(tech_weights, 1):
    try:
        mw_macro = 1.0 - tw
        
        # Compute scores with specific tech/macro weights
        scores = compute_composite_scores(prices, macro, tech_weight=tw, macro_weight=mw_macro)
        
        # Run backtest
        res = run_backtest(
            prices, scores,
            risk_aversion=OPTIMAL_RA,
            tilt_strength=OPTIMAL_TS,
            max_weight=OPTIMAL_MW,
            lookback=DEFAULT_LOOKBACK,
            start_date="2017-06-01"
        )
        
        # Calculate metrics
        strategy_metrics = performance_metrics(res["strategy_returns"], "s")
        benchmark_metrics = performance_metrics(res["benchmark_returns"], "b")
        
        sharpe = strategy_metrics["Sharpe Ratio"]
        bench_sharpe = benchmark_metrics["Sharpe Ratio"]
        excess_sharpe = sharpe - bench_sharpe
        
        ann_return = res["strategy_returns"].mean() * 252
        ann_vol = res["strategy_returns"].std() * np.sqrt(252)
        
        # Maximum drawdown
        cum_ret = (1 + res["strategy_returns"]).cumprod()
        running_max = cum_ret.expanding().max()
        drawdown = (cum_ret - running_max) / running_max
        max_dd = drawdown.min()
        
        results.append({
            "tech_weight": tw,
            "macro_weight": mw_macro,
            "sharpe": sharpe,
            "excess_sharpe": excess_sharpe,
            "ann_return": ann_return,
            "ann_vol": ann_vol,
            "max_dd": max_dd,
        })
        
        status = "✓" if excess_sharpe > 0.230 else ("✓" if excess_sharpe > 0.225 else "")
        print(f"  [{i}] Tech={tw:.1f} | Macro={mw_macro:.1f} | "
              f"Sharpe={sharpe:.4f} | Excess={excess_sharpe:.4f} | "
              f"AnnRet={ann_return:.2%} | AnnVol={ann_vol:.2%} {status}")
    
    except Exception as e:
        print(f"  [{i}] Tech={tw:.1f} | ERROR: {str(e)[:60]}")

# Create results dataframe
df_results = pd.DataFrame(results)

print("\n" + "="*80)
print("RESULTS SUMMARY")
print("="*80 + "\n")

print(df_results.to_string(index=False))

# Find best
best_idx = df_results["sharpe"].idxmax()
best = df_results.loc[best_idx]

print("\n" + "="*80)
print("OPTIMAL TECH/MACRO WEIGHT MIX")
print("="*80)
print(f"\nBest Configuration (by Sharpe Ratio):")
print(f"  Tech Weight:     {best['tech_weight']:.1f}")
print(f"  Macro Weight:    {best['macro_weight']:.1f}")
print(f"  Sharpe:          {best['sharpe']:.4f}")
print(f"  Excess Sharpe:   {best['excess_sharpe']:.4f}")
print(f"  Annual Return:   {best['ann_return']:.2%}")
print(f"  Annual Vol:      {best['ann_vol']:.2%}")
print(f"  Max Drawdown:    {best['max_dd']:.2%}")

# Comparison
current_config = df_results[(df_results['tech_weight'] == 0.60) & (df_results['macro_weight'] == 0.40)]
if not current_config.empty:
    curr = current_config.iloc[0]
    improvement = ((best['sharpe'] - curr['sharpe']) / curr['sharpe']) * 100
    print(f"\n  vs Current Config (0.60/0.40):")
    print(f"    Improvement: {improvement:+.2f}%")

print("\n")
