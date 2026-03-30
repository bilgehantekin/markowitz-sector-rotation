"""
Comprehensive Parameter Optimization
====================================
Test all combinations of key parameters to find optimal strategy configuration.

Parameters tested:
- Tech Weight vs Macro Weight
- Risk Aversion
- Tilt Strength
- Max Weight
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd
import numpy as np
import itertools
from asset_fetch import load_prices
from macro_fetch import get_macro_panel
from signal_generation import compute_composite_scores
from backtest import run_backtest, performance_metrics
from config import DEFAULT_LOOKBACK, DATA_DIR

print("\n" + "="*100)
print("COMPREHENSIVE PARAMETER OPTIMIZATION")
print("="*100)

# Load data once
print("\nLoading data ...")
prices = load_prices()
macro = get_macro_panel(prices.index)

print("Computing composite scores ...")
scores = compute_composite_scores(prices, macro)

# Define parameter grids
parameter_grids = {
    "tech_weight": [0.40, 0.50, 0.60, 0.70],  # Macro weight = 1 - tech_weight
    "risk_aversion": [1.0, 2.0, 3.0, 5.0, 7.0, 10.0],
    "tilt_strength": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
    "max_weight": [0.10, 0.15, 0.20, 0.25, 0.30],
}

total_combinations = (
    len(parameter_grids["tech_weight"]) *
    len(parameter_grids["risk_aversion"]) *
    len(parameter_grids["tilt_strength"]) *
    len(parameter_grids["max_weight"])
)

print(f"\nTotal combinations to test: {total_combinations}")
print(f"\nParameter ranges:")
print(f"  Tech Weight:     {parameter_grids['tech_weight']}")
print(f"  Risk Aversion:   {parameter_grids['risk_aversion']}")
print(f"  Tilt Strength:   {parameter_grids['tilt_strength']}")
print(f"  Max Weight:      {parameter_grids['max_weight']}")

# Generate all combinations
all_combinations = list(itertools.product(
    parameter_grids["tech_weight"],
    parameter_grids["risk_aversion"],
    parameter_grids["tilt_strength"],
    parameter_grids["max_weight"]
))

print(f"\n{'─'*100}")
print("TESTING COMBINATIONS")
print(f"{'─'*100}\n")

results = []
completed = 0

for idx, (tw, ra, ts, mw) in enumerate(all_combinations, 1):
    try:
        # Compute scores with specific tech/macro weights
        mw_macro = 1.0 - tw
        scores_custom = compute_composite_scores(prices, macro, tech_weight=tw, macro_weight=mw_macro)
        
        # Run backtest
        res = run_backtest(
            prices, scores_custom,
            risk_aversion=ra,
            tilt_strength=ts,
            max_weight=mw,
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
        cal_ratio = ann_return / ann_vol if ann_vol > 0 else 0
        
        # Maximum drawdown
        cum_ret = (1 + res["strategy_returns"]).cumprod()
        running_max = cum_ret.expanding().max()
        drawdown = (cum_ret - running_max) / running_max
        max_dd = drawdown.min()
        
        results.append({
            "tech_weight": tw,
            "macro_weight": mw_macro,
            "risk_aversion": ra,
            "tilt_strength": ts,
            "max_weight": mw,
            "sharpe": sharpe,
            "excess_sharpe": excess_sharpe,
            "ann_return": ann_return,
            "ann_vol": ann_vol,
            "calmar": cal_ratio,
            "max_dd": max_dd,
        })
        
        completed += 1
        
        # Progress bar
        progress = (idx / total_combinations) * 100
        bar_length = 40
        filled = int(bar_length * idx / total_combinations)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        status = "✅" if excess_sharpe > 0 else "⚠"
        print(f"  [{bar}] {progress:5.1f}% | "
              f"TW={tw:.1f} | RA={ra:4.1f} | TS={ts:.1f} | MW={mw:.2f} | "
              f"Sharpe={sharpe:.3f} | Excess={excess_sharpe:+.3f} {status}")
    
    except Exception as e:
        completed += 1
        progress = (idx / total_combinations) * 100
        print(f"  [{idx:3d}/{total_combinations}] {progress:5.1f}% | ERROR: {str(e)[:60]}")
        continue

print(f"\n{'─'*100}")
print(f"Completed {completed}/{total_combinations} combinations successfully")
print(f"{'─'*100}\n")

# Create results dataframe
df_results = pd.DataFrame(results)

# Save full results
full_results_path = DATA_DIR / "comprehensive_optimization_full.csv"
df_results.to_csv(full_results_path, index=False)
print(f"✓ Full results saved to {full_results_path}")

# ═══════════════════════════════════════════════════════════════════════════
# ANALYSIS: Top configurations
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*100)
print("TOP 15 CONFIGURATIONS BY SHARPE RATIO")
print("="*100 + "\n")

top_sharpe = df_results.nlargest(15, "sharpe")
display_cols = ["tech_weight", "macro_weight", "risk_aversion", "tilt_strength", 
                "max_weight", "sharpe", "excess_sharpe", "ann_return", "ann_vol", "max_dd"]
print(top_sharpe[display_cols].to_string(index=False))

print("\n" + "="*100)
print("TOP 15 CONFIGURATIONS BY EXCESS SHARPE")
print("="*100 + "\n")

top_excess = df_results.nlargest(15, "excess_sharpe")
print(top_excess[display_cols].to_string(index=False))

print("\n" + "="*100)
print("TOP 15 CONFIGURATIONS BY CALMAR RATIO")
print("="*100 + "\n")

top_calmar = df_results.nlargest(15, "calmar")
print(top_calmar[display_cols].to_string(index=False))

# ═══════════════════════════════════════════════════════════════════════════
# ANALYSIS: By parameter
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*100)
print("ANALYSIS BY PARAMETER (MEAN SHARPE RATIO)")
print("="*100)

print("\nBY TECH WEIGHT:")
by_tw = df_results.groupby("tech_weight")[["sharpe", "excess_sharpe", "ann_return", "ann_vol"]].mean()
print(by_tw.round(4))

print("\nBY RISK AVERSION:")
by_ra = df_results.groupby("risk_aversion")[["sharpe", "excess_sharpe", "ann_return", "ann_vol"]].mean()
print(by_ra.round(4))

print("\nBY TILT STRENGTH:")
by_ts = df_results.groupby("tilt_strength")[["sharpe", "excess_sharpe", "ann_return", "ann_vol"]].mean()
print(by_ts.round(4))

print("\nBY MAX WEIGHT:")
by_mw = df_results.groupby("max_weight")[["sharpe", "excess_sharpe", "ann_return", "ann_vol"]].mean()
print(by_mw.round(4))

# ═══════════════════════════════════════════════════════════════════════════
# SAVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

summary_path = DATA_DIR / "optimization_summary.csv"

# Save top 10 by each metric
top_10_by_metrics = pd.DataFrame({
    "Metric": ["Sharpe", "Excess Sharpe", "Calmar Ratio"],
    "Best Config": [
        f"TW={df_results.loc[df_results['sharpe'].idxmax(), 'tech_weight']:.1f}, "
        f"RA={df_results.loc[df_results['sharpe'].idxmax(), 'risk_aversion']:.1f}, "
        f"TS={df_results.loc[df_results['sharpe'].idxmax(), 'tilt_strength']:.1f}, "
        f"MW={df_results.loc[df_results['sharpe'].idxmax(), 'max_weight']:.2f}",
        f"TW={df_results.loc[df_results['excess_sharpe'].idxmax(), 'tech_weight']:.1f}, "
        f"RA={df_results.loc[df_results['excess_sharpe'].idxmax(), 'risk_aversion']:.1f}, "
        f"TS={df_results.loc[df_results['excess_sharpe'].idxmax(), 'tilt_strength']:.1f}, "
        f"MW={df_results.loc[df_results['excess_sharpe'].idxmax(), 'max_weight']:.2f}",
        f"TW={df_results.loc[df_results['calmar'].idxmax(), 'tech_weight']:.1f}, "
        f"RA={df_results.loc[df_results['calmar'].idxmax(), 'risk_aversion']:.1f}, "
        f"TS={df_results.loc[df_results['calmar'].idxmax(), 'tilt_strength']:.1f}, "
        f"MW={df_results.loc[df_results['calmar'].idxmax(), 'max_weight']:.2f}",
    ],
    "Value": [
        f"{df_results['sharpe'].max():.4f}",
        f"{df_results['excess_sharpe'].max():.4f}",
        f"{df_results['calmar'].max():.4f}",
    ]
})

top_10_by_metrics.to_csv(summary_path, index=False)
print(f"\n✓ Summary saved to {summary_path}")

print("\n" + "="*100)
print("OPTIMIZATION COMPLETE!")
print("="*100)

best_sharpe_idx = df_results["sharpe"].idxmax()
best_config = df_results.loc[best_sharpe_idx]

print(f"\n🏆 BEST CONFIGURATION (by Sharpe Ratio):")
print(f"  Tech Weight:    {best_config['tech_weight']:.1f}")
print(f"  Macro Weight:   {best_config['macro_weight']:.1f}")
print(f"  Risk Aversion:  {best_config['risk_aversion']:.1f}")
print(f"  Tilt Strength:  {best_config['tilt_strength']:.1f}")
print(f"  Max Weight:     {best_config['max_weight']:.2f}")
print(f"\n  Sharpe Ratio:   {best_config['sharpe']:.4f}")
print(f"  Excess Sharpe:  {best_config['excess_sharpe']:.4f}")
print(f"  Annual Return:  {best_config['ann_return']:.2%}")
print(f"  Annual Vol:     {best_config['ann_vol']:.2%}")
print(f"  Max Drawdown:   {best_config['max_dd']:.2%}")
print(f"  Calmar Ratio:   {best_config['calmar']:.4f}")

best_excess_idx = df_results["excess_sharpe"].idxmax()
best_excess = df_results.loc[best_excess_idx]

print(f"\n🥈 BEST CONFIGURATION (by Excess Sharpe):")
print(f"  Tech Weight:    {best_excess['tech_weight']:.1f}")
print(f"  Macro Weight:   {best_excess['macro_weight']:.1f}")
print(f"  Risk Aversion:  {best_excess['risk_aversion']:.1f}")
print(f"  Tilt Strength:  {best_excess['tilt_strength']:.1f}")
print(f"  Max Weight:     {best_excess['max_weight']:.2f}")
print(f"\n  Sharpe Ratio:   {best_excess['sharpe']:.4f}")
print(f"  Excess Sharpe:  {best_excess['excess_sharpe']:.4f}")
print(f"  Annual Return:  {best_excess['ann_return']:.2%}")
print(f"  Annual Vol:     {best_excess['ann_vol']:.2%}")
print(f"  Max Drawdown:   {best_excess['max_dd']:.2%}")
print(f"  Calmar Ratio:   {best_excess['calmar']:.4f}")

print("\n")
