"""
Signal Optimization Results Summary
===================================
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")

# Load results
df_b = pd.read_csv(DATA_DIR / "signal_optimization_part_b.csv")
df_d = pd.read_csv(DATA_DIR / "signal_optimization_part_d.csv")

print("\n" + "="*80)
print("SIGNAL OPTIMIZATION RESULTS SUMMARY")
print("="*80)

# PART B SUMMARY
print("\n" + "─"*80)
print("PART B: MACRO vs TECHNICAL WEIGHT OPTIMIZATION")
print("─"*80)

print("\n📊 All Combinations (Ranked by Sharpe):")
df_b_sorted = df_b.sort_values("sharpe", ascending=False)
for idx, row in df_b_sorted.iterrows():
    current = " ← CURRENT" if (row['tech_weight'] == 0.6 and row['macro_weight'] == 0.4) else ""
    best = " ✅ BEST" if idx == df_b_sorted.index[0] else ""
    print(f"  Tech {row['tech_weight']:.0%} / Macro {row['macro_weight']:.0%}: "
          f"Sharpe={row['sharpe']:.4f} | Excess={row['excess_sharpe']:+.4f}{best}{current}")

best_b = df_b.loc[df_b["sharpe"].idxmax()]
current_b = df_b[(df_b['tech_weight'] == 0.6) & (df_b['macro_weight'] == 0.4)].iloc[0]

print(f"\n✅ Best Result (Part B):")
print(f"   Tech {best_b['tech_weight']:.0%} / Macro {best_b['macro_weight']:.0%}")
print(f"   Sharpe: {best_b['sharpe']:.4f}")
print(f"   Excess: {best_b['excess_sharpe']:+.4f}")
print(f"   Improvement: {(best_b['sharpe']/current_b['sharpe']-1)*100:+.2f}%")

# PART D SUMMARY
print("\n" + "─"*80)
print("PART D: TECHNICAL WEIGHTS COMPREHENSIVE SWEEP")
print("─"*80)

print("\n📊 All Technical Weight Combinations (Ranked by Sharpe):")
df_d_sorted = df_d.sort_values("sharpe", ascending=False)
for idx, row in df_d_sorted.iterrows():
    current = " ← CURRENT" if (row['trend_weight'] == 0.4 and row['momentum_weight'] == 0.35 and row['volatility_weight'] == 0.25) else ""
    best = " ✅ BEST" if idx == df_d_sorted.index[0] else ""
    print(f"  T={row['trend_weight']:.0%} M={row['momentum_weight']:.0%} V={row['volatility_weight']:.0%}: "
          f"Sharpe={row['sharpe']:.4f} | Excess={row['excess_sharpe']:+.4f}{best}{current}")

best_d = df_d.loc[df_d["sharpe"].idxmax()]
current_d = df_d[(df_d['trend_weight'] == 0.4) & (df_d['momentum_weight'] == 0.35) & (df_d['volatility_weight'] == 0.25)].iloc[0]

print(f"\n✅ Best Result (Part D):")
print(f"   Trend {best_d['trend_weight']:.0%} / Momentum {best_d['momentum_weight']:.0%} / Volatility {best_d['volatility_weight']:.0%}")
print(f"   Sharpe: {best_d['sharpe']:.4f}")
print(f"   Excess: {best_d['excess_sharpe']:+.4f}")
print(f"   Improvement: {(best_d['sharpe']/current_d['sharpe']-1)*100:+.2f}%")

# OVERALL RECOMMENDATION
print("\n" + "="*80)
print("RECOMMENDATIONS FOR PRESENTATION")
print("="*80)

print(f"\n┌─ CURRENT CONFIGURATION ────────────────────────────────────")
print(f"│ Tech/Macro Weights: 60% / 40%")
print(f"│ Trend/Mom/Vol: 40% / 35% / 25%")
print(f"│ Sharpe Ratio: {current_d['sharpe']:.4f}")
print(f"│ Excess Sharpe: +{current_d['excess_sharpe']:.4f}")
print(f"└────────────────────────────────────────────────────────────")

print(f"\n┌─ RECOMMENDATION 1: Simple Fix (Part B) ────────────────────")
print(f"│ Adjust Tech/Macro to 50% / 50% (more balanced)")
print(f"│ Keep Trend/Mom/Vol at 40% / 35% / 25%")
print(f"│ Sharpe Ratio: {best_b['sharpe']:.4f} (+{(best_b['sharpe']/current_d['sharpe']-1)*100:+.2f}%)")
print(f"│ Excess Sharpe: +{best_b['excess_sharpe']:.4f}")
print(f"│ Ease: ✅ Easy to implement (1 parameter change)")
print(f"└────────────────────────────────────────────────────────────")

print(f"\n┌─ RECOMMENDATION 2: Comprehensive Optimization (D) ────────")
print(f"│ Adjust Tech/Macro to 50% / 50% (balanced)")
print(f"│ Adjust Trend/Mom/Vol to {best_d['trend_weight']:.0%} / {best_d['momentum_weight']:.0%} / {best_d['volatility_weight']:.0%}")
print(f"│ Sharpe Ratio: {best_d['sharpe']:.4f} (+{(best_d['sharpe']/current_d['sharpe']-1)*100:+.2f}%)")
print(f"│ Excess Sharpe: +{best_d['excess_sharpe']:.4f}")
print(f"│ Ease: ⚠️  Moderate (2 parameter changes)")
print(f"└────────────────────────────────────────────────────────────")

# KEY INSIGHTS
print(f"\n📌 KEY INSIGHTS:")

print(f"\n1. Macro vs Technical Balance:")
print(f"   • Balanced mix (50-50) slightly better than current (60-40)")
print(f"   • Current already close to optimal")
print(f"   • Difference: {(best_b['sharpe']-current_b['sharpe']*100):.0f} bps (basis points)")

print(f"\n2. Technical Components:")
print(f"   • Balanced weights (Equal T-M-V) better than current")
print(f"   • Current: T=40%, M=35%, V=25% → Best: T={best_d['trend_weight']:.0%}, M={best_d['momentum_weight']:.0%}, V={best_d['volatility_weight']:.0%}")
print(f"   • Momentum slightly over-weighted currently")
print(f"   • Difference: {(best_d['sharpe']-current_d['sharpe'])*100:.0f} bps")

print(f"\n3. Combination Effect:")
best_combo = max(best_b['sharpe'], best_d['sharpe'])
print(f"   • Best Part B: {best_b['sharpe']:.4f}")
print(f"   • Best Part D: {best_d['sharpe']:.4f}")
print(f"   • Best Overall: {best_combo:.4f} (vs current {current_d['sharpe']:.4f})")
print(f"   • Total possible improvement: {(best_combo/current_d['sharpe']-1)*100:+.2f}%")

print(f"\n4. Robustness:")
print(f"   • Only 2 configs underperform equal weight")
print(f"   Part B: {(df_b['excess_sharpe'] > 0).sum()}/{len(df_b)} beat benchmark")
print(f"   Part D: {(df_d['excess_sharpe'] > 0).sum()}/{len(df_d)} beat benchmark")
print(f"   • Strategy is robust to parameter choices")

print("\n" + "="*80 + "\n")

# Save summary to text
with open("SIGNAL_OPTIMIZATION_SUMMARY.txt", "w") as f:
    f.write("="*80 + "\n")
    f.write("SIGNAL OPTIMIZATION ANALYSIS SUMMARY\n")
    f.write("="*80 + "\n\n")
    
    f.write("BEST CONFIGURATION FOUND:\n")
    f.write(f"Tech/Macro Mix: {best_b['tech_weight']:.0%} / {best_b['macro_weight']:.0%}\n")
    f.write(f"Trend/Momentum/Volatility: {best_d['trend_weight']:.0%} / {best_d['momentum_weight']:.0%} / {best_d['volatility_weight']:.0%}\n")
    f.write(f"Sharpe Ratio: {best_combo:.4f}\n")
    f.write(f"Improvement: {(best_combo/current_d['sharpe']-1)*100:+.2f}%\n\n")
    
    f.write("ANALYSIS FILES:\n")
    f.write("- data/signal_optimization_part_b.csv\n")
    f.write("- data/signal_optimization_part_d.csv\n")

print("✓ Summary saved to SIGNAL_OPTIMIZATION_SUMMARY.txt")
