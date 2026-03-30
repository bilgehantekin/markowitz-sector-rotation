"""
Test Risk Aversion Parameter Impact
====================================
Compare strategy performance with different Risk Aversion values
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

print("\n" + "="*100)
print("RISK AVERSION SENSITIVITY ANALYSIS")
print("="*100)

# Load data once
print("\nLoading data ...")
prices = load_prices()
macro = get_macro_panel(prices.index)

print("Computing composite scores ...")
scores = compute_composite_scores(prices, macro)

# Test Risk Aversion values
risk_aversion_values = [1.0, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0]

print(f"\nTesting Risk Aversion values: {risk_aversion_values}")
print(f"Fixed parameters:")
print(f"  Tech Weight:      0.40")
print(f"  Macro Weight:     0.60")
print(f"  Tilt Strength:    0.0")
print(f"  Max Weight:       0.20")

print(f"\n{'─'*100}")
print("RESULTS")
print(f"{'─'*100}\n")

results = []

for ra in risk_aversion_values:
    try:
        # Run backtest with specific risk aversion
        res = run_backtest(
            prices, scores,
            risk_aversion=ra,
            tilt_strength=0.0,
            max_weight=0.20,
            lookback=252,
            start_date="2017-06-01"
        )
        
        # Calculate metrics for strategy
        strategy_metrics = performance_metrics(res["strategy_returns"], "s")
        benchmark_metrics = performance_metrics(res["benchmark_returns"], "b")
        
        sharpe = strategy_metrics["Sharpe Ratio"]
        bench_sharpe = benchmark_metrics["Sharpe Ratio"]
        excess_sharpe = sharpe - bench_sharpe
        
        ann_return = strategy_metrics["Ann. Return (%)"]
        ann_vol = strategy_metrics["Ann. Volatility (%)"]
        total_return = strategy_metrics["Total Return (%)"]
        max_dd = strategy_metrics["Max Drawdown (%)"]
        calmar = strategy_metrics["Calmar Ratio"]
        
        results.append({
            "Risk Aversion": ra,
            "Sharpe": sharpe,
            "Excess Sharpe": excess_sharpe,
            "Ann. Return (%)": ann_return,
            "Ann. Vol (%)": ann_vol,
            "Total Return (%)": total_return,
            "Max Drawdown (%)": max_dd,
            "Calmar": calmar,
        })
        
        # Print progress
        status = "✓" if sharpe >= 2.05 else " "
        print(f"{status} RA={ra:4.1f}  │  Sharpe={sharpe:.4f}  │  Return={ann_return:6.2f}% │ MaxDD={max_dd:7.2f}% │ Calmar={calmar:.3f}")
        
    except Exception as e:
        print(f"✗ RA={ra:4.1f}  │  ERROR: {str(e)[:50]}")

# Create summary DataFrame
results_df = pd.DataFrame(results)

print(f"\n{'─'*100}")
print("SUMMARY TABLE")
print(f"{'─'*100}\n")
print(results_df.to_string(index=False))

# Find optimal
optimal_idx = results_df["Sharpe"].idxmax()
optimal_ra = results_df.loc[optimal_idx, "Risk Aversion"]
optimal_sharpe = results_df.loc[optimal_idx, "Sharpe"]
optimal_return = results_df.loc[optimal_idx, "Ann. Return (%)"]
optimal_dd = results_df.loc[optimal_idx, "Max Drawdown (%)"]

print(f"\n{'─'*100}")
print("OPTIMAL CONFIGURATION")
print(f"{'─'*100}")
print(f"\n🏆 BEST RISK AVERSION: {optimal_ra:.1f}")
print(f"   Sharpe Ratio:       {optimal_sharpe:.4f}")
print(f"   Annual Return:      {optimal_return:.2f}%")
print(f"   Max Drawdown:       {optimal_dd:.2f}%")
print(f"   Calmar Ratio:       {results_df.loc[optimal_idx, 'Calmar']:.3f}")

# Comparison with current (RA=3.0)
current_ra_3 = results_df[results_df["Risk Aversion"] == 3.0].iloc[0]
print(f"\n{'─'*100}")
print("COMPARISON: RA=3.0 (Current) vs RA=4.0 (Candidate)")
print(f"{'─'*100}")

ra_4_data = results_df[results_df["Risk Aversion"] == 4.0].iloc[0]

comparison = pd.DataFrame({
    "Metric": ["Sharpe Ratio", "Annual Return (%)", "Annual Volatility (%)", "Max Drawdown (%)", "Calmar Ratio", "Total Return (%)"],
    "RA=3.0": [
        current_ra_3["Sharpe"],
        current_ra_3["Ann. Return (%)"],
        current_ra_3["Ann. Vol (%)"],
        current_ra_3["Max Drawdown (%)"],
        current_ra_3["Calmar"],
        current_ra_3["Total Return (%)"],
    ],
    "RA=4.0": [
        ra_4_data["Sharpe"],
        ra_4_data["Ann. Return (%)"],
        ra_4_data["Ann. Vol (%)"],
        ra_4_data["Max Drawdown (%)"],
        ra_4_data["Calmar"],
        ra_4_data["Total Return (%)"],
    ]
})

comparison["Change"] = comparison["RA=4.0"] - comparison["RA=3.0"]
comparison["Change (%)"] = (comparison["Change"] / comparison["RA=3.0"] * 100).round(2)

print("\n")
print(comparison.to_string(index=False))

# Save results
output_path = Path("data/risk_aversion_sensitivity.csv")
results_df.to_csv(output_path, index=False)
print(f"\n✓ Results saved to: {output_path}")

print(f"\n{'='*100}\n")
