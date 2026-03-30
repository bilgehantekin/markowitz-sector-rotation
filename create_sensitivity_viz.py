"""
Max Weight Sensitivity Analysis Visualization
==============================================
Create publication-ready PNG for presentationпа
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from pathlib import Path

# Load data
data = pd.read_csv("data/max_weight_sensitivity.csv")

# Create figure with subplots
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

# Color scheme
color_sharpe = "#1f77b4"  # Blue
color_vol = "#ff7f0e"    # Orange
color_optimal = "#d62728" # Red
color_current = "#2ca02c" # Green

# ============================================================================
# SUBPLOT 1: Main Sharpe Ratio vs Max Weight
# ============================================================================
ax1 = fig.add_subplot(gs[0, :])

x = data["max_weight"].values * 100  # Convert to percentage
y_sharpe = data["sharpe"].values
y_bench = data["bench_sharpe"].values

# Find optimal point
optimal_idx = y_sharpe.argmax()
optimal_mw = data["max_weight"].iloc[optimal_idx] * 100
optimal_sharpe = y_sharpe[optimal_idx]
current_mw = 25  # Current value
current_sharpe = data[data["max_weight"] == 0.25]["sharpe"].values[0]

# Main line plot
ax1.plot(x, y_sharpe, "o-", linewidth=3, markersize=10, color=color_sharpe, label="Strategy Sharpe", zorder=3)
ax1.axhline(y=y_bench[0], color="gray", linestyle="--", linewidth=2, label="Benchmark Sharpe (1/N)", alpha=0.7)

# Highlight optimal point
ax1.scatter([optimal_mw], [optimal_sharpe], s=400, color=color_optimal, marker="*", zorder=5, edgecolor="black", linewidth=2)
ax1.annotate(
    f"OPTIMAL\nMW = {optimal_mw:.0f}%\nSharpe = {optimal_sharpe:.4f}",
    xy=(optimal_mw, optimal_sharpe),
    xytext=(optimal_mw + 10, optimal_sharpe + 0.15),
    fontsize=12,
    fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.5", facecolor=color_optimal, alpha=0.2, edgecolor=color_optimal, linewidth=2),
    arrowprops=dict(arrowstyle="->", color=color_optimal, lw=2),
    zorder=6
)

# Highlight current point
ax1.scatter([current_mw], [current_sharpe], s=300, color=color_current, marker="s", zorder=5, edgecolor="black", linewidth=2)
ax1.annotate(
    f"CURRENT\nMW = {current_mw:.0f}%\nSharpe = {current_sharpe:.4f}",
    xy=(current_mw, current_sharpe),
    xytext=(current_mw - 25, current_sharpe - 0.15),
    fontsize=11,
    fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.5", facecolor=color_current, alpha=0.2, edgecolor=color_current, linewidth=2),
    arrowprops=dict(arrowstyle="->", color=color_current, lw=2),
    zorder=6
)

ax1.set_xlabel("Maximum Weight per Asset (%)", fontsize=13, fontweight="bold")
ax1.set_ylabel("Sharpe Ratio", fontsize=13, fontweight="bold")
ax1.set_title("Max Weight Sensitivity Analysis: Strategy Sharpe Ratio", fontsize=15, fontweight="bold", pad=20)
ax1.grid(True, alpha=0.3, linestyle="--")
ax1.legend(fontsize=11, loc="lower left")
ax1.set_xlim(5, 105)
ax1.set_ylim(1.4, 2.2)

# Format x-axis
ax1.set_xticks(np.arange(10, 110, 10))
ax1.set_xticklabels([f"{int(x)}%" for x in np.arange(10, 110, 10)])

# ============================================================================
# SUBPLOT 2: Return vs Volatility Trade-off
# ============================================================================
ax2 = fig.add_subplot(gs[1, 0])

ann_ret = data["ann_return"].values * 100
ann_vol = data["ann_vol"].values * 100

scatter = ax2.scatter(ann_vol, ann_ret, s=200, c=x, cmap="viridis", edgecolor="black", linewidth=1.5, zorder=3)

# Add labels for key points
for i, mw in enumerate(data["max_weight"].values):
    if mw in [0.1, 0.2, 0.25, 0.35, 0.5, 1.0]:
        ax2.annotate(f"{mw*100:.0f}%", (ann_vol[i], ann_ret[i]), 
                    fontsize=9, ha="center", va="bottom", fontweight="bold")

# Highlight optimal and current
ax2.scatter([ann_vol[optimal_idx]], [ann_ret[optimal_idx]], s=300, color=color_optimal, marker="*", 
           edgecolor="black", linewidth=2, zorder=5)
current_idx = (data["max_weight"] == 0.25).argmax()
ax2.scatter([ann_vol[current_idx]], [ann_ret[current_idx]], s=250, color=color_current, marker="s", 
           edgecolor="black", linewidth=2, zorder=5)

ax2.set_xlabel("Annual Volatility (%)", fontsize=12, fontweight="bold")
ax2.set_ylabel("Annual Return (%)", fontsize=12, fontweight="bold")
ax2.set_title("Risk-Return Profile", fontsize=13, fontweight="bold", pad=15)
ax2.grid(True, alpha=0.3, linestyle="--")
cbar = plt.colorbar(scatter, ax=ax2)
cbar.set_label("Max Weight (%)", fontsize=10, fontweight="bold")

# ============================================================================
# SUBPLOT 3: Excess Sharpe vs Max Weight
# ============================================================================
ax3 = fig.add_subplot(gs[1, 1])

excess_sharpe = data["excess_sharpe"].values
colors = [color_optimal if mw == optimal_mw/100 else color_current if mw == 0.25 else color_sharpe 
          for mw in data["max_weight"].values]

bars = ax3.bar(x, excess_sharpe, width=8, color=colors, edgecolor="black", linewidth=1.5, alpha=0.8)

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars, excess_sharpe)):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
            f"{val:.3f}",
            ha="center", va="bottom" if val > 0 else "top", fontsize=9, fontweight="bold")

# Add improvement annotation
improvement = ((optimal_sharpe / current_sharpe) - 1) * 100
ax3.text(0.98, 0.97, f"Improvement:\n+{improvement:.2f}%", 
        transform=ax3.transAxes, fontsize=11, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.7", facecolor="yellow", alpha=0.3, edgecolor="black", linewidth=2),
        ha="right", va="top")

ax3.axhline(y=0, color="black", linestyle="-", linewidth=0.8)
ax3.set_xlabel("Maximum Weight per Asset (%)", fontsize=12, fontweight="bold")
ax3.set_ylabel("Excess Sharpe vs Benchmark", fontsize=12, fontweight="bold")
ax3.set_title("Outperformance vs Equal-Weight Benchmark", fontsize=13, fontweight="bold", pad=15)
ax3.grid(True, alpha=0.3, linestyle="--", axis="y")
ax3.set_xlim(5, 105)
ax3.set_xticks(np.arange(10, 110, 10))
ax3.set_xticklabels([f"{int(x)}%" for x in np.arange(10, 110, 10)])

# ============================================================================
# Main title and summary
# ============================================================================
fig.suptitle(
    "Dynamic BIST Rotation Strategy: Max Weight Sensitivity Analysis",
    fontsize=18,
    fontweight="bold",
    y=0.98
)

# Summary text box
summary_text = f"""
KEY FINDINGS:
• Optimal Max Weight: {optimal_mw:.0f}% (Sharpe: {optimal_sharpe:.4f})
• Current Max Weight: {current_mw:.0f}% (Sharpe: {current_sharpe:.4f})
• Performance Gain: +{improvement:.2f}% Sharpe improvement by using {optimal_mw:.0f}%
• Optimal Strategy: Better balance between diversification and signal strength
• Risk Reduction: Volatility {data.loc[data['max_weight']==optimal_mw/100, 'ann_vol'].values[0]*100:.2f}% vs {data.loc[data['max_weight']==0.25, 'ann_vol'].values[0]*100:.2f}% at current setting
"""

fig.text(0.5, -0.02, summary_text, ha="center", fontsize=11, 
         bbox=dict(boxstyle="round,pad=1", facecolor="lightblue", alpha=0.3, edgecolor="black", linewidth=2),
         family="monospace")

# Save figure
output_path = Path("reports/max_weight_sensitivity_analysis.png")
output_path.parent.mkdir(exist_ok=True)
plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
print(f"✓ Saved publication-ready visualization to: {output_path}")
print(f"  Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
print(f"  Resolution: 300 DPI (suitable for presentations)")

plt.close()

# Also create a simple version without subplots
fig, ax = plt.subplots(figsize=(14, 8))

ax.plot(x, y_sharpe, "o-", linewidth=4, markersize=12, color=color_sharpe, label="Strategy Sharpe", zorder=3)
ax.axhline(y=y_bench[0], color="gray", linestyle="--", linewidth=2.5, label="Benchmark Sharpe (1/N)", alpha=0.7)

# Highlight optimal point
ax.scatter([optimal_mw], [optimal_sharpe], s=600, color=color_optimal, marker="*", zorder=5, edgecolor="black", linewidth=2.5)
ax.annotate(
    f"OPTIMAL\nMax Weight = {optimal_mw:.0f}%\nSharpe Ratio = {optimal_sharpe:.4f}\n(+{improvement:.2f}% vs current)",
    xy=(optimal_mw, optimal_sharpe),
    xytext=(optimal_mw + 12, optimal_sharpe + 0.18),
    fontsize=13,
    fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.6", facecolor=color_optimal, alpha=0.25, edgecolor=color_optimal, linewidth=2.5),
    arrowprops=dict(arrowstyle="->", color=color_optimal, lw=2.5),
    zorder=6
)

# Highlight current point
ax.scatter([current_mw], [current_sharpe], s=400, color=color_current, marker="s", zorder=5, edgecolor="black", linewidth=2.5)
ax.annotate(
    f"CURRENT\nMax Weight = {current_mw:.0f}%\nSharpe Ratio = {current_sharpe:.4f}",
    xy=(current_mw, current_sharpe),
    xytext=(current_mw - 30, current_sharpe - 0.20),
    fontsize=12,
    fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.6", facecolor=color_current, alpha=0.25, edgecolor=color_current, linewidth=2.5),
    arrowprops=dict(arrowstyle="->", color=color_current, lw=2.5),
    zorder=6
)

ax.set_xlabel("Maximum Weight per Asset (%)", fontsize=14, fontweight="bold")
ax.set_ylabel("Sharpe Ratio", fontsize=14, fontweight="bold")
ax.set_title("Max Weight Sensitivity Analysis\nDynamic BIST Rotation Strategy", fontsize=16, fontweight="bold", pad=20)
ax.grid(True, alpha=0.25, linestyle="--", linewidth=1.5)
ax.legend(fontsize=13, loc="lower left", framealpha=0.95)
ax.set_xlim(5, 105)
ax.set_ylim(1.35, 2.2)
ax.set_xticks(np.arange(10, 110, 10))
ax.set_xticklabels([f"{int(x)}%" for x in np.arange(10, 110, 10)], fontsize=11)
ax.tick_params(axis="y", labelsize=11)

# Add shaded region for best performance zone
ax.axvspan(15, 30, alpha=0.1, color=color_optimal, label="Optimal Range")
ax.legend(fontsize=13, loc="lower left", framealpha=0.95)

plt.tight_layout()
output_path_simple = Path("reports/max_weight_sensitivity_simple.png")
plt.savefig(output_path_simple, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
print(f"✓ Saved simple version to: {output_path_simple}")
print(f"  Size: {output_path_simple.stat().st_size / 1024 / 1024:.2f} MB")

plt.close()

print("\n" + "="*70)
print("SENSITIVITY ANALYSIS SUMMARY FOR PRESENTATION")
print("="*70)
print(f"\n📊 Optimal Configuration Found:")
print(f"   Max Weight: {optimal_mw:.0f}% (vs current {current_mw:.0f}%)")
print(f"   Sharpe Ratio: {optimal_sharpe:.4f} (vs current {current_sharpe:.4f})")
print(f"   Performance Gain: +{improvement:.2f}%")
print(f"\n📈 Risk Metrics at Optimal Setting:")
print(f"   Annual Return: {data.loc[data['max_weight']==optimal_mw/100, 'ann_return'].values[0]*100:.2f}%")
print(f"   Annual Volatility: {data.loc[data['max_weight']==optimal_mw/100, 'ann_vol'].values[0]*100:.2f}%")
print(f"   Max Drawdown: {data.loc[data['max_weight']==optimal_mw/100, 'max_drawdown'].values[0]:.2f}%")
print(f"   Total Return: {data.loc[data['max_weight']==optimal_mw/100, 'total_return'].values[0]:.2f}%")
print(f"\n💡 Insight:")
print(f"   Lower concentration (MW=20%) balances signal strength with diversification,")
print(f"   reducing portfolio volatility while maintaining strong excess returns.")
print("="*70)
