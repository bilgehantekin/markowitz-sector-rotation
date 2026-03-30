"""
Sensitivity Analysis Report
===========================
Generate summary tables comparing different parameter configurations
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Read sensitivity data
data_dir = Path("data")
ra_ts_df = pd.read_csv(data_dir / "sensitivity_ra_ts.csv")
mw_lb_df = pd.read_csv(data_dir / "sensitivity_mw_lb.csv")

print("\n" + "="*80)
print("PARAMETER SENSITIVITY ANALYSIS REPORT")
print("="*80)

# ════════════════════════════════════════════════════════════════════════════
# PART 1: RISK AVERSION × TILT STRENGTH
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("1. RISK AVERSION × TILT STRENGTH ANALYSIS")
print("─"*80)

# Pivot for display
ra_ts_pivot_sharpe = ra_ts_df.pivot(
    index="risk_aversion", 
    columns="tilt_strength", 
    values="sharpe"
).round(4)

ra_ts_pivot_excess = ra_ts_df.pivot(
    index="risk_aversion", 
    columns="tilt_strength", 
    values="excess_sharpe"
).round(4)

print("\n📊 Sharpe Ratio by Risk Aversion & Tilt Strength:")
print(ra_ts_pivot_sharpe.to_string())

print("\n💰 Excess Sharpe by Risk Aversion & Tilt Strength:")
print(ra_ts_pivot_excess.to_string())

# Find best combination
best_ra_ts_idx = ra_ts_df['sharpe'].idxmax()
best_ra_ts = ra_ts_df.loc[best_ra_ts_idx]
print(f"\n✅ Best Configuration (Risk Aversion × Tilt Strength):")
print(f"   Risk Aversion: {best_ra_ts['risk_aversion']:.1f}")
print(f"   Tilt Strength: {best_ra_ts['tilt_strength']:.2f}")
print(f"   Sharpe Ratio: {best_ra_ts['sharpe']:.4f}")
print(f"   Excess Sharpe: {best_ra_ts['excess_sharpe']:.4f}")

# ════════════════════════════════════════════════════════════════════════════
# PART 2: MAX WEIGHT × LOOKBACK
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("2. MAX WEIGHT × LOOKBACK PERIOD ANALYSIS")
print("─"*80)

# Pivot for display
mw_lb_pivot_sharpe = mw_lb_df.pivot(
    index="max_weight", 
    columns="lookback", 
    values="sharpe"
).round(4)

mw_lb_pivot_excess = mw_lb_df.pivot(
    index="max_weight", 
    columns="lookback", 
    values="excess_sharpe"
).round(4)

print("\n📊 Sharpe Ratio by Max Weight & Lookback:")
print(mw_lb_pivot_sharpe.to_string())

print("\n💰 Excess Sharpe by Max Weight & Lookback:")
print(mw_lb_pivot_excess.to_string())

# Find best combination
best_mw_lb_idx = mw_lb_df['sharpe'].idxmax()
best_mw_lb = mw_lb_df.loc[best_mw_lb_idx]
print(f"\n✅ Best Configuration (Max Weight × Lookback):")
print(f"   Max Weight: {best_mw_lb['max_weight']:.2f} ({best_mw_lb['max_weight']*100:.0f}%)")
print(f"   Lookback: {best_mw_lb['lookback']:.0f} days")
print(f"   Sharpe Ratio: {best_mw_lb['sharpe']:.4f}")
print(f"   Excess Sharpe: {best_mw_lb['excess_sharpe']:.4f}")

# ════════════════════════════════════════════════════════════════════════════
# PART 3: KEY INSIGHTS
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("3. KEY FINDINGS FOR PRESENTATION")
print("─"*80)

# Impact of max_weight
print("\n📌 Max Weight Parameter Impact:")
for mw in sorted(mw_lb_df['max_weight'].unique()):
    subset = mw_lb_df[mw_lb_df['max_weight'] == mw]
    avg_sharpe = subset['sharpe'].mean()
    avg_excess = subset['excess_sharpe'].mean()
    print(f"   Max Weight {mw:.0%}: Avg Sharpe={avg_sharpe:.4f}, Avg Excess={avg_excess:.4f}")

# Impact of risk_aversion
print("\n📌 Risk Aversion Parameter Impact:")
for ra in sorted(ra_ts_df['risk_aversion'].unique()):
    subset = ra_ts_df[ra_ts_df['risk_aversion'] == ra]
    avg_sharpe = subset['sharpe'].mean()
    avg_excess = subset['excess_sharpe'].mean()
    print(f"   Risk Aversion {ra:.1f}: Avg Sharpe={avg_sharpe:.4f}, Avg Excess={avg_excess:.4f}")

# Impact of tilt_strength
print("\n📌 Tilt Strength Parameter Impact:")
for ts in sorted(ra_ts_df['tilt_strength'].unique()):
    subset = ra_ts_df[ra_ts_df['tilt_strength'] == ts]
    avg_sharpe = subset['sharpe'].mean()
    avg_excess = subset['excess_sharpe'].mean()
    print(f"   Tilt Strength {ts:.2f}: Avg Sharpe={avg_sharpe:.4f}, Avg Excess={avg_excess:.4f}")

# Current vs Best
print("\n📌 Current Configuration vs Best Found:")
current_ra = 5.0
current_ts = 0.5
current_mw = 0.25
current_lb = 252

current_ra_ts = ra_ts_df[(ra_ts_df['risk_aversion'] == current_ra) & 
                          (ra_ts_df['tilt_strength'] == current_ts)].iloc[0]
current_mw_lb = mw_lb_df[(mw_lb_df['max_weight'] == current_mw) & 
                          (mw_lb_df['lookback'] == current_lb)].iloc[0]

# Average of current configs
current_sharpe_ra_ts = current_ra_ts['sharpe']
current_sharpe_mw_lb = current_mw_lb['sharpe']
current_avg_sharpe = (current_sharpe_ra_ts + current_sharpe_mw_lb) / 2

best_overall_idx = ra_ts_df['sharpe'].idxmax()
if mw_lb_df.loc[mw_lb_df['sharpe'].idxmax(), 'sharpe'] > best_overall_idx:
    best_overall_sharpe = mw_lb_df['sharpe'].max()
else:
    best_overall_sharpe = ra_ts_df['sharpe'].max()

print(f"\n   Current (RA=5.0, TS=0.5, MW=25%, LB=252):")
print(f"     Sharpe from RA×TS analysis: {current_sharpe_ra_ts:.4f}")
print(f"     Sharpe from MW×LB analysis: {current_sharpe_mw_lb:.4f}")

print(f"\n   Best Found Overall:")
print(f"     Sharpe: {best_overall_sharpe:.4f}")
print(f"     Improvement: {(best_overall_sharpe - current_avg_sharpe)*100:.2f}%")

# ════════════════════════════════════════════════════════════════════════════
# PART 4: ROBUSTNESS CHECK
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("4. ROBUSTNESS: HOW MANY CONFIGS BEAT BENCHMARK?")
print("─"*80)

ra_ts_beat = (ra_ts_df['excess_sharpe'] > 0).sum()
ra_ts_total = len(ra_ts_df)
ra_ts_pct = ra_ts_beat / ra_ts_total * 100

mw_lb_beat = (mw_lb_df['excess_sharpe'] > 0).sum()
mw_lb_total = len(mw_lb_df)
mw_lb_pct = mw_lb_beat / mw_lb_total * 100

print(f"\n✓ RA × TS: {ra_ts_beat}/{ra_ts_total} configurations beat benchmark ({ra_ts_pct:.1f}%)")
print(f"✓ MW × LB: {mw_lb_beat}/{mw_lb_total} configurations beat benchmark ({mw_lb_pct:.1f}%)")

combined_beat = ((ra_ts_df['excess_sharpe'] > 0).sum() + (mw_lb_df['excess_sharpe'] > 0).sum())
combined_total = len(ra_ts_df) + len(mw_lb_df)
combined_pct = combined_beat / combined_total * 100
print(f"✓ Combined: {combined_beat}/{combined_total} configurations beat benchmark ({combined_pct:.1f}%)")

print("\n" + "="*80 + "\n")
