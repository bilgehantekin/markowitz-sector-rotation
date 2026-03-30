import pandas as pd

df = pd.read_csv('/Users/bilgehan/Desktop/yap471_project/data/final_weights_history.csv', index_col=0)

print("=" * 130)
print("FIRST YEAR (2017): Monthly Rebalancing Weights")
print("=" * 130)
print()
first_12 = df.head(12)
for date in first_12.index[:12]:
    row = first_12.loc[date]
    non_zero = row[row > 0.001]
    print(f"{date}:")
    for ticker, weight in non_zero.items():
        print(f"  {ticker:12s}: {weight*100:6.2f}%")
    print()

print("\n" + "=" * 130)
print("MIDDLE PERIOD (2021): Monthly Rebalancing Weights")
print("=" * 130)
print()
mid_idx = len(df) // 2
mid_12 = df.iloc[mid_idx-6:mid_idx+6]
for date in mid_12.index:
    row = mid_12.loc[date]
    non_zero = row[row > 0.001]
    print(f"{date}:")
    for ticker, weight in non_zero.items():
        print(f"  {ticker:12s}: {weight*100:6.2f}%")
    print()

print("\n" + "=" * 130)
print("LAST YEAR (2025-2026): Monthly Rebalancing Weights")
print("=" * 130)
print()
last_12 = df.tail(12)
for date in last_12.index:
    row = last_12.loc[date]
    non_zero = row[row > 0.001]
    print(f"{date}:")
    for ticker, weight in non_zero.items():
        print(f"  {ticker:12s}: {weight*100:6.2f}%")
    print()

print("\n" + "=" * 130)
print("SUMMARY STATISTICS")
print("=" * 130)
print("\nAverage Weight by Stock (all periods):")
avg_weights = df.mean()
avg_weights_sorted = avg_weights.sort_values(ascending=False)
for ticker, weight in avg_weights_sorted.items():
    if weight > 0.001:
        print(f"  {ticker:12s}: {weight*100:6.2f}%")
