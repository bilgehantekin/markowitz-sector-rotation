"""
Create comparison visualization: Old vs New Configuration
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load sensitivity data
sensitivity_data = pd.read_csv("data/max_weight_sensitivity.csv")

# Extract old (0.25) and new (0.20) configurations
old_config = sensitivity_data[sensitivity_data["max_weight"] == 0.25].iloc[0]
new_config = sensitivity_data[sensitivity_data["max_weight"] == 0.20].iloc[0]

# Create comparison figure with 2x2 subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Configuration Comparison: MW 20% vs MW 25%", fontsize=17, fontweight="bold", y=0.995)

metrics = [
    ("Sharpe Ratio", old_config["sharpe"], new_config["sharpe"], "#2E86AB"),
    ("Annual Return (%)", old_config["ann_return"]*100, new_config["ann_return"]*100, "#06A77D"),
    ("Annual Volatility (%)", old_config["ann_vol"]*100, new_config["ann_vol"]*100, "#D62828"),
    ("Total Return (%)", old_config["total_return"], new_config["total_return"], "#F77F00")
]

for idx, (ax, (metric_name, old_val, new_val, color)) in enumerate(zip(axes.flat, metrics)):
    x_pos = np.arange(2)
    values = [old_val, new_val]
    bars = ax.bar(x_pos, values, color=[color, "#A23B72"], edgecolor="black", linewidth=2, width=0.6, alpha=0.85)
    
    # Add value labels on bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f"{val:.2f}",
               ha="center", va="bottom", fontsize=13, fontweight="bold")
    
    # Calculate improvement
    improvement = ((new_val / old_val) - 1) * 100
    
    ax.set_ylabel(metric_name, fontsize=13, fontweight="bold")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(["MW 25%\n(Current)", "MW 20%\n(Optimal)"], fontsize=11, fontweight="bold")
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    
    # Add improvement badge
    badge_color = "#06A77D" if improvement > 0 else "#D62828"
    badge_label = f"+{improvement:.2f}%" if improvement > 0 else f"{improvement:.2f}%"
    ax.text(0.98, 0.97, badge_label, transform=ax.transAxes,
           fontsize=12, fontweight="bold", ha="right", va="top",
           bbox=dict(boxstyle="round,pad=0.5", facecolor=badge_color, alpha=0.3, 
                    edgecolor=badge_color, linewidth=2))

plt.tight_layout()
plt.savefig("reports/configuration_comparison.png", dpi=300, bbox_inches="tight", 
           facecolor="white", edgecolor="none")
print("✓ Saved comparison PNG: reports/configuration_comparison.png")

plt.close()

# Create a performance metrics table visualization
fig, ax = plt.subplots(figsize=(12, 6))
ax.axis("tight")
ax.axis("off")

# Data for table
table_data = [
    ["Metric", "MW 25% (Current)", "MW 20% (Optimal)", "Improvement"],
    ["Sharpe Ratio", f"{old_config['sharpe']:.4f}", f"{new_config['sharpe']:.4f}", 
     f"+{((new_config['sharpe']/old_config['sharpe'])-1)*100:.2f}%"],
    ["Annual Return", f"{old_config['ann_return']*100:.2f}%", f"{new_config['ann_return']*100:.2f}%",
     f"+{(new_config['ann_return']-old_config['ann_return'])*100:.2f}%"],
    ["Annual Volatility", f"{old_config['ann_vol']*100:.2f}%", f"{new_config['ann_vol']*100:.2f}%",
     f"{(new_config['ann_vol']-old_config['ann_vol'])*100:.2f}%"],
    ["Total Return", f"{old_config['total_return']:.2f}%", f"{new_config['total_return']:.2f}%",
     f"+{(new_config['total_return']-old_config['total_return']):.2f}%"],
    ["Max Drawdown", f"{old_config['max_drawdown']:.2f}%", f"{new_config['max_drawdown']:.2f}%",
     f"{(new_config['max_drawdown']-old_config['max_drawdown']):.2f}%"],
]

table = ax.table(cellText=table_data, cellLoc="center", loc="center",
                colWidths=[0.25, 0.25, 0.25, 0.25])

table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 2.5)

# Style header row
for i in range(4):
    cell = table[(0, i)]
    cell.set_facecolor("#2E86AB")
    cell.set_text_props(weight="bold", color="white", size=12)

# Style data rows with alternating colors
for i in range(1, len(table_data)):
    for j in range(4):
        cell = table[(i, j)]
        if i % 2 == 0:
            cell.set_facecolor("#E8F4F8")
        else:
            cell.set_facecolor("#FFFFFF")
        
        # Highlight improvement column
        if j == 3:
            if "+" in table_data[i][j]:
                cell.set_facecolor("#D4EDDA")
            elif "-" in table_data[i][j] and "Drawdown" not in table_data[i][0]:
                cell.set_facecolor("#F8D7DA")
        
        cell.set_text_props(weight="bold" if j == 0 else "normal", size=11)

plt.title("Performance Metrics Comparison", fontsize=16, fontweight="bold", pad=20)
plt.savefig("reports/metrics_comparison_table.png", dpi=300, bbox_inches="tight",
           facecolor="white", edgecolor="none")
print("✓ Saved metrics table PNG: reports/metrics_comparison_table.png")

plt.close()

print("\n" + "="*70)
print("PRESENTATION READY - 3 Images Created:")
print("="*70)
print("1. max_weight_presentation.png - Main sensitivity curve (clean)")
print("2. configuration_comparison.png - Bar charts comparing MW 25% vs 20%")
print("3. metrics_comparison_table.png - Performance metrics table")
print("\nAll files saved to: reports/")
print("="*70)
