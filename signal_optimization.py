"""
Signal Optimization Analysis (B + D)
====================================
B: Macro vs Technical Weight Optimization
D: Comprehensive Technical Weights Sweep
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd
import numpy as np
from asset_fetch import load_prices
from macro_fetch import get_macro_panel
from signal_generation import (
    compute_technical_scores, 
    compute_macro_scores,
    TICKER_SECTOR
)
from backtest import run_backtest, performance_metrics
from config import (
    ALL_TICKERS,
    DEFAULT_LOOKBACK, 
    DEFAULT_RISK_AVERSION, 
    DEFAULT_TILT_STRENGTH,
    DEFAULT_MAX_WEIGHT, 
    DATA_DIR
)

print("\n" + "="*80)
print("SIGNAL OPTIMIZATION: MACRO WEIGHT × TECHNICAL WEIGHTS")
print("="*80)

# Load data
print("\nLoading data ...")
prices = load_prices()
macro = get_macro_panel(prices.index)

# Compute base signals
print("Computing base signals ...")
tech_scores = compute_technical_scores(prices)
macro_scores = compute_macro_scores(macro, ALL_TICKERS)

# Align indices
common_idx = prices.index.intersection(tech_scores.index).intersection(macro_scores.index)
prices = prices.loc[common_idx]
tech_scores = tech_scores.loc[common_idx]
macro_scores = macro_scores.loc[common_idx]

print(f"Common period: {prices.index[0].date()} to {prices.index[-1].date()}")

# ═══════════════════════════════════════════════════════════════════════════
# PART B: MACRO vs TECHNICAL WEIGHTS
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("PART B: MACRO vs TECHNICAL WEIGHT OPTIMIZATION")
print("─"*80)

macro_tech_weights = [
    (0.8, 0.2),  # Heavy technical
    (0.7, 0.3),  # Current: 60% tech, 40% macro → swap
    (0.6, 0.4),  # Current  
    (0.5, 0.5),  # Balanced
    (0.4, 0.6),  # Heavy macro
    (0.3, 0.7),  # Very heavy macro
]

results_b = []
print(f"\nTesting {len(macro_tech_weights)} macro-technical weight combinations:\n")

for tech_w, macro_w in macro_tech_weights:
    try:
        # Compute composite scores with custom weights
        composite = tech_w * tech_scores + macro_w * macro_scores
        composite = composite.clip(-1, 1)
        
        res = run_backtest(
            prices, composite,
            risk_aversion=DEFAULT_RISK_AVERSION,
            tilt_strength=DEFAULT_TILT_STRENGTH,
            max_weight=DEFAULT_MAX_WEIGHT,
            lookback=DEFAULT_LOOKBACK,
            start_date="2017-06-01"
        )
        
        strategy_metrics = performance_metrics(res["strategy_returns"], "s")
        benchmark_metrics = performance_metrics(res["benchmark_returns"], "b")
        
        sharpe = strategy_metrics["Sharpe Ratio"]
        bench_sharpe = benchmark_metrics["Sharpe Ratio"]
        excess_sharpe = sharpe - bench_sharpe
        
        total_return = (1 + res["strategy_returns"]).prod() - 1
        ann_return = res["strategy_returns"].mean() * 252
        ann_vol = res["strategy_returns"].std() * np.sqrt(252)
        
        results_b.append({
            "tech_weight": tech_w,
            "macro_weight": macro_w,
            "sharpe": sharpe,
            "bench_sharpe": bench_sharpe,
            "excess_sharpe": excess_sharpe,
            "ann_return": ann_return,
            "ann_vol": ann_vol,
            "total_return": total_return,
        })
        
        status = "✅" if excess_sharpe > 0 else "❌"
        marker = " ← CURRENT" if (tech_w == 0.6 and macro_w == 0.4) else ""
        print(f"  Tech {tech_w:.1%} / Macro {macro_w:.1%}: "
              f"Sharpe={sharpe:.4f} | Excess={excess_sharpe:+.4f} {status}{marker}")
    
    except Exception as e:
        print(f"  Tech {tech_w:.1%} / Macro {macro_w:.1%}: ERROR - {str(e)[:40]}")

df_b = pd.DataFrame(results_b)

# Find best in Part B
best_b_idx = df_b["sharpe"].idxmax()
best_b = df_b.loc[best_b_idx]
print(f"\n✅ Best macro-technical mix: Tech {best_b['tech_weight']:.0%} / Macro {best_b['macro_weight']:.0%}")
print(f"   Sharpe: {best_b['sharpe']:.4f}, Excess: {best_b['excess_sharpe']:+.4f}")

# ═══════════════════════════════════════════════════════════════════════════
# PART D: TECHNICAL WEIGHTS COMPREHENSIVE SWEEP
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("PART D: TECHNICAL WEIGHTS COMPREHENSIVE SWEEP")
print("─"*80)
print("(Trend % | Momentum % | Volatility %)")
print()

# Technical weight combinations: normalized to 1.0
tech_weight_combinations = [
    # Format: (trend_w, momentum_w, vol_w)
    (0.40, 0.35, 0.25),  # Current
    (0.50, 0.30, 0.20),
    (0.30, 0.45, 0.25),
    (0.33, 0.33, 0.34),  # Equal weight
    (0.60, 0.25, 0.15),  # Heavy trend
    (0.20, 0.60, 0.20),  # Heavy momentum
    (0.35, 0.35, 0.30),  # Balanced
    (0.45, 0.40, 0.15),
    (0.55, 0.30, 0.15),
    (0.40, 0.40, 0.20),
]

results_d = []
print(f"Testing {len(tech_weight_combinations)} technical weight combinations:\n")

for i, (trend_w, mom_w, vol_w) in enumerate(tech_weight_combinations):
    try:
        # Custom technical score calculation
        # Replicate signal_generation logic with custom weights
        from signal_generation import ma_trend_signal, momentum_signal, volatility_regime_signal
        
        trend_sig = ma_trend_signal(prices)
        mom_sig = momentum_signal(prices)
        vol_sig = volatility_regime_signal(prices)
        
        custom_tech = trend_w * trend_sig + mom_w * mom_sig + vol_w * vol_sig
        custom_tech = custom_tech.clip(-1, 1)
        
        # Combine with best macro weight from Part B
        best_macro_w = best_b['macro_weight']
        best_tech_w = best_b['tech_weight']
        composite = best_tech_w * custom_tech + best_macro_w * macro_scores
        composite = composite.clip(-1, 1)
        
        res = run_backtest(
            prices, composite,
            risk_aversion=DEFAULT_RISK_AVERSION,
            tilt_strength=DEFAULT_TILT_STRENGTH,
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
        
        results_d.append({
            "trend_weight": trend_w,
            "momentum_weight": mom_w,
            "volatility_weight": vol_w,
            "sharpe": sharpe,
            "bench_sharpe": bench_sharpe,
            "excess_sharpe": excess_sharpe,
            "ann_return": ann_return,
            "ann_vol": ann_vol,
        })
        
        status = "✅" if excess_sharpe > 0 else "❌"
        marker = " ← CURRENT" if (trend_w == 0.40 and mom_w == 0.35 and vol_w == 0.25) else ""
        print(f"  [{i+1:2d}/{len(tech_weight_combinations)}] "
              f"T={trend_w:.0%} M={mom_w:.0%} V={vol_w:.0%}: "
              f"Sharpe={sharpe:.4f} | Excess={excess_sharpe:+.4f} {status}{marker}")
    
    except Exception as e:
        print(f"  [{i+1:2d}/{len(tech_weight_combinations)}] ERROR: {str(e)[:40]}")

df_d = pd.DataFrame(results_d)

# Find best in Part D
best_d_idx = df_d["sharpe"].idxmax()
best_d = df_d.loc[best_d_idx]
print(f"\n✅ Best technical weights: T={best_d['trend_weight']:.0%} M={best_d['momentum_weight']:.0%} V={best_d['volatility_weight']:.0%}")
print(f"   Sharpe: {best_d['sharpe']:.4f}, Excess: {best_d['excess_sharpe']:+.4f}")

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY & RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("SUMMARY & RECOMMENDATIONS")
print("="*80)

# Save results
df_b.to_csv(DATA_DIR / "signal_optimization_part_b.csv", index=False)
df_d.to_csv(DATA_DIR / "signal_optimization_part_d.csv", index=False)
print(f"\n✓ Part B results saved: signal_optimization_part_b.csv")
print(f"✓ Part D results saved: signal_optimization_part_d.csv")

# Current configuration
current_tech_w = 0.6
current_macro_w = 0.4
current_trend_w = 0.40
current_mom_w = 0.35
current_vol_w = 0.25

current_b = df_b[(df_b['tech_weight'] == current_tech_w) & (df_b['macro_weight'] == current_macro_w)].iloc[0]
current_d = df_d[(df_d['trend_weight'] == current_trend_w) & 
                 (df_d['momentum_weight'] == current_mom_w) &
                 (df_d['volatility_weight'] == current_vol_w)].iloc[0]

print(f"\n┌─ CURRENT CONFIGURATION ─────────────────────────────────")
print(f"│ Tech/Macro: {current_tech_w:.0%} / {current_macro_w:.0%}")
print(f"│ Trend/Mom/Vol: {current_trend_w:.0%} / {current_mom_w:.0%} / {current_vol_w:.0%}")
print(f"│ Sharpe: {current_d['sharpe']:.4f}")
print(f"│ Excess Sharpe: {current_d['excess_sharpe']:+.4f}")
print(f"└─────────────────────────────────────────────────────────")

print(f"\n┌─ BEST MACRO-TECHNICAL MIX (Part B) ──────────────────────")
print(f"│ Tech/Macro: {best_b['tech_weight']:.0%} / {best_b['macro_weight']:.0%}")
print(f"│ Sharpe: {best_b['sharpe']:.4f}")
print(f"│ Excess Sharpe: {best_b['excess_sharpe']:+.4f}")
improvement_b = (best_b['sharpe'] - current_b['sharpe']) / current_b['sharpe'] * 100
print(f"│ Improvement: {improvement_b:+.2f}%")
print(f"└─────────────────────────────────────────────────────────")

print(f"\n┌─ BEST TECHNICAL WEIGHTS (Part D) ───────────────────────")
print(f"│ Trend/Mom/Vol: {best_d['trend_weight']:.0%} / {best_d['momentum_weight']:.0%} / {best_d['volatility_weight']:.0%}")
print(f"│ Sharpe: {best_d['sharpe']:.4f}")
print(f"│ Excess Sharpe: {best_d['excess_sharpe']:+.4f}")
improvement_d = (best_d['sharpe'] - current_d['sharpe']) / current_d['sharpe'] * 100
print(f"│ Improvement: {improvement_d:+.2f}%")
print(f"└─────────────────────────────────────────────────────────")

print(f"\n📊 BEST OVERALL COMBINATION:")
if best_b['sharpe'] > best_d['sharpe']:
    print(f"   Use Part B result: Tech {best_b['tech_weight']:.0%} / Macro {best_b['macro_weight']:.0%}")
    print(f"   (Keep current technical weights)")
    best_overall = best_b
else:
    print(f"   Use Part D result: Tech weights optimized")
    print(f"   Combined with best macro weight: {best_b['macro_weight']:.0%}")
    best_overall = best_d

print(f"   Sharpe: {best_overall['sharpe']:.4f}")
print(f"   Excess vs Benchmark: {best_overall['excess_sharpe']:+.4f} (+{best_overall['excess_sharpe']/current_d['excess_sharpe']*100:.1f}%)")

print("\n" + "="*80 + "\n")
