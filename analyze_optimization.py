import pandas as pd

# Load optimization results
df = pd.read_csv("data/comprehensive_optimization_full.csv")

print("\n" + "="*100)
print("COMPREHENSIVE OPTIMIZATION - 720 COMBINATIONS TESTED ✓")
print("="*100 + "\n")

print(f"Total tested: {len(df)} combinations\n")

# Top 15 by Sharpe
print("TOP 15 BY SHARPE RATIO:")
print("─" * 100)
top_sharpe = df.nlargest(15, "sharpe")[["tech_weight", "macro_weight", "risk_aversion", "tilt_strength", 
                                         "max_weight", "sharpe", "excess_sharpe", "ann_return", "ann_vol"]].copy()
for i, (idx, row) in enumerate(top_sharpe.iterrows()):
    mark = "🏆" if i == 0 else "  "
    print(f"{mark} TW={row['tech_weight']:.1f} MW={row['max_weight']:.2f} RA={row['risk_aversion']:4.1f} TS={row['tilt_strength']:.1f} | "
          f"Sharpe={row['sharpe']:.4f} | Excess={row['excess_sharpe']:.4f} | Ret={row['ann_return']:.2%} | Vol={row['ann_vol']:.2%}")

print("\n" + "="*100)
print("🏆 BEST BY SHARPE RATIO:")
print("="*100 + "\n")

best = df.loc[df['sharpe'].idxmax()]
print(f"Tech Weight:      {best['tech_weight']:.1f}")
print(f"Macro Weight:     {best['macro_weight']:.1f}")
print(f"Risk Aversion:    {best['risk_aversion']:.1f}")
print(f"Tilt Strength:    {best['tilt_strength']:.1f}")
print(f"Max Weight:       {best['max_weight']:.2f}")
print(f"\nSharpe Ratio:     {best['sharpe']:.4f}")
print(f"Excess Sharpe:    {best['excess_sharpe']:.4f} ⭐")
print(f"Ann. Return:      {best['ann_return']:.2%}")
print(f"Ann. Vol:         {best['ann_vol']:.2%}")
print(f"Max DD:           {best['max_dd']:.2%}")
print(f"Calmar:           {best['calmar']:.4f}")

# Top by Excess Sharpe
print("\n" + "="*100)
print("🥈 BEST BY EXCESS SHARPE:")
print("="*100 + "\n")

best_excess = df.loc[df['excess_sharpe'].idxmax()]
print(f"Tech Weight:      {best_excess['tech_weight']:.1f}")
print(f"Macro Weight:     {best_excess['macro_weight']:.1f}")
print(f"Risk Aversion:    {best_excess['risk_aversion']:.1f}")
print(f"Tilt Strength:    {best_excess['tilt_strength']:.1f}")
print(f"Max Weight:       {best_excess['max_weight']:.2f}")
print(f"\nSharpe Ratio:     {best_excess['sharpe']:.4f}")
print(f"Excess Sharpe:    {best_excess['excess_sharpe']:.4f} ⭐")
print(f"Ann. Return:      {best_excess['ann_return']:.2%}")
print(f"Ann. Vol:         {best_excess['ann_vol']:.2%}")
print(f"Max DD:           {best_excess['max_dd']:.2%}")
print(f"Calmar:           {best_excess['calmar']:.4f}")

# Compare our quick optimization finding
print("\n" + "="*100)
print("QUICK OPT FINDING (TW=0.30, MW=0.20, RA=5.0) - ALL TILT STRENGTHS:")
print("="*100 + "\n")

found = df[(df['tech_weight'] == 0.30) & (df['max_weight'] == 0.20) & (df['risk_aversion'] == 5.0)].sort_values('sharpe', ascending=False)
if not found.empty:
    for _, row in found.iterrows():
        print(f"TS={row['tilt_strength']:.1f} | Sharpe={row['sharpe']:.4f} | Excess={row['excess_sharpe']:.4f} | Return={row['ann_return']:.2%} | Vol={row['ann_vol']:.2%}")
else:
    print("Not found in dataset!")

print("\n" + "="*100)
print("SUMMARY:")
print("="*100 + "\n")

print(f"Current Config (TW=0.60, MW=0.20, RA=5.0, TS=0.0):   Sharpe ≈ 2.037")
print(f"Quick Opt Finding (TW=0.30, MW=0.20, RA=5.0, TS=0.0): Sharpe ≈ 2.055 (+0.88%)")
print(f"Comp. Opt Best (TW={best['tech_weight']:.1f}, MW={best['max_weight']:.2f}, RA={best['risk_aversion']:.1f}, TS={best['tilt_strength']:.1f}): Sharpe = {best['sharpe']:.4f} (+{((best['sharpe']/2.037)-1)*100:.2f}%)")
print()
