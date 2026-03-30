"""
Create clean presentation PNG for max weight results
No annotations - presentation will explain
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
data = pd.read_csv("data/max_weight_sensitivity.csv")

# Create simple, clean figure
fig, ax = plt.subplots(figsize=(14, 8))

x = data["max_weight"].values * 100
y_sharpe = data["sharpe"].values
y_bench = data["bench_sharpe"].values

# Optimal values
optimal_idx = y_sharpe.argmax()
optimal_mw = data["max_weight"].iloc[optimal_idx] * 100
optimal_sharpe = y_sharpe[optimal_idx]

# Plot
ax.plot(x, y_sharpe, "o-", linewidth=4, markersize=14, color="#2E86AB", 
        label="Strategy Sharpe Ratio", zorder=3)
ax.axhline(y=y_bench[0], color="#666666", linestyle="--", linewidth=2.5, 
          label="Benchmark (1/N Equal Weight)", alpha=0.7)

# Highlight optimal point (20%)
ax.scatter([optimal_mw], [optimal_sharpe], s=700, color="#A23B72", marker="*", 
          zorder=5, edgecolor="black", linewidth=2, label=f"Optimal: {optimal_mw:.0f}%")

# Fill area under curve
ax.fill_between(x, y_sharpe, alpha=0.1, color="#2E86AB")

# Grid and labels
ax.set_xlabel("Maximum Weight per Asset (%)", fontsize=15, fontweight="bold")
ax.set_ylabel("Sharpe Ratio", fontsize=15, fontweight="bold")
ax.set_title("Max Weight Sensitivity Analysis", fontsize=17, fontweight="bold", pad=20)
ax.grid(True, alpha=0.25, linestyle="--", linewidth=1.2)
ax.legend(fontsize=12, loc="lower left", framealpha=0.95, edgecolor="black", fancybox=True)

ax.set_xlim(5, 105)
ax.set_ylim(1.35, 2.2)
ax.set_xticks(np.arange(10, 110, 10))
ax.set_xticklabels([f"{int(x)}%" for x in np.arange(10, 110, 10)], fontsize=12)
ax.tick_params(axis="y", labelsize=12)

plt.tight_layout()
plt.savefig("reports/max_weight_presentation.png", dpi=300, bbox_inches="tight", 
           facecolor="white", edgecolor="none")
print("✓ Saved presentation PNG: reports/max_weight_presentation.png")

plt.close()
